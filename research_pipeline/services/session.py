import logging

from google.adk.sessions import DatabaseSessionService, InMemorySessionService

from research_pipeline.config.settings import Env, settings

logger = logging.getLogger(__name__)


def build_session_service():
    if settings.env == Env.PRODUCTION:
        try:
            from google.adk.sessions import VertexAiSessionService
            logger.info("Using VertexAiSessionService (production)")
            return VertexAiSessionService(
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
        except ImportError:
            logger.warning("VertexAiSessionService not available, falling back to DatabaseSessionService")

    if settings.database_url:
        logger.info("Using DatabaseSessionService")
        return DatabaseSessionService(db_url=settings.database_url)

    logger.warning("Falling back to InMemorySessionService")
    return InMemorySessionService()
