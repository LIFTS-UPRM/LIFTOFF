from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]


class ChatResponse(BaseModel):
    response: str
    source: str
    tool_calls: list[ToolCallRecord] = []
