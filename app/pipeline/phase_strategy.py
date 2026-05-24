from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InclusiveHybridStrategy:
    """Distribution analytics: hybrid studies contribute to all matching phase buckets."""

    mode: str = "inclusive_hybrid"


@dataclass(frozen=True)
class StrictFilterStrategy:
    """Filtered retrieval: hybrid studies match but display only under the requested phase."""

    phase_filter: tuple[str, ...]
    mode: str = "strict_display"


PhaseStrategy = InclusiveHybridStrategy | StrictFilterStrategy


def choose_strategy(phase_filter: list[str] | None) -> PhaseStrategy:
    """StrictFilter for a single-phase filter; InclusiveHybrid for all other cases."""
    if phase_filter and len(phase_filter) == 1:
        return StrictFilterStrategy(phase_filter=tuple(phase_filter))
    return InclusiveHybridStrategy()


def phase_meta_for(strategy: PhaseStrategy, phase_filter: list[str] | None) -> dict:
    """Return a metadata dict describing the active phase filter mode for the response."""
    if isinstance(strategy, StrictFilterStrategy):
        phase_str = ", ".join(strategy.phase_filter)
        return {
            "phase_filter_mode": "strict_display",
            "notes": [
                f"Hybrid studies (e.g. PHASE1|PHASE2) are included when matching "
                f"{phase_str} filters but displayed only under the requested phase.",
            ],
        }
    return {"phase_filter_mode": "inclusive_hybrid"}
