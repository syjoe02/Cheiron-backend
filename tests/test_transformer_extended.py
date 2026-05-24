"""Tests covering transformer branches not exercised by test_transformer.py."""
from unittest.mock import MagicMock

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transformer import (
    Transformer,
    _apply_year_filter,
    _infer_comparison_dims,
    _infer_distribution_dim,
    _infer_ranking_dim,
    normalize_studies,
    transform_comparison,
    transform_network,
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
