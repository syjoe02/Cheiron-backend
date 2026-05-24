from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd

from app.pipeline.entity_filters import (
    _is_condition_relevant,
    _is_stop_term,
    _normalize_entity,
)
from app.pipeline.normalizers import _apply_phase_filter, _apply_year_filter


def transform_network(
    df: pd.DataFrame,
    phase_filter: list[str] | None,
    start_year: int | None = None,
    end_year: int | None = None,
    min_edge_weight: int = 1,
    query_condition: str | None = None,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """
    Build a directed co-occurrence graph: Intervention -> Condition.
    Applies entity normalisation, stop-term filtering, self-loop removal,
    and optional query-relevance filtering before building.
    Returns (network_dict, citation_map) where network_dict has keys nodes and edges.
    """
    df = _apply_phase_filter(df, phase_filter)
    df = _apply_year_filter(df, start_year, end_year)

    G: nx.DiGraph = nx.DiGraph()
    citation_map: dict[str, list[str]] = {}

    for _, row in df.iterrows():
        nct_id: str = row["nct_id"]
        raw_interventions: list[str] = row["interventions"]
        raw_conditions: list[str] = row["conditions"][:3]

        interventions = [
            _normalize_entity(i)
            for i in raw_interventions
            if i and not _is_stop_term(i)
        ]
        conditions = [_normalize_entity(c) for c in raw_conditions if c]

        # Restrict conditions to the query domain when a condition filter is provided
        if query_condition:
            conditions = [c for c in conditions if _is_condition_relevant(c, query_condition)]

        for item in interventions:
            if not G.has_node(item):
                G.add_node(item, type="intervention", label=item)
        for item in conditions:
            if not G.has_node(item):
                G.add_node(item, type="condition", label=item)

        # Edges always Intervention -> Condition; self-loops (intr == cond) are skipped
        for intr in interventions:
            for cond in conditions:
                if intr == cond:
                    continue
                if G.has_edge(intr, cond):
                    G[intr][cond]["weight"] += 1
                    G[intr][cond]["nct_ids"].append(nct_id)
                else:
                    G.add_edge(intr, cond, weight=1, nct_ids=[nct_id])

    # Remove edges below the minimum weight threshold
    if min_edge_weight > 1:
        weak = [(u, v) for u, v, d in G.edges(data=True) if d.get("weight", 1) < min_edge_weight]
        G.remove_edges_from(weak)

    # Remove isolated nodes (no edges after filtering)
    G.remove_nodes_from(list(nx.isolates(G)))

    # Prune to top 50 nodes by total degree to keep the graph readable
    if len(G.nodes) > 50:
        degrees = dict(G.degree())
        top_nodes = sorted(degrees, key=lambda n: degrees[n], reverse=True)[:50]
        G = G.subgraph(top_nodes).copy()  # type: ignore[assignment]
        G.remove_nodes_from(list(nx.isolates(G)))

    degrees = dict(G.degree())
    max_degree = max(degrees.values(), default=1)

    nodes = [
        {
            "id": n,
            "label": G.nodes[n].get("label", n),
            "type": G.nodes[n].get("type", "unknown"),
            "degree": degrees.get(n, 0),
            "size": round((degrees.get(n, 0) / max_degree) * 100, 2),
        }
        for n in G.nodes
    ]

    edges = []
    for u, v, data in G.edges(data=True):
        edge_key = f"{u}|{v}"
        citation_map[edge_key] = data.get("nct_ids", [])
        edges.append({"source": u, "target": v, "weight": data.get("weight", 1)})

    return {"nodes": nodes, "edges": edges}, citation_map
