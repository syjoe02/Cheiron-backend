"""Tests for the improved transform_network pipeline: normalisation, filtering, pruning."""
from app.pipeline.transformer import (
    _is_condition_relevant,
    _is_stop_term,
    _normalize_entity,
    normalize_studies,
    transform_network,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_net_study(nct_id: str, interventions: list[str], conditions: list[str]) -> dict:
    return {
        "protocolSection": {
            "identificationModule": {"nctId": nct_id, "briefTitle": f"Study {nct_id}"},
            "statusModule": {"overallStatus": "RECRUITING", "startDateStruct": {"date": "2021"}},
            "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 100}},
            "conditionsModule": {"conditions": conditions},
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Sponsor A"}},
            "armsInterventionsModule": {"interventions": [{"name": n} for n in interventions]},
            "contactsLocationsModule": {"locations": [{"country": "US"}]},
        }
    }


# ---------------------------------------------------------------------------
# _normalize_entity
# ---------------------------------------------------------------------------

def test_normalize_known_alias():
    assert _normalize_entity("Type 2 Diabetes") == "T2DM"


def test_normalize_case_insensitive():
    assert _normalize_entity("DIABETES MELLITUS, TYPE 2") == "T2DM"


def test_normalize_whitespace_stripped():
    assert _normalize_entity("  Breast Cancer  ") == "Breast Cancer"


def test_normalize_unknown_returns_stripped_original():
    assert _normalize_entity("  Some Rare Condition  ") == "Some Rare Condition"


def test_normalize_breast_neoplasms():
    assert _normalize_entity("breast neoplasms") == "Breast Cancer"


def test_normalize_nsclc_variant():
    assert _normalize_entity("Carcinoma, Non-Small-Cell Lung") == "NSCLC"


def test_normalize_covid_variant():
    assert _normalize_entity("SARS-CoV-2 Infection") == "COVID-19"


# ---------------------------------------------------------------------------
# _is_stop_term
# ---------------------------------------------------------------------------

def test_stop_term_placebo():
    assert _is_stop_term("Placebo") is True


def test_stop_term_questionnaire():
    assert _is_stop_term("Questionnaire") is True


def test_stop_term_case_insensitive():
    assert _is_stop_term("USUAL CARE") is True


def test_stop_term_biomedical_drug_not_filtered():
    assert _is_stop_term("Metformin") is False


def test_stop_term_insulin_not_filtered():
    assert _is_stop_term("Insulin") is False


def test_stop_term_placebo_comparator():
    assert _is_stop_term("Placebo Comparator") is True


# ---------------------------------------------------------------------------
# Stop-term filtering in transform_network
# ---------------------------------------------------------------------------

def test_stop_terms_excluded_from_graph():
    studies = [_make_net_study("NCT001", ["Metformin", "Placebo"], ["T2DM"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "Placebo" not in node_ids
    assert "Metformin" in node_ids


def test_all_stop_terms_produce_empty_graph():
    studies = [_make_net_study("NCT001", ["Placebo", "Usual Care"], ["T2DM"])]
    df = normalize_studies(studies)
    result, cmap = transform_network(df, phase_filter=None)
    assert result["nodes"] == []
    assert result["edges"] == []
    assert cmap == {}


# ---------------------------------------------------------------------------
# Entity normalisation merges aliases into one node
# ---------------------------------------------------------------------------

def test_normalization_merges_condition_aliases():
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["Type 2 Diabetes"]),
        _make_net_study("NCT002", ["Insulin"], ["Diabetes Mellitus, Type 2"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "T2DM" in node_ids
    assert "Type 2 Diabetes" not in node_ids
    assert "Diabetes Mellitus, Type 2" not in node_ids


def test_normalization_aggregates_edge_weight():
    """Both NCT001 and NCT002 map to Metformin -> T2DM after normalisation."""
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["Type 2 Diabetes"]),
        _make_net_study("NCT002", ["Metformin"], ["Diabetes Mellitus, Type 2"]),
    ]
    df = normalize_studies(studies)
    result, cmap = transform_network(df, phase_filter=None)
    edge = next(e for e in result["edges"] if e["source"] == "Metformin")
    assert edge["weight"] == 2
    assert set(cmap["Metformin|T2DM"]) == {"NCT001", "NCT002"}


# ---------------------------------------------------------------------------
# Edge direction: always Intervention -> Condition
# ---------------------------------------------------------------------------

def test_edges_direction_intervention_to_condition():
    studies = [_make_net_study("NCT001", ["Metformin", "Insulin"], ["T2DM", "Obesity"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_by_id = {n["id"]: n for n in result["nodes"]}
    for edge in result["edges"]:
        assert node_by_id[edge["source"]]["type"] == "intervention"
        assert node_by_id[edge["target"]]["type"] == "condition"


def test_no_condition_to_intervention_edges():
    studies = [_make_net_study("NCT001", ["Metformin"], ["T2DM"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_by_id = {n["id"]: n for n in result["nodes"]}
    for edge in result["edges"]:
        # source must never be a condition
        assert node_by_id[edge["source"]]["type"] != "condition"


# ---------------------------------------------------------------------------
# Isolated node removal
# ---------------------------------------------------------------------------

def test_isolated_nodes_removed_when_stop_terms_only():
    # T2DM becomes isolated because its only connected intervention is Placebo
    studies = [_make_net_study("NCT001", ["Placebo"], ["T2DM"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "T2DM" not in node_ids


def test_non_isolated_nodes_retained():
    studies = [_make_net_study("NCT001", ["Metformin"], ["T2DM"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "Metformin" in node_ids
    assert "T2DM" in node_ids


# ---------------------------------------------------------------------------
# min_edge_weight filtering
# ---------------------------------------------------------------------------

def test_min_edge_weight_removes_low_weight_edges():
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["T2DM"]),  # weight=1
        _make_net_study("NCT002", ["Insulin"], ["T2DM"]),     # weight=1
        _make_net_study("NCT003", ["Insulin"], ["T2DM"]),     # Insulin weight becomes 2
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, min_edge_weight=2)
    edge_sources = {e["source"] for e in result["edges"]}
    assert "Metformin" not in edge_sources
    assert "Insulin" in edge_sources


def test_min_edge_weight_1_keeps_all_edges():
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["T2DM"]),
        _make_net_study("NCT002", ["Insulin"], ["T2DM"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, min_edge_weight=1)
    edge_sources = {e["source"] for e in result["edges"]}
    assert "Metformin" in edge_sources
    assert "Insulin" in edge_sources


def test_min_edge_weight_removes_newly_isolated_nodes():
    # After removing Metformin->T2DM (weight=1), Metformin becomes isolated
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["T2DM"]),
        _make_net_study("NCT002", ["Insulin"], ["T2DM"]),
        _make_net_study("NCT003", ["Insulin"], ["T2DM"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, min_edge_weight=2)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "Metformin" not in node_ids


# ---------------------------------------------------------------------------
# Node metadata: degree and size
# ---------------------------------------------------------------------------

def test_node_has_degree_field():
    studies = [_make_net_study("NCT001", ["Metformin"], ["T2DM"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    for node in result["nodes"]:
        assert "degree" in node
        assert node["degree"] >= 1  # isolated nodes are removed


def test_node_size_max_degree_gets_100():
    """The node with the highest degree should have size=100."""
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["T2DM"]),
        _make_net_study("NCT002", ["Insulin"], ["T2DM"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    # T2DM has in-degree=2, Metformin/Insulin each have out-degree=1 → T2DM has highest total degree
    t2dm = next(n for n in result["nodes"] if n["id"] == "T2DM")
    assert t2dm["size"] == 100.0


def test_node_size_lower_degree_less_than_100():
    studies = [
        _make_net_study("NCT001", ["Metformin"], ["T2DM"]),
        _make_net_study("NCT002", ["Insulin"], ["T2DM"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    metformin = next(n for n in result["nodes"] if n["id"] == "Metformin")
    assert metformin["size"] < 100.0


# ---------------------------------------------------------------------------
# Graph pruning (top-50)
# ---------------------------------------------------------------------------

def test_graph_pruned_to_50_nodes():
    """Graph with >50 candidate nodes should be pruned."""
    studies = [
        _make_net_study(f"NCT{i:04d}", [f"Drug{i}"], [f"Condition{i}", f"Condition{i + 1}"])
        for i in range(40)
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    assert len(result["nodes"]) <= 50


def test_empty_studies_returns_empty_graph():
    import pandas as pd
    result, cmap = transform_network(pd.DataFrame(), phase_filter=None)
    assert result["nodes"] == []
    assert result["edges"] == []
    assert cmap == {}


# ---------------------------------------------------------------------------
# Case normalization — "Carboplatin" and "carboplatin" must produce one node
# ---------------------------------------------------------------------------

def test_lowercase_entity_normalized_to_title_case():
    assert _normalize_entity("carboplatin") == "Carboplatin"


def test_uppercase_entity_normalized_to_title_case():
    assert _normalize_entity("CARBOPLATIN") == "Carboplatin"


def test_mixed_case_deduplicates_in_graph():
    """Studies using "Carboplatin" and "carboplatin" must produce a single node."""
    studies = [
        _make_net_study("NCT001", ["Carboplatin"], ["Lung Cancer"]),
        _make_net_study("NCT002", ["carboplatin"], ["Lung Cancer"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    carboplatin_nodes = [n for n in result["nodes"] if n["id"].lower() == "carboplatin"]
    assert len(carboplatin_nodes) == 1


def test_case_normalized_edge_weight_aggregated():
    """Edge weight must reflect both studies after case normalization."""
    studies = [
        _make_net_study("NCT001", ["Carboplatin"], ["Lung Cancer"]),
        _make_net_study("NCT002", ["carboplatin"], ["Lung Cancer"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    carboplatin_edge = next(
        e for e in result["edges"] if e["source"].lower() == "carboplatin"
    )
    assert carboplatin_edge["weight"] == 2


# ---------------------------------------------------------------------------
# Self-loop removal
# ---------------------------------------------------------------------------

def test_self_loop_not_added_to_graph():
    """A study where the same name appears as both intervention and condition must produce no edge."""
    studies = [_make_net_study("NCT001", ["Glycopyrrolate"], ["Glycopyrrolate"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    for edge in result["edges"]:
        assert edge["source"] != edge["target"]


def test_self_loop_via_normalization_not_added():
    """Aliases that normalize to the same canonical form must not produce a self-loop."""
    studies = [_make_net_study("NCT001", ["Breast Neoplasms"], ["Breast Cancer"])]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    for edge in result["edges"]:
        assert edge["source"] != edge["target"]


def test_valid_edges_still_present_after_self_loop_removal():
    """Self-loop removal must not discard valid Intervention -> Condition edges."""
    studies = [
        _make_net_study("NCT001", ["Metformin", "Glycopyrrolate"], ["Glycopyrrolate"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    sources = {e["source"] for e in result["edges"]}
    assert "Metformin" in sources


# ---------------------------------------------------------------------------
# Multi-word noise filtering
# ---------------------------------------------------------------------------

def test_questionnaire_administration_filtered():
    assert _is_stop_term("Questionnaire Administration") is True


def test_quality_of_life_assessment_filtered():
    assert _is_stop_term("Quality-of-Life Assessment") is True


def test_serum_collection_filtered():
    assert _is_stop_term("Serum Collection") is True


def test_multi_word_stop_term_excluded_from_graph():
    studies = [
        _make_net_study("NCT001", ["Metformin", "Quality-of-Life Assessment"], ["T2DM"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert not any("quality" in nid.lower() for nid in node_ids)
    assert "Metformin" in node_ids


def test_biomedical_drug_not_affected_by_substring_check():
    """Drug names that happen to contain a stop-word substring must not be filtered."""
    # "Serum albumin" contains "serum" but " collection" is the actual stop-substring
    # so "Serum Albumin" (no " collection" substring) must survive
    assert _is_stop_term("Serum Albumin") is False


# ---------------------------------------------------------------------------
# Query relevance filtering
# ---------------------------------------------------------------------------

def test_relevance_filters_unrelated_conditions():
    """When query_condition='lung cancer', breast cancer conditions should be excluded."""
    studies = [
        _make_net_study("NCT001", ["Carboplatin"], ["Lung Cancer", "Breast Cancer"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, query_condition="lung cancer")
    node_ids = [n["id"] for n in result["nodes"]]
    assert "Breast Cancer" not in node_ids
    assert "Lung Cancer" in node_ids


def test_relevance_keeps_domain_synonyms():
    """NSCLC must be retained when query_condition is 'lung cancer'."""
    studies = [
        _make_net_study("NCT001", ["Carboplatin"], ["NSCLC"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, query_condition="lung cancer")
    node_ids = [n["id"] for n in result["nodes"]]
    assert "NSCLC" in node_ids


def test_relevance_none_keeps_all_conditions():
    """Without query_condition, all conditions must be included in the graph."""
    studies = [
        _make_net_study("NCT001", ["Carboplatin"], ["Lung Cancer", "Breast Cancer"]),
    ]
    df = normalize_studies(studies)
    result, _ = transform_network(df, phase_filter=None, query_condition=None)
    node_ids = [n["id"] for n in result["nodes"]]
    assert "Lung Cancer" in node_ids
    assert "Breast Cancer" in node_ids


def test_is_condition_relevant_same_domain():
    assert _is_condition_relevant("NSCLC", "lung cancer") is True


def test_is_condition_relevant_different_domain():
    assert _is_condition_relevant("Breast Cancer", "lung cancer") is False


def test_is_condition_relevant_direct_substring():
    assert _is_condition_relevant("Non-Small-Cell Lung Cancer", "lung cancer") is True
