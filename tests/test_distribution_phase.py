"""Tests for phase distribution improvements: missing phase filtering, combined phase splitting."""
import pandas as pd

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import Transformer, normalize_studies, transform_distribution


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_phase_study(nct_id: str, phases: list[str], status: str = "RECRUITING") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": status, "startDateStruct": {"date": "2020"}},
            "designModule": {
                "phases": phases,
                "enrollmentInfo": {"count": 100},
            },
            "conditionsModule": {"conditions": ["Cancer"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor A"}},
            "armsInterventionsModule": {"interventions": [{"name": "Drug A"}]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


# ---------------------------------------------------------------------------
# Missing phase filtering
# ---------------------------------------------------------------------------

def test_missing_phase_excluded_from_distribution():
    """Studies with no phase should not produce an 'NA' category."""
    studies = [
        _make_phase_study("NCT001", []),          # no phase → should be excluded
        _make_phase_study("NCT002", ["PHASE2"]),
        _make_phase_study("NCT003", ["PHASE2"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str")
    categories = list(result["category"].values)
    assert "NA" not in categories
    assert "Phase 2" in categories


def test_all_missing_phases_returns_empty():
    """When every study lacks a phase the result is an empty DataFrame."""
    studies = [_make_phase_study(f"NCT{i:03d}", []) for i in range(5)]
    df = normalize_studies(studies)
    result, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str")
    assert result.empty
    assert cmap == {}


def test_mixed_missing_and_present_phases():
    """Studies with missing phases are dropped; remaining studies are counted correctly."""
    studies = [
        _make_phase_study("NCT001", []),          # excluded
        _make_phase_study("NCT002", []),           # excluded
        _make_phase_study("NCT003", ["PHASE1"]),
        _make_phase_study("NCT004", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str")
    categories = set(result["category"].values)
    assert "NA" not in categories
    assert categories == {"Phase 1", "Phase 3"}
    assert result[result["category"] == "Phase 1"].iloc[0]["trial_count"] == 1


# ---------------------------------------------------------------------------
# Combined phase splitting
# ---------------------------------------------------------------------------

def test_combined_phase_splits_into_individual_categories():
    """A study with PHASE1+PHASE2 should appear in both PHASE1 and PHASE2 categories."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
    ]
    df = normalize_studies(studies)
    # Verify the raw phase_str is combined (pre-existing behavior)
    assert df.iloc[0]["phase_str"] == "PHASE1|PHASE2"

    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str")
    categories = set(result["category"].values)
    assert "PHASE1|PHASE2" not in categories
    assert "Phase 1" in categories
    assert "Phase 2" in categories


def test_combined_phase_counts_study_in_each_split_phase():
    """A multi-phase study contributes a count of 1 to each of its phases."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_phase_study("NCT002", ["PHASE2"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str")
    row_p1 = result[result["category"] == "Phase 1"].iloc[0]
    row_p2 = result[result["category"] == "Phase 2"].iloc[0]
    assert row_p1["trial_count"] == 1   # only NCT001
    assert row_p2["trial_count"] == 2   # NCT001 and NCT002


def test_no_combined_phase_labels_in_output():
    """The output must never contain pipe-separated phase labels."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_phase_study("NCT002", ["PHASE2", "PHASE3"]),
        _make_phase_study("NCT003", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_distribution(df, phase_filter=None, group_by="phase_str")
    for cat in result["category"].values:
        assert "|" not in cat


# ---------------------------------------------------------------------------
# Citation preservation after explode
# ---------------------------------------------------------------------------

def test_citation_map_keys_are_individual_phases():
    """After explode, citation map keys must be individual phase strings."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_phase_study("NCT002", ["PHASE2"]),
    ]
    df = normalize_studies(studies)
    _, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str")
    assert "Phase 1" in cmap
    assert "Phase 2" in cmap
    assert "PHASE1|PHASE2" not in cmap
    assert "NA" not in cmap


def test_citation_map_contains_correct_nct_ids():
    """Each phase citation list contains exactly the studies that belong to that phase."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_phase_study("NCT002", ["PHASE2"]),
        _make_phase_study("NCT003", ["PHASE3"]),
    ]
    df = normalize_studies(studies)
    _, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str")
    assert set(cmap["Phase 1"]) == {"NCT001"}
    assert set(cmap["Phase 2"]) == {"NCT001", "NCT002"}
    assert set(cmap["Phase 3"]) == {"NCT003"}


def test_citation_map_missing_phase_studies_not_cited():
    """Studies with no phase must not appear in any citation list."""
    studies = [
        _make_phase_study("NCT_NO_PHASE", []),
        _make_phase_study("NCT001", ["PHASE2"]),
    ]
    df = normalize_studies(studies)
    _, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str")
    all_cited = {nct_id for ids in cmap.values() for nct_id in ids}
    assert "NCT_NO_PHASE" not in all_cited


# ---------------------------------------------------------------------------
# Non-phase groupby dimensions are unaffected
# ---------------------------------------------------------------------------

def test_distribution_by_status_unaffected():
    """Groupby 'status' should still use the scalar column path, not the explode path."""
    studies = [
        _make_phase_study("NCT001", ["PHASE2"], status="RECRUITING"),
        _make_phase_study("NCT002", ["PHASE2"], status="RECRUITING"),
        _make_phase_study("NCT003", ["PHASE2"], status="COMPLETED"),
    ]
    df = normalize_studies(studies)
    result, cmap = transform_distribution(df, phase_filter=None, group_by="status")
    assert "RECRUITING" in result["category"].values
    assert "COMPLETED" in result["category"].values
    assert "RECRUITING" in cmap
    assert set(cmap["RECRUITING"]) == {"NCT001", "NCT002"}


# ---------------------------------------------------------------------------
# Transformer dispatcher end-to-end
# ---------------------------------------------------------------------------

def test_transformer_dispatch_distribution_no_na_or_combined_phases():
    """End-to-end: DISTRIBUTION intent produces clean individual phase categories."""
    studies = [
        _make_phase_study("NCT001", ["PHASE1", "PHASE2"]),
        _make_phase_study("NCT002", ["PHASE2"]),
        _make_phase_study("NCT003", []),             # missing — should be excluded
        _make_phase_study("NCT004", ["PHASE3"]),
    ]
    t = Transformer()
    req = QueryRequest(query="distribution of trials by phase")
    data, cmap = t.transform(QueryIntent.DISTRIBUTION, studies, phase_filter=None, request=req)

    assert isinstance(data, pd.DataFrame)
    categories = set(data["category"].values)
    assert "NA" not in categories
    for cat in categories:
        assert "|" not in cat
    assert "Phase 2" in categories
    # NCT001 counts in both Phase 1 and Phase 2
    assert data[data["category"] == "Phase 2"].iloc[0]["trial_count"] == 2
