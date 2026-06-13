# Stage 43 Demo Experience And LLM User Profile

## Goal

Improve the project from a collection of usable modules into a defense-friendly product demo, while adding a real configurable LLM enhancement at the user profile layer.

This stage must not replace the course algorithms. Dijkstra, Top-K heap ranking, text search, compression, and graph-distance facility ranking remain deterministic and testable. The LLM only converts user behavior text into interest tags and profile explanations.

## Deliverables

- Add a defense demo page:
  - route: `/demo`;
  - shows one-click scenario status for destinations, routing, nearby facilities, diaries, foods, and AIGC/profile;
  - shows algorithm traces in a readable panel;
  - includes an ECharts relationship graph for the demo scenario.
- Upgrade the home page into a data dashboard:
  - data scale cards;
  - core algorithm cards;
  - demo scene entry points;
  - direct link to the defense demo page.
- Add LLM user profile extraction:
  - `POST /api/v1/users/{id}/profile/llm-extract`;
  - `GET /api/v1/users/{id}/profile/analysis`;
  - OpenAI-compatible chat-completions client;
  - deterministic fallback when no key is configured or when the provider fails;
  - extracted tags are written back to `user_interests`.
- Frontend personal center:
  - "AI 分析我的兴趣" action;
  - summary, evidence, weights, provider/model/fallback trace;
  - recommendation preview refresh after extraction.
- Harness updates:
  - `.env.example`;
  - feature matrix;
  - acceptance checklist;
  - backend tests with mocked/fallback LLM.

## Environment

```bash
LLM_API_KEY=your_openai_compatible_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=20
```

No key is required for local tests. Without a key, profile extraction uses deterministic behavior/tag aggregation and marks `fallback_used=true`.

## API Contract

```text
POST /api/v1/users/{id}/profile/llm-extract
GET  /api/v1/users/{id}/profile/analysis
```

Response shape:

```json
{
  "user_id": 1,
  "tags": ["history", "campus"],
  "weights": {"history": 0.86, "campus": 0.72},
  "summary": "用户偏好历史文化和校园参观。",
  "evidence": ["收藏了颐和园", "浏览了北京大学"],
  "updated_profile": {},
  "algorithm_trace": {
    "stage": "stage-43-llm-user-profile",
    "provider": "openai-compatible",
    "model": "gpt-4o-mini",
    "fallback_used": "false"
  }
}
```

## Validation

```bash
PYTHONPATH=backend python -m pytest backend/tests/test_stage43_llm_profile.py
cd frontend && npm run typecheck
bash scripts/check_all.sh
```

## Acceptance

- LLM profile extraction works with a mocked provider in tests.
- Missing LLM configuration does not break the application.
- Extracted tags affect `GET /api/v1/recommendations?strategy=interest|composite`.
- The personal center shows profile summary, evidence, weights, and algorithm trace.
- The demo page shows at least three real API traces and one relationship graph.
