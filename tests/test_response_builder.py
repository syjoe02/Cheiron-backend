import pandas as pd

from app.models.response import Citation, DataPoint, VisualizationResponse, VizSpec
from app.pipeline.query_parser import ParsedEntities, ParsedQuery, QueryIntent
from app.pipeline.response_builder import ResponseBuilder, build_citations
from app.pipeline.viz_selector import VizSpecOutput


def _make_study_lookup(sample_study: dict) -> dict:
    nct_id = sample_study["protocolSection"]["identificationModule"]["nctId"]
    return {nct_id: sample_study}


def _make_viz_spec_output(chart_type: str = "bar_chart", title: str = "Test Chart") -> VizSpecOutput:
    return VizSpecOutput(
        chart_type=chart_type,
        title=title,
        encoding={"x": {"field": "category", "type": "nominal"}, "y": {"field": "trial_count", "type": "quantitative"}},
    )


def _make_parsed_query(intent: QueryIntent = QueryIntent.DISTRIBUTION) -> ParsedQuery:
    return ParsedQuery(
        intent=intent,
        entities=ParsedEntities(),
        query_interpretation="Distribution of trials by phase",
        assumptions=[],
    )


def test_build_citations_extracts_excerpt(sample_study):
    lookup = _make_study_lookup(sample_study)
    citations = build_citations(["NCT12345678"], lookup)
    assert len(citations) == 1
    assert citations[0].nct_id == "NCT12345678"
    assert "Aspirin" in citations[0].excerpt
    assert len(citations[0].excerpt) <= 200


def test_build_citations_missing_nct_id(sample_study):
    lookup = _make_study_lookup(sample_study)
    citations = build_citations(["NCT99999999"], lookup)
    assert citations == []


def test_build_citations_respects_max(sample_study):
    lookup = _make_study_lookup(sample_study)
    nct_ids = ["NCT12345678"] * 10
    citations = build_citations(nct_ids, lookup, max_citations=3)
    assert len(citations) == 3


def test_response_builder_distribution(sample_study):
    from app.models.request import QueryRequest
    df = pd.DataFrame([
        {"category": "PHASE2", "trial_count": 5},
        {"category": "PHASE3", "trial_count": 3},
    ])
    citation_map = {"PHASE2": ["NCT12345678"], "PHASE3": []}
    lookup = _make_study_lookup(sample_study)

    builder = ResponseBuilder()
    req = QueryRequest(query="distribution by phase")
    result = builder.build(
        intent=QueryIntent.DISTRIBUTION,
        transformed_data=df,
        citation_map=citation_map,
        study_lookup=lookup,
        viz_spec_out=_make_viz_spec_output("bar_chart"),
        parsed_query=_make_parsed_query(),
        request=req,
        total_count=8,
    )

    assert isinstance(result, VisualizationResponse)
    assert result.visualization.type == "bar_chart"
    assert result.visualization.title == "Test Chart"
    assert len(result.visualization.data) == 2
    assert result.meta["trial_count"] == 1  # lookup has 1 study
    assert result.meta["total_matching"] == 8
    assert result.meta["source"] == "ClinicalTrials.gov v2 API"


def test_response_builder_empty_dataframe(sample_study):
    from app.models.request import QueryRequest
    builder = ResponseBuilder()
    req = QueryRequest(query="test")
    result = builder.build(
        intent=QueryIntent.DISTRIBUTION,
        transformed_data=pd.DataFrame(),
        citation_map={},
        study_lookup={},
        viz_spec_out=_make_viz_spec_output(),
        parsed_query=_make_parsed_query(),
        request=req,
        total_count=None,
    )
    assert result.visualization.data == []


def test_response_builder_network_graph(sample_study):
    from app.models.request import QueryRequest
    network_dict = {
        "nodes": [
            {"id": "Aspirin", "label": "Aspirin", "type": "intervention", "size": 50.0},
            {"id": "Heart Disease", "label": "Heart Disease", "type": "condition", "size": 40.0},
        ],
        "edges": [
            {"source": "Aspirin", "target": "Heart Disease", "weight": 3},
        ],
    }
    citation_map = {"Aspirin|Heart Disease": ["NCT12345678"]}
    lookup = _make_study_lookup(sample_study)

    builder = ResponseBuilder()
    req = QueryRequest(query="network of drugs and conditions")
    viz_out = _make_viz_spec_output("network_graph", "Drug-Condition Network")
    result = builder.build(
        intent=QueryIntent.RELATIONSHIP_NETWORK,
        transformed_data=network_dict,
        citation_map=citation_map,
        study_lookup=lookup,
        viz_spec_out=viz_out,
        parsed_query=_make_parsed_query(QueryIntent.RELATIONSHIP_NETWORK),
        request=req,
        total_count=10,
    )

    assert result.visualization.type == "network_graph"
    # First point should contain nodes list
    assert hasattr(result.visualization.data[0], "model_extra")
    nodes_point = result.visualization.data[0]
    assert "nodes" in nodes_point.model_extra
    # Edge points with citations
    edge_points = result.visualization.data[1:]
    assert len(edge_points) == 1
    assert edge_points[0].citations[0].nct_id == "NCT12345678"


def test_response_builder_filters_applied(sample_study):
    from app.models.request import QueryRequest
    from app.pipeline.query_parser import ParsedEntities, ParsedQuery
    req = QueryRequest(query="test", drug_name="Aspirin", condition="heart disease")
    parsed = ParsedQuery(
        intent=QueryIntent.DISTRIBUTION,
        entities=ParsedEntities(drug_name="Aspirin", condition="heart disease"),
        query_interpretation="test",
    )
    builder = ResponseBuilder()
    result = builder.build(
        intent=QueryIntent.DISTRIBUTION,
        transformed_data=pd.DataFrame([{"category": "PHASE2", "trial_count": 1}]),
        citation_map={},
        study_lookup={},
        viz_spec_out=_make_viz_spec_output(),
        parsed_query=parsed,
        request=req,
        total_count=None,
    )
    assert result.meta["filters_applied"]["drug_name"] == "Aspirin"
    assert result.meta["filters_applied"]["condition"] == "heart disease"


def test_response_builder_meta_includes_viz_extras(sample_study):
    from app.models.request import QueryRequest
    viz_out = VizSpecOutput(
        chart_type="time_series",
        title="Trend Chart",
        encoding={"x": {"field": "start_year"}, "y": {"field": "trial_count"}},
        sort_order="ascending",
        time_granularity="year",
        units="trials",
    )
    req = QueryRequest(query="trend over time")
    builder = ResponseBuilder()
    result = builder.build(
        intent=QueryIntent.TREND_OVER_TIME,
        transformed_data=pd.DataFrame([{"start_year": 2020, "trial_count": 5}]),
        citation_map={},
        study_lookup={},
        viz_spec_out=viz_out,
        parsed_query=_make_parsed_query(QueryIntent.TREND_OVER_TIME),
        request=req,
        total_count=None,
    )
    assert result.meta["sort_order"] == "ascending"
    assert result.meta["time_granularity"] == "year"
    assert result.meta["units"] == "trials"


def test_viz_spec_valid_types():
    for chart_type in ["bar_chart", "grouped_bar_chart", "time_series", "scatter_plot", "histogram", "network_graph"]:
        spec = VizSpec(type=chart_type, title="T", encoding={}, data=[])
        assert spec.type == chart_type


def test_data_point_allows_extra_fields():
    point = DataPoint(phase="PHASE2", trial_count=42, citations=[])
    assert point.model_extra["phase"] == "PHASE2"
    assert point.model_extra["trial_count"] == 42


def test_citation_model():
    c = Citation(nct_id="NCT12345678", excerpt="Phase 2 study of Aspirin")
    assert c.nct_id == "NCT12345678"
    assert "Aspirin" in c.excerpt
