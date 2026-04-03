"""HAB_Predictor MCP server — wraps the LIFTS-UPRM HAB_Predictor Flask API.

Can be run as a standalone MCP server:
    python -m mcp_servers.hab_predictor_server
"""
from __future__ import annotations

import json

import httpx
from fastmcp import FastMCP

from app.config import get_settings

mcp = FastMCP("liftoff-hab-predictor")


def _base_url() -> str:
    return get_settings().hab_predictor_url.rstrip("/")


async def hab_list_hardware() -> str:
    """Return the hardware catalog: all balloon models, parachute models, and gas types."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{_base_url()}/api/hardware")
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        return json.dumps({"status": "error", "tool": "hab_list_hardware", "message": str(exc)})


async def hab_get_elevation(lat: float, lon: float) -> str:
    """Look up terrain elevation at a launch site coordinate."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{_base_url()}/api/elevation", params={"lat": lat, "lon": lon}
            )
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        return json.dumps({"status": "error", "tool": "hab_get_elevation", "message": str(exc)})


async def hab_calculate_nozzle_lift(
    balloon_model: str,
    gas_type: str,
    payload_weight_kg: float,
    ascent_rate_ms: float = 5.0,
) -> str:
    """Calculate required nozzle lift for a given ascent rate."""
    payload = {
        "balloon_model": balloon_model,
        "gas_type": gas_type,
        "payload_weight_kg": payload_weight_kg,
        "ascent_rate_ms": ascent_rate_ms,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{_base_url()}/api/nozzle-lift", json=payload)
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        return json.dumps({"status": "error", "tool": "hab_calculate_nozzle_lift", "message": str(exc)})


async def hab_calculate_balloon_volume(
    balloon_model: str,
    gas_type: str,
    nozzle_lift_kg: float,
    payload_weight_kg: float,
) -> str:
    """Calculate gas fill volume, gas mass, and free lift."""
    payload = {
        "balloon_model": balloon_model,
        "gas_type": gas_type,
        "nozzle_lift_kg": nozzle_lift_kg,
        "payload_weight_kg": payload_weight_kg,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{_base_url()}/api/balloon-volume", json=payload)
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        return json.dumps({"status": "error", "tool": "hab_calculate_balloon_volume", "message": str(exc)})


async def hab_run_simulation(
    launch_lat: float,
    launch_lon: float,
    launch_datetime: str,
    balloon_model: str,
    gas_type: str,
    nozzle_lift_kg: float,
    payload_weight_kg: float,
    launch_elevation_m: float | None = None,
    parachute_model: str | None = None,
    num_runs: int = 5,
    floating_flight: bool = False,
    floating_altitude_m: float | None = None,
    cutdown: bool = False,
    cutdown_altitude_m: float | None = None,
    force_low_res: bool = False,
    compare_with_sondehub: bool = False,
    adjust_with_sondehub: bool = False,
    sondehub_adjustment_weight: float = 0.5,
) -> str:
    """Run a HAB_Predictor Monte Carlo balloon trajectory simulation.

    Returns per-run summaries, aggregate stats, trajectory path, and optional
    SondeHub calibration.
    """
    body: dict = {
        "launch_lat": launch_lat,
        "launch_lon": launch_lon,
        "launch_datetime": launch_datetime,
        "balloon_model": balloon_model,
        "gas_type": gas_type,
        "nozzle_lift_kg": nozzle_lift_kg,
        "payload_weight_kg": payload_weight_kg,
        "num_runs": num_runs,
        "floating_flight": floating_flight,
        "cutdown": cutdown,
        "force_low_res": force_low_res,
        "compare_with_sondehub": compare_with_sondehub,
        "adjust_with_sondehub": adjust_with_sondehub,
        "sondehub_adjustment_weight": sondehub_adjustment_weight,
    }
    if launch_elevation_m is not None:
        body["launch_elevation_m"] = launch_elevation_m
    if parachute_model is not None:
        body["parachute_model"] = parachute_model
    if floating_altitude_m is not None:
        body["floating_altitude_m"] = floating_altitude_m
    if cutdown_altitude_m is not None:
        body["cutdown_altitude_m"] = cutdown_altitude_m

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{_base_url()}/api/simulate", json=body)
            r.raise_for_status()
            return r.text
    except httpx.HTTPError as exc:
        return json.dumps({"status": "error", "tool": "hab_run_simulation", "message": str(exc)})


if __name__ == "__main__":
    mcp.run()
