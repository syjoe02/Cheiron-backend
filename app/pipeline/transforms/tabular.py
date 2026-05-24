from __future__ import annotations

import pandas as pd

from app.pipeline.normalizers import (
    _apply_phase_filter,
    _apply_year_filter,
    _normalize_phase,
)
from app.pipeline.phase_strategy import PhaseStrategy, StrictFilterStrategy


def transform_trend(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)
    df = df[df["start_year"].notna()].copy()
    df["start_year"] = df["start_year"].astype(int)

    grouped = (
        df.groupby("start_year")
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
        .sort_values("start_year")
    )
    citation_map = {
        str(row["start_year"]): row["nct_ids"]
        for _, row in grouped.iterrows()
    }
    return grouped.drop(columns=["nct_ids"]), citation_map


def transform_distribution(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    group_by: str = "phase_str",
    start_year: int | None = None,
    end_year: int | None = None,
    strategy: PhaseStrategy | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    if group_by == "phase_str":
        # Strict mode: studies already filtered by _apply_phase_filter; each is assigned
        # to its single matching display phase (no explode).
        if isinstance(strategy, StrictFilterStrategy) and strategy.phase_filter:
            if df.empty:
                return pd.DataFrame(columns=["category", "trial_count"]), {}
            df = df.copy()
            df["_display_phase"] = df["phases"].apply(
                lambda ps: _normalize_phase(
                    next((p for p in strategy.phase_filter if p in ps), ps[-1] if ps else "NA")
                )
            )
            grouped = (
                df.groupby("_display_phase")
                .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
                .reset_index()
                .sort_values("trial_count", ascending=False)
            )
            citation_map = {str(row["_display_phase"]): row["nct_ids"] for _, row in grouped.iterrows()}
            return (
                grouped.drop(columns=["nct_ids"]).rename(columns={"_display_phase": "category"}),
                citation_map,
            )

        # Inclusive mode (default): explode phases so hybrid studies contribute to each bucket.
        # Missing phases (empty list → NaN after explode) and "NA" strings are dropped.
        exploded = (
            df[["nct_id", "phases"]]
            .explode("phases")
            .rename(columns={"phases": "phase"})
        )
        exploded = exploded[
            exploded["phase"].notna()
            & (exploded["phase"].str.strip() != "")
            & (exploded["phase"].str.strip().str.upper() != "NA")
        ]
        if exploded.empty:
            return pd.DataFrame(columns=["category", "trial_count"]), {}

        exploded = exploded.copy()
        exploded["phase"] = exploded["phase"].apply(_normalize_phase)

        grouped = (
            exploded.groupby("phase")
            .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
            .reset_index()
            .sort_values("trial_count", ascending=False)
        )
        citation_map = {str(row["phase"]): row["nct_ids"] for _, row in grouped.iterrows()}
        return grouped.drop(columns=["nct_ids"]).rename(columns={"phase": "category"}), citation_map

    # Default path: scalar column groupby (status, primary_condition, primary_country, …)
    grouped = (
        df.groupby(group_by)
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
        .sort_values("trial_count", ascending=False)
    )
    citation_map = {str(row[group_by]): row["nct_ids"] for _, row in grouped.iterrows()}
    return grouped.drop(columns=["nct_ids"]).rename(columns={group_by: "category"}), citation_map


def transform_comparison(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    dim1: str = "phase_str",
    dim2: str = "status",
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    grouped = (
        df.groupby([dim1, dim2])
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
    )
    citation_map = {
        f"{row[dim1]}|{row[dim2]}": row["nct_ids"]
        for _, row in grouped.iterrows()
    }
    return (
        grouped.drop(columns=["nct_ids"]).rename(columns={dim1: "group1", dim2: "group2"}),
        citation_map,
    )


def transform_correlation(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)
    df = df[df["enrollment"].notna() & df["start_year"].notna()].copy()
    df["enrollment"] = df["enrollment"].astype(float)
    df["start_year"] = df["start_year"].astype(int)

    out = df[["nct_id", "brief_title", "start_year", "enrollment", "phase_str"]].copy()
    # Each row is self-referential for citations
    citation_map = {row["nct_id"]: [row["nct_id"]] for _, row in out.iterrows()}
    return out, citation_map


def transform_ranking(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    rank_by: str = "sponsor",
    top_n: int = 20,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    if rank_by == "interventions":
        # interventions is a list[str] column — must explode before grouping
        exploded = (
            df[["nct_id", "interventions"]]
            .explode("interventions")
            .rename(columns={"interventions": "intervention"})
        )
        # Drop rows where the intervention is missing or blank
        exploded = exploded[
            exploded["intervention"].notna()
            & (exploded["intervention"].str.strip() != "")
        ]
        if exploded.empty:
            return pd.DataFrame(columns=["category", "trial_count"]), {}

        grouped = (
            exploded.groupby("intervention")
            .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
            .reset_index()
            .sort_values("trial_count", ascending=False)
            .head(top_n)
        )
        citation_map = {
            str(row["intervention"]): row["nct_ids"]
            for _, row in grouped.iterrows()
        }
        return (
            grouped.drop(columns=["nct_ids"]).rename(columns={"intervention": "category"}),
            citation_map,
        )

    # Default path: rank_by is a scalar column (e.g. "sponsor")
    grouped = (
        df.groupby(rank_by)
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
        .sort_values("trial_count", ascending=False)
        .head(top_n)
    )
    citation_map = {
        str(row[rank_by]): row["nct_ids"]
        for _, row in grouped.iterrows()
    }
    return grouped.drop(columns=["nct_ids"]).rename(columns={rank_by: "category"}), citation_map


def transform_outlier_analysis(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    threshold: float = 2.0,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """
    Return individual studies with statistically high enrollment (z-score >= threshold).
    Uses sample z-score: z = (enrollment - mean) / std.
    Requires at least 3 studies with valid enrollment for meaningful results.
    """
    _empty_cols = ["nct_id", "brief_title", "enrollment", "z_score", "phase_str", "status", "sponsor"]
    _empty: pd.DataFrame = pd.DataFrame(columns=_empty_cols)

    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    if df.empty or "enrollment" not in df.columns:
        return _empty, {}

    df = df[df["enrollment"].notna()].copy()
    df["enrollment"] = df["enrollment"].astype(float)

    if len(df) < 3:
        return _empty, {}

    mean_enr = df["enrollment"].mean()
    std_enr = df["enrollment"].std()

    if std_enr == 0:
        return _empty, {}

    df["z_score"] = ((df["enrollment"] - mean_enr) / std_enr).round(2)

    outliers = (
        df[df["z_score"] >= threshold]
        [_empty_cols]
        .sort_values("z_score", ascending=False)
        .copy()
    )

    if outliers.empty:
        return outliers, {}

    citation_map = {row["nct_id"]: [row["nct_id"]] for _, row in outliers.iterrows()}
    return outliers, citation_map
