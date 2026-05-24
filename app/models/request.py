from pydantic import BaseModel, Field, model_validator
from typing import Self


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Natural language question about clinical trials") # ... is required
    drug_name: str | None = Field(default=None, description="Drug or intervention name (e.g. Pembrolizumab)")
    condition: str | None = Field(default=None, description="Disease or condition (e.g. breast cancer)")
    phase: list[str] | None = Field(default=None, description="Trial phases (e.g. ['Phase 1', 'Phase 2'])")
    sponsor: str | None = Field(default=None, description="Sponsor organization name")
    country: str | None = Field(default=None, description="Country or location filter")
    start_year: int | None = Field(default=None, ge=1960, le=2030, description="Filter trials starting from this year")
    end_year: int | None = Field(default=None, ge=1960, le=2030, description="Filter trials starting up to this year")
    max_results: int = Field(default=500, ge=1, le=2000, description="Maximum number of studies to fetch")

    # Pydantic V2 validation. Ensures start_year <= end_year if both are provided
    @model_validator(mode="after")
    def check_year_range(self) -> Self:
        if self.start_year is not None and self.end_year is not None:
            if self.start_year > self.end_year:
                raise ValueError("start_year must be <= end_year")
        return self
