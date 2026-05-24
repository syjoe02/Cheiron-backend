# ClinicalTrials.gov Query-to-Visualization Agent

A backend service that accepts natural-language clinical trial queries, fetches live data from ClinicalTrials.gov, and returns structured visualization specifications with deep citations.

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- An OpenAI API key (4.1, 4.1-mini, 4o-mini)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install

```bash
git clone <repo>
cd taskAssignment
uv sync
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

`.env` contents:
```
OPENAI_API_KEY=sk-...
FAST_MODEL=gpt-4o-mini
SMART_MODEL=gpt-4o
```

### 4. Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### 5. Test

```bash
uv run pytest tests/ -v --cov=app
```

---

## API Reference

### POST /query

**Request Schema**

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | Yes | Natural language question (3–500 chars) |
| `drug_name` | string | No | Drug or intervention (e.g. "Pembrolizumab") |
| `condition` | string | No | Disease or condition (e.g. "breast cancer") |
| `phase` | list[string] | No | Trial phases: `["Phase 1", "Phase 2"]` |
| `sponsor` | string | No | Sponsor organization name |
| `country` | string | No | Country or location filter |
| `start_year` | int | No | Filter trials starting from this year (1960–2030) |
| `end_year` | int | No | Filter trials starting up to this year (1960–2030) |
| `max_results` | int | No | Max studies to fetch (default 500, max 2000) |

**Example request:**
```json
{
  "query": "How many Pembrolizumab trials started each year?",
  "drug_name": "Pembrolizumab"
}
```

---

**Response Schema**

```json
{
  "visualization": {
    "type": "<chart_type>",
    "title": "<human-readable title>",
    "encoding": { ... },
    "data": [
      {
        "<field1>": "<value>",
        "<field2>": "<value>",
        "citations": [
          {
            "nct_id": "NCT01234567",
            "excerpt": "Phase 3 randomized study evaluating pembrolizumab..."
          }
        ]
      }
    ]
  },
  "meta": {
    "filters_applied": { ... },
    "source": "ClinicalTrials.gov v2 API",
    "query_interpretation": "...",
    "assumptions": [],
    "trial_count": 423,
    "total_matching": 1240
  }
}
```

**Chart types and encodings:**

| `type` | Encoding keys | Use case |
|---|---|---|
| `time_series` | `x.field`, `y.field` | Trials over years |
| `bar_chart` | `x.field`, `y.field` | Distribution by one dimension |
| `grouped_bar_chart` | `x.field`, `y.field`, `series.field` | Comparison across two dimensions |
| `scatter_plot` | `x.field`, `y.field`, `color.field` | Correlation between two numerics |
| `histogram` | `x.field`, `y.field` | Distribution of a continuous variable |
| `network_graph` | `nodes.{id,label,size,color}`, `edges.{source,target,weight}` | Entity co-occurrence graph |

**Network graph special format:**

For `network_graph`, `data[0]` contains the node list:
```json
{
  "nodes": [
    {"id": "Aspirin", "label": "Aspirin", "type": "intervention", "size": 42.0}
  ],
  "citations": []
}
```
`data[1..n]` contains edges:
```json
{
  "source": "Aspirin",
  "target": "Heart Disease",
  "weight": 17,
  "citations": [{"nct_id": "NCT...", "excerpt": "..."}]
}
```

---

### GET /health

Returns `{"status": "ok", "version": "0.1.0"}`.

---

## Design Decisions & Trade-offs

### Deterministic Pipeline with LLM Checkpoints

The core architecture is a 6-step pipeline where LLMs are used **only** for interpretation and schema decisions — never for computing data values:

```
Request → [LLM: parse intent] → [Rule-based: CT.gov params] → [Fetch] →
[Rule-based: pandas/networkx transform] → [LLM: viz encoding] → Response
```

**Why this design:**
- LLMs hallucinate numbers. By restricting LLMs to query parsing and schema selection, all numerical data comes exclusively from ClinicalTrials.gov.
- Each step is independently testable.
- Predictable API cost: 2 LLM calls per request maximum.

**Trade-off:** Less flexible than a free-form tool-calling agent loop. A complex multi-step question ("first filter by phase, then group by country, then rank") might need two separate requests. An agent with tools could handle it in one shot at the cost of unpredictability.

### Model Selection

- **gpt-4o-mini** for query parsing: Structured output is a simple classification + extraction task. Cheaper and faster.
- **gpt-4o** for visualization decisions: Requires more nuanced judgment about encoding and chart appropriateness.

### Phase Filtering

`filter.phase` does not exist in the ClinicalTrials.gov v2 API (returns HTTP 400). Phase filtering is applied post-fetch in pandas. This means slightly more data is fetched than strictly needed, but avoids a client-side API quirk.

### In-Memory Cache

`cachetools.TTLCache` (1-hour TTL) caches ClinicalTrials.gov API responses. This avoids redundant API calls for identical queries within the same server session.

**Trade-off:** Cache is lost on restart. A Redis-backed cache would persist across restarts and be shared across multiple server instances. Omitted for simplicity.

### Network Graph

Builds a bipartite co-occurrence graph between interventions (drugs) and conditions. Edges are weighted by the number of trials where both appear. Pruned to top 50 nodes by degree centrality to keep the output frontend-friendly.

**Trade-off:** Pruning favors highly-connected entities and may drop rare but interesting relationships.

---

## Limitations & Future Improvements

1. **main.py test coverage (0%)**: The FastAPI endpoint requires a running server and mocked OpenAI. A full integration test suite with `httpx.AsyncClient(app=app)` and `unittest.mock.patch` on OpenAI would address this.

2. **Year-range filtering**: ClinicalTrials.gov API has no date range filter parameter. Filtering is done post-fetch, so `max_results` studies are fetched before the year filter is applied — the final data may have fewer points than expected.

3. **Single-study multi-phase**: A study with both PHASE1 and PHASE2 appears in both phase buckets. This inflates counts in distribution charts. Future work could deduplicate by primary phase.

4. **LLM viz selector fallback**: If the OpenAI call fails, a rule-based fallback is used. The fallback encodings are good for most cases but don't adapt to unusual column names from the transformer.

5. **Histogram support**: The `histogram` chart type is in the schema but the transformer doesn't have a dedicated histogram handler — it falls back to distribution. A proper histogram would bucket a continuous variable (e.g. enrollment count) into bins.

6. **Streaming responses**: Long-running queries (>500 studies) can take 5–10 seconds. A streaming endpoint using Server-Sent Events would improve perceived performance.

---

## Tools Used

- **Architecture & planning**: Claude Code (Anthropic) — used for architecture analysis, trade-off assessment, and implementation planning.
- **AI layer**: OpenAI GPT-4o-mini (query parsing) + GPT-4o (viz selection) via the Python SDK's structured output (`client.beta.chat.completions.parse()`).
- **Data layer**: pandas + networkx — standard Python data science stack with no LLM involvement in data computation.

**Accuracy verification:**
- ClinicalTrials.gov API field paths were verified against the live API before coding.
- All data values (counts, dates, names) in responses come directly from ClinicalTrials.gov API responses — no LLM-generated values.
- Citations (`nct_id` + `excerpt`) are extracted directly from the raw study records, not generated.
- Tests mock the CT.gov API with realistic response fixtures to verify pagination, caching, and data transformation without network calls.
