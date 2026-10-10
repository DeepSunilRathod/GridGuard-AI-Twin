from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from backend.chat_routes import router as chat_router
from backend.evaluation_routes import router as evaluation_router

# Project paths and environment configuration.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env")

from backend.ai_routes import router as ai_router
from backend.notification_api import router as notification_router

# Locate the existing teammate simulator.
SIMULATOR_DIR = (
    PROJECT_ROOT
    / "simulator"
    / "teammate_v2"
    / "gridguard_dynamic_package"
)
sys.path.insert(0, str(SIMULATOR_DIR))

from sensor_simulator import SensorSimulator

# The existing backend.ai_routes module owns the CNN-LSTM model and AI endpoints.


ASSETS = ["TX-01", "TX-02", "TX-03"]
FAULT_OPTIONS = {
    "none", "overload", "overheating", "vibration", "voltage_sag"
}

app = FastAPI(
    title="GridGuard AI Twin API",
    description=(
        "Synthetic substation simulator API. "
        "Health status and RUL are demonstrations, not validated predictions."
    ),
    version="0.1.0",
)
app.include_router(ai_router)
app.include_router(notification_router)
app.include_router(chat_router)
app.include_router(evaluation_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

simulators = {
    asset: SensorSimulator(asset, seed=i)
    for i, asset in enumerate(ASSETS)
}

# Keep the simulator's 60-sample history window.
histories = {asset: deque(maxlen=60) for asset in ASSETS}
latest_readings = {asset: None for asset in ASSETS}


class ControlRequest(BaseModel):
    load_factor: float = Field(default=0.75, ge=0.1, le=1.5)
    fault: str = "none"


def calculate_status(reading, fault_active):
    """Existing demonstration thresholds; not a trained AI result."""
    temperature = reading["temperature_C"]
    vibration = reading["vibration_mm_s"]

    if temperature >= 80 or vibration >= 5:
        return "critical"
    if fault_active or temperature >= 65 or vibration >= 3:
        return "warning"
    return "normal"


def calculate_demo_rul(reading, status, load_factor):
    """A visible placeholder estimate only; not a validated RUL prediction."""
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


def create_snapshot(asset):
    sim = simulators[asset]
    reading = sim.step()

    status = calculate_status(reading, sim.fault is not None)
    demo_rul_hours = calculate_demo_rul(
        reading=reading,
        status=status,
        load_factor=sim.load_factor,
    )

    snapshot = {
        **reading,
        "asset_id": asset,
        "load_factor": sim.load_factor,
        "fault_scenario": sim.fault or "none",
        "status": status,
        "demo_rul_hours": demo_rul_hours,
        "rul_is_demo": True,
        "data_source": "synthetic_simulation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    histories[asset].append(snapshot)
    latest_readings[asset] = snapshot
    return snapshot



@app.get("/")
def root():
    return {
        "name": "GridGuard AI Twin API",
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gridguard-api"}



@app.get("/api/assets")
def get_assets():
    return {
        "assets": [
            {
                "asset_id": asset,
                "load_factor": simulators[asset].load_factor,
                "fault_scenario": simulators[asset].fault or "none",
                "demo_rul_hours": (
                    latest_readings[asset].get("demo_rul_hours")
                    if latest_readings[asset] else None
                ),
                "latest": latest_readings[asset],
            }
            for asset in ASSETS
        ]
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Advance all simulators by one sample and return dashboard data."""
    snapshots = {asset: create_snapshot(asset) for asset in ASSETS}
    statuses = {asset: snapshot["status"] for asset, snapshot in snapshots.items()}

    return {
        "data_source": "synthetic_simulation",
        "ai_model_connected": False,
        "rul_is_demo": True,
        "assets": list(snapshots.values()),
        "summary": {
            "asset_count": len(ASSETS),
            "normal": sum(status == "normal" for status in statuses.values()),
            "warning": sum(status == "warning" for status in statuses.values()),
            "critical": sum(status == "critical" for status in statuses.values()),
        },
    }


@app.get("/api/assets/{asset_id}/reading")
def get_reading(asset_id: str):
    if asset_id not in simulators:
        raise HTTPException(status_code=404, detail="Unknown asset")
    return create_snapshot(asset_id)


@app.get("/api/assets/{asset_id}/history")
def get_history(asset_id: str):
    if asset_id not in simulators:
        raise HTTPException(status_code=404, detail="Unknown asset")
    return {
        "asset_id": asset_id,
        "samples": list(histories[asset_id]),
        "window_size": 60,
        "sample_count": len(histories[asset_id]),
    }


@app.post("/api/assets/{asset_id}/controls")
def set_controls(asset_id: str, request: ControlRequest):
    if asset_id not in simulators:
        raise HTTPException(status_code=404, detail="Unknown asset")

    fault = request.fault.lower().strip()
    if fault not in FAULT_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail={"allowed_faults": sorted(FAULT_OPTIONS)},
        )

    sim = simulators[asset_id]
    sim.set_load(request.load_factor)
    if fault == "none":
        sim.clear_fault()
    else:
        sim.inject_fault(fault)

    return {
        "asset_id": asset_id,
        "load_factor": sim.load_factor,
        "fault_scenario": sim.fault or "none",
        "message": "Simulation controls updated",
    }


@app.post("/api/assets/{asset_id}/reset")
def reset_asset(asset_id: str):
    if asset_id not in simulators:
        raise HTTPException(status_code=404, detail="Unknown asset")

    simulators[asset_id].reset()
    histories[asset_id].clear()
    latest_readings[asset_id] = None

    return {
        "asset_id": asset_id,
        "message": "Simulator reset successfully",
        "load_factor": 0.75,
        "fault_scenario": "none",
    }
