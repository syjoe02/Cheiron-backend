from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.models.request import QueryRequest
from app.pipeline.dim_inference import (  # noqa: F401
    _extract_top_n,
    _infer_comparison_dims,
    _infer_comparison_group_by,
    _infer_distribution_dim,
    _infer_ranking_dim,
)
from app.pipeline.entity_filters import (  # noqa: F401
    CONDITION_HIERARCHY,
    NORMALIZATION_MAP,
    STOP_TERMS,
    _get_condition_domain,
    _is_condition_relevant,
    _is_stop_term,
    _normalize_entity,
)
from app.pipeline.normalizers import (  # noqa: F401
    _apply_phase_filter,
    _apply_year_filter,
    _normalize_phase,
    normalize_studies,
)
from app.pipeline.phase_strategy import (  # noqa: F401
    InclusiveHybridStrategy,
    PhaseStrategy,
    StrictFilterStrategy,
    choose_strategy,
    phase_meta_for,
)
from app.pipeline.query_parser import QueryIntent
from app.pipeline.transforms.comparison import (  # noqa: F401
    generate_comparison_insight,
    transform_entity_comparison,
)
from app.pipeline.transforms.network import transform_network  # noqa: F401
from app.pipeline.transforms.tabular import (  # noqa: F401
    transform_comparison,
    transform_correlation,
    transform_distribution,
    transform_outlier_analysis,
    transform_ranking,
    transform_trend,
)

_logger = logging.getLogger(__name__)


@dataclass
class TransformResult:
    """Wraps transform output with backward-compatible 2-tuple unpacking."""

    data: Any
    citation_map: dict[str, list[str]]
    phase_meta: dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        # Allows: data, cmap = transform_result  (backward compatible)
        yield self.data
        yield self.citation_map


def _log_filter_diagnostics(
    df: pd.DataFrame,
    request: QueryRequest,
    phase_filter: list[str] | None,
) -> None:
    """Log row counts at each filter stage to validate multi-filter query execution."""
    total = len(df)
    _logger.debug("[filter-diagnostics] total rows after normalize: %d", total)

    if request.condition:
        cond_lower = request.condition.lower()
        cond_match = int(
            df["conditions"]
            .apply(lambda cs: any(cond_lower in c.lower() for c in cs))
            .sum()
        )
        _logger.debug(
            "[filter-diagnostics] rows matching condition '%s': %d / %d",
            request.condition,
            cond_match,
            total,
        )

    if request.country:
        country_lower = request.country.lower()
        country_match = int(
            df["countries"]
            .apply(lambda cs: any(country_lower in c.lower() for c in cs))
            .sum()
        )
        _logger.debug(
            "[filter-diagnostics] rows matching country '%s': %d / %d",
            request.country,
            country_match,
            total,
        )

    phase_df = _apply_phase_filter(df, phase_filter)
    _logger.debug(
        "[filter-diagnostics] rows after phase filter %s: %d / %d",
        phase_filter,
        len(phase_df),
        total,
    )

    sample_cols = [c for c in ["nct_id", "phase_str", "primary_country", "conditions"] if c in df.columns]
    _logger.debug(
        "[filter-diagnostics] sample (top 10):\n%s",
        df[sample_cols].head(10).to_string(),
    )


class Transformer:
    def transform(
        self,
        intent: QueryIntent,
        studies: list[dict[str, Any]],
        phase_filter: list[str] | None,
        request: QueryRequest,
    ) -> TransformResult:
        df = normalize_studies(studies)
        if df.empty:
            return TransformResult(pd.DataFrame(), {})

        _log_filter_diagnostics(df, request, phase_filter)

        strategy = choose_strategy(phase_filter)
        sy = request.start_year
        ey = request.end_year

        match intent:
            case QueryIntent.TREND_OVER_TIME:
                data, cmap = transform_trend(df, phase_filter, sy, ey)
            case QueryIntent.DISTRIBUTION:
                dim = _infer_distribution_dim(request, df)
                data, cmap = transform_distribution(df, phase_filter, dim, sy, ey, strategy=strategy)
            case QueryIntent.COMPARISON:
                d1, d2 = _infer_comparison_dims(request, df)
                data, cmap = transform_comparison(df, phase_filter, d1, d2, sy, ey)
            case QueryIntent.CORRELATION:
                data, cmap = transform_correlation(df, phase_filter, sy, ey)
            case QueryIntent.RELATIONSHIP_NETWORK:
                data, cmap = transform_network(df, phase_filter, sy, ey, query_condition=request.condition)
            case QueryIntent.RANKING:
                dim = _infer_ranking_dim(request, df)
                top_n = _extract_top_n(request.query)
                data, cmap = transform_ranking(df, phase_filter, dim, top_n, sy, ey)
            case QueryIntent.OUTLIER_ANALYSIS:
                data, cmap = transform_outlier_analysis(df, phase_filter, start_year=sy, end_year=ey)
            case _:
                data, cmap = transform_distribution(df, phase_filter, "phase_str", sy, ey, strategy=strategy)

        return TransformResult(data, cmap, phase_meta_for(strategy, phase_filter))

    def transform_comparison_entities(
        self,
        entity_studies: dict[str, list[dict[str, Any]]],
        phase_filter: list[str] | None,
        request: QueryRequest,
    ) -> TransformResult:
        """Entry point for multi-entity comparison queries (X vs Y)."""
        combined_studies = [s for studies in entity_studies.values() for s in studies]
        if combined_studies:
            combined_df = normalize_studies(combined_studies)
            if not combined_df.empty:
                _log_filter_diagnostics(combined_df, request, phase_filter)

        strategy = choose_strategy(phase_filter)
        group_by = _infer_comparison_group_by(request.query)
        data, cmap = transform_entity_comparison(
            entity_studies,
            phase_filter,
            group_by,
            request.start_year,
            request.end_year,
            strategy=strategy,
        )
        return TransformResult(data, cmap, phase_meta_for(strategy, phase_filter))
