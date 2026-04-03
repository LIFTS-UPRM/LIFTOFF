from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryMessage] = Field(default_factory=list)


class TrajectoryArtifactPoint(BaseModel):
    lat: float
    lon: float
    alt_m: float
    time_s: float | None = None


class TrajectoryArtifact(BaseModel):
    launch: TrajectoryArtifactPoint
    mean_trajectory: list[TrajectoryArtifactPoint] = Field(default_factory=list)
    mean_burst: TrajectoryArtifactPoint | None = None
    mean_landing: TrajectoryArtifactPoint | None = None
    landing_uncertainty_sigma_m: float = 0.0


class ChatResponse(BaseModel):
    response: str
    source: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    trajectory_artifact: TrajectoryArtifact | None = None
