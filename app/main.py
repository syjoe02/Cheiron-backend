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
from app.pipeline.api_builder import build_ct_params, get_phase_filter
from app.pipeline.data_fetcher import DataFetcher
from app.pipeline.query_parser import QueryParser
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

        # Step 3: Fetch data from ClinicalTrials.gov
        ct_client = ClinicalTrialsClient(_http_client)
        fetcher = DataFetcher(ct_client)
        studies, total_count = await fetcher.fetch(ct_params, max_results=request.max_results)

        if not studies:
            raise AppException(ErrorCode.NO_CLINICAL_TRIALS)

        # Build study lookup dict for citation resolution
        study_lookup = {
            s["protocolSection"]["identificationModule"]["nctId"]: s
            for s in studies
            if s.get("protocolSection", {}).get("identificationModule", {}).get("nctId")
        }

        # Step 4: ClinicalTrials raw JSON to chart data (pandas / networkx)
        transformer = Transformer()
        transformed_data, citation_map = transformer.transform(
            parsed.intent, studies, phase_filter, request
        )

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
        )

    except AppException:
        raise
    except Exception as e:
        logger.exception("Unhandled exception in /query: %s", e)
        raise AppException(ErrorCode.INTERNAL_SERVER_ERROR) from e
