"""Tests covering transformer branches not exercised by test_transformer.py."""
from unittest.mock import MagicMock

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import (
    Transformer,
    _apply_year_filter,
    _extract_top_n,
    _infer_comparison_dims,
    _infer_distribution_dim,
    _infer_ranking_dim,
    normalize_studies,
    transform_comparison,
    transform_network,
    transform_ranking,
)


def make_study(nct_id: str, phase: str, status: str = "RECRUITING", year: str = "2020") -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": status, "startDateStruct": {"date": year}},
            "designModule": {"phases": [phase], "enrollmentInfo": {"count": 50}},
            "conditionsModule": {"conditions": ["Cancer"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor"}},
            "armsInterventionsModule": {"interventions": [{"name": "Drug A"}]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


def test_normalize_invalid_date():
    """Invalid date string should not raise — start_year should be None."""
    study = make_study("NCT001", "PHASE1")
    study["protocolSection"]["statusModule"]["startDateStruct"]["date"] = "INVALID"
    df = normalize_studies([study])
    assert df.iloc[0]["start_year"] is None


def test_apply_year_filter_end_year(sample_study, sample_study_phase3):
    df = normalize_studies([sample_study, sample_study_phase3])
    result = _apply_year_filter(df, start_year=None, end_year=2019)
    assert all(result["start_year"] <= 2019)
    assert 2018 in result["start_year"].values
    assert 2020 not in result["start_year"].values


def test_apply_year_filter_empty_df():
    import pandas as pd
    empty = pd.DataFrame()
    result = _apply_year_filter(empty, start_year=2020, end_year=2022)
    assert result.empty


def test_transform_comparison_groups_correctly(sample_study, sample_study_phase3):
    studies = [sample_study] * 4 + [sample_study_phase3] * 3
    df = normalize_studies(studies)
    result, cmap = transform_comparison(df, phase_filter=None, dim1="phase_str", dim2="status")
    assert "group1" in result.columns
    assert "group2" in result.columns
    assert "trial_count" in result.columns
    assert len(cmap) > 0
    for key in cmap:
        assert "|" in key


def test_transform_comparison_with_phase_filter(sample_study, sample_study_phase3):
    studies = [sample_study, sample_study_phase3]
    df = normalize_studies(studies)
    result, _ = transform_comparison(df, phase_filter=["PHASE2"], dim1="phase_str", dim2="status")
    assert all(result["group1"] == "PHASE2")


def test_transform_network_large_graph():
    """Create >50 nodes to exercise the pruning branch."""
    studies = []
    for i in range(30):
        studies.append({
            "protocolSection": {
                "identificationModule": {"nctId": f"NCT{i:08d}", "briefTitle": f"Study {i}"},
                "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2020"}},
                "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
                "conditionsModule": {"conditions": [f"Condition{i}", f"Condition{i+1}"]},
                "sponsorCollaboratorsModule": {"leadSponsor": {"name": f"Sponsor{i}"}},
                "armsInterventionsModule": {"interventions": [{"name": f"Drug{i}"}, {"name": f"Drug{i+1}"}]},
                "contactsLocationsModule": {"locations": [{"country": "US"}]},
            }
        })
    df = normalize_studies(studies)
    result, cmap = transform_network(df, phase_filter=None)
    # Should have been pruned to at most 50 nodes
    assert len(result["nodes"]) <= 50
    assert len(result["edges"]) > 0


def test_infer_distribution_dim_drug_name():
    req = QueryRequest(query="test", drug_name="Aspirin")
    import pandas as pd
    dim = _infer_distribution_dim(req, pd.DataFrame())
    assert dim == "primary_condition"


def test_infer_distribution_dim_country():
    req = QueryRequest(query="test", country="Germany")
    import pandas as pd
    dim = _infer_distribution_dim(req, pd.DataFrame())
    assert dim == "primary_country"


def test_infer_distribution_dim_condition():
    req = QueryRequest(query="test", condition="cancer")
    import pandas as pd
    dim = _infer_distribution_dim(req, pd.DataFrame())
    assert dim == "status"


def test_infer_distribution_dim_default():
    req = QueryRequest(query="test")
    import pandas as pd
    dim = _infer_distribution_dim(req, pd.DataFrame())
    assert dim == "phase_str"


def test_infer_ranking_dim():
    req = QueryRequest(query="test", condition="cancer")
    import pandas as pd
    dim = _infer_ranking_dim(req, pd.DataFrame())
    assert dim == "sponsor"


def test_infer_comparison_dims():
    req = QueryRequest(query="test", drug_name="Aspirin")
    import pandas as pd
    d1, d2 = _infer_comparison_dims(req, pd.DataFrame())
    assert d1 == "phase_str"
    assert d2 == "status"


def test_transformer_dispatch_all_intents(sample_study, sample_study_phase3):
    studies = [sample_study] * 3 + [sample_study_phase3] * 2
    t = Transformer()

    for intent in QueryIntent:
        req = QueryRequest(query="test")
        data, cmap = t.transform(intent, studies, phase_filter=None, request=req)
        # All intents should return something non-None
        assert data is not None


def test_transformer_dispatch_empty_studies():
    t = Transformer()
    import pandas as pd
    data, cmap = t.transform(QueryIntent.DISTRIBUTION, [], phase_filter=None, request=QueryRequest(query="test"))
    assert isinstance(data, pd.DataFrame)
    assert data.empty
    assert cmap == {}


def test_transformer_with_year_range(sample_study, sample_study_phase3):
    studies = [sample_study, sample_study_phase3]
    t = Transformer()
    req = QueryRequest(query="test", start_year=2019, end_year=2021)
    data, _ = t.transform(QueryIntent.TREND_OVER_TIME, studies, phase_filter=None, request=req)
    import pandas as pd
    if isinstance(data, pd.DataFrame) and not data.empty:
        assert all(data["start_year"] >= 2019)
        assert all(data["start_year"] <= 2021)


# ---------------------------------------------------------------------------
# _infer_ranking_dim — intervention keyword detection
# ---------------------------------------------------------------------------

def test_infer_ranking_dim_interventions_keyword():
    import pandas as pd
    req = QueryRequest(query="What are the top 5 most commonly used interventions in diabetes studies?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "interventions"


def test_infer_ranking_dim_drug_keyword():
    import pandas as pd
    req = QueryRequest(query="Which drugs are most common in phase 3 trials?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "interventions"


def test_infer_ranking_dim_treatment_keyword():
    import pandas as pd
    req = QueryRequest(query="Top treatments used in breast cancer trials")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "interventions"


def test_infer_ranking_dim_sponsor_when_no_keyword():
    import pandas as pd
    req = QueryRequest(query="Which sponsors have the most trials?", condition="cancer")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "sponsor"


def test_infer_ranking_dim_default_no_keywords():
    import pandas as pd
    req = QueryRequest(query="Who is leading the most studies?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "sponsor"


# ---------------------------------------------------------------------------
# _infer_ranking_dim — new dimension mappings
# ---------------------------------------------------------------------------

def test_infer_ranking_dim_country():
    import pandas as pd
    req = QueryRequest(query="Which countries conduct the most lung cancer clinical trials?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "primary_country"


def test_infer_ranking_dim_countries_plural():
    import pandas as pd
    req = QueryRequest(query="Top countries by trial count")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "primary_country"


def test_infer_ranking_dim_nation():
    import pandas as pd
    req = QueryRequest(query="Which nation runs the most cancer studies?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "primary_country"


def test_infer_ranking_dim_phase():
    import pandas as pd
    req = QueryRequest(query="Which phase has the most trials?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "phase_str"


def test_infer_ranking_dim_phases_plural():
    import pandas as pd
    req = QueryRequest(query="Show trial counts across phases")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "phase_str"


def test_infer_ranking_dim_status():
    import pandas as pd
    req = QueryRequest(query="What recruitment statuses are most common?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "status"


def test_infer_ranking_dim_recruiting_keyword():
    import pandas as pd
    req = QueryRequest(query="Which recruiting categories have the highest trial counts?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "status"


def test_infer_ranking_dim_sponsor_explicit():
    import pandas as pd
    req = QueryRequest(query="Which company sponsors the most cancer studies?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "sponsor"


def test_infer_ranking_dim_organization_keyword():
    import pandas as pd
    req = QueryRequest(query="Which organizations run the most trials?")
    assert _infer_ranking_dim(req, pd.DataFrame()) == "sponsor"


# ---------------------------------------------------------------------------
# _extract_top_n
# ---------------------------------------------------------------------------

def test_extract_top_n_explicit():
    assert _extract_top_n("What are the top 5 most common interventions?") == 5


def test_extract_top_n_different_number():
    assert _extract_top_n("Show me the top 10 sponsors") == 10


def test_extract_top_n_default_when_absent():
    assert _extract_top_n("Which interventions are most common?") == 20


def test_extract_top_n_custom_default():
    assert _extract_top_n("Any interventions?", default=15) == 15


# ---------------------------------------------------------------------------
# transform_ranking with rank_by="interventions"
# ---------------------------------------------------------------------------

def _make_diabetes_study(nct_id: str, interventions: list[str]) -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2021"}},
            "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": ["Diabetes"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor A"}},
            "armsInterventionsModule": {
                "interventions": [{"name": n} for n in interventions]
            },
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


def test_ranking_interventions_returns_intervention_names():
    studies = [
        _make_diabetes_study("NCT001", ["Metformin", "Lifestyle Intervention"]),
        _make_diabetes_study("NCT002", ["Metformin"]),
        _make_diabetes_study("NCT003", ["Insulin"]),
        _make_diabetes_study("NCT004", ["Metformin", "Insulin"]),
    ]
    df = normalize_studies(studies)
    result, cmap = transform_ranking(df, phase_filter=None, rank_by="interventions", top_n=20)

    assert list(result.columns) == ["category", "trial_count"]
    # Metformin appears in 3 studies — must be ranked first
    assert result.iloc[0]["category"] == "Metformin"
    assert result.iloc[0]["trial_count"] == 3
    # Insulin appears in 2 studies
    insulin_row = result[result["category"] == "Insulin"]
    assert len(insulin_row) == 1
    assert insulin_row.iloc[0]["trial_count"] == 2
    # No sponsor names in the output
    assert "Sponsor A" not in result["category"].values


def test_ranking_interventions_citation_map():
    studies = [
        _make_diabetes_study("NCT001", ["Metformin"]),
        _make_diabetes_study("NCT002", ["Metformin"]),
    ]
    df = normalize_studies(studies)
    _, cmap = transform_ranking(df, phase_filter=None, rank_by="interventions", top_n=20)

    assert "Metformin" in cmap
    assert set(cmap["Metformin"]) == {"NCT001", "NCT002"}


def test_ranking_interventions_respects_top_n():
    studies = [
        _make_diabetes_study(f"NCT{i:03d}", [f"Drug{i}", "Metformin"])
        for i in range(10)
    ]
    df = normalize_studies(studies)
    result, _ = transform_ranking(df, phase_filter=None, rank_by="interventions", top_n=3)
    assert len(result) <= 3


def test_ranking_interventions_empty_lists_handled():
    """Studies with no interventions should not produce empty-string rows."""
    studies = [
        _make_diabetes_study("NCT001", []),
        _make_diabetes_study("NCT002", ["Metformin"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_ranking(df, phase_filter=None, rank_by="interventions", top_n=20)
    assert "" not in result["category"].values
    assert result.iloc[0]["category"] == "Metformin"


def test_ranking_interventions_all_empty_returns_empty_df():
    studies = [_make_diabetes_study("NCT001", []), _make_diabetes_study("NCT002", [])]
    df = normalize_studies(studies)
    result, cmap = transform_ranking(df, phase_filter=None, rank_by="interventions", top_n=20)
    assert result.empty
    assert cmap == {}


# ---------------------------------------------------------------------------
# End-to-end: Transformer dispatcher picks up "top 5 interventions"
# ---------------------------------------------------------------------------

def test_transformer_dispatch_intervention_ranking():
    studies = [
        _make_diabetes_study("NCT001", ["Metformin", "Lifestyle Intervention"]),
        _make_diabetes_study("NCT002", ["Metformin"]),
        _make_diabetes_study("NCT003", ["Insulin"]),
    ]
    t = Transformer()
    req = QueryRequest(
        query="What are the top 5 most commonly used interventions in studies related to diabetes?",
        condition="diabetes",
    )
    result, cmap = t.transform(QueryIntent.RANKING, studies, phase_filter=None, request=req)
    import pandas as pd
    assert isinstance(result, pd.DataFrame)
    assert "category" in result.columns
    assert "trial_count" in result.columns
    assert len(result) <= 5
    # Metformin should be ranked first (2 studies)
    assert result.iloc[0]["category"] == "Metformin"
    assert "Sponsor A" not in result["category"].values


# ---------------------------------------------------------------------------
# End-to-end: Transformer dispatcher picks up country ranking
# ---------------------------------------------------------------------------

def _make_country_study(nct_id: str, country: str) -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2021"}},
            "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": ["Lung Cancer"]},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor X"}},
            "armsInterventionsModule": {"interventions": [{"name": "Chemo"}]},
            "contactsLocationsModule": {"locations": [{"country": country}]},
        }
    }


def test_transformer_dispatch_country_ranking():
    import pandas as pd
    studies = (
        [_make_country_study(f"NCT1{i:02d}", "US") for i in range(5)]
        + [_make_country_study(f"NCT2{i:02d}", "China") for i in range(3)]
        + [_make_country_study(f"NCT3{i:02d}", "Korea") for i in range(2)]
    )
    t = Transformer()
    req = QueryRequest(query="Which countries conduct the most lung cancer clinical trials?")
    result, _ = t.transform(QueryIntent.RANKING, studies, phase_filter=None, request=req)
    assert isinstance(result, pd.DataFrame)
    assert "category" in result.columns
    # US has most studies — must be top
    assert result.iloc[0]["category"] == "US"
    # Sponsor should NOT appear
    assert "Sponsor X" not in result["category"].values
