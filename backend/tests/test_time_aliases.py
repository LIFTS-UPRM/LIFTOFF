from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_servers import weather_server


def test_weather_normalise_dt_accepts_now(monkeypatch) -> None:
    fixed_now = datetime(2026, 5, 14, 16, 37, 22, tzinfo=timezone.utc)
    monkeypatch.setattr(weather_server, "_utcnow", lambda: fixed_now)

    assert weather_server._normalise_dt(" now ") == "2026-05-14T16:37"


def test_weather_nearest_forecast_index_uses_closest_grid_time() -> None:
    target = datetime(2026, 5, 14, 16, 37, 22, tzinfo=timezone.utc)
    times = [
        "2026-05-14T16:00",
        "2026-05-14T17:00",
        "2026-05-14T18:00",
    ]

    assert weather_server._nearest_forecast_index(times, target) == 1
