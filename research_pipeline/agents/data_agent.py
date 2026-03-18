"""
agents/data_agent.py

Parallel branch 2 of 2.

Uses BigQueryToolset to answer the data_questions from the parsed brief.
Runs concurrently with research_agent inside the ParallelAgent.

Writes findings to session.state["data_findings"].
The writing agent reads this via {data_findings} key templating.
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
from research_pipeline.tools.bigquery_tools import build_bigquery_toolset

data_agent = LlmAgent(
    name="data_agent",
    model=settings.worker_model,
    description=(
        "Answers data questions by querying internal BigQuery tables. "
        "Produces statistics, trends, and metrics relevant to the research brief."
    ),
    instruction=f"""
You are a senior data analyst with access to BigQuery.
You have been given a parsed research brief:

{{parsed_brief}}

Your task is to answer the DATA QUESTIONS in the brief using BigQuery tools.

Workflow:
1. Use bigquery-list-dataset-ids to discover available datasets.
2. Use bigquery-list-table-ids and bigquery-get-table-info to find relevant tables.
3. Write precise SELECT queries to answer each data question.
4. Execute queries with bigquery-execute-sql.
5. Summarize results clearly with key statistics.

Always run queries in project: {settings.google_cloud_project}.
NEVER modify data — read-only queries only.

Output format — return a JSON object:
{{
  "data_questions_answered": [
    {{
      "question": "...",
      "answer": "...",
      "key_metrics": {{"metric_name": "value", "metric_name2": "value2"}},
      "query_used": "SELECT ...",
      "data_quality_notes": "e.g. data through 2024-09-30"
    }}
  ],
  "notable_trends": ["trend1", "trend2"],
  "data_limitations": ["limitation1"],
  "tables_queried": ["dataset.table_name"]
}}

Output ONLY the JSON. No markdown fences. No preamble.
""",
    tools=[build_bigquery_toolset()],
    # CRITICAL: unique key — does not overlap with research_agent's output_key
    output_key="data_findings",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
