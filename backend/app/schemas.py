from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


McpToolGroupId = Literal["trajectory", "weather", "airspace"]

CHAT_MESSAGE_MAX_CHARS = 8_000
CHAT_HISTORY_MESSAGE_MAX_CHARS = 8_000
CHAT_HISTORY_MAX_ITEMS = 30
CHAT_PAYLOAD_MAX_BYTES = 512 * 1024
CHAT_PAYLOAD_MAX_DEPTH = 20


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    content: str = Field(max_length=CHAT_HISTORY_MESSAGE_MAX_CHARS)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str = Field(max_length=CHAT_MESSAGE_MAX_CHARS)
    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=CHAT_HISTORY_MAX_ITEMS,
    )
    enabled_tool_groups: list[McpToolGroupId] | None = None


class TrustedConversationState(BaseModel):
    """Server-owned prior tool activity reconstructed from observed execution."""

    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


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
