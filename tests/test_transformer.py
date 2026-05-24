from app.pipeline.transformer import (
    normalize_studies,
    transform_correlation,
    transform_distribution,
    transform_network,
    transform_ranking,
    transform_trend,
)


def test_normalize_extracts_start_year(sample_study):
    df = normalize_studies([sample_study])
    assert len(df) == 1
    assert df.iloc[0]["start_year"] == 2020
    assert df.iloc[0]["nct_id"] == "NCT12345678"
    assert df.iloc[0]["status"] == "RECRUITING"


def test_normalize_partial_date(sample_study):
    sample_study["protocolSection"]["statusModule"]["startDateStruct"]["date"] = "2018-06"
    df = normalize_studies([sample_study])
    assert df.iloc[0]["start_year"] == 2018


def test_normalize_missing_date(sample_study):
    del sample_study["protocolSection"]["statusModule"]["startDateStruct"]
    df = normalize_studies([sample_study])
    assert df.iloc[0]["start_year"] is None


def test_normalize_empty_studies():
    df = normalize_studies([])
    assert df.empty


def test_trend_groups_by_year(sample_study, sample_study_phase3):
    studies = [sample_study] * 3 + [sample_study_phase3] * 2
    df_result, cmap = transform_trend(normalize_studies(studies), phase_filter=None)
    assert 2020 in df_result["start_year"].values
    assert 2018 in df_result["start_year"].values
    assert df_result.loc[df_result["start_year"] == 2020, "trial_count"].iloc[0] == 3
    assert df_result.loc[df_result["start_year"] == 2018, "trial_count"].iloc[0] == 2


def test_trend_phase_filter(sample_study, sample_study_phase3):
    studies = [sample_study, sample_study_phase3]
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=["PHASE3"])
    # Only PHASE3 study (2018) should remain
    assert len(result) == 1
    assert result.iloc[0]["start_year"] == 2018


def test_trend_year_range_filter(sample_study, sample_study_phase3):
    studies = [sample_study] * 2 + [sample_study_phase3]
    df = normalize_studies(studies)
    result, _ = transform_trend(df, phase_filter=None, start_year=2019)
    assert all(result["start_year"] >= 2019)


def test_trend_citation_map(sample_study):
    df = normalize_studies([sample_study] * 3)
    _, cmap = transform_trend(df, phase_filter=None)
    assert "2020" in cmap
    assert len(cmap["2020"]) == 3
    assert all(nct == "NCT12345678" for nct in cmap["2020"])


def test_distribution_groups_by_phase(sample_study):
    df = normalize_studies([sample_study] * 5)
    result, cmap = transform_distribution(df, phase_filter=None, group_by="phase_str")
    assert len(result) == 1
    assert result.iloc[0]["trial_count"] == 5


def test_ranking_returns_top_n(sample_study, sample_study_phase3):
    studies = [sample_study] * 7 + [sample_study_phase3] * 3
    df = normalize_studies(studies)
    result, _ = transform_ranking(df, phase_filter=None, rank_by="sponsor", top_n=5)
    assert len(result) <= 5
    # Test University has more trials — should be ranked first
    assert result.iloc[0]["category"] == "Test University"


def test_correlation_filters_missing_enrollment(sample_study):
    no_enrollment = dict(sample_study)
    no_enrollment["protocolSection"] = dict(sample_study["protocolSection"])
    no_enrollment["protocolSection"]["designModule"] = {
        "phases": ["PHASE2"],
        "enrollmentInfo": None,
    }
    studies = [sample_study, no_enrollment]
    df = normalize_studies(studies)
    result, _ = transform_correlation(df, phase_filter=None)
    # Row with no enrollment should be excluded
    assert result["enrollment"].notna().all()


def test_network_builds_nodes_and_edges(sample_study, sample_study_phase3):
    studies = [sample_study] * 5 + [sample_study_phase3] * 5
    df = normalize_studies(studies)
    result, cmap = transform_network(df, phase_filter=None)
    assert "nodes" in result
    assert "edges" in result
    assert len(result["nodes"]) > 0
    assert len(result["edges"]) > 0
    # Each edge should have source, target, weight
    for edge in result["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "weight" in edge


def test_network_citation_map_populated(sample_study):
    studies = [sample_study] * 3
    df = normalize_studies(studies)
    _, cmap = transform_network(df, phase_filter=None)
    # Citation map keys should be "source|target" strings
    for key in cmap:
        assert "|" in key
        assert len(cmap[key]) > 0
