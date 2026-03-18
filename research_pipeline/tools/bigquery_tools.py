"""
tools/bigquery_tools.py

Builds the BigQuery toolset for the data agent.
Write operations are BLOCKED — the agent can only read and query.
"""

import google.auth
from google.adk.tools.bigquery import (
    BigQueryCredentialsConfig,
    BigQueryToolset,
)
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode

from research_pipeline.config.settings import settings


def build_bigquery_toolset() -> BigQueryToolset:
    """
    Returns a read-only BigQueryToolset scoped to the configured project.

    Available tools the LLM can call:
      - bigquery-list-dataset-ids        → discover available datasets
      - bigquery-get-dataset-info        → get dataset metadata & description
      - bigquery-list-table-ids          → list tables in a dataset
      - bigquery-get-table-info          → fetch schema + sample rows
      - bigquery-execute-sql             → run a SELECT query
      - bigquery-forecast                → TimesFM time-series prediction
      - bigquery-analyze-contribution    → contribution analysis

    Write operations (INSERT, UPDATE, DELETE, CREATE) are explicitly blocked.
    """
    adc, _ = google.auth.default()

    tool_config = BigQueryToolConfig(
        write_mode=WriteMode.BLOCKED,           # production safety gate
    )

    credentials_config = BigQueryCredentialsConfig(
        credentials=adc,
    )

    return BigQueryToolset(
        credentials_config=credentials_config,
        bigquery_tool_config=tool_config,
    )
