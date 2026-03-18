"""
agents/research_agent.py

Parallel branch 1 of 2.

Uses Vertex AI Search (internal knowledge base) and Google Search (live web)
to answer the research_questions extracted from the parsed brief.

Writes findings to session.state["research_findings"].
The writing agent reads this via {research_findings} key templating.
"""

from google.adk.agents import LlmAgent

from research_pipeline.callbacks.lifecycle import (
    after_agent_callback,
    after_model_callback,
    after_tool_callback,
    before_agent_callback,
    before_model_callback,
    before_tool_callback,
)
from research_pipeline.config.settings import settings
from research_pipeline.tools.search_tools import build_search_tools

research_agent = LlmAgent(
    name="research_agent",
    model=settings.worker_model,
    description=(
        "Answers research questions using Vertex AI Search (internal documents) "
        "and Google Search (live web). Produces a structured findings summary."
    ),
    instruction="""
You are a senior research analyst. You have been given a parsed research brief:

{parsed_brief}

Your task is to answer the RESEARCH QUESTIONS in the brief using your search tools.

Instructions:
1. Use Vertex AI Search first to check internal documents and knowledge bases.
2. Use Google Search to supplement with current public information.
3. For each research question, provide:
   - A direct answer (2-4 sentences)
   - Key supporting evidence (bullet points with sources)
   - Confidence level: HIGH / MEDIUM / LOW

Output format — return a JSON object:
{
  "research_questions_answered": [
    {
      "question": "...",
      "answer": "...",
      "evidence": ["source1: ...", "source2: ..."],
      "confidence": "HIGH"
    }
  ],
  "key_themes": ["theme1", "theme2"],
  "knowledge_gaps": ["gap1", "gap2"],
  "sources_consulted": ["url or doc name"]
}

Output ONLY the JSON. No markdown fences. No preamble.
""",
    tools=build_search_tools(),
    # CRITICAL: use a unique output_key — parallel agents share session.state
    # and must write to different keys to avoid race conditions
    output_key="research_findings",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
