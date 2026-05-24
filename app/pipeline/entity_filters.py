from __future__ import annotations

# Keys must be lower-cased; values are canonical display strings.
NORMALIZATION_MAP: dict[str, str] = {
    # T2DM aliases
    "diabetes mellitus, type 2": "T2DM",
    "type 2 diabetes": "T2DM",
    "type 2 diabetes mellitus": "T2DM",
    "t2dm": "T2DM",
    "diabetes mellitus type 2": "T2DM",
    "non-insulin-dependent diabetes mellitus": "T2DM",
    # Breast cancer aliases
    "breast neoplasms": "Breast Cancer",
    "breast cancer": "Breast Cancer",
    "breast carcinoma": "Breast Cancer",
    "carcinoma, breast": "Breast Cancer",
    # NSCLC aliases (with and without hyphens)
    "carcinoma, non-small-cell lung": "NSCLC",
    "non-small cell lung cancer": "NSCLC",
    "non-small-cell lung cancer": "NSCLC",
    "nsclc": "NSCLC",
    # Lung cancer aliases
    "lung neoplasms": "Lung Cancer",
    "lung neoplasm": "Lung Cancer",
    "lung cancer": "Lung Cancer",
    "carcinoma, lung": "Lung Cancer",
    # COVID-19 aliases
    "covid-19": "COVID-19",
    "sars-cov-2 infection": "COVID-19",
    "coronavirus disease 2019": "COVID-19",
    "sars-cov-2": "COVID-19",
}

# Interventions that carry no biomedical signal and should be excluded from the graph.
STOP_TERMS: frozenset[str] = frozenset({
    "placebo",
    "placebo comparator",
    "sham",
    "control",
    "control group",
    "usual care",
    "standard care",
    "standard of care",
    "active comparator",
    "no intervention",
    "observation",
    "questionnaire",
    "questionnaire administration",
    "survey",
    "interview",
    "education",
    "counseling",
    "counselling",
    "exercise",
    "diet",
    "lifestyle",
    "lifestyle intervention",
    "behavioral intervention",
    "behavioural intervention",
    "wait list",
    "waitlist",
    "watchful waiting",
    "serum collection",
    "blood collection",
    "blood sample collection",
    "tissue collection",
    "urine collection",
    "sample collection",
    "blood draw",
    "quality-of-life assessment",
    "quality of life assessment",
    "qol assessment",
})

# Substrings that identify administrative/procedural interventions not in STOP_TERMS as exact phrases.
_STOP_TERM_SUBSTRINGS: tuple[str, ...] = (
    "questionnaire",
    "quality of life",
    "quality-of-life",
    " collection",  # e.g. "serum collection", "biopsy collection"
    "blood draw",
)


def _normalize_entity(name: str) -> str:
    """Return canonical form from NORMALIZATION_MAP; fall back to title-cased input for consistent casing."""
    key = name.strip().lower()
    return NORMALIZATION_MAP.get(key, name.strip().title())


def _is_stop_term(name: str) -> bool:
    """Return True if *name* is a low-signal intervention stop term (exact or substring match)."""
    normalized = name.strip().lower()
    if normalized in STOP_TERMS:
        return True
    return any(sub in normalized for sub in _STOP_TERM_SUBSTRINGS)


# Maps lowercased condition names/aliases → broad disease domain (lowercased).
# Used to determine whether a condition node belongs to the same domain as the query.
CONDITION_HIERARCHY: dict[str, str] = {
    "lung cancer": "lung cancer",
    "lung neoplasm": "lung cancer",
    "lung neoplasms": "lung cancer",
    "nsclc": "lung cancer",
    "non-small cell lung cancer": "lung cancer",
    "non-small-cell lung cancer": "lung cancer",
    "carcinoma, non-small-cell lung": "lung cancer",
    "small cell lung cancer": "lung cancer",
    "sclc": "lung cancer",
    "breast cancer": "breast cancer",
    "breast neoplasms": "breast cancer",
    "breast carcinoma": "breast cancer",
    "carcinoma, breast": "breast cancer",
    "t2dm": "diabetes",
    "type 2 diabetes": "diabetes",
    "type 2 diabetes mellitus": "diabetes",
    "diabetes mellitus, type 2": "diabetes",
    "diabetes mellitus type 2": "diabetes",
    "type 1 diabetes": "diabetes",
    "type 1 diabetes mellitus": "diabetes",
    "diabetes mellitus, type 1": "diabetes",
    "covid-19": "covid-19",
    "sars-cov-2 infection": "covid-19",
    "sars-cov-2": "covid-19",
    "coronavirus disease 2019": "covid-19",
}


def _get_condition_domain(condition: str) -> str:
    """Return the broad disease domain for a condition string (lowercased key lookup)."""
    lower = condition.strip().lower()
    if lower in CONDITION_HIERARCHY:
        return CONDITION_HIERARCHY[lower]
    normalized = _normalize_entity(condition).lower()
    return CONDITION_HIERARCHY.get(normalized, lower)


def _is_condition_relevant(condition_node: str, query_condition: str) -> bool:
    """Return True if condition_node belongs to the same disease domain as query_condition."""
    node_domain = _get_condition_domain(condition_node)
    query_domain = _get_condition_domain(query_condition)
    if node_domain == query_domain:
        return True
    node_lower = condition_node.strip().lower()
    query_lower = query_condition.strip().lower()
    return query_lower in node_lower or node_lower in query_lower
