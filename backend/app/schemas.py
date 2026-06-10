from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


McpToolGroupId = Literal["trajectory", "weather", "airspace"]
RuntimeOperation = Literal["chat", "write_intent"]
WriteIntentOperation = Literal[
    "checklist_item_set_status",
    "append_planning_note",
    "append_decision_entry",
    "update_status_summary",
]

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


class WriteIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: WriteIntentOperation
    target_file: str = Field(min_length=1)
    mission_id: str | None = None
    item_id: str | None = None
    new_status: str | None = None
    entry: dict[str, Any] | None = None
    summary: str | None = None

    @field_validator("mission_id", "target_file", "item_id", "new_status", "summary")
    @classmethod
    def _strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class RuntimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    operation: RuntimeOperation
    message: str = Field(max_length=CHAT_MESSAGE_MAX_CHARS)
    write_intent: WriteIntent | None = None
    enabled_tool_groups: list[McpToolGroupId] | None = None

    @field_validator("user_id", "mission_id", "session_id", "message")
    @classmethod
    def _strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped

    @model_validator(mode="after")
    def _validate_operation_contract(self) -> "RuntimeRequest":
        if self.operation == "chat" and self.write_intent is not None:
            raise ValueError("Chat requests must not include write_intent.")

        if self.operation == "write_intent" and self.write_intent is None:
            raise ValueError("write_intent operation requires write_intent.")

        if self.write_intent is not None:
            if (
                self.write_intent.mission_id is not None
                and self.write_intent.mission_id != self.mission_id
            ):
                raise ValueError("write_intent.mission_id must match mission_id.")

            target_path = PurePosixPath(self.write_intent.target_file)
            if target_path.is_absolute() or ".." in target_path.parts:
                raise ValueError("write_intent.target_file must stay inside mission files.")

            if (
                len(target_path.parts) < 3
                or target_path.parts[0] != "missions"
                or target_path.parts[1] != self.mission_id
            ):
                raise ValueError(
                    "write_intent.target_file must be under missions/{mission_id}/."
                )

        return self


class TrustedConversationState(BaseModel):
    """Server-owned prior tool activity reconstructed from observed execution."""

    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class RuntimeSharedContext(BaseModel):
    """Server-owned mission context envelope placeholder for runtime calls."""

    core_documents: list[str] = Field(default_factory=list)
    intent_documents: list[str] = Field(default_factory=list)


class RuntimeRequestContext(BaseModel):
    user_id: str
    mission_id: str
    session_id: str
    operation: RuntimeOperation
    message: str
    write_intent: WriteIntent | None = None
    shared_context: RuntimeSharedContext = Field(default_factory=RuntimeSharedContext)


class TrajectoryArtifactPoint(BaseModel):
    lat: float
    lon: float
    alt_m: float
    time_s: float | None = None


class SondehubRequestSummary(BaseModel):
    profile: str | None = None
    launch_latitude: float | None = None
    launch_longitude: float | None = None
    launch_altitude: float | None = None
    launch_datetime: str | None = None
    ascent_rate: float | None = None
    burst_altitude: float | None = None
    descent_rate: float | None = None


class SondehubTrajectoryReference(BaseModel):
    provider: Literal["sondehub-tawhiri"] = "sondehub-tawhiri"
    status: str
    request: SondehubRequestSummary | None = None
    trajectory: list[TrajectoryArtifactPoint] = Field(default_factory=list)
    burst: TrajectoryArtifactPoint | None = None
    landing: TrajectoryArtifactPoint | None = None


class TrajectoryArtifact(BaseModel):
    launch: TrajectoryArtifactPoint
    mean_trajectory: list[TrajectoryArtifactPoint] = Field(default_factory=list)
    mean_burst: TrajectoryArtifactPoint | None = None
    mean_landing: TrajectoryArtifactPoint | None = None
    landing_uncertainty_sigma_m: float = 0.0
    sondehub_reference: SondehubTrajectoryReference | None = None
    restriction_overlay: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    response: str
    source: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    trajectory_artifact: TrajectoryArtifact | None = None


class WriteResult(BaseModel):
    status: Literal["validated"] = "validated"
    operation: WriteIntentOperation
    target_file: str
    summary: str


class RuntimeResponse(BaseModel):
    response: str
    source: str
    session_id: str
    mission_id: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    trajectory_artifact: TrajectoryArtifact | None = None
    write_result: WriteResult | None = None
