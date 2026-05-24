import httpx
import pytest
import respx

from app.clients.clinicaltrials import ClinicalTrialsClient, CT_BASE


@pytest.mark.asyncio
async def test_fetch_all_single_page(mock_ct_response):
    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(
            return_value=httpx.Response(200, json=mock_ct_response)
        )
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            studies, total = await ct_client.fetch_all({"query.cond": "cancer"}, max_results=200)

    assert len(studies) == 10
    assert total == 10


@pytest.mark.asyncio
async def test_fetch_all_paginates(sample_study):
    page1 = {"studies": [sample_study] * 5, "totalCount": 8, "nextPageToken": "TOKEN1"}
    page2 = {"studies": [sample_study] * 3}  # no nextPageToken = last page

    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(
            side_effect=[
                httpx.Response(200, json=page1),
                httpx.Response(200, json=page2),
            ]
        )
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            studies, total = await ct_client.fetch_all({"query.cond": "cancer"}, max_results=200)

    assert len(studies) == 8
    assert total == 8


@pytest.mark.asyncio
async def test_fetch_all_respects_max_results(sample_study):
    page = {"studies": [sample_study] * 100, "nextPageToken": "INFINITE"}

    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(return_value=httpx.Response(200, json=page))
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            studies, _ = await ct_client.fetch_all({"query.cond": "cancer"}, max_results=7)

    assert len(studies) == 7


@pytest.mark.asyncio
async def test_fetch_all_empty_response():
    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(
            return_value=httpx.Response(200, json={"studies": [], "totalCount": 0})
        )
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            studies, total = await ct_client.fetch_all({"query.term": "zzz"}, max_results=100)

    assert studies == []
    assert total == 0


@pytest.mark.asyncio
async def test_fetch_all_passes_page_token(sample_study):
    """Verify that nextPageToken from response is sent as pageToken in next request."""
    page1 = {"studies": [sample_study], "nextPageToken": "MY_TOKEN"}
    page2 = {"studies": [sample_study]}

    captured_params: list[dict] = []

    def handler(req: httpx.Request) -> httpx.Response:
        captured_params.append(dict(req.url.params))
        if len(captured_params) == 1:
            return httpx.Response(200, json=page1)
        return httpx.Response(200, json=page2)

    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(side_effect=handler)
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            await ct_client.fetch_all({"query.cond": "test"}, max_results=200)

    assert len(captured_params) == 2
    assert captured_params[1].get("pageToken") == "MY_TOKEN"


@pytest.mark.asyncio
async def test_data_fetcher_caches(mock_ct_response):
    """Second call with same params should use cache and not hit the network."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, json=mock_ct_response)

    from app.config import _study_cache
    _study_cache.clear()

    from app.pipeline.data_fetcher import DataFetcher

    with respx.mock(base_url=CT_BASE) as mock:
        mock.get("/studies").mock(side_effect=handler)
        async with httpx.AsyncClient() as client:
            ct_client = ClinicalTrialsClient(client)
            fetcher = DataFetcher(ct_client)
            params = {"query.cond": "unique_test_condition_cache", "countTotal": "true"}
            await fetcher.fetch(params, max_results=100)
            await fetcher.fetch(params, max_results=100)

    assert call_count == 1  # network hit only once; second call from cache
