from __future__ import annotations

from typing import Any

import pandas as pd


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
            "primary_phase": _primary_phase(phases),
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


# Map raw ClinicalTrials.gov phase codes to human-readable labels.
_PHASE_DISPLAY: dict[str, str] = {
    "EARLY_PHASE1": "Early Phase 1",
    "PHASE1": "Phase 1",
    "PHASE2": "Phase 2",
    "PHASE3": "Phase 3",
    "PHASE4": "Phase 4",
}

# Ordering used to determine the primary (highest) phase for hybrid studies.
_PHASE_ORDER: dict[str, int] = {
    "EARLY_PHASE1": 0,
    "PHASE1": 1,
    "PHASE2": 2,
    "PHASE3": 3,
    "PHASE4": 4,
}


def _normalize_phase(phase: str) -> str:
    """Map raw ClinicalTrials.gov phase codes to human-readable display labels."""
    return _PHASE_DISPLAY.get(phase.strip().upper(), phase.strip())


def _primary_phase(phases: list[str]) -> str:
    """Return the highest-order phase from the list; 'NA' when the list is empty."""
    if not phases:
        return "NA"
    return max(phases, key=lambda p: _PHASE_ORDER.get(p, -1))
