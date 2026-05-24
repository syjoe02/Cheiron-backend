import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from app.clients.clinicaltrials import ClinicalTrialsClient
from app.config import settings
from app.errors.error_code import ErrorCode
from app.errors.exceptions import AppException
from app.errors.handlers import app_exception_handler
from app.models.request import QueryRequest
from app.models.response import VisualizationResponse
from app.pipeline.api_builder import build_ct_params, build_ct_params_for_entity, get_phase_filter
from app.pipeline.data_fetcher import DataFetcher
from app.pipeline.query_parser import QueryIntent, QueryParser
from app.pipeline.response_builder import ResponseBuilder
from app.pipeline.transformer import Transformer
from app.pipeline.viz_selector import VizSelector

logger = logging.getLogger(__name__)

_http_client: httpx.AsyncClient | None = None
_openai_client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _http_client, _openai_client
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20),
    )
    _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    yield
    if _http_client:
        await _http_client.aclose()


app = FastAPI(
    title="ClinicalTrials.gov Query-to-Visualization Agent",
    version="0.1.0",
    description="First Agent",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_exception_handler(AppException, app_exception_handler)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}

# Main flows
@app.post("/query", response_model=VisualizationResponse)
async def query_endpoint(request: QueryRequest) -> VisualizationResponse:
    if _http_client is None or _openai_client is None:
        raise AppException(ErrorCode.SERVICE_NOT_READY)

    try:
        # Step 1: LLM query parsing (gpt-4.1-mini)
        parser = QueryParser(_openai_client, model=settings.fast_model)
        parsed = await parser.parse(
            request.query,
            overrides={
                "drug_name": request.drug_name,
                "condition": request.condition,
                "phase": request.phase,
                "sponsor": request.sponsor,
                "country": request.country,
                "start_year": request.start_year,
                "end_year": request.end_year,
            },
        )

        # Step 2: Build CT.gov API params
        ct_params = build_ct_params(parsed, request)
        phase_filter = get_phase_filter(request, parsed)

        # Merge LLM-extracted temporal entities; explicit request fields take priority.
        effective_request = request.model_copy(update={
            "start_year": request.start_year if request.start_year is not None else parsed.entities.start_year,
            "end_year": request.end_year if request.end_year is not None else parsed.entities.end_year,
        })

        # Step 3 & 4: Fetch data and transform
        ct_client = ClinicalTrialsClient(_http_client)
        fetcher = DataFetcher(ct_client)
        transformer = Transformer()

        comparison_entities = parsed.entities.comparison_entities
        comparison_dim = parsed.entities.comparison_dimension or "drug_name"
        phase_meta: dict = {}

        if (
            parsed.intent == QueryIntent.COMPARISON
            and comparison_entities
            and len(comparison_entities) >= 2
        ):
            # Fetch a separate dataset for each named entity
            entity_studies: dict[str, list] = {}
            for entity in comparison_entities:
                e_params = build_ct_params_for_entity(parsed, request, entity, comparison_dim)
                e_list, _ = await fetcher.fetch(e_params, max_results=request.max_results)
                entity_studies[entity] = e_list

            if not any(entity_studies.values()):
                raise AppException(ErrorCode.NO_CLINICAL_TRIALS)

            study_lookup = {}
            for e_list in entity_studies.values():
                for s in e_list:
                    nct_id = (
                        s.get("protocolSection", {})
                        .get("identificationModule", {})
                        .get("nctId")
                    )
                    if nct_id:
                        study_lookup[nct_id] = s

            total_count = sum(len(v) for v in entity_studies.values())
            _result = transformer.transform_comparison_entities(
                entity_studies, phase_filter, effective_request
            )
            transformed_data, citation_map = _result
            phase_meta = _result.phase_meta
        else:
            # Single-entity path (all non-comparison intents)
            studies, total_count = await fetcher.fetch(ct_params, max_results=request.max_results)

            if not studies:
                raise AppException(ErrorCode.NO_CLINICAL_TRIALS)

            study_lookup = {
                s["protocolSection"]["identificationModule"]["nctId"]: s
                for s in studies
                if s.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
            }
            _result = transformer.transform(
                parsed.intent, studies, phase_filter, effective_request
            )
            transformed_data, citation_map = _result
            phase_meta = _result.phase_meta

        # Step 5: LLM viz selection (gpt-4.1, sees schema only — no raw values)
        viz_selector = VizSelector(_openai_client, model=settings.smart_model)

        import pandas as pd  # local import to avoid top-level dep in tests
        if isinstance(transformed_data, pd.DataFrame):
            columns = list(transformed_data.columns)
            row_count = len(transformed_data)
            sample = transformed_data.iloc[0].to_dict() if row_count > 0 else {}
            # Strip list fields from sample (not serializable cleanly)
            sample = {k: v for k, v in sample.items() if not isinstance(v, list)}
        else:
            # Network graph dict
            columns = ["nodes", "edges"]
            row_count = len(transformed_data.get("edges", []))
            sample = {
                "node_count": len(transformed_data.get("nodes", [])),
                "edge_count": row_count,
            }

        viz_spec = await viz_selector.select(
            intent=parsed.intent,
            columns=columns,
            row_count=row_count,
            sample_row=sample,
            query_interpretation=parsed.query_interpretation,
        )

        # Step 6: Assemble final response with citations
        builder = ResponseBuilder()
        return builder.build(
            intent=parsed.intent,
            transformed_data=transformed_data,
            citation_map=citation_map,
            study_lookup=study_lookup,
            viz_spec_out=viz_spec,
            parsed_query=parsed,
            request=request,
            total_count=total_count,
            phase_meta=phase_meta,
        )

    except AppException:
        raise
    except Exception as e:
        logger.exception("Unhandled exception in /query: %s", e)
        raise AppException(ErrorCode.INTERNAL_SERVER_ERROR) from e
