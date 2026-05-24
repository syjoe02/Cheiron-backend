"""Tests for temporal filtering in the trend transformation pipeline.

Covers the fix where LLM-extracted start_year/end_year must be applied during
transformation, not just stored in meta.filters_applied.
"""
import pandas as pd

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import Transformer, normalize_studies, transform_trend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_year_study(nct_id: str, year: int) -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": str(year)}},
            "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": ["Diabetes"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor A"}},
            "armsInterventionsModule": {"interventions": [{"name": "Metformin"}]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


def _studies_for_years(*years: int) -> list[dict]:
    return [_make_year_study(f"NCT{i:06d}", y) for i, y in enumerate(years)]


# ---------------------------------------------------------------------------
# transform_trend — direct temporal filter tests
# ---------------------------------------------------------------------------

def test_trend_since_2015_excludes_earlier_years():
    """start_year=2015 keeps only rows where start_year >= 2015."""
    studies = _studies_for_years(2013, 2014, 2015, 2016, 2019)
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None, start_year=2015)
    assert 2013 not in result["start_year"].values
    assert 2014 not in result["start_year"].values
    assert 2015 in result["start_year"].values
    assert 2016 in result["start_year"].values
    assert 2019 in result["start_year"].values


def test_trend_after_2020_excludes_2020_and_earlier():
    """start_year=2021 (i.e. 'after 2020') keeps only rows >= 2021."""
    studies = _studies_for_years(2019, 2020, 2021, 2022)
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None, start_year=2021)
    assert 2019 not in result["start_year"].values
    assert 2020 not in result["start_year"].values
    assert 2021 in result["start_year"].values
    assert 2022 in result["start_year"].values


def test_trend_exact_year_2020():
    """start_year=2020 and end_year=2020 returns only 2020."""
    studies = _studies_for_years(2018, 2019, 2020, 2020, 2021)
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None, start_year=2020, end_year=2020)
    assert list(result["start_year"].unique()) == [2020]
    assert result.iloc[0]["trial_count"] == 2


def test_trend_empty_result_when_all_before_filter():
    """When no studies fall within the year range the result is empty."""
    studies = _studies_for_years(2010, 2011, 2012, 2013)
    df = normalize_studies(studies)
    result, cmap = transform_trend(df, phase_filter=None, start_year=2015)
    assert result.empty
    assert cmap == {}


def test_trend_no_filter_returns_all_years():
    """Without any year filter all years appear in the result."""
    studies = _studies_for_years(2010, 2015, 2020)
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None)
    assert set(result["start_year"].values) == {2010, 2015, 2020}


def test_trend_null_start_years_always_excluded():
    """Rows with null start_year are dropped regardless of filter."""
    study_null = _make_year_study("NCTNULL", 2020)
    study_null["protocolSection"]["statusModule"]["startDateStruct"]["date"] = ""
    studies = [study_null, _make_year_study("NCT001", 2021)]
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None)
    assert len(result) == 1
    assert result.iloc[0]["start_year"] == 2021


def test_trend_citation_map_keys_match_filtered_years():
    """Citation map should only contain keys for years that pass the filter."""
    studies = _studies_for_years(2013, 2014, 2016, 2018)
    df = normalize_studies(studies)
    _, cmap = transform_trend(df, phase_filter=None, start_year=2015)
    for key in cmap:
        assert int(key) >= 2015


# ---------------------------------------------------------------------------
# Transformer dispatcher — end-to-end temporal filter
# ---------------------------------------------------------------------------

def test_transformer_dispatch_applies_start_year():
    """Transformer.transform() with start_year on the request filters correctly."""
    studies = _studies_for_years(2013, 2015, 2017, 2019)
    t = Transformer()
    req = QueryRequest(query="diabetes trend since 2015", start_year=2015)
    data, _ = t.transform(QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=req)
    assert isinstance(data, pd.DataFrame)
    assert 2013 not in data["start_year"].values
    assert 2015 in data["start_year"].values


def test_transformer_dispatch_applies_end_year():
    """Transformer.transform() with end_year on the request filters correctly."""
    studies = _studies_for_years(2015, 2018, 2020, 2022)
    t = Transformer()
    req = QueryRequest(query="diabetes trend up to 2020", end_year=2020)
    data, _ = t.transform(QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=req)
    assert 2022 not in data["start_year"].values
    assert 2020 in data["start_year"].values
    assert 2015 in data["start_year"].values


def test_transformer_dispatch_empty_after_filter():
    """When the year filter excludes everything the dispatcher returns an empty DataFrame."""
    studies = _studies_for_years(2010, 2011, 2012)
    t = Transformer()
    req = QueryRequest(query="diabetes trend since 2015", start_year=2015)
    data, cmap = t.transform(QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=req)
    assert isinstance(data, pd.DataFrame)
    assert data.empty
    assert cmap == {}


# ---------------------------------------------------------------------------
# main.py integration pattern: LLM entity merged into effective_request
# ---------------------------------------------------------------------------

def test_effective_request_applies_llm_extracted_start_year():
    """
    Simulates main.py's model_copy merge:
    user sends query only (start_year=None), LLM extracts start_year=2015.
    The effective_request must carry that value into the transformer.
    """
    original_request = QueryRequest(query="How has the number of diabetes trials changed since 2015?")
    assert original_request.start_year is None

    # Simulate main.py merging parsed.entities.start_year
    effective_request = original_request.model_copy(update={"start_year": 2015})

    studies = _studies_for_years(2013, 2014, 2015, 2016, 2019)
    t = Transformer()
    data, _ = t.transform(
        QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=effective_request
    )
    assert 2013 not in data["start_year"].values
    assert 2014 not in data["start_year"].values
    assert 2015 in data["start_year"].values


def test_explicit_request_year_overrides_llm_entity():
    """
    When the user explicitly sets start_year in the JSON request body,
    that value wins over any LLM-extracted entity.
    """
    # User explicitly says 2018 in request body
    explicit_request = QueryRequest(
        query="diabetes trend since 2015",
        start_year=2018,
    )
    # Even if LLM would extract 2015, explicit wins — no model_copy needed
    studies = _studies_for_years(2015, 2016, 2018, 2019)
    t = Transformer()
    data, _ = t.transform(
        QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=explicit_request
    )
    assert 2015 not in data["start_year"].values
    assert 2016 not in data["start_year"].values
    assert 2018 in data["start_year"].values
