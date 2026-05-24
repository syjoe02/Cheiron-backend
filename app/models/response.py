from pydantic import BaseModel, ConfigDict
from typing import Any, Literal


class Citation(BaseModel):
    nct_id: str
    excerpt: str  # <= 200 chars


class DataPoint(BaseModel):
    model_config = ConfigDict(extra="allow") # access any additional fields
    citations: list[Citation] = []


class VizSpec(BaseModel):
    # prevent hallucination of visualization types
    type: Literal[
        "bar_chart",
        "grouped_bar_chart",
        "time_series",
        "scatter_plot",
        "histogram",
        "network_graph",
    ]
    title: str
    encoding: dict[str, Any] # X,Y axis definitions
    data: list[DataPoint]

# response model to frontend
class VisualizationResponse(BaseModel):
    visualization: VizSpec
    meta: dict[str, Any]
    # meta keys (example): filters_applied, source, query_interpretation,
    #            assumptions, trial_count, total_matching, data_timestamp
