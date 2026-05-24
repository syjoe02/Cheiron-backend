import pytest

from app.models.request import QueryRequest
from app.pipeline.api_builder import PHASE_MAP, build_ct_params, get_phase_filter
from app.pipeline.query_parser import ParsedEntities, ParsedQuery, QueryIntent


def make_parsed(
    intent: QueryIntent = QueryIntent.RANKING,
    drug: str | None = None,
    condition: str | None = None,
    sponsor: str | None = None,
    country: str | None = None,
) -> ParsedQuery:
    return ParsedQuery(
        intent=intent,
        entities=ParsedEntities(
            drug_name=drug,
            condition=condition,
            phase=None,
            sponsor=sponsor,
            country=country,
            start_year=None,
            end_year=None,
        ),
        query_interpretation="test query",
        assumptions=[],
    )


def test_build_params_condition():
    req = QueryRequest(query="cancer trials")
    parsed = make_parsed(condition="cancer")
    params = build_ct_params(parsed, req)
    assert params["query.cond"] == "cancer"
    assert params["countTotal"] == "true"


def test_build_params_drug():
    req = QueryRequest(query="aspirin trials")
    parsed = make_parsed(drug="Aspirin")
    params = build_ct_params(parsed, req)
    assert params["query.intr"] == "Aspirin"


def test_build_params_request_overrides_parsed():
    req = QueryRequest(query="some query", drug_name="Pembrolizumab")
    parsed = make_parsed(drug="Aspirin")  # LLM extracted different drug
    params = build_ct_params(parsed, req)
    # request.drug_name takes priority
    assert params["query.intr"] == "Pembrolizumab"


def test_build_params_fallback_to_term():
    req = QueryRequest(query="randomized controlled trials in neurology")
    parsed = make_parsed()  # no entities extracted
    params = build_ct_params(parsed, req)
    assert "query.term" in params
    assert "query.cond" not in params
    assert "query.intr" not in params


def test_build_params_sponsor():
    req = QueryRequest(query="Pfizer trials")
    parsed = make_parsed(sponsor="Pfizer")
    params = build_ct_params(parsed, req)
    assert params["query.spons"] == "Pfizer"


def test_get_phase_filter_normalizes():
    req = QueryRequest(query="test", phase=["Phase 1", "Phase 2"])
    parsed = make_parsed()
    pf = get_phase_filter(req, parsed)
    assert pf is not None
    assert "PHASE1" in pf
    assert "PHASE2" in pf
    assert "Phase 1" not in pf


def test_get_phase_filter_none_when_unset():
    req = QueryRequest(query="test")
    parsed = make_parsed()
    assert get_phase_filter(req, parsed) is None


def test_phase_map_completeness():
    for key in ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Early Phase 1"]:
        assert key in PHASE_MAP
        assert PHASE_MAP[key].startswith("PHASE") or PHASE_MAP[key] == "EARLY_PHASE1"


def test_request_year_validation():
    with pytest.raises(Exception):
        QueryRequest(query="test", start_year=2020, end_year=2015)
