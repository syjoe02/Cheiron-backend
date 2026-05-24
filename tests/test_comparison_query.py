"""Tests for multi-entity comparison query support (X vs Y, X versus Y, compare X and Y)."""
import pandas as pd
import pytest

from app.models.request import QueryRequest
from app.pipeline.api_builder import build_ct_params_for_entity
from app.pipeline.query_parser import ParsedEntities, ParsedQuery, QueryIntent
from app.pipeline.transformer import (
    Transformer,
    _infer_comparison_group_by,
    _normalize_phase,
    generate_comparison_insight,
    normalize_studies,
    transform_entity_comparison,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_study(nct_id: str, phases: list[str], drug: str, condition: str = "Diabetes",
                status: str = "RECRUITING", sponsor: str = "Sponsor A") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": status, "startDateStruct": {"date": "2021"}},
            "designModule": {"phases": phases, "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": [condition]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": sponsor}},
            "armsInterventionsModule": {"interventions": [{"name": drug}]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


def _parsed_query(entities: ParsedEntities) -> ParsedQuery:
    return ParsedQuery(
        intent=QueryIntent.COMPARISON,
        entities=entities,
        query_interpretation="Comparison query",
        assumptions=[],
    )


# ---------------------------------------------------------------------------
# _infer_comparison_group_by — "vs / versus / compare...and" syntax
# ---------------------------------------------------------------------------

def test_group_by_phase_from_vs_query():
    """'Metformin vs Insulin by phase' should infer phase_str."""
    assert _infer_comparison_group_by("Compare phases for Metformin vs Insulin") == "phase_str"


def test_group_by_phase_from_versus_query():
    assert _infer_comparison_group_by("Metformin versus Insulin phase distribution") == "phase_str"


def test_group_by_phase_from_compare_and_query():
    assert _infer_comparison_group_by("Compare phases for Metformin and Insulin") == "phase_str"


def test_group_by_status_keyword():
    assert _infer_comparison_group_by("Metformin vs Insulin recruitment status") == "status"


def test_group_by_sponsor_keyword():
    assert _infer_comparison_group_by("Compare sponsors for Metformin versus Insulin") == "sponsor"


def test_group_by_default_no_keyword():
    """When no grouping keyword is present, defaults to phase_str."""
    assert _infer_comparison_group_by("Metformin vs Insulin") == "phase_str"


# ---------------------------------------------------------------------------
# transform_entity_comparison — phase grouping
# ---------------------------------------------------------------------------

def _metformin_insulin_studies() -> dict[str, list[dict]]:
    return {
        "Metformin": [
            _make_study("NCT001", ["PHASE2"], "Metformin"),
            _make_study("NCT002", ["PHASE2"], "Metformin"),
            _make_study("NCT003", ["PHASE3"], "Metformin"),
        ],
        "Insulin": [
            _make_study("NCT101", ["PHASE2"], "Insulin"),
            _make_study("NCT102", ["PHASE3"], "Insulin"),
            _make_study("NCT103", ["PHASE3"], "Insulin"),
        ],
    }


def test_entity_comparison_output_schema():
    result, _ = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    assert list(result.columns) == ["entity", "phase", "trial_count"] or \
           set(result.columns) >= {"entity", "category", "trial_count"}


def test_entity_comparison_contains_both_entities():
    result, _ = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    assert "Metformin" in result["entity"].values
    assert "Insulin" in result["entity"].values


def test_entity_comparison_correct_trial_counts():
    result, _ = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    met_p2 = result[(result["entity"] == "Metformin") & (result["category"] == "Phase 2")]
    assert len(met_p2) == 1
    assert met_p2.iloc[0]["trial_count"] == 2

    ins_p3 = result[(result["entity"] == "Insulin") & (result["category"] == "Phase 3")]
    assert len(ins_p3) == 1
    assert ins_p3.iloc[0]["trial_count"] == 2


def test_entity_comparison_no_combined_phase_labels():
    """Multi-phase studies must be split, not joined with '|'."""
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["PHASE1", "PHASE2"], "DrugA")],
        "DrugB": [_make_study("NCT101", ["PHASE2"], "DrugB")],
    }
    result, _ = transform_entity_comparison(entity_studies, phase_filter=None, group_by="phase_str")
    for cat in result["category"].values:
        assert "|" not in cat


def test_entity_comparison_multi_phase_split_counts():
    """DrugA with PHASE1+PHASE2 contributes 1 to each phase bucket."""
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["PHASE1", "PHASE2"], "DrugA")],
    }
    result, _ = transform_entity_comparison(entity_studies, phase_filter=None, group_by="phase_str")
    assert result[result["category"] == "Phase 1"].iloc[0]["trial_count"] == 1
    assert result[result["category"] == "Phase 2"].iloc[0]["trial_count"] == 1


# ---------------------------------------------------------------------------
# transform_entity_comparison — status and sponsor grouping
# ---------------------------------------------------------------------------

def test_entity_comparison_by_status():
    entity_studies = {
        "Metformin": [
            _make_study("NCT001", ["PHASE2"], "Metformin", status="RECRUITING"),
            _make_study("NCT002", ["PHASE2"], "Metformin", status="COMPLETED"),
        ],
        "Insulin": [
            _make_study("NCT101", ["PHASE2"], "Insulin", status="RECRUITING"),
        ],
    }
    result, cmap = transform_entity_comparison(
        entity_studies, phase_filter=None, group_by="status"
    )
    assert "entity" in result.columns
    assert "category" in result.columns
    # Metformin|RECRUITING citation key
    assert "Metformin|RECRUITING" in cmap
    assert "Insulin|RECRUITING" in cmap


def test_entity_comparison_by_sponsor():
    entity_studies = {
        "Metformin": [
            _make_study("NCT001", ["PHASE2"], "Metformin", sponsor="BigPharma"),
            _make_study("NCT002", ["PHASE2"], "Metformin", sponsor="BigPharma"),
            _make_study("NCT003", ["PHASE2"], "Metformin", sponsor="SmallLab"),
        ],
    }
    result, cmap = transform_entity_comparison(
        entity_studies, phase_filter=None, group_by="sponsor"
    )
    bigpharma_row = result[(result["entity"] == "Metformin") & (result["category"] == "BigPharma")]
    assert bigpharma_row.iloc[0]["trial_count"] == 2


# ---------------------------------------------------------------------------
# Citation map correctness
# ---------------------------------------------------------------------------

def test_citation_map_keys_use_entity_pipe_category():
    result, cmap = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    for key in cmap:
        entity, category = key.split("|", 1)
        assert entity in result["entity"].values
        assert category in result["category"].values


def test_citation_map_nct_ids_are_correct():
    result, cmap = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    assert set(cmap["Metformin|Phase 2"]) == {"NCT001", "NCT002"}
    assert set(cmap["Metformin|Phase 3"]) == {"NCT003"}
    assert set(cmap["Insulin|Phase 3"]) == {"NCT102", "NCT103"}


def test_citation_map_no_cross_entity_contamination():
    """Metformin NCT IDs must not appear in Insulin citation lists."""
    _, cmap = transform_entity_comparison(
        _metformin_insulin_studies(), phase_filter=None, group_by="phase_str"
    )
    metformin_ncts = {"NCT001", "NCT002", "NCT003"}
    insulin_ncts = {"NCT101", "NCT102", "NCT103"}
    for key, nct_ids in cmap.items():
        entity = key.split("|")[0]
        if entity == "Metformin":
            assert not (set(nct_ids) & insulin_ncts)
        if entity == "Insulin":
            assert not (set(nct_ids) & metformin_ncts)


# ---------------------------------------------------------------------------
# Empty and edge cases
# ---------------------------------------------------------------------------

def test_empty_entity_studies_returns_empty_df():
    result, cmap = transform_entity_comparison({}, phase_filter=None)
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert cmap == {}


def test_all_entities_have_no_studies():
    result, cmap = transform_entity_comparison(
        {"Metformin": [], "Insulin": []}, phase_filter=None
    )
    assert result.empty
    assert cmap == {}


def test_one_entity_empty_other_has_data():
    entity_studies = {
        "Metformin": [_make_study("NCT001", ["PHASE2"], "Metformin")],
        "Insulin": [],
    }
    result, cmap = transform_entity_comparison(entity_studies, phase_filter=None)
    # Only Metformin rows should appear
    assert set(result["entity"].values) == {"Metformin"}
    assert "Insulin" not in result["entity"].values


def test_missing_phases_excluded_from_comparison():
    entity_studies = {
        "DrugA": [_make_study("NCT001", [], "DrugA")],  # no phase
        "DrugB": [_make_study("NCT101", ["PHASE2"], "DrugB")],
    }
    result, _ = transform_entity_comparison(
        entity_studies, phase_filter=None, group_by="phase_str"
    )
    categories = result["category"].values
    assert "NA" not in categories
    # DrugA has no phases → no rows for DrugA
    assert "DrugA" not in result["entity"].values
    assert "DrugB" in result["entity"].values


# ---------------------------------------------------------------------------
# Transformer.transform_comparison_entities — end-to-end dispatcher
# ---------------------------------------------------------------------------

def test_transformer_comparison_entities_phase_dispatch():
    """End-to-end: transformer dispatches correctly and returns valid schema."""
    entity_studies = _metformin_insulin_studies()
    t = Transformer()
    req = QueryRequest(query="Compare phases for trials involving Metformin vs Insulin")
    result, cmap = t.transform_comparison_entities(entity_studies, phase_filter=None, request=req)

    assert isinstance(result, pd.DataFrame)
    assert set(result.columns) >= {"entity", "category", "trial_count"}
    assert "Metformin" in result["entity"].values
    assert "Insulin" in result["entity"].values
    assert len(cmap) > 0


def test_transformer_comparison_entities_infers_status_group_by():
    entity_studies = {
        "Metformin": [_make_study("NCT001", ["PHASE2"], "Metformin", status="RECRUITING")],
        "Insulin": [_make_study("NCT101", ["PHASE2"], "Insulin", status="COMPLETED")],
    }
    t = Transformer()
    req = QueryRequest(query="Compare recruitment status for Metformin versus Insulin")
    result, _ = t.transform_comparison_entities(entity_studies, phase_filter=None, request=req)
    categories = set(result["category"].values)
    assert "RECRUITING" in categories or "COMPLETED" in categories


# ---------------------------------------------------------------------------
# build_ct_params_for_entity
# ---------------------------------------------------------------------------

def _dummy_parsed(condition: str | None = None, country: str | None = None) -> ParsedQuery:
    return _parsed_query(ParsedEntities(condition=condition, country=country))


def _dummy_request(condition: str | None = None, country: str | None = None) -> QueryRequest:
    return QueryRequest(query="test", condition=condition, country=country)


def test_build_params_drug_name_dimension():
    params = build_ct_params_for_entity(
        _dummy_parsed(), _dummy_request(), entity="Metformin", dimension="drug_name"
    )
    assert params["query.intr"] == "Metformin"
    assert "query.spons" not in params


def test_build_params_condition_dimension():
    params = build_ct_params_for_entity(
        _dummy_parsed(), _dummy_request(), entity="Diabetes", dimension="condition"
    )
    assert params["query.cond"] == "Diabetes"
    assert "query.intr" not in params


def test_build_params_sponsor_dimension():
    params = build_ct_params_for_entity(
        _dummy_parsed(), _dummy_request(), entity="Pfizer", dimension="sponsor"
    )
    assert params["query.spons"] == "Pfizer"


def test_build_params_preserves_country_filter():
    params = build_ct_params_for_entity(
        _dummy_parsed(country="Germany"),
        _dummy_request(),
        entity="Metformin",
        dimension="drug_name",
    )
    assert params["query.intr"] == "Metformin"
    assert params["query.locn"] == "Germany"


def test_build_params_preserves_condition_when_drug_dimension():
    params = build_ct_params_for_entity(
        _dummy_parsed(condition="Diabetes"),
        _dummy_request(),
        entity="Metformin",
        dimension="drug_name",
    )
    assert params["query.intr"] == "Metformin"
    assert params["query.cond"] == "Diabetes"


def test_build_params_always_has_count_total():
    params = build_ct_params_for_entity(
        _dummy_parsed(), _dummy_request(), entity="X", dimension="drug_name"
    )
    assert params["countTotal"] == "true"


# ---------------------------------------------------------------------------
# Phase normalization
# ---------------------------------------------------------------------------

def test_normalize_phase_phase1():
    assert _normalize_phase("PHASE1") == "Phase 1"


def test_normalize_phase_phase2():
    assert _normalize_phase("PHASE2") == "Phase 2"


def test_normalize_phase_phase3():
    assert _normalize_phase("PHASE3") == "Phase 3"


def test_normalize_phase_phase4():
    assert _normalize_phase("PHASE4") == "Phase 4"


def test_normalize_phase_early_phase1():
    assert _normalize_phase("EARLY_PHASE1") == "Early Phase 1"


def test_normalize_phase_unknown_passes_through():
    assert _normalize_phase("CUSTOM_PHASE") == "CUSTOM_PHASE"


def test_normalize_phase_case_insensitive():
    assert _normalize_phase("phase2") == "Phase 2"


def test_early_phase1_normalized_in_comparison():
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["EARLY_PHASE1"], "DrugA")],
    }
    result, _ = transform_entity_comparison(entity_studies, phase_filter=None, group_by="phase_str")
    assert "Early Phase 1" in result["category"].values


def test_na_string_phase_excluded_from_comparison():
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["NA"], "DrugA")],
        "DrugB": [_make_study("NCT101", ["PHASE2"], "DrugB")],
    }
    result, _ = transform_entity_comparison(entity_studies, phase_filter=None, group_by="phase_str")
    assert "NA" not in result["category"].values
    assert "Phase 2" in result["category"].values


# ---------------------------------------------------------------------------
# Visualization schema consistency
# ---------------------------------------------------------------------------

def test_comparison_encoding_uses_category_and_entity():
    from app.pipeline.viz_selector import _rule_based_viz
    spec = _rule_based_viz(
        QueryIntent.COMPARISON, ["entity", "category", "trial_count"], "Comparison"
    )
    assert spec.encoding["x"]["field"] == "category"
    assert spec.encoding["series"]["field"] == "entity"
    assert spec.encoding["y"]["field"] == "trial_count"


# ---------------------------------------------------------------------------
# Comparative insight generation
# ---------------------------------------------------------------------------

def test_insight_mentions_both_entities():
    df = pd.DataFrame([
        {"entity": "Metformin", "category": "Phase 2", "trial_count": 10},
        {"entity": "Metformin", "category": "Phase 3", "trial_count": 3},
        {"entity": "Insulin", "category": "Phase 3", "trial_count": 8},
        {"entity": "Insulin", "category": "Phase 2", "trial_count": 2},
    ])
    insight = generate_comparison_insight(df)
    assert "Metformin" in insight
    assert "Insulin" in insight


def test_insight_includes_top_category():
    df = pd.DataFrame([
        {"entity": "Metformin", "category": "Phase 2", "trial_count": 10},
        {"entity": "Metformin", "category": "Phase 3", "trial_count": 3},
        {"entity": "Insulin", "category": "Phase 3", "trial_count": 8},
        {"entity": "Insulin", "category": "Phase 2", "trial_count": 2},
    ])
    insight = generate_comparison_insight(df)
    assert "Phase 2" in insight
    assert "Phase 3" in insight


def test_insight_empty_on_missing_entity_column():
    df = pd.DataFrame([{"category": "Phase 2", "trial_count": 5}])
    assert generate_comparison_insight(df) == ""


def test_insight_empty_on_single_entity():
    df = pd.DataFrame([{"entity": "Metformin", "category": "Phase 2", "trial_count": 5}])
    assert generate_comparison_insight(df) == ""


def test_insight_empty_on_empty_dataframe():
    assert generate_comparison_insight(pd.DataFrame()) == ""


def test_insight_includes_percentage():
    df = pd.DataFrame([
        {"entity": "DrugA", "category": "Phase 2", "trial_count": 8},
        {"entity": "DrugA", "category": "Phase 3", "trial_count": 2},
        {"entity": "DrugB", "category": "Phase 3", "trial_count": 6},
        {"entity": "DrugB", "category": "Phase 2", "trial_count": 4},
    ])
    insight = generate_comparison_insight(df)
    assert "%" in insight
