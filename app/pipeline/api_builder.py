from app.models.request import QueryRequest
from app.pipeline.query_parser import ParsedQuery

# User-facing phase strings → CT.gov API canonical enum values
# filter.phase does NOT exist in CT.gov v2 API — phase filtering is done post-fetch
PHASE_MAP: dict[str, str] = {
    "Phase 1": "PHASE1",
    "Phase 2": "PHASE2",
    "Phase 3": "PHASE3",
    "Phase 4": "PHASE4",
    "Early Phase 1": "EARLY_PHASE1",
    "phase 1": "PHASE1",
    "phase 2": "PHASE2",
    "phase 3": "PHASE3",
    "phase 4": "PHASE4",
    "early phase 1": "EARLY_PHASE1",
    # Pass-through for already-canonical values
    "PHASE1": "PHASE1",
    "PHASE2": "PHASE2",
    "PHASE3": "PHASE3",
    "PHASE4": "PHASE4",
    "EARLY_PHASE1": "EARLY_PHASE1",
}


def build_ct_params(parsed: ParsedQuery, request: QueryRequest) -> dict[str, str]:
    """
    Maps parsed query + request fields → CT.gov v2 query parameters.
    Phase filtering is NOT included here (no filter.phase in CT.gov v2 API).
    Returns a dict of query params ready for httpx.
    """
    params: dict[str, str] = {}
    e = parsed.entities

    drug = request.drug_name or e.drug_name
    if drug:
        params["query.intr"] = drug

    condition = request.condition or e.condition
    if condition:
        params["query.cond"] = condition

    sponsor = request.sponsor or e.sponsor
    if sponsor:
        params["query.spons"] = sponsor

    country = request.country or e.country
    if country:
        params["query.locn"] = country

    # Fallback: if no specific field was set, use the raw query as full-text search
    if not params:
        params["query.term"] = request.query

    # Always request total count for meta reporting
    params["countTotal"] = "true"

    return params


def get_phase_filter(request: QueryRequest, parsed: ParsedQuery) -> list[str] | None:
    """
    Returns canonical CT.gov phase enum values to apply as a post-fetch filter.
    Returns None if no phase filter is requested.
    """
    phases = request.phase or parsed.entities.phase
    if not phases:
        return None
    return [PHASE_MAP.get(p, p) for p in phases]
