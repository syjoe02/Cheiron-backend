from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd

from app.models.request import QueryRequest
from app.pipeline.query_parser import QueryIntent


def normalize_studies(studies: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Flatten nested protocolSection fields into a flat DataFrame.
    One row per study. Multi-value fields are kept as Python lists.
    """
    rows = []
    for s in studies:
        ps = s.get("protocolSection", {})
        id_mod = ps.get("identificationModule", {})
        status_mod = ps.get("statusModule", {})
        design_mod = ps.get("designModule", {})
        cond_mod = ps.get("conditionsModule", {})
        sponsor_mod = ps.get("sponsorCollaboratorsModule", {})
        arms_mod = ps.get("armsInterventionsModule", {})
        loc_mod = ps.get("contactsLocationsModule", {})

        start_date_raw = status_mod.get("startDateStruct", {}).get("date", "")
        start_year: int | None = None
        if start_date_raw:
            try:
                start_year = int(str(start_date_raw)[:4])
            except (ValueError, IndexError):
                pass

        phases = design_mod.get("phases", []) or []
        conditions = cond_mod.get("conditions", []) or []
        interventions = [
            i.get("name", "") for i in (arms_mod.get("interventions", []) or [])
            if i.get("name")
        ]
        countries = list({
            loc.get("country", "")
            for loc in (loc_mod.get("locations", []) or [])
            if loc.get("country")
        })

        enrollment = None
        enrollment_info = design_mod.get("enrollmentInfo", {})
        if enrollment_info:
            enrollment = enrollment_info.get("count")

        rows.append({
            "nct_id": id_mod.get("nctId", ""),
            "brief_title": id_mod.get("briefTitle", ""),
            "status": status_mod.get("overallStatus", ""),
            "start_year": start_year,
            "start_date": start_date_raw,
            "phases": phases,
            "phase_str": "|".join(phases) if phases else "NA",
            "conditions": conditions,
            "primary_condition": conditions[0] if conditions else "Unknown",
            "interventions": interventions,
            "sponsor": sponsor_mod.get("leadSponsor", {}).get("name", "Unknown"),
            "enrollment": enrollment,
            "countries": countries,
            "primary_country": countries[0] if countries else "Unknown",
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _apply_phase_filter(df: pd.DataFrame, phase_filter: list[str] | None) -> pd.DataFrame:
    if not phase_filter or df.empty:
        return df
    mask = df["phases"].apply(lambda phases: any(p in phase_filter for p in phases))
    return df[mask]


def _apply_year_filter(
    df: pd.DataFrame,
    start_year: int | None,
    end_year: int | None,
) -> pd.DataFrame:
    if df.empty or "start_year" not in df.columns:
        return df
    if start_year is not None:
        df = df[df["start_year"] >= start_year]
    if end_year is not None:
        df = df[df["start_year"] <= end_year]
    return df


# ---------------------------------------------------------------------------
# Intent-specific transform functions
# Each returns (transformed_data, citation_map)
# citation_map: str key → list of nct_ids that contributed to that row/edge
# ---------------------------------------------------------------------------

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
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    grouped = (
        df.groupby(group_by)
        .agg(trial_count=("nct_id", "count"), nct_ids=("nct_id", list))
        .reset_index()
        .sort_values("trial_count", ascending=False)
    )
    citation_map = {
        str(row[group_by]): row["nct_ids"]
        for _, row in grouped.iterrows()
    }
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


def transform_network(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """
    Build a bipartite co-occurrence graph of interventions and conditions.
    Returns (network_dict, citation_map) where network_dict has keys nodes and edges.
    """
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    G: nx.Graph = nx.Graph()
    citation_map: dict[str, list[str]] = {}

    for _, row in df.iterrows():
        nct_id: str = row["nct_id"]
        interventions: list[str] = row["interventions"]
        conditions: list[str] = row["conditions"][:3]  # cap per study to avoid noise

        for item in interventions:
            if not G.has_node(item):
                G.add_node(item, type="intervention", label=item)
        for item in conditions:
            if not G.has_node(item):
                G.add_node(item, type="condition", label=item)

        for intr in interventions:
            for cond in conditions:
                if intr and cond:
                    if G.has_edge(intr, cond):
                        G[intr][cond]["weight"] += 1
                        G[intr][cond]["nct_ids"].append(nct_id)
                    else:
                        G.add_edge(intr, cond, weight=1, nct_ids=[nct_id])

    # Prune to top 50 nodes by degree to keep the graph readable
    if len(G.nodes) > 50:
        degrees = dict(G.degree())
        top_nodes = sorted(degrees, key=lambda n: degrees[n], reverse=True)[:50]
        G = G.subgraph(top_nodes).copy()

    centrality = nx.degree_centrality(G)

    nodes = [
        {
            "id": n,
            "label": G.nodes[n].get("label", n),
            "type": G.nodes[n].get("type", "unknown"),
            "size": round(centrality.get(n, 0) * 100, 2),
        }
        for n in G.nodes
    ]

    edges = []
    for u, v, data in G.edges(data=True):
        edge_key = f"{u}|{v}"
        citation_map[edge_key] = data.get("nct_ids", [])
        edges.append({"source": u, "target": v, "weight": data.get("weight", 1)})

    return {"nodes": nodes, "edges": edges}, citation_map


# ---------------------------------------------------------------------------
# Dimension inference helpers (rule-based, no LLM)
# ---------------------------------------------------------------------------

def _infer_distribution_dim(request: QueryRequest, df: pd.DataFrame) -> str:  # noqa: ARG001
    if request.drug_name:
        return "primary_condition"
    if request.country:
        return "primary_country"
    if request.condition:
        return "status"
    return "phase_str"


def _infer_ranking_dim(request: QueryRequest, df: pd.DataFrame) -> str:  # noqa: ARG001
    if request.condition or request.drug_name:
        return "sponsor"
    return "sponsor"


def _infer_comparison_dims(request: QueryRequest, df: pd.DataFrame) -> tuple[str, str]:  # noqa: ARG001
    if request.drug_name:
        return ("phase_str", "status")
    return ("phase_str", "status")


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

class Transformer:
    def transform(
        self,
        intent: QueryIntent,
        studies: list[dict[str, Any]],
        phase_filter: list[str] | None,
        request: QueryRequest,
    ) -> tuple[Any, dict[str, list[str]]]:
        df = normalize_studies(studies)
        if df.empty:
            return pd.DataFrame(), {}

        sy = request.start_year
        ey = request.end_year

        match intent:
            case QueryIntent.TREND_OVER_TIME:
                return transform_trend(df, phase_filter, sy, ey)
            case QueryIntent.DISTRIBUTION:
                dim = _infer_distribution_dim(request, df)
                return transform_distribution(df, phase_filter, dim, sy, ey)
            case QueryIntent.COMPARISON:
                d1, d2 = _infer_comparison_dims(request, df)
                return transform_comparison(df, phase_filter, d1, d2, sy, ey)
            case QueryIntent.CORRELATION:
                return transform_correlation(df, phase_filter, sy, ey)
            case QueryIntent.RELATIONSHIP_NETWORK:
                return transform_network(df, phase_filter, sy, ey)
            case QueryIntent.RANKING:
                dim = _infer_ranking_dim(request, df)
                return transform_ranking(df, phase_filter, dim, 20, sy, ey)
            case _:
                return transform_distribution(df, phase_filter, "phase_str", sy, ey)
