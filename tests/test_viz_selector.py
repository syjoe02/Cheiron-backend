from app.pipeline.query_parser import QueryIntent
from app.pipeline.viz_selector import (
    INTENT_DEFAULT_TYPE,
    VizSpecOutput,
    _rule_based_viz,
)


def test_intent_default_type_covers_all_intents():
    for intent in QueryIntent:
        assert intent in INTENT_DEFAULT_TYPE


def test_rule_based_viz_trend():
    result = _rule_based_viz(QueryIntent.TREND_OVER_TIME, ["start_year", "trial_count"], "Trend over time")
    assert result.chart_type == "time_series"
    assert "x" in result.encoding
    assert "y" in result.encoding


def test_rule_based_viz_network():
    result = _rule_based_viz(QueryIntent.RELATIONSHIP_NETWORK, ["nodes", "edges"], "Drug network")
    assert result.chart_type == "network_graph"
    assert "nodes" in result.encoding
    assert "edges" in result.encoding


def test_rule_based_viz_distribution():
    result = _rule_based_viz(QueryIntent.DISTRIBUTION, ["category", "trial_count"], "Distribution")
    assert result.chart_type == "bar_chart"


def test_rule_based_viz_ranking():
    result = _rule_based_viz(QueryIntent.RANKING, ["category", "trial_count"], "Top sponsors")
    assert result.chart_type == "bar_chart"


def test_rule_based_viz_comparison():
    result = _rule_based_viz(QueryIntent.COMPARISON, ["group1", "group2", "trial_count"], "Comparison")
    assert result.chart_type == "grouped_bar_chart"


def test_rule_based_viz_correlation():
    result = _rule_based_viz(QueryIntent.CORRELATION, ["start_year", "enrollment"], "Scatter")
    assert result.chart_type == "scatter_plot"


def test_viz_spec_output_defaults():
    out = VizSpecOutput(chart_type="bar_chart", title="Test", encoding={})
    assert out.sort_order is None
    assert out.time_granularity is None
    assert out.units is None
    assert out.assumptions == []
