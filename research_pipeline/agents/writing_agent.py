"""
agents/writing_agent.py

Stage 3 of the pipeline (SequentialAgent step 3, after ParallelAgent).

Reads research_findings and data_findings from session state via
ADK's {key} templating and produces the final structured report.

After the agent completes, the after_agent_callback saves the report
as a persistent artifact via GcsArtifactService.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

from research_pipeline.callbacks.lifecycle import (
    after_model_callback,
    before_agent_callback,
    before_model_callback,
    save_report_artifact,
)
from research_pipeline.config.settings import settings


async def writing_agent_after_callback(callback_context: CallbackContext) -> None:
    """
    After the writing agent finishes, persist the report as an artifact
    and stamp the session state with completion metadata.
    """
    report = callback_context.state.get("final_report", "")
    if report:
        await save_report_artifact(callback_context, report)

    # Mark the pipeline as complete — useful for polling / webhooks
    callback_context.state["pipeline_status"] = "complete"
    callback_context.state["pipeline_complete"] = True


writing_agent = LlmAgent(
    name="writing_agent",
    model=settings.orchestrator_model,   # use the stronger model for synthesis
    description=(
        "Synthesises research findings and internal data metrics into a "
        "polished, structured report tailored to the intended audience."
    ),
    instruction="""
You are a principal analyst and expert technical writer.

You have been given:

ORIGINAL BRIEF:
{parsed_brief}

RESEARCH FINDINGS (from web + internal docs):
{research_findings}

DATA FINDINGS (from internal BigQuery metrics):
{data_findings}

Your task is to write a complete, polished report.

Report structure (adapt section titles to match output_format and audience):
─────────────────────────────────────────────────────────────
# [Report Title]

**Prepared for:** [audience from brief]
**Date:** [today's date]
**Classification:** Internal

## Executive Summary
2-4 paragraph overview. State the key conclusion first.

## Key Findings
### Research Insights
Synthesise web + document findings. Cite sources inline.

### Internal Metrics
Present data findings with specific numbers. Call out trends.

## Analysis
Interpret what the findings mean together. Connect research to data.
Highlight agreements and contradictions.

## Recommendations
3-5 actionable recommendations numbered and prioritised.

## Data Limitations & Caveats
Be transparent about confidence levels and data gaps.

## Sources
List all sources consulted.
─────────────────────────────────────────────────────────────

Rules:
- Match the tone and depth to the audience (e.g. executive = concise;
  engineering = technical detail)
- Use specific numbers from data findings — never say "significant increase",
  say "23% increase"
- Do not invent facts. If a data question was unanswerable, say so explicitly.
- Output the full report in Markdown.
""",
    # Writing agent's output goes to final_report in session state
    output_key="final_report",
    before_agent_callback=before_agent_callback,
    after_agent_callback=writing_agent_after_callback,  # custom: saves artifact
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
