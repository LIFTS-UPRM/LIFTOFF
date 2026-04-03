"""LLM provider abstraction — OpenAI implementation.

Exports:
  ALL_TOOLS         — merged OpenAI function-calling tool schema list
  SYSTEM_PROMPT     — Agent system prompt
  execute_tool(name, input) — dispatches to all MCP tool functions
  LLMProvider       — abstract base class
  OpenAIProvider    — OpenAI implementation
"""
from __future__ import annotations

import abc
import json
from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings

# ── Tool schemas ──────────────────────────────────────────────────────────────

WEATHER_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_surface_weather",
            "description": (
                "Fetch surface weather conditions and GO/CAUTION/NO-GO launch assessment "
                "for a site. Returns hourly conditions for the forecast window: wind speed, "
                "gusts, cloud cover, precipitation probability, CAPE, visibility. "
                "Always call this before recommending a launch window."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude":       {"type": "number",  "description": "Launch site latitude (-90 to 90)"},
                    "longitude":      {"type": "number",  "description": "Launch site longitude (-180 to 180)"},
                    "forecast_hours": {"type": "integer", "description": "Hours ahead to forecast (1-72)", "default": 24},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_winds_aloft",
            "description": (
                "Fetch winds aloft profile at 9 pressure levels (1000-200 hPa) for a "
                "launch site at a specific forecast time. Returns u/v components, wind "
                "speed/direction, altitude mapping, and jet stream alerts (>40 m/s). "
                "Use when upper-level wind patterns affect trajectory planning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude":          {"type": "number", "description": "Launch site latitude"},
                    "longitude":         {"type": "number", "description": "Launch site longitude"},
                    "forecast_datetime": {
                        "type": "string",
                        "description": "ISO 8601 datetime for the forecast (e.g. '2026-03-15T12:00:00Z')",
                    },
                },
                "required": ["latitude", "longitude", "forecast_datetime"],
            },
        },
    },
]

NOTAM_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "check_notam_airspace",
            "description": (
                "Check NOTAMs for balloon launch airspace using FAA + AviationWeather.gov. "
                "Returns relevant NOTAMs and clearance status: NO_CRITICAL_ALERTS, "
                "REVIEW_REQUIRED, or MANUAL_CHECK_REQUIRED. "
                "Call this when the user asks about airspace safety or launch clearance."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude":        {"type": "number", "description": "Launch site latitude"},
                    "longitude":       {"type": "number", "description": "Launch site longitude"},
                    "radius_km":       {"type": "number", "description": "Search radius in km (default 25)", "default": 25},
                    "launch_datetime": {"type": "string", "description": "ISO 8601 launch datetime"},
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
]

ASTRA_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "astra_list_balloons",
            "description": (
                "List the balloon models supported by the vendored ASTRA simulator. "
                "Use this before selecting a balloon for ASTRA calculations or simulations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "description": "Preferred output format. Use json for structured consumption.",
                        "default": "json",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "astra_list_parachutes",
            "description": (
                "List the parachute models supported by the vendored ASTRA simulator. "
                "Use this before choosing descent hardware for a simulation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "response_format": {
                        "type": "string",
                        "enum": ["json", "markdown"],
                        "description": "Preferred output format. Use json for structured consumption.",
                        "default": "json",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "astra_calculate_nozzle_lift",
            "description": (
                "Calculate the nozzle lift needed to reach a target ascent rate for a "
                "specific ASTRA balloon model, payload weight, and gas type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "balloon_model": {
                        "type": "string",
                        "description": "ASTRA balloon model ID, such as TA800 or HW1000.",
                    },
                    "gas_type": {
                        "type": "string",
                        "enum": ["Helium", "Hydrogen"],
                        "description": "Lifting gas type.",
                    },
                    "payload_weight_kg": {
                        "type": "number",
                        "description": "Total payload train weight in kilograms.",
                    },
                    "ascent_rate_ms": {
                        "type": "number",
                        "description": "Target ascent rate in metres per second.",
                        "default": 5.0,
                    },
                },
                "required": ["balloon_model", "gas_type", "payload_weight_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "astra_calculate_balloon_volume",
            "description": (
                "Calculate gas mass, fill volume, balloon diameter, and free lift for a "
                "specific ASTRA balloon model and nozzle lift."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "balloon_model": {
                        "type": "string",
                        "description": "ASTRA balloon model ID, such as TA800 or HW1000.",
                    },
                    "gas_type": {
                        "type": "string",
                        "enum": ["Helium", "Hydrogen"],
                        "description": "Lifting gas type.",
                    },
                    "nozzle_lift_kg": {
                        "type": "number",
                        "description": "Target nozzle lift in kilograms.",
                    },
                    "payload_weight_kg": {
                        "type": "number",
                        "description": "Total payload train weight in kilograms.",
                    },
                },
                "required": [
                    "balloon_model",
                    "gas_type",
                    "nozzle_lift_kg",
                    "payload_weight_kg",
                ],
            },
        },
    },
]

HAB_PREDICTOR_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "hab_list_hardware",
            "description": (
                "Return the full HAB_Predictor hardware catalog: all balloon models, "
                "parachute models, and supported gas types. "
                "Use as a combined alternative to astra_list_balloons + astra_list_parachutes."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hab_get_elevation",
            "description": (
                "Look up terrain elevation (metres above sea level) at a given lat/lon "
                "using OpenTopoData. Use when the launch site elevation is unknown."
            ),
            "parameters": {
                "type": "object",
                "properties": {
<<<<<<< Updated upstream
                    "launch_lat": {"type": "number", "description": "Launch site latitude in decimal degrees."},
                    "launch_lon": {"type": "number", "description": "Launch site longitude in decimal degrees."},
                    "launch_elevation_m": {
                        "type": "number",
                        "description": "Launch site elevation above mean sea level in metres.",
                    },
                    "launch_datetime": {
                        "type": "string",
                        "description": "Launch time in ISO 8601 format.",
                    },
                    "balloon_model": {
                        "type": "string",
                        "description": "ASTRA balloon model ID.",
                    },
=======
                    "lat": {"type": "number", "description": "Latitude in decimal degrees."},
                    "lon": {"type": "number", "description": "Longitude in decimal degrees."},
                },
                "required": ["lat", "lon"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hab_calculate_nozzle_lift",
            "description": (
                "Calculate the nozzle lift (kg) needed to reach a target ascent rate "
                "for a specific balloon model, payload, and gas type via HAB_Predictor."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "balloon_model": {"type": "string", "description": "Balloon model ID."},
>>>>>>> Stashed changes
                    "gas_type": {
                        "type": "string",
                        "enum": ["Helium", "Hydrogen"],
                        "description": "Lifting gas type.",
                    },
                    "payload_weight_kg": {"type": "number", "description": "Payload weight in kg."},
                    "ascent_rate_ms": {
                        "type": "number",
                        "description": "Target ascent rate in m/s.",
                        "default": 5.0,
                    },
                },
                "required": ["balloon_model", "gas_type", "payload_weight_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hab_calculate_balloon_volume",
            "description": (
                "Calculate gas fill volume, gas mass, balloon diameter, and free lift "
                "via HAB_Predictor."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "balloon_model": {"type": "string", "description": "Balloon model ID."},
                    "gas_type": {
                        "type": "string",
                        "enum": ["Helium", "Hydrogen"],
                        "description": "Lifting gas type.",
                    },
                    "nozzle_lift_kg": {"type": "number", "description": "Target nozzle lift in kg."},
                    "payload_weight_kg": {"type": "number", "description": "Payload weight in kg."},
                },
                "required": ["balloon_model", "gas_type", "nozzle_lift_kg", "payload_weight_kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hab_run_simulation",
            "description": (
                "Run a HAB_Predictor Monte Carlo balloon trajectory simulation using NOAA GFS data. "
                "Returns per-run summaries, aggregate stats, a sampled trajectory path, and optional "
                "SondeHub calibration. Prefer this over astra_run_simulation when SondeHub "
                "calibration or richer trajectory output is needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "launch_lat": {"type": "number", "description": "Launch latitude in decimal degrees."},
                    "launch_lon": {"type": "number", "description": "Launch longitude in decimal degrees."},
                    "launch_datetime": {
                        "type": "string",
                        "description": "Launch time in ISO 8601 format.",
                    },
                    "balloon_model": {"type": "string", "description": "Balloon model ID."},
                    "gas_type": {
                        "type": "string",
                        "enum": ["Helium", "Hydrogen"],
                        "description": "Lifting gas type.",
                    },
                    "nozzle_lift_kg": {"type": "number", "description": "Nozzle lift in kg."},
                    "payload_weight_kg": {"type": "number", "description": "Payload weight in kg."},
                    "launch_elevation_m": {
                        "type": "number",
                        "description": "Launch elevation in metres (optional; auto-looked-up if omitted).",
                    },
                    "parachute_model": {"type": "string", "description": "Optional parachute model ID."},
                    "num_runs": {
                        "type": "integer",
                        "description": "Number of Monte Carlo runs (1-20).",
                        "default": 5,
                    },
                    "floating_flight": {"type": "boolean", "default": False},
                    "floating_altitude_m": {
                        "type": "number",
                        "description": "Target float altitude in metres.",
                    },
                    "cutdown": {"type": "boolean", "default": False},
                    "cutdown_altitude_m": {
                        "type": "number",
                        "description": "Cutdown trigger altitude in metres.",
                    },
                    "force_low_res": {
                        "type": "boolean",
                        "default": False,
                        "description": "Use lower-resolution GFS for faster simulations.",
                    },
                    "compare_with_sondehub": {
                        "type": "boolean",
                        "default": False,
                        "description": "Fetch SondeHub independent prediction for comparison.",
                    },
                    "adjust_with_sondehub": {
                        "type": "boolean",
                        "default": False,
                        "description": "Apply SondeHub-based calibration to the trajectory.",
                    },
                    "sondehub_adjustment_weight": {
                        "type": "number",
                        "default": 0.5,
                        "description": "Weight (0-1) for SondeHub calibration blend.",
                    },
                },
                "required": [
                    "launch_lat",
                    "launch_lon",
                    "launch_datetime",
                    "balloon_model",
                    "gas_type",
                    "nozzle_lift_kg",
                    "payload_weight_kg",
                ],
            },
        },
    },
]

<<<<<<< Updated upstream
ALL_TOOLS = WEATHER_TOOLS + NOTAM_TOOLS + ASTRA_TOOLS
=======
ALL_TOOLS = WEATHER_TOOLS + AIRSPACE_TOOLS + ASTRA_TOOLS + HAB_PREDICTOR_TOOLS
>>>>>>> Stashed changes


def get_tools() -> list[dict]:
    """Return the full list of tool schemas."""
    return ALL_TOOLS

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are LIFTOFF Agent, an AI mission planning assistant for weather balloon operations.

When a user asks about a launch location or conditions, use your tools to retrieve data \
and return a clear, structured mission brief.

Guidelines:
- Always call get_surface_weather before recommending a launch window.
- Call get_winds_aloft when the user needs upper-level wind patterns outside of an ASTRA simulation.
- Call check_notam_airspace when the user asks about airspace clearance or launch safety.
- Call astra_list_balloons and astra_list_parachutes when hardware selection is unclear.
- Call astra_calculate_nozzle_lift before astra_run_simulation when the user gives a target ascent rate but not a nozzle lift.
- Call hab_run_simulation to compute landing prediction and uncertainty; it pulls NOAA GFS data itself, so do not call get_winds_aloft first unless the user separately wants the wind profile.
- Lead with the overall GO / CAUTION / NO-GO recommendation.
- Explicitly name threshold violations (e.g., "Surface wind 8.2 m/s exceeds the 7.0 m/s CAUTION threshold").
- Report NOTAM clearance_status clearly; MANUAL_CHECK_REQUIRED always requires human review.
- Include observation_links when available from tool results.
- Be concise. Use short paragraphs and bullet points.
- Use hab_get_elevation when the launch site elevation is unknown before running a simulation.
- Use hab_list_hardware as a combined alternative to calling astra_list_balloons and astra_list_parachutes separately.
"""

# ── Tool dispatcher ───────────────────────────────────────────────────────────

async def execute_tool(name: str, tool_input: dict) -> str:
<<<<<<< Updated upstream
    """Execute any named tool and return a JSON string result."""
    from mcp_servers.astra_server import (
        astra_calculate_balloon_volume,
        astra_calculate_nozzle_lift,
        astra_list_balloons,
        astra_list_parachutes,
        astra_run_simulation,
    )
    from mcp_servers.notam_server import check_notam_airspace
    from mcp_servers.weather_server import get_surface_weather, get_winds_aloft

    def _normalize_tool_result(tool_name: str, raw_result: Any) -> dict | list | str | int | float | bool | None:
        if isinstance(raw_result, str):
            if raw_result.startswith("Error"):
                return {
                    "status": "error",
                    "tool": tool_name,
                    "message": raw_result,
                }

            try:
                return json.loads(raw_result)
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "tool": tool_name,
                    "message": f"Tool returned non-JSON output: {raw_result}",
                }

        return raw_result

=======
    """Execute any named tool and return a JSON string result.

    Each import is scoped to its branch so a failure in one server (e.g. a
    missing vendored dependency) cannot prevent other servers from loading.
    """
>>>>>>> Stashed changes
    if name == "get_surface_weather":
        from mcp_servers.weather_server import get_surface_weather
        result = await get_surface_weather(**tool_input)

    elif name == "get_winds_aloft":
        from mcp_servers.weather_server import get_winds_aloft
        result = await get_winds_aloft(**tool_input)

<<<<<<< Updated upstream
    elif name == "check_notam_airspace":
        s = get_settings()
        result = await check_notam_airspace(
            **tool_input,
            faa_client_id=s.faa_client_id,
            faa_client_secret=s.faa_client_secret,
        )
=======
    elif name == "check_airspace_hazards":
        from mcp_servers.notam_server import check_airspace_hazards
        result = await check_airspace_hazards(**tool_input)
>>>>>>> Stashed changes

    elif name == "astra_list_balloons":
        from mcp_servers.astra_server import astra_list_balloons
        result = await astra_list_balloons(**tool_input)

    elif name == "astra_list_parachutes":
        from mcp_servers.astra_server import astra_list_parachutes
        result = await astra_list_parachutes(**tool_input)

    elif name == "astra_calculate_nozzle_lift":
        from mcp_servers.astra_server import astra_calculate_nozzle_lift
        result = await astra_calculate_nozzle_lift(**tool_input)

    elif name == "astra_calculate_balloon_volume":
        from mcp_servers.astra_server import astra_calculate_balloon_volume
        result = await astra_calculate_balloon_volume(**tool_input)

    elif name == "hab_list_hardware":
        from mcp_servers.hab_predictor_server import hab_list_hardware
        result = await hab_list_hardware()

    elif name == "hab_get_elevation":
        from mcp_servers.hab_predictor_server import hab_get_elevation
        result = await hab_get_elevation(**tool_input)

    elif name == "hab_calculate_nozzle_lift":
        from mcp_servers.hab_predictor_server import hab_calculate_nozzle_lift
        result = await hab_calculate_nozzle_lift(**tool_input)

    elif name == "hab_calculate_balloon_volume":
        from mcp_servers.hab_predictor_server import hab_calculate_balloon_volume
        result = await hab_calculate_balloon_volume(**tool_input)

    elif name == "hab_run_simulation":
        from mcp_servers.hab_predictor_server import hab_run_simulation
        result = await hab_run_simulation(**tool_input)

    else:
        result = {
            "status": "error",
            "tool": name,
            "message": f"Unknown tool: {name}",
        }

    return json.dumps(_normalize_tool_result(name, result))


# ── Provider abstraction ──────────────────────────────────────────────────────

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def get_client(self) -> Any: ...

    @abc.abstractmethod
    def get_model(self) -> str: ...

    @abc.abstractmethod
    def get_tools(self) -> list[dict]: ...

    @abc.abstractmethod
    def get_system_prompt(self) -> str: ...


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        s = get_settings()
        self._client = AsyncOpenAI(api_key=s.llm_api_key)
        self._model  = s.llm_model

    def get_client(self) -> AsyncOpenAI:
        return self._client

    def get_model(self) -> str:
        return self._model

    def get_tools(self) -> list[dict]:
        return ALL_TOOLS

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT
