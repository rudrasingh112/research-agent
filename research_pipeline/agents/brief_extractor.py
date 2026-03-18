"""
agents/brief_extractor.py

Stage 1 of the pipeline (SequentialAgent step 1).

Parses the user's free-text research brief into a structured JSON object
and writes it to session state under the key "parsed_brief".

Downstream agents read {parsed_brief} via ADK's key-templating feature.
"""

from google.adk.agents import LlmAgent

from research_pipeline.callbacks.lifecycle import (
    after_agent_callback,
    after_model_callback,
    before_agent_callback,
    before_model_callback,
)
from research_pipeline.config.settings import settings

brief_extractor = LlmAgent(
    name="brief_extractor",
    model=settings.orchestrator_model,
    description=(
        "Parses a research brief into a structured JSON object with clearly "
        "defined research questions, data requirements, and output format."
    ),
    instruction="""
You are a research brief analyst. Your only job is to parse the user's
research request into a structured JSON object.

Extract the following fields:
  - topic: (string) the main subject of the research
  - research_questions: (list[str]) specific questions to answer from web/docs
  - data_questions: (list[str]) specific questions answerable from internal data
  - output_format: (string) "executive_summary" | "technical_report" | "briefing"
  - audience: (string) intended reader, e.g. "C-suite", "engineering team"
  - constraints: (list[str]) any constraints, e.g. "focus on Q3 2024", "EMEA only"

Output ONLY the JSON object. No preamble. No explanation. No markdown fences.

Example output:
{
  "topic": "Market share of our cloud product vs competitors",
  "research_questions": [
    "What are analysts saying about cloud market trends in 2024?",
    "What is AWS, Azure, and GCP market share trajectory?"
  ],
  "data_questions": [
    "What was our MRR growth in the past 6 months?",
    "Which customer segments grew fastest in Q3?"
  ],
  "output_format": "executive_summary",
  "audience": "C-suite",
  "constraints": ["Focus on enterprise segment", "2024 data only"]
}
""",
    # output_key writes the agent's final response into session.state["parsed_brief"]
    # The parallel agents and writing agent can then reference it as {parsed_brief}
    output_key="parsed_brief",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
