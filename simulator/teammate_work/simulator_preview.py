import streamlit as st
from sensor_simulator import SensorSimulator
from grid_simulator import build_grid_figure

st.set_page_config(
    page_title="GridGuard AI Twin",
    page_icon="⚡",
    layout="wide",
)

ASSETS = ["TX-01", "TX-02", "TX-03"]
FAULT_OPTIONS = ["None", "overload", "overheating", "vibration", "voltage_sag"]

st.title("⚡ GridGuard AI Twin")
st.caption("Dynamic virtual substation | Synthetic demonstration data")

if "simulators" not in st.session_state:
    st.session_state.simulators = {
        name: SensorSimulator(name, seed=i) for i, name in enumerate(ASSETS)
    }
if "applied_loads" not in st.session_state:
    st.session_state.applied_loads = {name: 0.75 for name in ASSETS}
if "applied_faults" not in st.session_state:
    st.session_state.applied_faults = {name: "None" for name in ASSETS}
if "ticks" not in st.session_state:
    st.session_state.ticks = 0

simulators = st.session_state.simulators

st.sidebar.header("Simulation Controls")
asset = st.sidebar.selectbox("Select transformer", ASSETS)

with st.sidebar.form("controls"):
    load = st.slider(
        "Simulated load", 0.1, 1.5,
        float(st.session_state.applied_loads[asset]), 0.1
    )
    current_fault = st.session_state.applied_faults[asset]
    fault = st.selectbox(
        "Fault scenario", FAULT_OPTIONS,
        index=FAULT_OPTIONS.index(current_fault)
    )
    apply = st.form_submit_button("Apply controls")

if apply:
    sim = simulators[asset]
    sim.set_load(load)
    if fault == "None":
        sim.clear_fault()
    else:
        sim.inject_fault(fault)
    st.session_state.applied_loads[asset] = load
    st.session_state.applied_faults[asset] = fault
    st.rerun()

if st.sidebar.button("Reset selected transformer"):
    simulators[asset].reset()
    st.session_state.applied_loads[asset] = 0.75
    st.session_state.applied_faults[asset] = "None"
    st.rerun()


@st.fragment(run_every="1s")
def live_view():
    readings = {name: sim.step() for name, sim in simulators.items()}
    st.session_state.ticks += 1

    statuses = {}
    demo_rul = {}

    for name, reading in readings.items():
        sim = simulators[name]
        temp = reading["temperature_C"]
        vib = reading["vibration_mm_s"]
        fault_active = sim.fault is not None

        # Immediate fault visibility; readings still evolve over time.
        if temp >= 80 or vib >= 5:
            status = "critical"
        elif fault_active or temp >= 65 or vib >= 3:
            status = "warning"
        else:
            status = "normal"

        statuses[name] = status
        demo_rul[name] = {
            "normal": 140.0,
            "warning": 54.0,
            "critical": 12.0,
        }[status]

    fig = build_grid_figure(
        status_by_asset=statuses,
        readings_by_asset=readings,
        rul_by_asset=demo_rul,
        selected_asset=asset,
    )
    st.plotly_chart(
        fig, use_container_width=True,
        key="grid_live",
        config={"displayModeBar": False, "responsive": True},
    )

    st.subheader(f"Live sensor readings — {asset}")
    reading = readings[asset]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current", f'{reading["current_A"]:.2f} A')
    c2.metric("Voltage", f'{reading["voltage_kV"]:.2f} kV')
    c3.metric("Temperature", f'{reading["temperature_C"]:.1f} °C')
    c4.metric("Vibration", f'{reading["vibration_mm_s"]:.2f} mm/s')

    st.write(f"**Health status:** {statuses[asset].upper()}")
    st.write(f"**Demo RUL:** {demo_rul[asset]:.1f} hours")
    st.caption(
        f"Update #{st.session_state.ticks} | "
        f"Load: {reading['load_factor']} | "
        f"Fault: {reading['fault_scenario']}"
    )
    st.warning(
        "Synthetic readings and rule-based demo status. "
        "RUL values are placeholders; the trained AI model is not connected."
    )

live_view()
