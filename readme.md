# Enterprise Research & Report Generation Pipeline

A production-grade multi-agent system built with Google ADK, deployed to Agent Engine.

## Architecture

```
ResearchPipeline (SequentialAgent)
 ├── brief_extractor       (LlmAgent)         — parse + validate the user brief
 ├── parallel_gather       (ParallelAgent)     — fan-out concurrent research
 │    ├── research_agent   (LlmAgent)          — Vertex AI Search + Google Search
 │    └── data_agent       (LlmAgent)          — BigQuery internal metrics
 └── writing_agent         (LlmAgent)          — merge + write structured report
```

All agents share `session.state` via `output_key`. The writing agent reads
`{research_findings}` and `{data_findings}` injected by the parallel agents.

## Session & Persistence

| Environment | SessionService               | ArtifactService        |
|-------------|------------------------------|------------------------|
| Local dev   | `DatabaseSessionService`     | `InMemoryArtifactService` |
| Production  | `VertexAiSessionService`     | `GcsArtifactService`   |

The final report PDF is saved as a GCS artifact and referenced in session state
so any downstream system can fetch it by `session_id`.

## Project layout

```
research_pipeline/
├── agents/
│   ├── brief_extractor.py
│   ├── research_agent.py
│   ├── data_agent.py
│   ├── writing_agent.py
│   └── pipeline.py          ← root agent exported here
├── services/
│   ├── session.py
│   └── artifacts.py
├── tools/
│   ├── search_tools.py
│   └── bigquery_tools.py
├── callbacks/
│   └── lifecycle.py
├── config/
│   └── settings.py
├── main.py                   ← local runner / FastAPI server
├── requirements.txt
├── .env.example
└── Dockerfile
```

## Quickstart

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env && vim .env

# 3. Run locally
python main.py

# 4. Deploy to Agent Engine
adk deploy agent_engine \
  --staging_bucket="gs://$PROJECT_ID-adk-staging" \
  --display_name="Research Pipeline" \
  --trace_to_cloud \
  ./research_pipeline
```