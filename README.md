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
git clone https://github.com/syjoe02/Cheiron-backend.git
cd Cheiron-backend/ 
uv sync
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 4. Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- The API is now available at `http://localhost:8000`.
- And swagger docs: `http://localhost:8000/docs`

---

## Schema Reference

### 1. Request Schema — `POST /query`

| Field         | Type       | Required | Description                               |
| ------------- | ---------- | -------- | ----------------------------------------- |
| `query`       | `string`   | Required | User query (3–500 characters)             |
| `drug_name`   | `string`   | Optional | Drug / treatment name                     |
| `condition`   | `string`   | Optional | Disease / medical condition               |
| `phase`       | `string[]` | Optional | Clinical trial phases                     |
| `sponsor`     | `string`   | Optional | Sponsor organization                      |
| `country`     | `string`   | Optional | Country / location filter                 |
| `start_year`  | `number`   | Optional | Minimum start year (starting from 1960)   |
| `end_year`    | `number`   | Optional | Maximum start year                        |
| `max_results` | `number`   | Optional | Maximum number of results to fetch        |

### 2. Response Schema — `POST /query`

| Field           | Type                | Description       |
| --------------- | ------------------- | ----------------- |
| `visualization` | `VisualizationSpec` | Visualization data |
| `meta`          | `MetaInfo`          | Query / meta information |

### 3. Chart types and encodings

| `type` | Encoding keys | Use case |
|---|---|---|
| `time_series` | `x.field`, `y.field` | Trials over years |
| `bar_chart` | `x.field`, `y.field` | Distribution by one dimension |
| `grouped_bar_chart` | `x.field`, `y.field`, `series.field` | Comparison across two dimensions |
| `scatter_plot` | `x.field`, `y.field`, `color.field` | Correlation between two numerics |
| `histogram` | `x.field`, `y.field` | Distribution of a continuous variable |
| `network_graph` | `nodes.{id,label,size,color}`, `edges.{source,target,weight}` | Entity co-occurrence graph |

### 4. GET /health

Returns `{"status": "ok", "version": "0.1.0"}`

### 5. Example Runs

See detailed example requests and responses here: [exampleRuns.md](./exampleRuns.md)

---

## Tools Used
 
### 1. Architecture & Planning
 
- All statistics, computed values, and aggregations are confined to a deterministic pipeline to eliminate hallucination risk.
- The architecture was designed using Claude CLI's Planning Agent.
- The Planning Agent and Implementation Agent (code generator) were kept separate to verify that the implementation never drifted from the original architecture.

### 2. Claude CLI
 
- **Test generation:** All 14 test files under `tests/` were generated via Claude CLI, written against the actual implementation interfaces — ultimately achieving over 85% test coverage.
- **Prompt optimization:** LLM prompts were iteratively refined through Claude CLI. Each iteration was validated against real queries, improving intent classification rules, the phase normalization table, and comparison entity extraction grammar.
- **Frontend implementation:** Repetitive frontend work was built with Claude CLI, including the pipeline that parses structured JSON from the backend and renders it on screen.

### 3. Data Layer
 
- Python analytics stack (Pandas + NetworkX)
- The LLM plays no role in computation — ensuring accuracy and reproducibility.

---

## Core Architecture — 6-Stage Deterministic Pipeline
 
The most important design principle of this system:
 
- Statistics, calculations, and aggregations must always be performed by deterministic code.

- The LLM is invoked at only two points — to "interpret meaning" — and never produces numerical values.
This guarantees that a figure like "203 trials in 2018" is an accurate computation from real data, not an LLM hallucination.

```
         User Query (natural language)
                │
                ▼
┌──────────────────────────────────────┐
│  1. LLM: Intent Classification       │  ← GPT-4.1-mini
│          + Entity Extraction         │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  2. Rule-based: API Parameter        │  ← Code (1:1 mapping)
│                 Construction         │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  3. Fetch: ClinicalTrials.gov API    │  ← HTTP request + cache
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  4. Rule-based: Data Transformation  │  ← Pandas / NetworkX
│                 & Aggregation        │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  5. LLM: Visualization Schema        │  ← GPT-4.1
│          Selection                   │
└──────────────┬───────────────────────┘
               ▼
        Frontend Response (JSON)
```

The LLM is called in **stages 1 and 5 only**. Stages 2, 3, and 4 run entirely on rule-based code, guaranteeing data accuracy.

### Stage 1 — LLM: Intent Classification + Entity Extraction
 
**Module:** `query_parser.py` → `QueryParser.parse()`
 
Converts the user's natural language query into structured data. GPT-4.1-mini is called with a `ParsedQuery` Pydantic schema enforced via structured output.
 
**Why use an LLM here?**
 
Expressions like "how many per year", "show me the annual trend", and "year-over-year" must all resolve to the same intent (`TREND_OVER_TIME`). This kind of semantic judgment cannot be captured by static rules.
 
**Input → Output:**
 
| Input (natural language) | Output (structured data) |
|---|---|
| `"How many Pembrolizumab trials started each year?"` | See below |

```
"each year", "started" → intent = TREND_OVER_TIME
"Pembrolizumab"        → entities.drug_name = "Pembrolizumab"
```
 
```python
ParsedQuery(
    intent          = QueryIntent.TREND_OVER_TIME,
    entities        = ParsedEntities(drug_name="Pembrolizumab"),
    query_interpretation = "Number of Pembrolizumab trials started per year",
    assumptions     = []
)
```
 
 ### Stage 2 — Rule-based: API Parameter Construction
 
**Module:** `api_builder.py` → `build_ct_params()`, `get_phase_filter()`
 
Maps the entities extracted in Stage 1 to ClinicalTrials.gov API parameters. This is a direct 1:1 mapping against the API spec, so no LLM is needed.
 
| Extracted Entity | API Parameter | Description |
|---|---|---|
| `drug_name = "Pembrolizumab"` | `query.intr = "Pembrolizumab"` | Intervention field |
| `condition = "lung cancer"` | `query.cond = "lung cancer"` | Condition field |
| `sponsor = "Merck"` | `query.spons = "Merck"` | Sponsor field |
 
In this example, only `drug_name` is present, so the output is `query.intr = "Pembrolizumab"`

---
 
### Stage 3 — Fetch: ClinicalTrials.gov API Call
 
Module: `data_fetcher.py` + `clinicaltrials.py`
 
Calls the ClinicalTrials.gov API with the parameters built in Stage 2 to retrieve actual clinical trial (study) data.
 
Key behaviors:
 
- Paginates through the full result set
- Uses `TTLCache` (1-hour TTL) to prevent redundant API calls for identical requests
- Output: hundreds of study records as a JSON list

---
 
### Stage 4 — Rule-based: Data Transformation with Pandas/NetworkX
 
Module: `transformer.py` → `normalizers.py` → `transforms/tabular.py`
 
Normalizes the raw data from Stage 3 into an analyzable format, then performs aggregations matching the intent identified in Stage 1 (`TREND_OVER_TIME`).
 
Why Pandas instead of an LLM?
 
- Operations like `groupby`, `count`, and `filter` are executed accurately and deterministically by Pandas. If an LLM says "203 trials in 2018," there is no way to verify whether that number is real or hallucinated. Pandas results are always exact.
 
Transformation flow:
 
```
Raw data (nested study dict list)
    │
    ▼  normalizers.py — flatten into a DataFrame
    │
    ├─ Parse startDate → extract year column
    ├─ Normalize phase (e.g., "Phase 2/Phase 3" → ["PHASE2", "PHASE3"])
    │
    ▼  transforms/tabular.py — aggregate by intent
    │
    └─ TREND_OVER_TIME → df.groupby("year").size()
```
 Resulting dataset:
 
| year | count |
|------|-------|
| 2015 | 12 |
| 2016 | 28 |
| 2017 | 45 |
| 2018 | 67 |
| … | … |
 
---
 
### Stage 5 — LLM: Visualization Schema Selection
 
Module: `pipeline/viz_selector.py` → `VizSelector.select()`
 
Given the schema information from Stage 4 (column names, data types, row count, etc.), GPT-4.1 determines the most appropriate chart type and encoding.
 
Why use an LLM here?
 
- The judgment that "a time-series chart is the best fit for year-over-year trend data" requires understanding the semantic meaning of the data — a task that goes beyond mechanical rules.
 
Input (data schema):
 
```
Columns: [year (int), count (int)]
Rows:    10
Intent:  TREND_OVER_TIME
```
 
Output (visualization spec):
 
```json
{
  "type": "time_series",
  "encoding": {
    "x": { "field": "year",  "type": "temporal" },
    "y": { "field": "count", "type": "quantitative" }
  },
  "data": [
    { "year": 2015, "count": 12 },
    { "year": 2016, "count": 28 },
    ...
  ]
}
```
 
This JSON is sent to the frontend, where it is rendered as a chart
    
## Design Decisions & Tradeoffs
 
### 1. Two-Model Strategy
 
| Stage | Model | Rationale |
|-------|-------|-----------|
| Query Parsing (Stage 1) | GPT-4.1-mini | Intent classification and entity extraction are lightweight structured-output tasks — a fast, cost-effective model is sufficient. |
| Visualization Selection (Stage 5) | GPT-4.1 | Choosing the right chart requires reasoning about data semantics and chart appropriateness — a higher-capability model is needed. |
 
### 2. Dual Phase Counting Strategy
 
Clinical trials can span multiple phases (e.g., "Phase 2/Phase 3"), which creates duplicate counting issues with naive aggregation. Two strategies handle this:
 
| Strategy | When Applied | Behavior |
|----------|-------------|----------|
| InclusiveHybridStrategy | No phase filter, or multi-phase query | Includes hybrid trials in all matching phase buckets |
| StrictFilterStrategy | Single-phase query | Includes hybrid trials but displays them only under the requested phase |
 
For example, when querying Phase 3 only, a "Phase 2/Phase 3" trial would incorrectly appear under Phase 2 without StrictFilterStrategy.
 
### 3. In-Memory TTL Cache
 
ClinicalTrials.gov responses are cached in server memory for 1 hour using `cachetools.TTLCache`
 
| Aspect | Detail |
|--------|--------|
| Rationale | CT.gov responses for the same query do not change within an hour — caching eliminates unnecessary API round-trips. |
| Why not Redis | At the current single-instance scale, simplicity is prioritized over distributed caching. |
| Known limitations | Cache is lost on server restart; cache is not shared across instances in a multi-instance deployment. |
 
---
 
## Future Improvements
 
| Area | Planned Enhancement |
|------|---------------------|
| Caching | Redis-based cross-request caching for multi-instance support |
| Response delivery | gRPC-based streaming responses for long-running queries |
| Security | Prompt refactoring to defend against prompt injection attacks |