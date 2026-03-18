"""
main.py

Three modes of operation:

  1. CLI / interactive  →  python main.py --brief "..."
  2. FastAPI server     →  python main.py --serve
  3. Agent Engine       →  adk deploy agent_engine picks up root_agent
                           from agents/pipeline.py automatically

For Agent Engine deployment, you don't need main.py at all — ADK's CLI finds
root_agent in the package. main.py is for local development and Cloud Run.
"""

import argparse
import asyncio
import json
import logging
import uuid

from google.adk.runners import Runner

from agents.pipeline import root_agent
from config.settings import settings
from services.artifacts import build_artifact_service
from services.session import build_session_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ── Core runner factory ────────────────────────────────────────────────────────

def build_runner() -> Runner:
    return Runner(
        agent=root_agent,
        app_name=settings.app_name,
        session_service=build_session_service(),
        artifact_service=build_artifact_service(),
    )


# ── Pipeline invocation ────────────────────────────────────────────────────────

async def run_pipeline(brief: str, user_id: str = "default_user") -> dict:
    """
    Submit a research brief and stream the pipeline to completion.

    Returns a dict with session_id, final_report, and artifact filename.
    Supports resuming a session by passing an existing session_id.
    """
    import google.genai.types as genai_types

    runner = build_runner()
    session_service = runner.session_service

    # Create a new durable session
    session = await session_service.create_session(
        app_name=settings.app_name,
        user_id=user_id,
    )
    session_id = session.id
    logger.info("Pipeline started | session_id=%s user_id=%s", session_id, user_id)

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=brief)],
    )

    # Stream events — each yield is an ADK Event
    final_report = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    final_report = part.text

    # Reload session to read final state (includes artifact filename)
    updated_session = await session_service.get_session(
        app_name=settings.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    state = updated_session.state if updated_session else {}

    return {
        "session_id": session_id,
        "pipeline_status": state.get("pipeline_status", "unknown"),
        "report_artifact": state.get("report_artifact"),
        "report_artifact_version": state.get("report_artifact_version"),
        "final_report_preview": (final_report or "")[:500],
    }


async def resume_pipeline(session_id: str, user_id: str = "default_user") -> dict:
    """
    Resume a pipeline that was interrupted mid-run.
    Rehydrates session state and picks up from the last completed stage.

    Useful for long-running jobs that survive Agent Engine restarts.
    """
    import google.genai.types as genai_types

    runner = build_runner()
    session_service = runner.session_service

    session = await session_service.get_session(
        app_name=settings.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    if not session:
        raise ValueError(f"Session {session_id} not found")

    completed = session.state.get("_completed_stages", [])
    logger.info(
        "Resuming session | session_id=%s completed_stages=%s",
        session_id, completed,
    )

    # Re-submit the last user message to continue from where we left off
    last_user_content = None
    for event in reversed(session.events):
        if event.author == "user" and event.content:
            last_user_content = event.content
            break

    if not last_user_content:
        raise ValueError("No user message found in session to resume from")

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=last_user_content,
    ):
        pass  # stream to completion

    updated_session = await session_service.get_session(
        app_name=settings.app_name,
        user_id=user_id,
        session_id=session_id,
    )
    return {
        "session_id": session_id,
        "pipeline_status": updated_session.state.get("pipeline_status"),
        "report_artifact": updated_session.state.get("report_artifact"),
    }


# ── FastAPI server (for Cloud Run deployment) ──────────────────────────────────

def build_fastapi_app():
    """
    Wraps the pipeline in a FastAPI server.
    Use this for Cloud Run deployment as an alternative to Agent Engine.
    """
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Research Pipeline", version="1.0.0")

    class BriefRequest(BaseModel):
        brief: str
        user_id: str = "default_user"

    class ResumeRequest(BaseModel):
        session_id: str
        user_id: str = "default_user"

    @app.post("/run")
    async def run_endpoint(req: BriefRequest):
        try:
            return await run_pipeline(req.brief, req.user_id)
        except Exception as exc:
            logger.exception("Pipeline error")
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/resume")
    async def resume_endpoint(req: ResumeRequest):
        try:
            return await resume_pipeline(req.session_id, req.user_id)
        except Exception as exc:
            logger.exception("Resume error")
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": settings.app_name, "env": settings.env}

    return app


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research Pipeline Runner")
    parser.add_argument("--brief", type=str, help="Research brief text")
    parser.add_argument("--resume", type=str, help="Resume a session by ID")
    parser.add_argument("--user-id", type=str, default="cli_user")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI server")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if args.serve:
        import uvicorn
        app = build_fastapi_app()
        uvicorn.run(app, host="0.0.0.0", port=args.port)

    elif args.resume:
        result = asyncio.run(resume_pipeline(args.resume, args.user_id))
        print(json.dumps(result, indent=2))

    elif args.brief:
        result = asyncio.run(run_pipeline(args.brief, args.user_id))
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()