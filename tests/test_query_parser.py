"""Tests for query_parser.py using mocked OpenAI client."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pipeline.query_parser import ParsedEntities, ParsedQuery, QueryIntent, QueryParser


def make_mock_completion(intent: QueryIntent, **entity_kwargs) -> MagicMock:
    """Build a fake OpenAI completion response with ParsedQuery as .parsed."""
    parsed = ParsedQuery(
        intent=intent,
        entities=ParsedEntities(**entity_kwargs),
        query_interpretation="Mock interpretation",
        assumptions=[],
    )
    mock_msg = MagicMock()
    mock_msg.parsed = parsed
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


def make_mock_client(completion: MagicMock) -> MagicMock:
    """Build a fake AsyncOpenAI client that returns the given completion."""
    mock_client = MagicMock()
    mock_client.beta = MagicMock()
    mock_client.beta.chat = MagicMock()
    mock_client.beta.chat.completions = MagicMock()
    mock_client.beta.chat.completions.parse = AsyncMock(return_value=completion)
    return mock_client


@pytest.mark.asyncio
async def test_query_parser_returns_parsed_intent():
    completion = make_mock_completion(QueryIntent.TREND_OVER_TIME)
    client = make_mock_client(completion)
    parser = QueryParser(client, model="gpt-4.1-mini")

    result = await parser.parse("How many trials per year?", overrides={})
    assert result.intent == QueryIntent.TREND_OVER_TIME
    assert result.query_interpretation == "Mock interpretation"


@pytest.mark.asyncio
async def test_query_parser_override_drug_name():
    completion = make_mock_completion(QueryIntent.DISTRIBUTION, drug_name="WrongDrug")
    client = make_mock_client(completion)
    parser = QueryParser(client, model="gpt-4.1-mini")

    result = await parser.parse(
        "Distribution by phase",
        overrides={"drug_name": "Pembrolizumab"},
    )
    # Request override should replace LLM extraction
    assert result.entities.drug_name == "Pembrolizumab"


@pytest.mark.asyncio
async def test_query_parser_override_condition():
    completion = make_mock_completion(QueryIntent.RANKING)
    client = make_mock_client(completion)
    parser = QueryParser(client)

    result = await parser.parse("Top sponsors", overrides={"condition": "breast cancer"})
    assert result.entities.condition == "breast cancer"


@pytest.mark.asyncio
async def test_query_parser_override_phase():
    completion = make_mock_completion(QueryIntent.DISTRIBUTION)
    client = make_mock_client(completion)
    parser = QueryParser(client)

    result = await parser.parse("Phase 2 trials", overrides={"phase": ["PHASE2"]})
    assert result.entities.phase == ["PHASE2"]


@pytest.mark.asyncio
async def test_query_parser_override_years():
    completion = make_mock_completion(QueryIntent.TREND_OVER_TIME)
    client = make_mock_client(completion)
    parser = QueryParser(client)

    result = await parser.parse(
        "Trend since 2015",
        overrides={"start_year": 2015, "end_year": 2023},
    )
    assert result.entities.start_year == 2015
    assert result.entities.end_year == 2023


@pytest.mark.asyncio
async def test_query_parser_no_overrides_passes_through():
    completion = make_mock_completion(
        QueryIntent.RELATIONSHIP_NETWORK,
        drug_name="Aspirin",
        condition="heart disease",
    )
    client = make_mock_client(completion)
    parser = QueryParser(client)

    result = await parser.parse(
        "Drug-condition network",
        overrides={k: None for k in ["drug_name", "condition", "phase", "sponsor", "country", "start_year", "end_year"]},
    )
    # LLM extractions preserved when no overrides
    assert result.entities.drug_name == "Aspirin"
    assert result.entities.condition == "heart disease"


@pytest.mark.asyncio
async def test_query_parser_adds_overrides_to_user_message():
    completion = make_mock_completion(QueryIntent.DISTRIBUTION)
    client = make_mock_client(completion)
    parser = QueryParser(client)

    await parser.parse("test query", overrides={"drug_name": "Aspirin"})

    call_kwargs = client.beta.chat.completions.parse.call_args
    user_message = call_kwargs[1]["messages"][1]["content"]
    assert "Aspirin" in user_message
