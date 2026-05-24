import httpx
from typing import Any

CT_BASE = "https://clinicaltrials.gov/api/v2"

# Sparse field list — only fetch what we need to minimize response size
FIELDS = ",".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct",
    "protocolSection.designModule.phases",
    "protocolSection.designModule.enrollmentInfo",
    "protocolSection.conditionsModule.conditions",
    "protocolSection.armsInterventionsModule.interventions",
    "protocolSection.sponsorCollaboratorsModule.leadSponsor",
    "protocolSection.contactsLocationsModule.locations",
])


class ClinicalTrialsClient:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def fetch_page(
        self,
        params: dict[str, str],
        page_token: str | None = None,
    ) -> dict[str, Any]:
        request_params: dict[str, str] = {
            "format": "json",
            "pageSize": "100",
            "fields": FIELDS,
            **params,
        }
        if page_token:
            request_params["pageToken"] = page_token

        response = await self._client.get(
            f"{CT_BASE}/studies",
            params=request_params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def fetch_all(
        self,
        params: dict[str, str],
        max_results: int = 500,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """
        Paginate and collect studies up to max_results.
        Returns (studies, total_count).
        total_count is only available when countTotal=true is in params.
        """
        studies: list[dict[str, Any]] = []
        page_token: str | None = None
        total_count: int | None = None

        while len(studies) < max_results:
            page = await self.fetch_page(params, page_token)

            if total_count is None:
                total_count = page.get("totalCount")

            batch = page.get("studies", [])
            if not batch:
                break

            studies.extend(batch)

            page_token = page.get("nextPageToken")
            if not page_token:
                break

        return studies[:max_results], total_count
