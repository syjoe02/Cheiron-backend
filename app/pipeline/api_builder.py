from app.models.request import QueryRequest
from app.pipeline.query_parser import ParsedQuery

# filter.phase does NOT exist in CT.gov v2 API
PHASE_MAP: dict[str, str] = {
    "Phase 1": "PHASE1",
    "Phase 2": "PHASE2",
    "Phase 3": "PHASE3",
    "Phase 4": "PHASE4",
    # special phase
    "Early Phase 1": "EARLY_PHASE1",
    # lowercase
    "phase 1": "PHASE1",
    "phase 2": "PHASE2",
    "phase 3": "PHASE3",
    "phase 4": "PHASE4",
    "early phase 1": "EARLY_PHASE1",
    # pass. already-canonical values
    "PHASE1": "PHASE1",
    "PHASE2": "PHASE2",
    "PHASE3": "PHASE3",
    "PHASE4": "PHASE4",
    "EARLY_PHASE1": "EARLY_PHASE1",
}


def build_ct_params(parsed: ParsedQuery, request: QueryRequest) -> dict[str, str]:
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

    # fallback: if no specific field was set, use the raw query as full-text search
    if not params:
        params["query.term"] = request.query

    # request total count for meta reporting
    params["countTotal"] = "true"

    # returns a dict of query params
    return params


def build_ct_params_for_entity(
    parsed: ParsedQuery,
    request: QueryRequest,
    entity: str,
    dimension: str,
) -> dict[str, str]:
    
    # CT.gv query params
    params: dict[str, str] = {}
    e = parsed.entities

    # compare to entity in parsed query
    if dimension == "drug_name":
        params["query.intr"] = entity
        condition = request.condition or e.condition
        if condition:
            params["query.cond"] = condition
    elif dimension == "condition":
        params["query.cond"] = entity
        drug = request.drug_name or e.drug_name
        if drug:
            params["query.intr"] = drug
    elif dimension == "sponsor":
        params["query.spons"] = entity
        condition = request.condition or e.condition
        if condition:
            params["query.cond"] = condition
    # fallback
    else:
        params["query.term"] = entity

    country = request.country or e.country
    if country:
        params["query.locn"] = country

    if not params:
        params["query.term"] = entity

    params["countTotal"] = "true"
    return params


# phase normalization
def get_phase_filter(request: QueryRequest, parsed: ParsedQuery) -> list[str] | None:

    phases = request.phase or parsed.entities.phase
    if not phases:
        return None
    return [PHASE_MAP.get(p, p) for p in phases]
