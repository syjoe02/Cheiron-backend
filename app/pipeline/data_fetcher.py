import hashlib # generated hash values - to use as cache key
import json
from typing import Any

from app.clients.clinicaltrials import ClinicalTrialsClient
from app.config import _cache_lock, _study_cache


class DataFetcher:
    def __init__(self, client: ClinicalTrialsClient) -> None:
        self._client = client

    def _cache_key(self, params: dict[str, str], max_results: int) -> str:
        payload = json.dumps({"params": params, "max": max_results}, sort_keys=True)
        return hashlib.md5(payload.encode()).hexdigest()  # noqa: S324 (ignore lint/securiy checker warning about MD5)

    async def fetch(
        self,
        params: dict[str, str],
        max_results: int = 500,
    ) -> tuple[list[dict[str, Any]], int | None]:

        # generate cache key
        key = self._cache_key(params, max_results)

        # get a lock to prevent multiple concurrent fetches for the same key
        async with _cache_lock:
            if key in _study_cache:
                return _study_cache[key]

        studies, total_count = await self._client.fetch_all(params, max_results)

        async with _cache_lock:
            _study_cache[key] = (studies, total_count)

        return studies, total_count
