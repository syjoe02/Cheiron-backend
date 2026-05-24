from typing import Any

import pandas as pd

from app.models.request import QueryRequest
from app.models.response import Citation, DataPoint, VisualizationResponse, VizSpec
from app.pipeline.query_parser import ParsedQuery, QueryIntent
from app.pipeline.viz_selector import VizSpecOutput


def build_citations(
    nct_ids: list[str],
    study_lookup: dict[str, dict[str, Any]],
    max_citations: int = 5,
) -> list[Citation]:
    citations = []
    for nct_id in nct_ids[:max_citations]:
        study = study_lookup.get(nct_id)
        if not study:
            continue
        brief_title = (
            study.get("protocolSection", {})
            .get("identificationModule", {})
            .get("briefTitle", "")
        )
        citations.append(Citation(nct_id=nct_id, excerpt=brief_title[:200]))
    return citations


class ResponseBuilder:
    def build(
        self,
        intent: QueryIntent,
        transformed_data: Any,
        citation_map: dict[str, list[str]],
        study_lookup: dict[str, dict[str, Any]],
        viz_spec_out: VizSpecOutput,
        parsed_query: ParsedQuery,
        request: QueryRequest,
        total_count: int | None,
    ) -> VisualizationResponse:
        if intent == QueryIntent.RELATIONSHIP_NETWORK:
            data_points = self._build_network_points(
                transformed_data, citation_map, study_lookup
            )
        else:
            data_points = self._build_tabular_points(
                transformed_data, citation_map, study_lookup
            )

        viz = VizSpec(
            type=viz_spec_out.chart_type,  # type: ignore[arg-type]
            title=viz_spec_out.title,
            encoding=viz_spec_out.encoding,
            data=data_points,
        )

        e = parsed_query.entities
        filters_applied = {
            k: v for k, v in {
                "drug_name": request.drug_name or e.drug_name,
                "condition": request.condition or e.condition,
                "phase": request.phase or e.phase,
                "sponsor": request.sponsor or e.sponsor,
                "country": request.country or e.country,
                "start_year": request.start_year or e.start_year,
                "end_year": request.end_year or e.end_year,
            }.items() if v is not None
        }

        all_assumptions = (parsed_query.assumptions or []) + (viz_spec_out.assumptions or [])

        meta: dict[str, Any] = {
            "filters_applied": filters_applied,
            "source": "ClinicalTrials.gov v2 API",
            "query_interpretation": parsed_query.query_interpretation,
            "assumptions": all_assumptions,
            "trial_count": len(study_lookup),
            "total_matching": total_count,
        }

        if viz_spec_out.sort_order:
            meta["sort_order"] = viz_spec_out.sort_order
        if viz_spec_out.time_granularity:
            meta["time_granularity"] = viz_spec_out.time_granularity
        if viz_spec_out.units:
            meta["units"] = viz_spec_out.units

        return VisualizationResponse(visualization=viz, meta=meta)

    def _build_tabular_points(
        self,
        df: pd.DataFrame,
        citation_map: dict[str, list[str]],
        study_lookup: dict[str, dict[str, Any]],
    ) -> list[DataPoint]:
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return []

        points = []
        for _, row in df.iterrows():
            row_dict = {
                k: (int(v) if hasattr(v, "item") else v)
                for k, v in row.to_dict().items()
                if not isinstance(v, list)  # skip list fields from correlation
            }

            # Try to find the citation key from the first column value
            first_val = str(list(row.to_dict().values())[0])
            nct_ids = citation_map.get(first_val, [])

            # For scatter/correlation, nct_id is the key
            if "nct_id" in row_dict:
                nct_ids = citation_map.get(str(row_dict["nct_id"]), [])

            citations = build_citations(nct_ids, study_lookup)
            points.append(DataPoint(**row_dict, citations=citations))

        return points

    def _build_network_points(
        self,
        network_dict: dict[str, Any],
        citation_map: dict[str, list[str]],
        study_lookup: dict[str, dict[str, Any]],
    ) -> list[DataPoint]:
        if not network_dict:
            return []

        edge_points = []
        for edge in network_dict.get("edges", []):
            key = f"{edge['source']}|{edge['target']}"
            nct_ids = citation_map.get(key, [])
            edge_points.append(DataPoint(**edge, citations=build_citations(nct_ids, study_lookup)))

        # Embed the nodes list as the first data point (frontend uses this to render graph)
        nodes_point = DataPoint(
            nodes=network_dict.get("nodes", []),
            citations=[],
        )

        return [nodes_point] + edge_points
