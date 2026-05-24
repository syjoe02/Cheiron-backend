from __future__ import annotations

import logging
import re

import pandas as pd

from app.models.request import QueryRequest

_rank_logger = logging.getLogger(__name__)

# Ordered list of (keyword_set, dimension) — first match wins.
_RANKING_DIM_RULES: list[tuple[frozenset[str], str]] = [
    (frozenset({"intervention", "interventions", "drug", "drugs",
                "medication", "medications", "treatment", "treatments",
                "therapy", "therapies"}), "interventions"),
    (frozenset({"country", "countries", "nation", "nations",
                "location", "locations", "region", "regions"}), "primary_country"),
    (frozenset({"phase", "phases"}), "phase_str"),
    (frozenset({"status", "recruitment", "recruiting"}), "status"),
    (frozenset({"sponsor", "sponsors", "company", "companies",
                "organization", "organizations", "organisation", "organisations",
                "manufacturer", "manufacturers", "funder", "funders"}), "sponsor"),
]

# Ordered rules for inferring which dimension to group by in entity comparisons.
_COMPARISON_GROUP_BY_RULES: list[tuple[frozenset[str], str]] = [
    (frozenset({"phase", "phases"}), "phase_str"),
    (frozenset({"status", "recruitment", "recruiting"}), "status"),
    (frozenset({"sponsor", "sponsors", "company", "companies",
                "organization", "organizations"}), "sponsor"),
]


def _infer_distribution_dim(request: QueryRequest, df: pd.DataFrame) -> str:  # noqa: ARG001
    if request.drug_name:
        return "primary_condition"
    if request.country:
        return "primary_country"
    if request.condition:
        return "status"
    return "phase_str"


def _infer_ranking_dim(request: QueryRequest, df: pd.DataFrame) -> str:  # noqa: ARG001
    query_words = set(re.findall(r"\w+", request.query.lower()))
    for keywords, dim in _RANKING_DIM_RULES:
        matched = query_words & keywords
        if matched:
            _rank_logger.debug(
                "ranking dim inferred: %r  matched: %r  query: %r",
                dim, matched, request.query,
            )
            return dim
    _rank_logger.debug("ranking dim fallback: 'sponsor'  query: %r", request.query)
    return "sponsor"


def _extract_top_n(query: str, default: int = 20) -> int:
    """Return the N from 'top N' in the query, or *default* if absent."""
    match = re.search(r"\btop\s+(\d+)\b", query.lower())
    return int(match.group(1)) if match else default


def _infer_comparison_dims(request: QueryRequest, df: pd.DataFrame) -> tuple[str, str]:  # noqa: ARG001
    if request.drug_name:
        return ("phase_str", "status")
    return ("phase_str", "status")


def _infer_comparison_group_by(query: str) -> str:
    """Infer the grouping dimension for a multi-entity comparison from the query text."""
    words = set(re.findall(r"\w+", query.lower()))
    for keywords, dim in _COMPARISON_GROUP_BY_RULES:
        if words & keywords:
            return dim
    return "phase_str"
