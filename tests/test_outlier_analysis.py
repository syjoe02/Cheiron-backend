"""Tests for enrollment outlier / anomaly detection (QueryIntent.OUTLIER_ANALYSIS)."""
import pandas as pd

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import Transformer, normalize_studies, transform_outlier_analysis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_study(nct_id: str, enrollment: int | None, phase: str = "PHASE2",
                status: str = "RECRUITING") -> dict:
    design: dict = {"phases": [phase]}
    if enrollment is not None:
        design["enrollmentInfo"] = {"count": enrollment}
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": status, "startDateStruct": {"date": "2021"}},
            "designModule": design,
            "conditionsModule": {"conditions": ["Diabetes"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor A"}},
            "armsInterventionsModule": {"interventions": [{"name": "Metformin"}]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


def _normal_studies(n: int = 8, enrollment: int = 100) -> list[dict]:
    return [_make_study(f"NCT{i:03d}", enrollment) for i in range(n)]


# ---------------------------------------------------------------------------
# transform_outlier_analysis — basic detection
# ---------------------------------------------------------------------------

def test_outlier_study_detected():
    """A study with enrollment far above the mean must appear in results."""
    studies = _normal_studies(8, 100) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    assert "NCT999" in result["nct_id"].values


def test_normal_studies_not_flagged():
    """Studies with enrollment close to the mean must not appear."""
    studies = _normal_studies(8, 100) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    normal_ids = {f"NCT{i:03d}" for i in range(8)}
    assert not (set(result["nct_id"].values) & normal_ids)


def test_output_schema():
    """Result must include required columns."""
    studies = _normal_studies(8) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    required = {"nct_id", "brief_title", "enrollment", "z_score"}
    assert required.issubset(set(result.columns))


def test_sorted_by_z_score_descending():
    """Results must be sorted with highest z-score first."""
    studies = (
        _normal_studies(6, 100)
        + [_make_study("NCT_HIGH", 20000)]
        + [_make_study("NCT_MED", 5000)]
    )
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    assert result.iloc[0]["nct_id"] == "NCT_HIGH"


def test_z_score_values_are_positive_for_outliers():
    """All returned studies must have z_score >= threshold (default 2.0)."""
    studies = _normal_studies(8) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    assert (result["z_score"] >= 2.0).all()


def test_z_score_float_precision_preserved():
    """z_score must be a float, not truncated to int."""
    studies = _normal_studies(8) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    z = result.iloc[0]["z_score"]
    assert isinstance(z, float)
    assert z != int(z)  # ensure it was not truncated


# ---------------------------------------------------------------------------
# Phrase variations: "unusually high", "outlier", "abnormal", etc.
# ---------------------------------------------------------------------------

def _outlier_studies() -> list[dict]:
    return _normal_studies(8, 100) + [_make_study("NCT999", 10000)]


def test_unusually_high_enrollment_query():
    studies = _outlier_studies()
    t = Transformer()
    req = QueryRequest(query="Which diabetes studies have unusually high enrollment?")
    data, _ = t.transform(QueryIntent.OUTLIER_ANALYSIS, studies, phase_filter=None, request=req)
    assert isinstance(data, pd.DataFrame)
    assert "nct_id" in data.columns
    assert "NCT999" in data["nct_id"].values


def test_outlier_studies_query():
    studies = _outlier_studies()
    t = Transformer()
    req = QueryRequest(query="Show outlier studies by participant count")
    data, _ = t.transform(QueryIntent.OUTLIER_ANALYSIS, studies, phase_filter=None, request=req)
    assert "NCT999" in data["nct_id"].values


def test_abnormal_participant_count_query():
    studies = _outlier_studies()
    t = Transformer()
    req = QueryRequest(query="Find studies with abnormal participant counts")
    data, _ = t.transform(QueryIntent.OUTLIER_ANALYSIS, studies, phase_filter=None, request=req)
    assert not data.empty


def test_extreme_enrollment_query():
    studies = _outlier_studies()
    t = Transformer()
    req = QueryRequest(query="Diabetes studies with extreme enrollment values")
    data, _ = t.transform(QueryIntent.OUTLIER_ANALYSIS, studies, phase_filter=None, request=req)
    assert "NCT999" in data["nct_id"].values


# ---------------------------------------------------------------------------
# Custom threshold
# ---------------------------------------------------------------------------

def test_higher_threshold_reduces_outliers():
    """With threshold=3.0 fewer studies should be flagged than with 2.0."""
    studies = _normal_studies(8, 100) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result_loose, _ = transform_outlier_analysis(df, phase_filter=None, threshold=2.0)
    result_strict, _ = transform_outlier_analysis(df, phase_filter=None, threshold=3.0)
    assert len(result_strict) <= len(result_loose)


def test_lower_threshold_may_include_more_studies():
    """threshold=1.5 should detect at least as many outliers as threshold=2.0."""
    studies = (
        _normal_studies(6, 100)
        + [_make_study("NCT_HIGH", 10000)]
        + [_make_study("NCT_MED", 2000)]
    )
    df = normalize_studies(studies)
    result_strict, _ = transform_outlier_analysis(df, phase_filter=None, threshold=2.0)
    result_loose, _ = transform_outlier_analysis(df, phase_filter=None, threshold=1.5)
    assert len(result_loose) >= len(result_strict)


# ---------------------------------------------------------------------------
# Empty and edge cases
# ---------------------------------------------------------------------------

def test_no_outliers_returns_empty_df():
    """When all studies have similar enrollment, no outliers should be found."""
    studies = _normal_studies(10, 100)  # all identical — std=0
    df = normalize_studies(studies)
    result, cmap = transform_outlier_analysis(df, phase_filter=None)
    assert result.empty
    assert cmap == {}


def test_fewer_than_3_studies_returns_empty():
    """z-score requires at least 3 studies with enrollment data."""
    studies = [_make_study("NCT001", 100), _make_study("NCT002", 5000)]
    df = normalize_studies(studies)
    result, cmap = transform_outlier_analysis(df, phase_filter=None)
    assert result.empty
    assert cmap == {}


def test_missing_enrollment_values_excluded():
    """Studies without enrollment data must not be included."""
    studies = (
        _normal_studies(7, 100)
        + [_make_study("NCT_NULL", None)]   # no enrollment
        + [_make_study("NCT_HIGH", 10000)]
    )
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None)
    assert "NCT_NULL" not in result["nct_id"].values
    assert "NCT_HIGH" in result["nct_id"].values


def test_empty_dataframe_returns_empty():
    result, cmap = transform_outlier_analysis(pd.DataFrame(), phase_filter=None)
    assert result.empty
    assert cmap == {}


# ---------------------------------------------------------------------------
# Citation map
# ---------------------------------------------------------------------------

def test_citation_map_keys_match_nct_ids():
    studies = _normal_studies(8) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    result, cmap = transform_outlier_analysis(df, phase_filter=None)
    assert set(cmap.keys()) == set(result["nct_id"].values)


def test_citation_map_each_study_cites_itself():
    studies = _normal_studies(8) + [_make_study("NCT999", 10000)]
    df = normalize_studies(studies)
    _, cmap = transform_outlier_analysis(df, phase_filter=None)
    for nct_id, nct_ids in cmap.items():
        assert nct_ids == [nct_id]


# ---------------------------------------------------------------------------
# Year filtering is applied before outlier detection
# ---------------------------------------------------------------------------

def test_year_filter_applied_before_outlier_detection():
    """start_year should exclude studies before the filter year."""
    studies = (
        _normal_studies(6, 100)
        + [_make_study("NCT_OLD", 10000)]     # would be an outlier but excluded by year
        + [_make_study("NCT_NEW", 10000)]
    )
    # Assign different years to old vs new
    studies[-2]["protocolSection"]["statusModule"]["startDateStruct"]["date"] = "2010"
    studies[-1]["protocolSection"]["statusModule"]["startDateStruct"]["date"] = "2022"
    df = normalize_studies(studies)
    result, _ = transform_outlier_analysis(df, phase_filter=None, start_year=2020)
    assert "NCT_OLD" not in result["nct_id"].values
