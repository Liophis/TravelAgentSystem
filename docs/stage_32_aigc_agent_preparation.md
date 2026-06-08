# Stage 32 AIGC Agent Preparation

## Scope

This is a preparation stage for upgrading the current AIGC placeholder into a lightweight workflow Agent. It updates harness docs and fixes the acceptance target before backend/frontend implementation.

The goal is not to claim real external video generation. The next code stage should demonstrate an Agent-style orchestration flow with deterministic local tools, clear trace output, and replaceable external-model boundaries.

## Target Behavior

The AIGC assistant should accept diary text, destination/campus context, and scenic/school media URLs, then orchestrate several tools:

```text
input context
  -> media_analyzer
  -> diary_writer
  -> storyboard_planner
  -> prompt_builder
  -> video_generator_mock
  -> diary_compressor_summary
  -> final artifact
```

## New API Target

```text
POST /api/v1/aigc/agent/run
```

Request fields:

```text
task: diary_animation | diary_draft | storyboard
text: user description or diary body
destination_name: optional attraction/school/campus name
style: natural | lively | formal | cinematic
media_urls: image/video URL or path list
scene_count: 1-8
user_id: optional personalization context
diary_id: optional source diary
```

Response fields:

```text
result.title
result.draft
result.storyboard
result.prompt
result.simulated_video_url
agent_trace.steps[]
agent_trace.total_duration_ms
algorithm_trace.mode
algorithm_trace.tool_count
algorithm_trace.media_inputs
```

Each `agent_trace.steps[]` item should include:

```text
step
tool
input_summary
output_summary
status
duration_ms
```

## Compatibility Rule

Keep the existing endpoints for backward compatibility:

```text
POST /api/v1/aigc/diary-draft
POST /api/v1/aigc/storyboard
```

They may call the new Agent internally later, but public behavior should not break existing tests.

## Frontend Target

`AigcAssistantPage` should become a single Agent workspace:

- task selector
- destination/campus context input
- text/media inputs
- scene count/style controls
- generated title/draft/storyboard/video artifact
- compact Agent trace timeline/table

The page should not present the result as real video generation. Use labels such as `模拟视频链接` and `Agent 执行轨迹`.

## Acceptance Criteria

- `POST /api/v1/aigc/agent/run` works without network access.
- Response includes both `result` and `agent_trace`.
- Agent trace lists at least 4 tool steps.
- `media_urls` affects media analysis and storyboard output.
- Existing `diary-draft` and `storyboard` endpoints still pass.
- Frontend can call the Agent endpoint and display trace/result.
- Tests verify deterministic output and trace shape.

## Planned Validation

After implementation:

```bash
bash scripts/check_backend.sh
bash scripts/check_frontend.sh
bash scripts/check_all.sh
```

Before implementation, this documentation stage only requires:

```bash
bash scripts/check_merge_markers.sh
```
