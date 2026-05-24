"""Tests for phase strategy: InclusiveHybridStrategy and StrictFilterStrategy."""
import pandas as pd
import pytest

from app.models.request import QueryRequest
from app.pipeline.normalizers import normalize_studies
from app.pipeline.phase_strategy import (
    InclusiveHybridStrategy,
    StrictFilterStrategy,
    choose_strategy,
    phase_meta_for,
)
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import Transformer, TransformResult
from app.pipeline.transforms.comparison import transform_entity_comparison
from app.pipeline.transforms.tabular import transform_distribution


def _make_study(nct_id: str, phases: list[str], condition: str = "Cancer", country: str = "US") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2021"}},
            "designModule": {"phases": phases, "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": [condition]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
            "armsInterventionsModule": {"interventions": [{"name": "Drug"}]},
            "contactsLocationsModule": {"locations": [{"country": country}]},
        }
    }


# ---------------------------------------------------------------------------
# choose_strategy
# ---------------------------------------------------------------------------

def test_choose_strategy_none_returns_inclusive():
    assert isinstance(choose_strategy(None), InclusiveHybridStrategy)


def test_choose_strategy_empty_list_returns_inclusive():
    assert isinstance(choose_strategy([]), InclusiveHybridStrategy)


def test_choose_strategy_single_phase_returns_strict():
    strategy = choose_strategy(["PHASE3"])
    assert isinstance(strategy, StrictFilterStrategy)
    assert strategy.phase_filter == ("PHASE3",)


def test_choose_strategy_multi_phase_returns_inclusive():
    assert isinstance(choose_strategy(["PHASE2", "PHASE3"]), InclusiveHybridStrategy)


# ---------------------------------------------------------------------------
# primary_phase field added by normalize_studies
# ---------------------------------------------------------------------------

def test_primary_phase_single_phase():
    df = normalize_studies([_make_study("NCT001", ["PHASE3"])])
    assert df.iloc[0]["primary_phase"] == "PHASE3"


def test_primary_phase_hybrid_returns_highest():
    """PHASE2|PHASE3 study: primary_phase should be PHASE3."""
    df = normalize_studies([_make_study("NCT001", ["PHASE2", "PHASE3"])])
    assert df.iloc[0]["primary_phase"] == "PHASE3"


def test_primary_phase_early_phase1_lower_than_phase1():
    df = normalize_studies([_make_study("NCT001", ["EARLY_PHASE1", "PHASE1"])])
    assert df.iloc[0]["primary_phase"] == "PHASE1"


def test_primary_phase_empty_returns_na():
    df = normalize_studies([_make_study("NCT001", [])])
    assert df.iloc[0]["primary_phase"] == "NA"


# ---------------------------------------------------------------------------
# InclusiveHybridStrategy — transform_distribution
# ---------------------------------------------------------------------------

def test_inclusive_hybrid_explodes_hybrid_to_both_phases():
    """PHASE2|PHASE3 study contributes to both Phase 2 and Phase 3 categories."""
    df = normalize_studies([_make_study("NCT001", ["PHASE2", "PHASE3"])])
    result, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str",
                                          strategy=InclusiveHybridStrategy())
    categories = set(result["category"].values)
    assert "Phase 2" in categories
    assert "Phase 3" in categories


def test_inclusive_hybrid_count_per_bucket():
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str",
                                       strategy=InclusiveHybridStrategy())
    assert result[result["category"] == "Phase 2"].iloc[0]["trial_count"] == 1
    assert result[result["category"] == "Phase 3"].iloc[0]["trial_count"] == 2


def test_inclusive_hybrid_citation_map_lists_all_phases():
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    _, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str",
                                     strategy=InclusiveHybridStrategy())
    assert set(cmap["Phase 2"]) == {"NCT001"}
    assert set(cmap["Phase 3"]) == {"NCT001", "NCT002"}


# ---------------------------------------------------------------------------
# StrictFilterStrategy — transform_distribution
# ---------------------------------------------------------------------------

def test_strict_filter_hybrid_shows_only_requested_phase():
    """PHASE2|PHASE3 study filtered by PHASE3 appears only under Phase 3."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    result, _ = transform_distribution(df, phase_filter=["PHASE3"], group_by="phase_str",
                                       strategy=strategy)
    categories = set(result["category"].values)
    assert "Phase 3" in categories
    assert "Phase 2" not in categories


def test_strict_filter_count_includes_hybrid():
    """Both the pure Phase 3 study and the hybrid study are counted under Phase 3."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    result, _ = transform_distribution(df, phase_filter=["PHASE3"], group_by="phase_str",
                                       strategy=strategy)
    assert result.iloc[0]["trial_count"] == 2


def test_strict_filter_citation_map_correct():
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    _, cmap = transform_distribution(df, phase_filter=["PHASE3"], group_by="phase_str",
                                     strategy=strategy)
    assert set(cmap["Phase 3"]) == {"NCT001", "NCT002"}
    assert "Phase 2" not in cmap


def test_strict_filter_excludes_non_matching_phase():
    """PHASE1|PHASE2 study is excluded when PHASE3 filter is active."""
    studies = [
        _make_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    result, cmap = transform_distribution(df, phase_filter=["PHASE3"], group_by="phase_str",
                                          strategy=strategy)
    all_cited = {nct for ids in cmap.values() for nct in ids}
    assert "NCT001" not in all_cited
    assert "NCT002" in all_cited


def test_strict_filter_no_pipe_in_categories():
    """Output category labels must never contain '|' in strict mode."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    result, _ = transform_distribution(df, phase_filter=["PHASE3"], group_by="phase_str",
                                       strategy=strategy)
    for cat in result["category"].values:
        assert "|" not in cat


# ---------------------------------------------------------------------------
# StrictFilterStrategy — transform_entity_comparison
# ---------------------------------------------------------------------------

def test_strict_entity_comparison_hybrid_under_requested_phase():
    """Entity comparison with PHASE3 filter: PHASE2|PHASE3 drug appears only under Phase 3."""
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["PHASE2", "PHASE3"])],
        "DrugB": [_make_study("NCT101", ["PHASE3"])],
    }
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    result, cmap = transform_entity_comparison(entity_studies, phase_filter=["PHASE3"],
                                               group_by="phase_str", strategy=strategy)
    categories = set(result["category"].values)
    assert "Phase 3" in categories
    assert "Phase 2" not in categories
    assert "DrugA|Phase 3" in cmap
    assert "DrugA|Phase 2" not in cmap


def test_strict_entity_comparison_citation_includes_hybrid():
    entity_studies = {
        "DrugA": [
            _make_study("NCT001", ["PHASE2", "PHASE3"]),
            _make_study("NCT002", ["PHASE3"]),
        ],
    }
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    _, cmap = transform_entity_comparison(entity_studies, phase_filter=["PHASE3"],
                                          group_by="phase_str", strategy=strategy)
    assert set(cmap["DrugA|Phase 3"]) == {"NCT001", "NCT002"}


# ---------------------------------------------------------------------------
# Transformer end-to-end
# ---------------------------------------------------------------------------

def test_transformer_result_is_transform_result():
    studies = [_make_study("NCT001", ["PHASE3"])]
    t = Transformer()
    req = QueryRequest(query="phase distribution")
    result = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=None, request=req)
    assert isinstance(result, TransformResult)


def test_transformer_result_backward_compat_unpacking():
    """TransformResult must support 2-tuple unpacking for backward compatibility."""
    studies = [_make_study("NCT001", ["PHASE3"])]
    t = Transformer()
    req = QueryRequest(query="phase distribution")
    data, cmap = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=None, request=req)
    assert isinstance(data, pd.DataFrame)
    assert isinstance(cmap, dict)


def test_transformer_distribution_no_filter_uses_inclusive():
    """No phase filter → InclusiveHybrid → hybrid study appears in both buckets."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    t = Transformer()
    req = QueryRequest(query="how are trials distributed across phases?")
    result = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=None, request=req)
    data, _ = result
    categories = set(data["category"].values)
    assert "Phase 2" in categories and "Phase 3" in categories
    assert result.phase_meta["phase_filter_mode"] == "inclusive_hybrid"


def test_transformer_distribution_single_phase_filter_uses_strict():
    """Single-phase filter → StrictFilter → hybrid study shown only under Phase 3."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
        _make_study("NCT002", ["PHASE3"]),
    ]
    t = Transformer()
    req = QueryRequest(query="show phase 3 trials")
    result = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=["PHASE3"], request=req)
    data, _ = result
    categories = set(data["category"].values)
    assert "Phase 3" in categories
    assert "Phase 2" not in categories
    assert result.phase_meta["phase_filter_mode"] == "strict_display"
    assert "notes" in result.phase_meta


def test_transformer_multi_phase_filter_uses_inclusive():
    """Multi-phase filter → InclusiveHybrid even with a filter set."""
    studies = [
        _make_study("NCT001", ["PHASE2", "PHASE3"]),
    ]
    t = Transformer()
    req = QueryRequest(query="phase 2 and 3 distribution")
    result = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=["PHASE2", "PHASE3"], request=req)
    assert result.phase_meta["phase_filter_mode"] == "inclusive_hybrid"


def test_transformer_comparison_entities_strict_mode():
    entity_studies = {
        "DrugA": [_make_study("NCT001", ["PHASE2", "PHASE3"])],
        "DrugB": [_make_study("NCT101", ["PHASE3"])],
    }
    t = Transformer()
    req = QueryRequest(query="Compare DrugA vs DrugB in phase 3")
    result = t.transform_comparison_entities(entity_studies, phase_filter=["PHASE3"], request=req)
    assert result.phase_meta["phase_filter_mode"] == "strict_display"
    data, _ = result
    assert "Phase 2" not in set(data["category"].values)


# ---------------------------------------------------------------------------
# phase_meta_for
# ---------------------------------------------------------------------------

def test_phase_meta_inclusive_mode():
    meta = phase_meta_for(InclusiveHybridStrategy(), None)
    assert meta["phase_filter_mode"] == "inclusive_hybrid"
    assert "notes" not in meta


def test_phase_meta_strict_mode_has_notes():
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    meta = phase_meta_for(strategy, ["PHASE3"])
    assert meta["phase_filter_mode"] == "strict_display"
    assert isinstance(meta["notes"], list)
    assert len(meta["notes"]) > 0


def test_phase_meta_strict_notes_mention_phase():
    strategy = StrictFilterStrategy(phase_filter=("PHASE3",))
    meta = phase_meta_for(strategy, ["PHASE3"])
    assert "PHASE3" in meta["notes"][0]
