from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.schemas import CHAT_PAYLOAD_MAX_BYTES, CHAT_PAYLOAD_MAX_DEPTH


def make_message(content: str) -> SimpleNamespace:
    return SimpleNamespace(content=content, tool_calls=None)


class FakeCompletions:
    def __init__(self, responses: list[SimpleNamespace] | None = None) -> None:
        self.last_kwargs: dict | None = None
        self.calls: list[dict] = []
        self.responses = responses or [make_message("Runtime chat response.")]

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self.responses.pop(0))],
            usage=None,
        )


class FakeProvider:
    completions = FakeCompletions()

    def __init__(self) -> None:
        self._client = SimpleNamespace(
            chat=SimpleNamespace(completions=self.completions),
        )

    def get_client(self):
        return self._client

    def get_model(self) -> str:
        return "test-model"

    def get_tools(self, enabled_tool_groups=None):
        from llm import get_tools

        return get_tools(enabled_tool_groups)

    def get_system_prompt(self) -> str:
        return "Test prompt"


def runtime_chat_payload(**overrides):
    payload = {
        "user_id": "u_123",
        "mission_id": "aero",
        "session_id": "sess_abc123",
        "operation": "chat",
        "message": "Summarize the current weather concerns.",
        "write_intent": None,
    }
    payload.update(overrides)
    return payload


def test_runtime_chat_returns_mission_runtime_metadata(monkeypatch) -> None:
    FakeProvider.completions = FakeCompletions()
    monkeypatch.setattr("app.main.OpenAIProvider", FakeProvider)

    response = TestClient(app).post(
        "/runtime/request",
        json=runtime_chat_payload(enabled_tool_groups=["weather"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "response": "Runtime chat response.",
        "source": "stratos-runtime-orchestrator",
        "session_id": "sess_abc123",
        "mission_id": "aero",
        "tool_calls": [],
        "trajectory_artifact": None,
        "write_result": None,
    }
    assert FakeProvider.completions.last_kwargs is not None
    assert FakeProvider.completions.last_kwargs["messages"] == [
        {"role": "system", "content": "Test prompt"},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "content": "Summarize the current weather concerns.",
                    "kind": "user_input",
                    "source": "current_user",
                    "trust": "untrusted",
                }
            ),
        },
    ]
    tool_names = [
        tool["function"]["name"]
        for tool in FakeProvider.completions.last_kwargs["tools"]
    ]
    assert tool_names == ["get_surface_weather", "get_winds_aloft"]


def test_runtime_request_rejects_missing_identity_fields() -> None:
    for field in ("user_id", "mission_id", "session_id", "operation", "message"):
        payload = runtime_chat_payload()
        payload.pop(field)

        response = TestClient(app).post("/runtime/request", json=payload)

        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "Invalid runtime request."


def test_runtime_request_rejects_invalid_operation() -> None:
    response = TestClient(app).post(
        "/runtime/request",
        json=runtime_chat_payload(operation="delete_mission"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "Invalid runtime request."


def test_runtime_chat_rejects_client_history() -> None:
    response = TestClient(app).post(
        "/runtime/request",
        json=runtime_chat_payload(
            history=[{"role": "user", "content": "trusted mission state"}],
        ),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "Invalid runtime request."


def test_runtime_write_intent_validates_without_mutating() -> None:
    response = TestClient(app).post(
        "/runtime/request",
        json={
            "user_id": "u_123",
            "mission_id": "aero",
            "session_id": "sess_abc123",
            "operation": "write_intent",
            "message": "Mark payload power verification complete.",
            "write_intent": {
                "operation": "checklist_item_set_status",
                "mission_id": "aero",
                "target_file": "missions/aero/checklists/preflight.md",
                "item_id": "payload-power-verification",
                "new_status": "done",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "stratos-runtime-orchestrator"
    assert body["session_id"] == "sess_abc123"
    assert body["mission_id"] == "aero"
    assert body["tool_calls"] == []
    assert body["trajectory_artifact"] is None
    assert body["write_result"] == {
        "status": "validated",
        "operation": "checklist_item_set_status",
        "target_file": "missions/aero/checklists/preflight.md",
        "summary": (
            "Validated structured write intent. No shared mission file was "
            "mutated because the v1 mission workspace writer is not implemented yet."
        ),
    }


def test_runtime_write_intent_rejects_invalid_operation() -> None:
    payload = {
        "user_id": "u_123",
        "mission_id": "aero",
        "session_id": "sess_abc123",
        "operation": "write_intent",
        "message": "Rewrite the whole mission.",
        "write_intent": {
            "operation": "rewrite_mission",
            "target_file": "missions/aero/mission.md",
        },
    }

    response = TestClient(app).post("/runtime/request", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "Invalid runtime request."


def test_runtime_write_intent_rejects_cross_mission_and_traversal_paths() -> None:
    invalid_intents = [
        {
            "operation": "append_planning_note",
            "mission_id": "other",
            "target_file": "missions/aero/planning/weather-notes.md",
        },
        {
            "operation": "append_planning_note",
            "target_file": "missions/other/planning/weather-notes.md",
        },
        {
            "operation": "append_planning_note",
            "target_file": "missions/aero/../other/notes.md",
        },
        {
            "operation": "append_planning_note",
            "target_file": "/missions/aero/planning/weather-notes.md",
        },
    ]

    for write_intent in invalid_intents:
        response = TestClient(app).post(
            "/runtime/request",
            json={
                "user_id": "u_123",
                "mission_id": "aero",
                "session_id": "sess_abc123",
                "operation": "write_intent",
                "message": "Add a note.",
                "write_intent": write_intent,
            },
        )

        assert response.status_code == 422
        assert response.json()["detail"]["error"] == "Invalid runtime request."


def test_runtime_request_reuses_serialized_payload_limit() -> None:
    body = json.dumps(runtime_chat_payload(message="x" * CHAT_PAYLOAD_MAX_BYTES))

    response = TestClient(app).post(
        "/runtime/request",
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413


def test_runtime_request_reuses_json_depth_limit() -> None:
    nested = "x"
    for _ in range(CHAT_PAYLOAD_MAX_DEPTH + 1):
        nested = [nested]

    response = TestClient(app).post(
        "/runtime/request",
        json=runtime_chat_payload(metadata=nested),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "Runtime request JSON is too deeply nested."
