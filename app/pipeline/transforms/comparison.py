from __future__ import annotations

from typing import Any

import pandas as pd

from app.pipeline.normalizers import (
    _apply_phase_filter,
    _apply_year_filter,
    _normalize_phase,
    normalize_studies,
)
from app.pipeline.phase_strategy import PhaseStrategy, StrictFilterStrategy


def transform_entity_comparison(
    entity_studies: dict[str, list[dict[str, Any]]],
    phase_filter: list[str] | None,
    group_by: str = "phase_str",
    start_year: int | None = None,
    end_year: int | None = None,
    strategy: PhaseStrategy | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """
    Normalize each entity's studies, tag with an 'entity' column, and concat.
    Group by (entity, category_dim) to produce comparison rows with schema:
        {entity, category, trial_count}
    Citation map keys use the format "entity|category".
    """
    dfs = []
    for entity_name, studies in entity_studies.items():
        df = normalize_studies(studies)
        if not df.empty:
            df = df.copy()
            df["entity"] = entity_name
            dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=["entity", "category", "trial_count"]), {}

    combined = pd.concat(dfs, ignore_index=True)
    combined = _apply_phase_filter(combined, phase_filter)
    combined = _apply_year_filter(combined, start_year, end_year)

    if group_by == "phase_str":
        # Strict mode: map each study to its single matching display phase (no explode).
        if isinstance(strategy, StrictFilterStrategy) and strategy.phase_filter:
            if combined.empty:
                return pd.DataFrame(columns=["entity", "category", "trial_count"]), {}
            combined = combined.copy()
            combined["_display_phase"] = combined["phases"].apply(
                lambda ps: _normalize_phase(
                    next((p for p in strategy.phase_filter if p in ps), ps[-1] if ps else "NA")
                )
            )
            grouped = (
                combined.groupby(["entity", "_display_phase"])
                .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
                .reset_index()
                .sort_values(["entity", "trial_count"], ascending=[True, False])
            )
            citation_map = {
                f"{row['entity']}|{row['_display_phase']}": row["nct_ids"]
                for _, row in grouped.iterrows()
            }
            return (
                grouped.drop(columns=["nct_ids"]).rename(columns={"_display_phase": "category"}),
                citation_map,
            )

        # Inclusive mode (default): explode so hybrid studies contribute to each phase bucket.
        exploded = (
            combined[["nct_id", "entity", "phases"]]
            .explode("phases")
            .rename(columns={"phases": "phase"})
        )
        exploded = exploded[
            exploded["phase"].notna()
            & (exploded["phase"].str.strip() != "")
            & (exploded["phase"].str.strip().str.upper() != "NA")
        ]
        if exploded.empty:
            return pd.DataFrame(columns=["entity", "category", "trial_count"]), {}

        exploded = exploded.copy()
        exploded["phase"] = exploded["phase"].apply(_normalize_phase)

        grouped = (
            exploded.groupby(["entity", "phase"])
            .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
            .reset_index()
            .sort_values(["entity", "trial_count"], ascending=[True, False])
        )
        citation_map = {
            f"{row['entity']}|{row['phase']}": row["nct_ids"]
            for _, row in grouped.iterrows()
        }
        return (
            grouped.drop(columns=["nct_ids"]).rename(columns={"phase": "category"}),
            citation_map,
        )

    # Scalar column path (status, sponsor, …)
    grouped = (
        combined.groupby(["entity", group_by])
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
        .sort_values(["entity", "trial_count"], ascending=[True, False])
    )
    citation_map = {
        f"{row['entity']}|{row[group_by]}": row["nct_ids"]
        for _, row in grouped.iterrows()
    }
    return (
        grouped.drop(columns=["nct_ids"]).rename(columns={group_by: "category"}),
        citation_map,
    )


def generate_comparison_insight(df: pd.DataFrame) -> str:
    """
    Return a one-sentence plain-English comparison of entity trial distributions.
    Requires a DataFrame with columns: entity, category, trial_count.
    Returns empty string when the data is insufficient for a meaningful summary.
    """
    required = {"entity", "category", "trial_count"}
    if df.empty or not required.issubset(df.columns):
        return ""
    entities = [e for e in df["entity"].unique() if pd.notna(e)]
    if len(entities) < 2:
        return ""
    summaries: list[str] = []
    for entity in entities:
        sub = df[df["entity"] == entity].sort_values("trial_count", ascending=False)
        if sub.empty:
            continue
        top_cat = sub.iloc[0]["category"]
        top_count = int(sub.iloc[0]["trial_count"])
        total = int(sub["trial_count"].sum())
        pct = round(top_count / total * 100)
        summaries.append(f"{entity} is concentrated in {top_cat} ({pct}% of trials)")
    if not summaries:
        return ""
    if len(summaries) == 1:
        return summaries[0] + "."
    return summaries[0] + ", while " + "; ".join(summaries[1:]) + "."
