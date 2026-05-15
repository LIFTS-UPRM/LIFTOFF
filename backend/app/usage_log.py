from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)
DEFAULT_LATEST_CHAT_USAGE_PATH = (
    Path(__file__).resolve().parents[1] / "logs" / "latest_chat_usage.json"
)


def _latest_chat_usage_path() -> Path:
    configured_path = os.getenv("CHAT_USAGE_LOG_PATH", "").strip()
    if configured_path:
        return Path(configured_path).expanduser()

    return DEFAULT_LATEST_CHAT_USAGE_PATH


def write_latest_chat_usage(record: dict[str, Any]) -> None:
    """Overwrite the local latest-chat usage artifact without breaking chat."""
    path: Path | None = None
    try:
        path = _latest_chat_usage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat().replace(
                "+00:00",
                "Z",
            ),
            **record,
        }

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temp_path = Path(temp_name)

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                json.dump(payload, temp_file, indent=2, sort_keys=True, default=str)
                temp_file.write("\n")

            temp_path.replace(path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
    except Exception:
        logger.warning("Failed to write latest chat usage log: %s", path, exc_info=True)
