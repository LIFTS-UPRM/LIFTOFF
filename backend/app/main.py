from __future__ import annotations

import asyncio
import json
import logging
import time

from pydantic import ValidationError
from fastapi import FastAPI, HTTPException, Request, status

from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_current_user_id
from app.prompt_assembly import (
    format_client_history_message,
    format_current_user_message,
    format_tool_output_message,
)
from app.supabase_client import get_supabase
from app.usage_log import write_latest_chat_usage
from llm import OpenAIProvider, execute_tool
from app.config import get_settings
from app.logging import configure_logging
from app.schemas import (
    CHAT_HISTORY_MAX_ITEMS,
    CHAT_HISTORY_MESSAGE_MAX_CHARS,
    CHAT_MESSAGE_MAX_CHARS,
    CHAT_PAYLOAD_MAX_BYTES,
    CHAT_PAYLOAD_MAX_DEPTH,
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    McpToolGroupId,
    RuntimeRequest,
    RuntimeResponse,
    TrajectoryArtifact,
    ToolCallRecord,
    WriteResult,
)
from fastapi import Depends


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)
ALLOWED_HISTORY_ROLES = frozenset({"user", "assistant"})
TOOL_GROUP_INTENT_PATTERNS: dict[McpToolGroupId, tuple[str, ...]] = {
    "trajectory": (
        "ascent rate",
        "burst altitude",
        "descent rate",
        "landing area",
        "landing prediction",
        "monte carlo",
        "num runs",
        "run sondehub",
        "run a trajectory",
        "simulate",
        "simulation",
        "sondehub",
        "trajectory",
        "trajectory analysis",
        "trajectory simulation",
    ),
    "weather": (
        "cape",
        "cloud",
        "forecast",
        "gust",
        "launch conditions",
        "launch window",
        "precip",
        "rain",
        "surface wind",
        "weather",
        "wind",
        "winds aloft",
    ),
    "airspace": (
        "airspace",
        "aviation",
        "faa",
        "hazard",
        "no flight zone",
        "no-fly",
        "restricted",
        "restriction",
        "tfr",
    ),
}
TOOL_CONTINUATION_RESPONSES = frozenset(
    {
        "confirm",
        "confirmed",
        "correct",
        "do it",
        "go ahead",
        "looks good",
        "ok",
        "okay",
        "please proceed",
        "proceed",
        "run it",
        "that's correct",
        "yes",
        "y",
        "yeah",
        "yep",
    }
)
RUNTIME_RESPONSE_SOURCE = "stratos-runtime-orchestrator"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting %s in %s", settings.app_name, settings.app_env)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

async def _read_limited_body(request: Request) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = CHAT_PAYLOAD_MAX_BYTES + 1

        if declared_size > CHAT_PAYLOAD_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "Chat request payload is too large.",
                    "limit_bytes": CHAT_PAYLOAD_MAX_BYTES,
                },
            )

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > CHAT_PAYLOAD_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "Chat request payload is too large.",
                    "limit_bytes": CHAT_PAYLOAD_MAX_BYTES,
                },
            )

    return bytes(body)


def _within_json_depth(value: object) -> bool:
    stack = [(value, 1)]

    while stack:
        current, depth = stack.pop()
        if depth > CHAT_PAYLOAD_MAX_DEPTH:
            return False

        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)

    return True


def _validation_error_details(exc: ValidationError) -> list[dict]:
    try:
        return exc.errors(include_context=False)
    except TypeError:
        return exc.errors()


async def _parse_raw_payload(request: Request, label: str) -> dict:
    try:
        raw_body = await _read_limited_body(request)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": f"{label} payload is too large.",
                    "limit_bytes": CHAT_PAYLOAD_MAX_BYTES,
                },
            ) from exc
        raise

    try:
        raw_payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"{label} body must be valid JSON."},
        ) from exc
    except RecursionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"{label} JSON is too deeply nested."},
        ) from exc

    if not isinstance(raw_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": f"{label} body must be a JSON object."},
        )

    if not _within_json_depth(raw_payload):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": f"{label} JSON is too deeply nested.", "limit_depth": CHAT_PAYLOAD_MAX_DEPTH},
        )

    return raw_payload


async def _parse_chat_request(request: Request) -> ChatRequest:
    raw_payload = await _parse_raw_payload(request, "Chat request")
    try:
        return ChatRequest.model_validate(raw_payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Invalid chat request.",
                "details": _validation_error_details(exc),
            },
        ) from exc


async def _parse_runtime_request(request: Request) -> RuntimeRequest:
    raw_payload = await _parse_raw_payload(request, "Runtime request")
    try:
        return RuntimeRequest.model_validate(raw_payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Invalid runtime request.",
                "details": _validation_error_details(exc),
            },
        ) from exc


def _sanitize_history_message(message: ChatHistoryMessage) -> dict[str, str] | None:
    if message.role not in ALLOWED_HISTORY_ROLES:
        return None

    content = message.content.strip()
    if not content:
        return None

    return {"role": message.role, "content": content}


def _normalise_confirmation_text(message: str) -> str:
    return " ".join(message.casefold().strip().strip(".!").split())


def _is_tool_continuation_response(message: str) -> bool:
    return _normalise_confirmation_text(message) in TOOL_CONTINUATION_RESPONSES


def _select_relevant_tool_groups(
    message: str,
    enabled_tool_groups: list[McpToolGroupId] | None,
    context_messages: list[str] | None = None,
) -> list[McpToolGroupId]:
    """Return only enabled tool groups that are relevant to this chat turn."""
    allowed_groups = (
        tuple(TOOL_GROUP_INTENT_PATTERNS)
        if enabled_tool_groups is None
        else tuple(enabled_tool_groups)
    )
    intent_texts = [message]
    if context_messages and _is_tool_continuation_response(message):
        intent_texts.extend(context_messages[-6:])

    normalized = "\n".join(intent_texts).casefold()

    return [
        group_id
        for group_id in allowed_groups
        if any(
            marker in normalized
            for marker in TOOL_GROUP_INTENT_PATTERNS[group_id]
        )
    ]


def _llm_usage_to_dict(usage: object) -> dict[str, object] | None:
    if usage is None:
        return None

    if hasattr(usage, "model_dump"):
        return usage.model_dump(mode="json")

    usage_fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    usage_payload = {
        field: getattr(usage, field)
        for field in usage_fields
        if hasattr(usage, field)
    }
    return usage_payload or None


def _record_latest_chat_usage(
    *,
    payload: ChatRequest,
    response: ChatResponse,
    selected_tool_groups: list[McpToolGroupId],
    model: str | None,
    llm_steps: int,
    llm_usage: list[dict[str, object]],
    request_started_at: float,
    usage_source: str = "chat",
) -> ChatResponse:
    write_latest_chat_usage(
        {
            "usage_source": usage_source,
            "request": {
                "enabled_tool_groups": payload.enabled_tool_groups,
                "history_items": len(payload.history),
                "message": payload.message,
                "message_chars": len(payload.message),
                "selected_tool_groups": selected_tool_groups,
            },
            "result": {
                "elapsed_seconds": round(time.perf_counter() - request_started_at, 3),
                "has_trajectory_artifact": response.trajectory_artifact is not None,
                "llm_steps": llm_steps,
                "llm_usage": llm_usage,
                "model": model,
                "response": response.response,
                "response_chars": len(response.response),
                "source": response.source,
                "tool_call_count": len(response.tool_calls),
                "tool_calls": [
                    tool_call.model_dump(mode="json")
                    for tool_call in response.tool_calls
                ],
            },
        }
    )
    return response


def _upsert_session(user_id: str, session_id: str, mission_id: str) -> None:
    try:
        get_supabase().table("user_sessions").upsert(
            {
                "id": session_id,
                "user_id": user_id,
                "mission_id": mission_id,
                "last_active_at": "now()",
            },
            on_conflict="id",
        ).execute()
    except Exception:
        logger.warning("Failed to upsert user session %s", session_id, exc_info=True)


def _load_history(session_id: str) -> list[dict]:
    try:
        result = (
            get_supabase()
            .table("messages")
            .select("role,content")
            .eq("session_id", session_id)
            .order("created_at")
            .limit(CHAT_HISTORY_MAX_ITEMS)
            .execute()
        )
        return result.data or []
    except Exception:
        logger.warning("Failed to load history for session %s", session_id, exc_info=True)
        return []


def _save_messages(
    *,
    session_id: str,
    user_id: str,
    mission_id: str,
    user_content: str,
    assistant_content: str,
) -> None:
    try:
        get_supabase().table("messages").insert([
            {
                "session_id": session_id,
                "user_id": user_id,
                "mission_id": mission_id,
                "role": "user",
                "content": user_content,
            },
            {
                "session_id": session_id,
                "user_id": user_id,
                "mission_id": mission_id,
                "role": "assistant",
                "content": assistant_content,
            },
        ]).execute()
    except Exception:
        logger.warning("Failed to save messages for session %s", session_id, exc_info=True)


def _to_runtime_response(
    *,
    payload: RuntimeRequest,
    chat_response: ChatResponse,
) -> RuntimeResponse:
    return RuntimeResponse(
        response=chat_response.response,
        source=RUNTIME_RESPONSE_SOURCE,
        session_id=payload.session_id,
        mission_id=payload.mission_id,
        tool_calls=chat_response.tool_calls,
        trajectory_artifact=chat_response.trajectory_artifact,
        write_result=None,
    )


def _write_intent_validated_response(payload: RuntimeRequest) -> RuntimeResponse:
    write_result = WriteResult(
        operation=payload.write_intent.operation,  # type: ignore[union-attr]
        target_file=payload.write_intent.target_file,  # type: ignore[union-attr]
        summary=(
            "Validated structured write intent. No shared mission file was "
            "mutated because the v1 mission workspace writer is not implemented yet."
        ),
    )

    return RuntimeResponse(
        response=write_result.summary,
        source=RUNTIME_RESPONSE_SOURCE,
        session_id=payload.session_id,
        mission_id=payload.mission_id,
        tool_calls=[],
        trajectory_artifact=None,
        write_result=write_result,
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["message"],
                        "properties": {
                            "message": {
                                "type": "string",
                                "maxLength": CHAT_MESSAGE_MAX_CHARS,
                            },
                            "history": {
                                "type": "array",
                                "maxItems": CHAT_HISTORY_MAX_ITEMS,
                                "items": {
                                    "type": "object",
                                    "required": ["role", "content"],
                                    "properties": {
                                        "role": {
                                            "type": "string",
                                            "enum": ["user", "assistant"],
                                        },
                                        "content": {
                                            "type": "string",
                                            "maxLength": CHAT_HISTORY_MESSAGE_MAX_CHARS,
                                        },
                                    },
                                },
                            },
                            "enabled_tool_groups": {
                                "type": "array",
                                "nullable": True,
                                "items": {
                                    "type": "string",
                                    "enum": ["trajectory", "weather", "airspace"],
                                },
                            },
                        },
                    },
                    "example": {
                        "message": "hello",
                        "history": [],
                        "enabled_tool_groups": [],
                    },
                }
            },
        }
    },
)

async def chat(request: Request) -> ChatResponse:
    request_started_at = time.perf_counter()
    payload = await _parse_chat_request(request)
    return await _run_chat_completion(
        payload=payload,
        request_started_at=request_started_at,
    )


async def _run_chat_completion(
    *,
    payload: ChatRequest,
    request_started_at: float,
    usage_source: str = "chat",
) -> ChatResponse:
    logger.info("Received chat message (%d chars)", len(payload.message))

    tool_calls_log: list[ToolCallRecord] = []
    trajectory_artifact: TrajectoryArtifact | None = None
    enabled_tool_groups: list[McpToolGroupId] = []
    llm_steps = 0
    llm_usage: list[dict[str, object]] = []
    model: str | None = None
    try:
        provider = OpenAIProvider()
        client = provider.get_client()
        model = provider.get_model()

        messages: list[dict] = [{"role": "system", "content": provider.get_system_prompt()}]
        history_context: list[str] = []
        for history_message in payload.history:
            sanitized_message = _sanitize_history_message(history_message)
            if sanitized_message is not None:
                history_context.append(sanitized_message["content"])
                messages.append(format_client_history_message(**sanitized_message))

        messages.append(format_current_user_message(payload.message))
        enabled_tool_groups = _select_relevant_tool_groups(
            payload.message,
            payload.enabled_tool_groups,
            history_context,
        )
        logger.info(
            "Selected chat tool groups: %s",
            enabled_tool_groups or "none",
        )
        last_tool_name = "llm"
        max_steps = 10
        seen_calls: set[tuple[str, str]] = set()
        # Any future cross-request replay must come from server-owned
        # TrustedConversationState, never from client-supplied history.

        for step in range(max_steps):
            logger.info("LLM step %d", step + 1)

            completion_kwargs = {
                "model": model,
                "messages": messages,
            }
            enabled_tools = provider.get_tools(enabled_tool_groups)
            if enabled_tools:
                completion_kwargs["tools"] = enabled_tools
                completion_kwargs["tool_choice"] = "auto"

            llm_started_at = time.perf_counter()
            response = await client.chat.completions.create(**completion_kwargs)
            llm_steps = step + 1
            usage_payload = _llm_usage_to_dict(getattr(response, "usage", None))
            if usage_payload is not None:
                llm_usage.append({"step": step + 1, **usage_payload})
            logger.info(
                "LLM step %d latency %.3fs",
                step + 1,
                time.perf_counter() - llm_started_at,
            )

            assistant_message = response.choices[0].message

            logger.info("Assistant content: %s", assistant_message.content)
            logger.info("Assistant tool calls: %s", assistant_message.tool_calls)

            # If no tool calls, we are done
            if not assistant_message.tool_calls:
                final_text = assistant_message.content or "No response returned."
                source = "llm_with_tools" if last_tool_name != "llm" else "llm"
                logger.info(
                    "Chat completed in %.3fs (%d LLM step%s, %d tool call%s)",
                    time.perf_counter() - request_started_at,
                    step + 1,
                    "" if step == 0 else "s",
                    len(tool_calls_log),
                    "" if len(tool_calls_log) == 1 else "s",
                )
                return _record_latest_chat_usage(
                    payload=payload,
                    response=ChatResponse(
                        response=final_text,
                        source=source,
                        tool_calls=tool_calls_log,
                        trajectory_artifact=trajectory_artifact,
                    ),
                    selected_tool_groups=enabled_tool_groups,
                    model=model,
                    llm_steps=llm_steps,
                    llm_usage=llm_usage,
                    request_started_at=request_started_at,
                    usage_source=usage_source,
                )

            # Append assistant tool-call message
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in assistant_message.tool_calls
                    ],
                }
            )

            # Execute all requested tool calls
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                last_tool_name = tool_name
                try:
                    tool_args = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    logger.exception("Invalid JSON arguments for tool %s", tool_name)
                    return _record_latest_chat_usage(
                        payload=payload,
                        response=ChatResponse(
                            response=(
                                "Tool call failed: invalid JSON arguments "
                                f"for {tool_name}."
                            ),
                            source="tool_error",
                            tool_calls=tool_calls_log,
                            trajectory_artifact=trajectory_artifact,
                        ),
                        selected_tool_groups=enabled_tool_groups,
                        model=model,
                        llm_steps=llm_steps,
                        llm_usage=llm_usage,
                        request_started_at=request_started_at,
                        usage_source=usage_source,
                    )

                tool_key = (tool_name, json.dumps(tool_args, sort_keys=True))
                if tool_key in seen_calls:
                    logger.warning("Duplicate tool call detected: %s %s", tool_name, tool_args)

                    messages.append(
                        format_tool_output_message(
                            tool_call_id=tool_call.id,
                            tool_name=tool_name,
                            raw_result=json.dumps(
                                {
                                    "error": (
                                        "Duplicate tool call detected for "
                                        f"{tool_name}. Do not retry with the same arguments. "
                                        "Provide the final answer."
                                    )
                                }
                            ),
                        )
                    )
                    continue

                seen_calls.add(tool_key)
                tool_calls_log.append(ToolCallRecord(name=tool_name, args=tool_args))

                logger.info("Tool requested: %s", tool_name)
                logger.info("Tool args: %s", tool_args)
                
                try:
                    # Use longer timeout for simulation tools (up to 2 minutes)
                    timeout = (
                        120
                        if tool_name in {"sondehub_run_simulation", "get_balloon_no_flight_zone"}
                        else 30
                    )
                    tool_result = await asyncio.wait_for(
                        execute_tool(tool_name, tool_args),
                        timeout=timeout
                    )

                    # execute_tool returns a JSON string, so inspect it
                    try:
                        parsed_result = json.loads(tool_result)
                        if isinstance(parsed_result, dict) and parsed_result.get("error"):
                            logger.warning("Tool returned error payload: %s", tool_name)
                        if (
                            isinstance(parsed_result, dict)
                            and parsed_result.get("trajectory_artifact")
                        ):
                            try:
                                trajectory_artifact = TrajectoryArtifact.model_validate(
                                    parsed_result["trajectory_artifact"]
                                )
                            except Exception:
                                logger.exception(
                                    "Failed to parse trajectory artifact from %s",
                                    tool_name,
                                )
                    except json.JSONDecodeError:
                        # If it's not JSON, just leave it alone
                        parsed_result = None

                except asyncio.TimeoutError:
                    logger.warning("Tool execution timed out: %s", tool_name)
                    tool_result = json.dumps({"error": f"{tool_name} timed out after {timeout} seconds"})

                except Exception as e:
                    logger.exception("Tool execution failed: %s", tool_name)
                    tool_result = json.dumps({"error": f"{tool_name} failed: {str(e)}"})

                messages.append(
                    format_tool_output_message(
                        tool_call_id=tool_call.id,
                        tool_name=tool_name,
                        raw_result=tool_result,
                    )
                )

        return _record_latest_chat_usage(
            payload=payload,
            response=ChatResponse(
                response="Tool-calling loop reached the maximum number of steps.",
                source="tool_loop_limit",
                tool_calls=tool_calls_log,
                trajectory_artifact=trajectory_artifact,
            ),
            selected_tool_groups=enabled_tool_groups,
            model=model,
            llm_steps=llm_steps,
            llm_usage=llm_usage,
            request_started_at=request_started_at,
            usage_source=usage_source,
        )

    except Exception as e:
        logger.exception("Unhandled error in chat endpoint")
        return _record_latest_chat_usage(
            payload=payload,
            response=ChatResponse(
                response=f"Server error: {str(e)}",
                source="error",
                tool_calls=tool_calls_log,
                trajectory_artifact=trajectory_artifact,
            ),
            selected_tool_groups=enabled_tool_groups,
            model=model,
            llm_steps=llm_steps,
            llm_usage=llm_usage,
            request_started_at=request_started_at,
            usage_source=usage_source,
        )


@app.post(
    "/runtime/request",
    response_model=RuntimeResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "u_123",
                        "mission_id": "aero",
                        "session_id": "sess_abc123",
                        "operation": "chat",
                        "message": "What are the current pre-flight blockers?",
                        "write_intent": None,
                    }
                }
            },
        }
    },
)
async def runtime_request(
    request: Request,
    user_id: str = Depends(get_current_user_id),
) -> RuntimeResponse:
    request_started_at = time.perf_counter()
    payload = await _parse_runtime_request(request)

    logger.info(
        "Received runtime request operation=%s mission_id=%s session_id=%s user_id=%s",
        payload.operation,
        payload.mission_id,
        payload.session_id,
        user_id,
    )

    _upsert_session(user_id, payload.session_id, payload.mission_id)

    if payload.operation == "write_intent":
        return _write_intent_validated_response(payload)

    db_history = _load_history(payload.session_id)
    chat_history = [
        ChatHistoryMessage(role=m["role"], content=m["content"])
        for m in db_history
    ]

    chat_payload = ChatRequest(
        message=payload.message,
        history=chat_history,
        enabled_tool_groups=payload.enabled_tool_groups,
    )
    chat_response = await _run_chat_completion(
        payload=chat_payload,
        request_started_at=request_started_at,
        usage_source="runtime",
    )

    _save_messages(
        session_id=payload.session_id,
        user_id=user_id,
        mission_id=payload.mission_id,
        user_content=payload.message,
        assistant_content=chat_response.response,
    )

    return _to_runtime_response(
        payload=payload,
        chat_response=chat_response,
    )
