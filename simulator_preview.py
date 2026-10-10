import os
import requests
import streamlit as st
from grid_simulator import build_grid_figure

st.set_page_config(
    page_title="GridGuard AI Twin",
    page_icon="⚡",
    layout="wide",
)

ASSETS = ["TX-01", "TX-02", "TX-03"]
FAULT_OPTIONS = ["None", "overload", "overheating", "vibration", "voltage_sag"]
BACKEND_URL = os.getenv("GRIDGUARD_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 3

st.title("⚡ GridGuard AI Twin")
st.caption("Virtual substation controls connected to the main GridGuard FastAPI backend")
st.info(
    "This interface reads and changes the same simulator state used by the main dashboard. "
    "Values are synthetic demonstration data."
)


def api_get(path):
    response = requests.get(f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def api_post(path, payload=None):
    response = requests.post(
        f"{BACKEND_URL}{path}", json=payload, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def get_asset_controls(asset_id):
    data = api_get("/api/assets")
    for item in data.get("assets", []):
        if item.get("asset_id") == asset_id:
            return item
    raise RuntimeError(f"Backend did not return {asset_id}")


# Verify the main backend and read its current shared control state.
try:
    backend_health = api_get("/api/health")
    backend_assets = api_get("/api/assets").get("assets", [])
    if not backend_assets:
        raise RuntimeError("Backend returned no assets")
    st.sidebar.success(f"Backend connected: {BACKEND_URL}")
except requests.RequestException as exc:
    st.error(
        f"Cannot connect to the main backend at {BACKEND_URL}. "
        "Start the existing FastAPI backend on port 8000, then refresh this page."
    )
    st.code(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Could not load assets from the main backend: {exc}")
    st.stop()

st.sidebar.header("Shared Simulation Controls")
asset = st.sidebar.selectbox("Select transformer", ASSETS)

try:
    current = get_asset_controls(asset)
    current_load = float(current.get("load_factor", 0.75))
    current_fault_raw = str(current.get("fault_scenario", "none")).lower()
    current_fault = "None" if current_fault_raw in ("", "none") else current_fault_raw
    current_breaker = bool(current.get("breaker_closed", True))
    if current_fault not in FAULT_OPTIONS:
        current_fault = "None"
except Exception as exc:
    st.sidebar.error(f"Could not read {asset} controls: {exc}")
    current_load, current_fault, current_breaker = 0.75, "None", True

# Keys are asset-specific so controls for each transformer remain separate.
load_widget_key = f"load_factor_{asset}"
fault_widget_key = f"fault_scenario_{asset}"
breaker_widget_key = f"breaker_closed_{asset}"
if load_widget_key not in st.session_state:
    st.session_state[load_widget_key] = min(1.5, max(0.1, current_load))
if fault_widget_key not in st.session_state:
    st.session_state[fault_widget_key] = current_fault
if breaker_widget_key not in st.session_state:
    st.session_state[breaker_widget_key] = current_breaker

# Reset is handled before these widgets are created so session-state values can be safely updated.
if st.sidebar.button("Reset selected transformer in shared backend"):
    try:
        api_post(f"/api/assets/{asset}/reset")
        st.session_state[load_widget_key] = 0.75
        st.session_state[fault_widget_key] = "None"
        st.session_state[breaker_widget_key] = True
        st.rerun()
    except requests.RequestException as exc:
        st.sidebar.error(f"Could not reset {asset}: {exc}")

with st.sidebar.form(f"controls_{asset}"):
    load = st.slider(
        "Simulated load factor", min_value=0.1, max_value=1.5,
        step=0.1, key=load_widget_key,
        help="1.0 represents the simulator's nominal load factor; these are demo units.",
    )
    fault = st.selectbox("Fault scenario", FAULT_OPTIONS, key=fault_widget_key)
    breaker_closed = st.checkbox("Feeder breaker closed", key=breaker_widget_key)
    apply = st.form_submit_button("Apply controls to shared backend")

if apply:
    try:
        result = api_post(
            f"/api/assets/{asset}/controls",
            {"load_factor": float(load), "fault": "none" if fault == "None" else fault,
             "breaker_closed": bool(breaker_closed)},
        )
        st.sidebar.success(
            f"Updated {asset}: load={result.get('load_factor')}, "
            f"fault={result.get('fault_scenario')}, "
            f"breaker={'closed' if result.get('breaker_closed', True) else 'open'}"
        )
        st.rerun()
    except requests.RequestException as exc:
        st.sidebar.error(f"Could not update backend controls: {exc}")

st.sidebar.caption("The React dashboard on port 5173 reads this same backend on port 8000.")


@st.fragment(run_every="1s")
def live_view(selected_asset):
    try:
        dashboard = api_get("/api/dashboard")
    except requests.RequestException as exc:
        st.error(f"Backend connection lost: {exc}")
        return

    readings_list = dashboard.get("assets", [])
    readings = {
        item.get("asset_id"): item
        for item in readings_list
        if item.get("asset_id") in ASSETS
    }
    if not readings:
        st.warning("The backend returned no asset readings yet.")
        return

    statuses = {name: item.get("status", "unknown") for name, item in readings.items()}
    breaker_by_asset = {
        item.get("asset_id"): bool(item.get("breaker_closed", True))
        for item in api_get("/api/assets").get("assets", [])
    }
    fig = build_grid_figure(
        status_by_asset=statuses,
        readings_by_asset=readings,
        selected_asset=selected_asset,
        breaker_by_asset=breaker_by_asset,
    )
    st.plotly_chart(
        fig, use_container_width=True,
        key="grid_live_shared_backend",
        config={"displayModeBar": False, "responsive": True},
    )

    st.subheader(f"Live sensor readings — {selected_asset}")
    reading = readings.get(selected_asset)
    if not reading:
        st.warning(f"No reading available for {selected_asset}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current", f'{reading.get("current_A", 0):.2f} A')
    c2.metric("Voltage", f'{reading.get("voltage_kV", 0):.2f} kV')
    c3.metric("Temperature", f'{reading.get("temperature_C", 0):.1f} °C')
    c4.metric("Vibration", f'{reading.get("vibration_mm_s", 0):.2f} mm/s')

    s1, s2, s3 = st.columns(3)
    s1.metric("Health status", str(reading.get("status", "unknown")).upper())
    s2.metric("Load factor", f'{reading.get("load_factor", 0):.2f}')
    s3.metric("Fault scenario", str(reading.get("fault_scenario", "none")).upper())
    loading = reading.get("transformer_loading_percent")
    if loading is not None:
        st.metric("Power-flow transformer loading", f"{loading:.1f}%")
    st.caption("Breaker: " + ("CLOSED" if reading.get("breaker_closed", True) else "OPEN"))

    st.caption(
        f"Power flow converged: {dashboard.get('power_flow_converged', False)} · "
        f"Source: {dashboard.get('data_source', 'unknown')} · "
        f"Backend: {BACKEND_URL} · "
        f"Timestamp: {reading.get('timestamp', 'not provided')}"
    )
    if reading.get("rul_is_demo", True):
        st.warning(
            f"Displayed demo RUL: {reading.get('demo_rul_hours', 'unavailable')} hours. "
            "This is a placeholder estimate, not a validated AI RUL prediction."
        )
    st.subheader("Shared backend status summary")
    summary = dashboard.get("summary", {})
    a, b, c, d = st.columns(4)
    a.metric("Assets", summary.get("asset_count", len(readings)))
    b.metric("Normal", summary.get("normal", 0))
    c.metric("Warnings", summary.get("warning", 0))
    d.metric("Critical", summary.get("critical", 0))


live_view(asset)
