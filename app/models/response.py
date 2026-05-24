from pydantic import BaseModel, ConfigDict
from typing import Any, Literal


class Citation(BaseModel):
    nct_id: str
    excerpt: str  # ≤200 chars from briefTitle or relevant field


class DataPoint(BaseModel):
    model_config = ConfigDict(extra="allow")
    citations: list[Citation] = []


class VizSpec(BaseModel):
    type: Literal[
        "bar_chart",
        "grouped_bar_chart",
        "time_series",
        "scatter_plot",
        "histogram",
        "network_graph",
    ]
    title: str
    encoding: dict[str, Any]
    data: list[DataPoint]


class VisualizationResponse(BaseModel):
    visualization: VizSpec
    meta: dict[str, Any]
    # meta keys: filters_applied, source, query_interpretation,
    #            assumptions, trial_count, total_matching, data_timestamp
