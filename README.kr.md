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

### 1. Architecture & Plan

- 통계, 계산된 숫자 및 aggregation은 hallucination 위험을 줄이기 위해 `deterministic pipeline`으로 제한하기로 결정

- 아키텍처를 설계는 claude cli를 통해서 Planning agent를 이용하여 아키텍처를 설계

- Planning agent와 implementation agent(code generator)를 분리하여 구현 코드가 초기 아키텍처에서 벗어나지 않는지 검증

### 2. Claude CLI

- tests 내부의 14개 테스트 파일은 Claude cli를 통해 생성되었다. 실제 implementation interface 기준으로 테스트를 작성 → 최종적으로 test coverage를 85%이상 달성

- LLM prompts를 Claude cli를 통해 반복적으로 개선. 실제 query 테스트를 진행하면서 intent classification rules, phase normalization table, comparison entity extraction grammar
를 통해서 검증되고 prompt가 개선되었다

- 반복적인 Frontend 구현 작업은 Claude Cli를 활용하여 구축하였으며 이 안에 Backend에서 오는 Structured-JSON 데이터를 해석하고 화면에 렌더링하는 파이트라인은 설계 및 구현

### 3. Data layer

- Python 분석 스택을 사용 (Pandas + networkx)

- 계산 과정에서 LLM은 관여하지 않음 — 정확성과 재현 가능성을 보장

---

## 핵심 아키텍처 - 6단계 Deterministic Pipeline

이 시스템의 가장 중요한 설계 원칙은 다음과 같습니다.

- 통계, 계산, 집계는 반드시 결정론적(deterministic) 코드로 수행
- LLM은 "의미를 해석"하는 두 지점에서만 호출하고, 숫자를 만들어내지 않는다
 
이를 통해 "2018년에 203건"과 같은 수치가 LLM의 hallucination이 아닌 실제 데이터 기반의 정확한 계산 결과임을 보장

```
         사용자 질의 (자연어)
                │
                ▼
┌──────────────────────────────────┐
│  1. LLM: 의도 분류 + 엔티티 추출      │  ← GPT-4.1-mini
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  2.Rule-based: API 파라미터 생성    │  ← 코드 (1:1 매핑)
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  3. Fetch: ClinicalTrials.gov    │  ← HTTP 요청 + 캐시
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  4. Rule-based: 데이터 변환/집계     │  ← Pandas / NetworkX
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│  5. LLM: 시각화 스키마 선택          │  ← GPT-4.1
└──────────────┬───────────────────┘
               ▼
        프론트엔드 응답 (JSON)
```

LLM이 호출되는 곳은 1과 5단 두 곳뿐입니다. 나머지 2,3,4는 규칙 기반 코드로만 동작하여, 데이터의 정확성을 보장


### 1. LLM: 의도 분류 + 엔티티 추출

담당 모듈: `query_parser.py` → `QueryParser.parse()`

사용자의 자연어 질의를 구조화된 데이터로 변환합니다. GPT-4.1-mini에게 `ParsedQuery` Pydantic 스키마를 강제(structured output)하여 응답

Why LLM? 

- "각 연도별로 몇 개?", "연간 추세를 보여줘", "year-over-year" 등 다양한 표현이 모두 동일한 의도(`TREND_OVER_TIME`)로 수렴해야 하므로, 규칙 기반으로는 커버할 수 없는 `의미적 판단`이 필요

| 입력 (자연어) | 출력 (구조화 데이터) |
|---|---|
| `"How many Pembrolizumab trials started each year?"` | 아래 참조 |

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
 
 ### 2. Rule-based: ClinicalTrials.gov API 파라미터 생성
 
담당 모듈: `api_builder.py` → `build_ct_params()`, `get_phase_filter()`
 
1번에서 추출한 엔티티를 ClinicalTrials.gov API가 이해하는 파라미터로 변환. 이 변환은 API 스펙과의 1:1 매핑이므로 LLM이 필요 없다
 
| 추출된 엔티티 | API 파라미터 | 설명 |
|---|---|---|
| `drug_name = "Pembrolizumab"` | `query.intr = "Pembrolizumab"` | 시험 약물(intervention) 필드 |
| `condition = "lung cancer"` | `query.cond = "lung cancer"` | 질환 필드 |
| `sponsor = "Merck"` | `query.spons = "Merck"` | 후원 기관 필드 |
 
이 예시에서는 `drug_name`만 존재하므로, `query.intr = "Pembrolizumab"`이 생성됩니다.
 
---
 
### 3. Fetch: ClinicalTrials.gov API 호출
 
담당 모듈: `data_fetcher.py` + `clinicaltrials.py`
 
2번에서 만든 파라미터로 ClinicalTrials.gov API를 호출하여 실제 임상시험(study) 데이터를 가져온다
 
핵심 동작
 
- 페이지네이션을 통해 전체 결과를 수집
- `TTLCache`(1시간)로 동일 요청의 중복 API 호출을 방지
- 결과: 수백 건의 study 데이터 (JSON 리스트)
---
 
### 4. Rule-based: Pandas/NetworkX 데이터 변환
 
담당 모듈: `transformer.py` → `normalizers.py` → `transforms/tabular.py`
 
3번에서 받은 원시 데이터를 분석 가능한 형태로 정규화하고, 1번에서 파악한 의도(`TREND_OVER_TIME`)에 맞는 집계를 수행
 
왜 LLM이 아닌 Pandas인가?
 
- `groupby`, `count`, `filter` 같은 연산은 Pandas가 정확하고 결정론적으로 수행합니다. LLM이 "2018년에 203건"이라고 응답하면 그것이 실제 수치인지 hallucination인지 검증할 수 없지만, Pandas의 결과는 항상 정확합니다.
 
변환 과정 예시:
 
```
원시 데이터 (중첩된 study dict 리스트)
    │
    ▼  normalizers.py: 플랫 DataFrame으로 정규화
    │
    ├─ startDate 파싱 → year 컬럼 추출
    ├─ phase 정규화 (예: "Phase 2/Phase 3" → ["PHASE2", "PHASE3"])
    │
    ▼  transforms/tabular.py: intent에 따른 집계
    │
    └─ TREND_OVER_TIME → df.groupby("year").size()
```
 
**최종 산출 데이터:**
 
| year | count |
|------|-------|
| 2015 | 12 |
| 2016 | 28 |
| 2017 | 45 |
| 2018 | 67 |
| … | … |
 
---
 
### 5. LLM: 시각화 스키마 선택
 
담당 모듈: `pipeline/viz_selector.py` → `VizSelector.select()`
 
4번에서 산출된 데이터의 스키마 정보(컬럼 이름, 데이터 타입, 행 수 등)를 보고, GPT-4.1이 어떤 차트 타입과 인코딩이 적합한지 결정합니다.
 
Why LLM?
 
- "연도별 추이 데이터에는 시계열 차트가 어울린다"는 판단은 데이터의 의미를 이해해야 하는 시맨틱 판단이기 때문이다
 
입력 (데이터 스키마):
 
```
컬럼: [year (int), count (int)]
행 수: 10
의도: TREND_OVER_TIME
```
 
출력 (시각화 스펙):
 
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
 
이 JSON이 프론트엔드로 전달되어 차트가 렌더링됩니다.
    
## 설계 결정과 트레이드오프
 
### 1. Two-Model 전략
 
| 단계 | 모델 | 선택 근거 |
|------|------|-----------|
| Query Parsing (①) | GPT-4.1-mini | intent 분류와 엔티티 추출은 structured output 중심의 경량 작업이므로 빠르고 저렴한 모델로 충분 |
| Visualization Selection (⑤) | GPT-4.1 | 데이터의 의미적 특성과 차트 적합성을 함께 판단해야 하므로 추론 품질이 높은 모델이 필요 |
 
### 2. Dual Phase Counting 전략
 
임상시험은 "Phase 2/Phase 3"처럼 여러 단계에 걸치는 경우가 있어, 단순 카운팅 시 중복 집계 문제가 발생 
 
| 전략 | 적용 조건 | 동작 방식 |
|------|-----------|-----------|
| **InclusiveHybridStrategy** | phase 필터 미지정 또는 복수 phase 질의 | 하이브리드 시험을 해당하는 모든 phase 버킷에 포함 |
| **StrictFilterStrategy** | 단일 phase 질의 | 하이브리드 시험을 포함하되, 요청된 phase에만 표시 |
 
예를 들어, Phase 3만 질의했을 때 "Phase 2/Phase 3" 시험이 Phase 2 그래프에 불필요하게 나타나는 문제를 StrictFilterStrategy로 방지
 
### 3. In-Memory TTL Cache
 
`cachetools.TTLCache`를 사용하여 ClinicalTrials.gov 응답을 서버 메모리에 1시간 동안 캐싱합니다.
 
| 항목 | 내용 |
|------|------|
| 도입 근거 | 동일 query에 대한 CT.gov 응답은 1시간 내에 변하지 않으므로, 불필요한 API 왕복을 제거 |
| Redis 미도입 사유 | 현재 single-instance 규모이므로 단순성을 우선시 |
| 알려진 한계 | 서버 재시작 시 캐시 소멸, multi-instance 환경에서 캐시 공유 불가 |
 
---

## 향후 개선 사항

| 영역 | 개선 내용 |
|------|-----------|
| 캐싱 | Redis 기반 cross-request 캐싱으로 multi-instance 환경 지원 |
| 응답 방식 | 장시간 쿼리를 위한 gRPC 기반 스트리밍 응답 구현 |
| 보안 | Prompt injection 방어를 위한 프롬프트 리팩토링 |