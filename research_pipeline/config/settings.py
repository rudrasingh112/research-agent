"""
config/settings.py
Central configuration loaded from environment variables.
Uses pydantic-settings so every value is type-checked at startup.
"""
import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ── GCP ────────────────────────────────────────────────────────────────
    google_cloud_project: str
    google_cloud_location: str = "us-central1"
    env: Env = Env.LOCAL

    # ── App identity ───────────────────────────────────────────────────────
    app_name: str = "research_pipeline"

    # ── Models ─────────────────────────────────────────────────────────────
    orchestrator_model: str = "gemini-2.5-flash"
    worker_model: str = "gemini-2.5-flash"

    # ── BigQuery ───────────────────────────────────────────────────────────
    bq_dataset: str = "analytics"           # dataset the data agent can query
    bq_write_mode: str = "BLOCKED"          # never let agents mutate data

    # ── Vertex AI Search ───────────────────────────────────────────────────
    vertex_search_engine_id: str = ""       # e.g. "my-engine_1234567890"

    # ── Session persistence ────────────────────────────────────────────────
    # Local: sqlite+aiosqlite:///./sessions.db
    # Prod:  postgresql+asyncpg://user:pass@host/db
    database_url: str = "sqlite+aiosqlite:///./sessions.db"

    # ── Artifact storage ───────────────────────────────────────────────────
    gcs_artifact_bucket: str = ""           # required in staging / production

    # ── Observability ──────────────────────────────────────────────────────
    enable_cloud_trace: bool = True
    bq_analytics_dataset: str = "adk_logs"
    bq_analytics_table: str = "agent_events"

    @property
    def is_production(self) -> bool:
        return self.env == Env.PRODUCTION

    @property
    def is_local(self) -> bool:
        return self.env == Env.LOCAL


settings = Settings()