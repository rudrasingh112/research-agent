import json
import logging
import time
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)


def _log(level: str, agent: str, event: str, **extra: Any) -> None:
    record = {
        "severity": level.upper(),
        "agent": agent,
        "event": event,
        **extra,
    }
    logger.info(json.dumps(record))


async def before_agent_callback(callback_context: CallbackContext) -> None:
    agent_name = callback_context.agent_name
    callback_context.state[f"_timing:{agent_name}:start"] = time.time()
    _log("INFO", agent_name, "agent_start")


async def after_agent_callback(callback_context: CallbackContext) -> None:
    agent_name = callback_context.agent_name
    start = callback_context.state.get(f"_timing:{agent_name}:start", time.time())
    duration_ms = round((time.time() - start) * 1000)

    completed = callback_context.state.get("_completed_stages", [])
    if agent_name not in completed:
        completed.append(agent_name)
    callback_context.state["_completed_stages"] = completed

    _log("INFO", agent_name, "agent_complete", duration_ms=duration_ms)


async def before_model_callback(callback_context: CallbackContext, llm_request) -> None:
    _log("DEBUG", callback_context.agent_name, "model_call_start")
    return None


async def after_model_callback(callback_context: CallbackContext, llm_response) -> None:
    usage = getattr(llm_response, "usage_metadata", None)
    if usage:
        _log(
            "INFO", callback_context.agent_name, "model_call_complete",
            input_tokens=getattr(usage, "prompt_token_count", 0),
            output_tokens=getattr(usage, "candidates_token_count", 0),
        )
    return None


def before_tool_callback(tool, args: dict, tool_context: ToolContext) -> dict | None:
    tool_name = getattr(tool, "name", str(tool))
    _log("DEBUG", tool_context.agent_name, "tool_call_start", tool=tool_name)
    return None


def after_tool_callback(tool, args: dict, tool_context: ToolContext, tool_response) -> Any:
    tool_name = getattr(tool, "name", str(tool))
    _log("DEBUG", tool_context.agent_name, "tool_call_complete", tool=tool_name)
    return tool_response


async def save_report_artifact(callback_context: CallbackContext, report_markdown: str) -> str:
    import google.genai.types as genai_types

    report_bytes = report_markdown.encode("utf-8")
    artifact = genai_types.Part.from_bytes(
        data=report_bytes,
        mime_type="text/markdown",
    )
    filename = "report_latest.md"

    try:
        version = await callback_context.save_artifact(
            filename=filename,
            artifact=artifact,
        )
        callback_context.state["report_artifact"] = filename
        callback_context.state["report_artifact_version"] = version
        _log("INFO", callback_context.agent_name, "report_artifact_saved", filename=filename)
        return filename
    except Exception as exc:
        _log("ERROR", callback_context.agent_name, "report_artifact_save_failed", error=str(exc))
        raise