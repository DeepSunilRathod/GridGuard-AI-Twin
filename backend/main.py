"""GridGuard API with a software digital-twin-backed dashboard data source.

This file preserves the existing AI, notification, chatbot, and evaluation routers.
All grid values are software simulated; this is not a protection or control system.
"""
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

from backend.chat_routes import router as chat_router
from backend.evaluation_routes import router as evaluation_router
from backend.ai_routes import router as ai_router
from backend.notification_api import router as notification_router
from backend.grid_twin_engine import GridTwin, ASSETS, SCENARIOS

# Keep the existing sensor simulator in sync for any older routes/model tooling that use it.
SIMULATOR_DIR = PROJECT_ROOT / "simulator" / "teammate_v2" / "gridguard_dynamic_package"
if SIMULATOR_DIR.exists():
    sys.path.insert(0, str(SIMULATOR_DIR))
try:
    from sensor_simulator import SensorSimulator
except Exception:
    SensorSimulator = None

app = FastAPI(
    title="GridGuard AI Twin API",
    description=(
        "GridGuard software digital twin. Power-flow and condition values are simulated; "
        "demo thresholds are not real protection settings."
    ),
    version="0.2.0",
)
app.include_router(ai_router)
app.include_router(notification_router)
app.include_router(chat_router)
app.include_router(evaluation_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

twin = GridTwin()
simulators = {
    asset: SensorSimulator(asset, seed=i) for i, asset in enumerate(ASSETS)
} if SensorSimulator else {}
histories = {asset: deque(maxlen=60) for asset in ASSETS}
latest_readings = {asset: None for asset in ASSETS}


class ControlRequest(BaseModel):
    # Optional fields allow old clients to change only the fields they send.
    load_factor: float | None = Field(default=None, ge=0.1, le=1.5)
    fault: str | None = None
    breaker_closed: bool | None = None


def calculate_demo_rul(reading, status, load_factor):
    """Visible placeholder only; not a validated RUL model output."""
    temperature = float(reading.get("temperature_C", 25))
    vibration = float(reading.get("vibration_mm_s", 0))
    load_factor = float(load_factor)
    estimate = (
        240
        - max(0.0, temperature - 40.0) * 2.0
        - max(0.0, vibration) * 8.0
        - max(0.0, load_factor - 0.75) * 100.0
        - (80 if status == "critical" else 30 if status == "warning" else 0)
    )
    return max(1, int(estimate))


def make_snapshot(asset, twin_state):
    source = twin_state["assets"][asset]
    status = str(source.get("status", "unknown")).lower()
    load_factor = float(twin.load_factor[asset])
    snapshot = {
        **source,
        "asset_id": asset,
        "load_factor": round(load_factor, 2),
        "fault_scenario": twin.scenarios[asset],
        "status": status,
        "demo_rul_hours": calculate_demo_rul(source, status, load_factor),
        "rul_is_demo": True,
        "data_source": "software_digital_twin_pandapower",
        "simulated_data": True,
        "timestamp": twin_state["timestamp"],
    }
    histories[asset].append(snapshot)
    latest_readings[asset] = snapshot
    return snapshot


@app.get("/")
def root():
    return {"name": "GridGuard AI Twin API", "status": "running", "documentation": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gridguard-api", "digital_twin": True, "simulated_data": True}


@app.get("/api/twin/state")
def get_twin_state():
    """Detailed power-flow state for the schematic simulator and debugging."""
    return twin.solve()


@app.get("/api/assets")
def get_assets():
    return {
        "assets": [
            {
                "asset_id": asset,
                "load_factor": twin.load_factor[asset],
                "fault_scenario": twin.scenarios[asset],
                "breaker_closed": twin.breaker_closed[asset],
                "demo_rul_hours": latest_readings[asset].get("demo_rul_hours") if latest_readings[asset] else None,
                "latest": latest_readings[asset],
            }
            for asset in ASSETS
        ]
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Return one consistent solved twin state for all assets."""
    state = twin.solve()
    snapshots = {asset: make_snapshot(asset, state) for asset in ASSETS}
    statuses = {asset: snapshot["status"] for asset, snapshot in snapshots.items()}
    return {
        "data_source": "software_digital_twin_pandapower",
        "simulated_data": True,
        "ai_model_connected": False,
        "rul_is_demo": True,
        "power_flow_converged": state["converged"],
        "simulation_type": state["simulation_type"],
        "assets": list(snapshots.values()),
        "summary": {
            "asset_count": len(ASSETS),
            "normal": sum(s == "normal" for s in statuses.values()),
            "warning": sum(s == "warning" for s in statuses.values()),
            "critical": sum(s in ("critical", "simulation_error") for s in statuses.values()),
        },
    }


@app.get("/api/assets/{asset_id}/reading")
def get_reading(asset_id: str):
    if asset_id not in ASSETS:
        raise HTTPException(status_code=404, detail="Unknown asset")
    state = twin.solve()
    return make_snapshot(asset_id, state)


@app.get("/api/assets/{asset_id}/history")
def get_history(asset_id: str):
    if asset_id not in ASSETS:
        raise HTTPException(status_code=404, detail="Unknown asset")
    return {"asset_id": asset_id, "samples": list(histories[asset_id]), "window_size": 60, "sample_count": len(histories[asset_id])}


@app.post("/api/assets/{asset_id}/controls")
def set_controls(asset_id: str, request: ControlRequest):
    if asset_id not in ASSETS:
        raise HTTPException(status_code=404, detail="Unknown asset")
    load_factor = request.load_factor if request.load_factor is not None else twin.load_factor[asset_id]
    fault = request.fault.strip().lower() if request.fault is not None else twin.scenarios[asset_id]
    if fault not in SCENARIOS:
        raise HTTPException(status_code=422, detail={"allowed_faults": sorted(SCENARIOS)})
    try:
        state = twin.set_controls(asset_id, load_factor, fault, request.breaker_closed)
        # Keep legacy simulator object aligned for any existing model code that still uses it.
        if asset_id in simulators:
            sim = simulators[asset_id]
            sim.set_load(load_factor)
            if fault == "none":
                sim.clear_fault()
            else:
                sim.inject_fault(fault)
        make_snapshot(asset_id, state)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "asset_id": asset_id,
        "load_factor": twin.load_factor[asset_id],
        "fault_scenario": twin.scenarios[asset_id],
        "breaker_closed": twin.breaker_closed[asset_id],
        "status": state["assets"][asset_id]["status"].lower(),
        "message": "Digital twin controls updated",
        "data_source": "software_digital_twin_pandapower",
    }


@app.post("/api/assets/{asset_id}/reset")
def reset_asset(asset_id: str):
    if asset_id not in ASSETS:
        raise HTTPException(status_code=404, detail="Unknown asset")
    state = twin.reset_asset(asset_id)
    if asset_id in simulators:
        simulators[asset_id].reset()
    histories[asset_id].clear()
    latest_readings[asset_id] = None
    make_snapshot(asset_id, state)
    return {
        "asset_id": asset_id,
        "message": "Digital twin asset reset",
        "load_factor": twin.load_factor[asset_id],
        "fault_scenario": twin.scenarios[asset_id],
        "breaker_closed": twin.breaker_closed[asset_id],
    }


@app.post("/api/twin/reset")
def reset_twin():
    state = twin.reset()
    for asset in ASSETS:
        if asset in simulators:
            simulators[asset].reset()
        histories[asset].clear()
        latest_readings[asset] = None
        make_snapshot(asset, state)
    return {"message": "Digital twin reset", "state": state}
