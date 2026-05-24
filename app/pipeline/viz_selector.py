from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.pipeline.query_parser import QueryIntent

# Default chart type per intent — used as both the suggestion hint and the fallback
INTENT_DEFAULT_TYPE: dict[QueryIntent, str] = {
    QueryIntent.TREND_OVER_TIME: "time_series",
    QueryIntent.DISTRIBUTION: "bar_chart",
    QueryIntent.COMPARISON: "grouped_bar_chart",
    QueryIntent.CORRELATION: "scatter_plot",
    QueryIntent.RELATIONSHIP_NETWORK: "network_graph",
    QueryIntent.RANKING: "bar_chart",
    QueryIntent.OUTLIER_ANALYSIS: "scatter_plot",
}

# Intent-specific encoding overrides for the rule-based fallback path.
# Takes precedence over _FALLBACK_ENCODINGS when set.
_INTENT_ENCODING_OVERRIDES: dict[QueryIntent, dict[str, Any]] = {
    QueryIntent.COMPARISON: {
        "x": {"field": "category", "type": "nominal"},
        "y": {"field": "trial_count", "type": "quantitative"},
        "series": {"field": "entity", "type": "nominal"},
    },
    QueryIntent.OUTLIER_ANALYSIS: {
        "x": {"field": "enrollment", "type": "quantitative"},
        "y": {"field": "z_score", "type": "quantitative"},
        "color": {"field": "phase_str", "type": "nominal"},
        "label": {"field": "nct_id", "type": "nominal"},
    },
}

# Rule-based encoding fallbacks per chart type
_FALLBACK_ENCODINGS: dict[str, dict[str, Any]] = {
    "time_series": {
        "x": {"field": "start_year", "type": "temporal"},
        "y": {"field": "trial_count", "type": "quantitative"},
    },
    "bar_chart": {
        "x": {"field": "category", "type": "nominal"},
        "y": {"field": "trial_count", "type": "quantitative"},
    },
    "grouped_bar_chart": {
        "x": {"field": "group1", "type": "nominal"},
        "y": {"field": "trial_count", "type": "quantitative"},
        "series": {"field": "group2", "type": "nominal"},
    },
    "scatter_plot": {
        "x": {"field": "start_year", "type": "quantitative"},
        "y": {"field": "enrollment", "type": "quantitative"},
        "color": {"field": "phase_str", "type": "nominal"},
    },
    "histogram": {
        "x": {"field": "enrollment", "type": "quantitative", "bin": True},
        "y": {"field": "count", "type": "quantitative"},
    },
    "network_graph": {
        "nodes": {"id": "id", "label": "label", "size": "size", "color": "type"},
        "edges": {"source": "source", "target": "target", "weight": "weight"},
    },
}


class VizSpecOutput(BaseModel):
    chart_type: str
    title: str
    encoding: dict[str, Any]
    sort_order: str | None = None
    time_granularity: str | None = None
    units: str | None = None
    assumptions: list[str] = []


_SYSTEM_PROMPT = """\
You are a data visualization expert for clinical trial data.
Given metadata about a dataset, produce a visualization specification.

IMPORTANT: Return ONLY schema-level information. Do NOT include any actual data values.
The encoding must reference field NAMES only — not values.

Choose chart_type from:
bar_chart, grouped_bar_chart, time_series, scatter_plot, histogram, network_graph

Encoding format per chart type:
- bar_chart / histogram:
  {"x": {"field": "...", "type": "nominal|ordinal"}, "y": {"field": "...", "type": "quantitative"}}
- time_series:
  {"x": {"field": "start_year", "type": "temporal"}, "y": {"field": "trial_count", "type": "quantitative"}}
- grouped_bar_chart:
  {"x": {"field": "...", "type": "nominal"}, "y": {"field": "...", "type": "quantitative"},
   "series": {"field": "...", "type": "nominal"}}
- scatter_plot:
  {"x": {"field": "...", "type": "quantitative"}, "y": {"field": "...", "type": "quantitative"},
   "color": {"field": "...", "type": "nominal"}}
- network_graph:
  {"nodes": {"id": "id", "label": "label", "size": "size", "color": "type"},
   "edges": {"source": "source", "target": "target", "weight": "weight"}}

Generate a clear, descriptive title for the chart based on the query interpretation.
"""


class VizSelector:
    def __init__(self, openai_client: AsyncOpenAI, model: str = "gpt-4.1") -> None:
        self._client = openai_client
        self._model = model

    async def select(
        self,
        intent: QueryIntent,
        columns: list[str],
        row_count: int,
        sample_row: dict[str, Any],
        query_interpretation: str,
    ) -> VizSpecOutput:
        suggested_type = INTENT_DEFAULT_TYPE.get(intent, "bar_chart")

        schema_desc = (
            f"Intent: {intent.value}\n"
            f"Columns available: {columns}\n"
            f"Number of data rows: {row_count}\n"
            f"Field names in sample row: {list(sample_row.keys())}\n"
            f"Query interpretation: {query_interpretation}\n"
            f"Suggested chart type: {suggested_type}"
        )

        try:
            completion = await self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": schema_desc},
                ],
                response_format=VizSpecOutput,
                temperature=0,
            )
            result: VizSpecOutput = completion.choices[0].message.parsed  # type: ignore[assignment]
            # Validate chart_type is one of the allowed values
            allowed = set(INTENT_DEFAULT_TYPE.values()) | {"histogram"}
            if result.chart_type not in allowed:
                result.chart_type = suggested_type
            return result
        except Exception:
            return _rule_based_viz(intent, columns, query_interpretation)


def _rule_based_viz(
    intent: QueryIntent,
    columns: list[str],  # noqa: ARG001
    query_interpretation: str,
) -> VizSpecOutput:
    chart_type = INTENT_DEFAULT_TYPE.get(intent, "bar_chart")
    encoding = (
        _INTENT_ENCODING_OVERRIDES.get(intent)
        or _FALLBACK_ENCODINGS.get(chart_type, {})
    )
    return VizSpecOutput(
        chart_type=chart_type,
        title=query_interpretation,
        encoding=encoding,
        assumptions=["Visualization type determined by rule-based fallback"],
    )
