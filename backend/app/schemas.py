from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


<<<<<<< Updated upstream
class ChatResponse(BaseModel):
    response: str
    source: str
=======
class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]


class TrajectoryPoint(BaseModel):
    lat: float
    lng: float
    alt: float


class ChatResponse(BaseModel):
    response: str
    source: str
    tool_calls: list[ToolCallRecord] = []
    trajectory: list[TrajectoryPoint] | None = None
>>>>>>> Stashed changes
