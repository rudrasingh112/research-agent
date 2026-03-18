"""
agents/pipeline.py

Assembles the full multi-agent pipeline.

Execution flow:
  SequentialAgent
    │
    ├─ [1] brief_extractor          → session.state["parsed_brief"]
    │
    ├─ [2] parallel_gather          (ParallelAgent — both run concurrently)
    │    ├─ research_agent          → session.state["research_findings"]
    │    └─ data_agent              → session.state["data_findings"]
    │
    └─ [3] writing_agent            → session.state["final_report"]
                                       + artifact: report_{session_id[:8]}.md

Key design decisions:
  - ParallelAgent children each write to UNIQUE output_key values.
    Sharing a key between parallel agents causes race conditions.
  - SequentialAgent passes the same InvocationContext to all steps,
    so session.state is naturally shared across all agents.
  - The pipeline is the root_agent — ADK's `adk deploy` and `Runner`
    both expect a module-level `root_agent` symbol.
"""

from google.adk.agents import ParallelAgent, SequentialAgent

from research_pipeline.agents.brief_extractor import brief_extractor
from research_pipeline.agents.data_agent import data_agent
from research_pipeline.agents.research_agent import research_agent
from research_pipeline.agents.writing_agent import writing_agent

# ── Stage 2: parallel fan-out ──────────────────────────────────────────────────
# research_agent and data_agent run simultaneously.
# Each writes to its own unique state key — no contention.
parallel_gather = ParallelAgent(
    name="parallel_gather",
    description=(
        "Runs web research and internal data retrieval concurrently "
        "to minimise total pipeline latency."
    ),
    sub_agents=[research_agent, data_agent],
)

# ── Root pipeline ──────────────────────────────────────────────────────────────
# ADK requires a module-level `root_agent` for `adk deploy` and `adk run`.
root_agent = SequentialAgent(
    name="ResearchPipeline",
    description=(
        "End-to-end research and report generation pipeline. "
        "Accepts a free-text brief, gathers web + data findings in parallel, "
        "and produces a structured report saved as a persistent artifact."
    ),
    sub_agents=[
        brief_extractor,    # step 1: parse brief → parsed_brief
        parallel_gather,    # step 2: research + data in parallel
        writing_agent,      # step 3: synthesise → final_report + artifact
    ],
)
