"""
services/artifacts.py

Returns the correct ArtifactService implementation based on the environment.

┌─────────────┬──────────────────────────────────┬───────────────────────────┐
│ Environment │ Service                          │ Backend                   │
├─────────────┼──────────────────────────────────┼───────────────────────────┤
│ local       │ InMemoryArtifactService          │ RAM (lost on restart)     │
│ staging /   │ GcsArtifactService               │ GCS bucket                │
│ production  │                                  │ gs://<bucket>/artifacts/  │
└─────────────┴──────────────────────────────────┴───────────────────────────┘

GCS artifacts are automatically versioned by ADK. Each save_artifact() call
returns a version number. The writing_agent stores the version in session state
so the report can be retrieved deterministically:

  artifact = await runner.artifact_service.load_artifact(
      app_name=app_name,
      user_id=user_id,
      session_id=session_id,
      filename="report_abc12345.md",
      version=2,   # or None for latest
  )
"""

import logging

from google.adk.artifacts import InMemoryArtifactService

from research_pipeline.config.settings import Env, settings

logger = logging.getLogger(__name__)


def build_artifact_service():
    """
    Factory: return the right ArtifactService for the current environment.
    """
    if settings.env in (Env.STAGING, Env.PRODUCTION) and settings.gcs_artifact_bucket:
        try:
            from google.adk.artifacts import GcsArtifactService
            logger.info(
                "Using GcsArtifactService (bucket=%s)", settings.gcs_artifact_bucket
            )
            return GcsArtifactService(bucket_name=settings.gcs_artifact_bucket)
        except ImportError:
            logger.warning(
                "GcsArtifactService not available; falling back to InMemory. "
                "Install google-cloud-storage."
            )

    logger.warning(
        "Using InMemoryArtifactService — artifacts will be lost on restart. "
        "Set GCS_ARTIFACT_BUCKET for persistent artifact storage."
    )
    return InMemoryArtifactService()
