

import { useCallback, useEffect, useState } from "react";

import {

  Activity,

  AlertTriangle,

  CheckCircle2,

  ChevronDown,

  CircleGauge,

  Clock3,

  Cpu,

  LayoutDashboard,

  LoaderCircle,

  Network,

  RefreshCw,

  Settings2,

  ShieldCheck,

  Thermometer,

  Zap,

  Waves,

  XCircle,

  BrainCircuit,

} from "lucide-react";

import {

  Area,

  AreaChart,

  CartesianGrid,

  ResponsiveContainer,

  Tooltip,

  XAxis,

  YAxis,

} from "recharts";

import "./App.css";

import Chatbot from "./Chatbot";

import "./Chatbot.css";

import AIEvaluationPanel from "./AIEvaluationPanel";

import "./AIEvaluationPanel.css";

import FaultDemoPanel from "./FaultDemoPanel";

import "./FaultDemoPanel.css";

const API = "http://127.0.0.1:8000";

const ASSETS = ["TX-01", "TX-02", "TX-03"];

const initialControls = Object.fromEntries(

  ASSETS.map((id) => [

    id,

    { load_factor: 0.75, fault: "none" },

  ])

);

function MetricCard({

  title,

  value,

  unit,

  icon: Icon,

  color,

  note,

}) {

  return (

    <article className="metric-card">

      <div className="metric-top">

        <span>{title}</span>

        <span className={`metric-icon ${color}`}>

          <Icon size={19} />

        </span>

      </div>

      <div className="metric-value">

        {value ?? "--"} <small>{unit}</small>

      </div>

      <div className="metric-note">

        <span className="live-dot" />

        {note}

      </div>

    </article>

  );

}

function StatusBadge({ status }) {

  const label = status || "unknown";

  return (

    <span className={`status-badge ${label}`}>

      <span className="status-dot" />

      {label.toUpperCase()}

    </span>

  );

}


function DigitalSubstation({ assets, selected, onSelect }) {
  const getAsset = (id) => assets.find((asset) => asset.asset_id === id);
  const statusColor = (asset) => {
    if (!asset) return "#64748b";
    if (asset.status === "critical") return "#fb7185";
    if (asset.status === "warning") return "#fbbf24";
    return "#34d399";
  };
  return (
    <section className="section-block twin-section" id="digital-twin">
      <div className="section-heading">
        <div>
          <div className="eyebrow">LIVE NETWORK MODEL</div>
          <h2>Digital substation</h2>
          <p>Select a feeder to inspect its readings and operate its simulation controls.</p>
        </div>
        <span className="live-pill"><span className="live-dot" /> SOFTWARE TWIN</span>
      </div>
      <article className="panel twin-canvas">
        <div className="twin-canvas-top">
          <div><span className="twin-overline">GRIDGUARD / SINGLE-LINE VIEW</span><strong>110 kV → 11 kV → 0.4 kV</strong></div>
          <span className="twin-status"><span className="live-dot" /> Live model state</span>
        </div>
        <svg className="substation-svg" viewBox="0 0 1000 430" role="img" aria-label="Interactive simulated substation single-line diagram">
          <defs>
            <linearGradient id="busGlow" x1="0" x2="1"><stop offset="0%" stopColor="#1e9eb8"/><stop offset="100%" stopColor="#57d9f2"/></linearGradient>
            <filter id="softGlow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>
          <text x="35" y="36" className="svg-label">UTILITY SOURCE</text>
          <rect x="35" y="58" width="150" height="76" rx="12" className="svg-equipment"/>
          <circle cx="64" cy="84" r="7" className="svg-led"/>
          <text x="110" y="88" textAnchor="middle" className="svg-title">GRID INPUT</text>
          <text x="110" y="111" textAnchor="middle" className="svg-subtitle">110 kV nominal</text>
          <path d="M185 96 H245" className="svg-wire"/>
          <rect x="245" y="70" width="76" height="52" rx="8" className="svg-equipment"/>
          <path d="M260 108 L305 82" className="svg-breaker"/>
          <text x="283" y="58" textAnchor="middle" className="svg-label">CB-MAIN</text>
          <path d="M321 96 H375 V164 H420" className="svg-wire"/>
          <rect x="420" y="126" width="160" height="76" rx="12" className="svg-equipment transformer-box"/>
          <circle cx="462" cy="164" r="20" className="svg-coil"/>
          <circle cx="500" cy="164" r="20" className="svg-coil"/>
          <text x="536" y="158" textAnchor="middle" className="svg-title">MAIN TX</text>
          <text x="536" y="180" textAnchor="middle" className="svg-subtitle">110 / 11 kV</text>
          <path d="M500 202 V244 H930 M500 244 H270" className="svg-wire bus-wire" filter="url(#softGlow)"/>
          <text x="716" y="228" textAnchor="middle" className="svg-label">11 kV MAIN BUSBAR</text>
          {[0,1,2].map((idx) => {
            const id = `TX-0${idx+1}`;
            const asset = getAsset(id);
            const x = [270, 575, 850][idx];
            const color = statusColor(asset);
            const isSelected = selected === id;
            return (
              <g key={id} className={`svg-feeder ${isSelected ? "is-selected" : ""}`} onClick={() => onSelect(id)} role="button" tabIndex="0" onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") onSelect(id); }}>
                <rect x={x-112} y="266" width="224" height="142" rx="13" className="svg-feeder-card"/>
                <path d={`M${x} 244 V284`} className="svg-wire feeder-wire"/>
                <rect x={x-27} y="284" width="54" height="34" rx="5" className="svg-equipment"/>
                <path d={`M${x-17} 309 L${x+17} 291`} className="svg-breaker"/>
                <circle cx={x-14} cy="344" r="14" fill="none" stroke={color} strokeWidth="4"/>
                <circle cx={x+14} cy="344" r="14" fill="none" stroke={color} strokeWidth="4"/>
                <text x={x} y="278" textAnchor="middle" className="svg-label">{`CB-0${idx+1}`}</text>
                <text x={x} y="382" textAnchor="middle" className="svg-title">{id}</text>
                <text x={x} y="399" textAnchor="middle" className="svg-subtitle">{asset ? `${Number(asset.load_factor ?? 0).toFixed(2)}× load` : "Waiting for data"}</text>
                <rect x={x-39} y="417" width="78" height="5" rx="3" fill={color}/>
                <circle cx={x+83} cy="284" r="5" fill={color}/>
              </g>
            );
          })}
          <text x="35" y="186" className="svg-subtitle">Software simulation only · not a protection relay</text>
        </svg>
        <div className="twin-legend">
          <span><i className="legend-normal" /> Normal</span>
          <span><i className="legend-warning" /> Warning</span>
          <span><i className="legend-critical" /> Critical</span>
          <span className="twin-hint">Click a feeder to select its asset</span>
        </div>
      </article>
    </section>
  );
}

export default function App() {

  const [dashboard, setDashboard] = useState(null);

  const [selected, setSelected] = useState("TX-01");

  const [history, setHistory] = useState([]);

  const [controls, setControls] = useState(initialControls);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [actionMessage, setActionMessage] = useState("");

  const [busy, setBusy] = useState(false);

  const [lastUpdated, setLastUpdated] = useState(null);

  // CNN-LSTM prediction state

  const [aiPrediction, setAiPrediction] = useState(null);

  const [aiError, setAiError] = useState("");

  const [aiLoading, setAiLoading] = useState(true);

  const [alertEvents, setAlertEvents] = useState([]);

  const [notificationBusy, setNotificationBusy] = useState(false);

  const [notificationMessage, setNotificationMessage] = useState("");

  // Fetch virtual grid dashboard data

  const refresh = useCallback(async () => {

    try {

      const response = await fetch(`${API}/api/dashboard`);

      if (!response.ok) {

        throw new Error(`API returned ${response.status}`);

      }

      const data = await response.json();

      setDashboard(data);

      setError("");

      setLastUpdated(new Date());

    } catch {

      setError(

        "Cannot connect to backend. Check that FastAPI is running on port 8000."

      );

    } finally {

      setLoading(false);

    }

  }, []);

  // Fetch sensor history for the selected asset

  const refreshHistory = useCallback(async (asset) => {

    try {

      const response = await fetch(

        `${API}/api/assets/${asset}/history`

      );

      if (!response.ok) return;

      const data = await response.json();

      setHistory(

        data.samples.map((item, index) => ({

          ...item,

          sample: index + 1,

        }))

      );

    } catch {

      // The main dashboard displays backend connection errors.

    }

  }, []);

  // Fetch the saved CNN-LSTM model's experimental prediction

  const refreshAiPrediction = useCallback(async () => {

    setAiLoading(true);

    try {

      const response = await fetch(`${API}/api/ai/prediction`);

      const data = await response.json();

      if (!response.ok) {

        throw new Error(

          data.detail || `AI API returned ${response.status}`

        );

      }

      setAiPrediction(data);

      setAiError("");

      setAlertEvents((previous) => [

        {

          id: `${Date.now()}-${previous.length}`,

          time: new Date().toLocaleString(),

          label: data.alert_level || data.predicted_label || "UNKNOWN",

          probability: Number(data.fault_probability ?? 0),

          source: data.note || "CNN + LSTM dataset demo",

        },

        ...previous,

      ].slice(0, 5));

    } catch (err) {

      setAiPrediction(null);

      setAiError(err.message || "AI prediction unavailable");

    } finally {

      setAiLoading(false);

    }

  }, []);

  // Refresh simulator data every three seconds

  useEffect(() => {

    const initial = setTimeout(() => void refresh(), 0);

    const timer = setInterval(() => void refresh(), 3000);

    return () => {

      clearTimeout(initial);

      clearInterval(timer);

    };

  }, [refresh]);

  // Refresh history when the selected asset or dashboard data changes

  useEffect(() => {

    const timer = setTimeout(() => void refreshHistory(selected), 0);

    return () => clearTimeout(timer);

  }, [selected, dashboard, refreshHistory]);

  // Load AI prediction when the dashboard opens

  useEffect(() => {

    const timer = setTimeout(() => void refreshAiPrediction(), 0);

    return () => clearTimeout(timer);

  }, [refreshAiPrediction]);

  const assets = dashboard?.assets || [];

  const active = assets.find(

    (asset) => asset.asset_id === selected

  );

  const summary = dashboard?.summary || {

    asset_count: 0,

    normal: 0,

    warning: 0,

    critical: 0,

  };

  const updateControl = (key, value) => {

    setControls((old) => ({

      ...old,

      [selected]: {

        ...old[selected],

        [key]: value,

      },

    }));

  };

  // Send an email or WhatsApp test/alert through the backend notification API.

  async function sendNotification(channel) {

    if (!aiPrediction) {

      setNotificationMessage("Run a CNN + LSTM prediction before sending an alert.");

      return;

    }

    setNotificationBusy(true);

    setNotificationMessage("");

    const predictedLabel = String(

      aiPrediction.predicted_label || aiPrediction.alert_level || "UNKNOWN"

    ).toUpperCase();

    const faultProbability = Number(aiPrediction.fault_probability ?? 0);

    const message = [

      "GridGuard AI Twin notification",

      `Asset selected: ${selected}`,

      `CNN + LSTM dataset-demo status: ${predictedLabel}`,

      `Fault probability: ${(faultProbability * 100).toFixed(1)}%`,

      `Threshold: ${(Number(aiPrediction.threshold ?? 0.5) * 100).toFixed(0)}%`,

      `Simulator status: ${active?.status ?? "unknown"}`,

      `Demo RUL: ${active?.demo_rul_hours ?? "not available"} hours`,

      "Important: CNN + LSTM prediction uses the CSV demo dataset, not live sensor input.",

    ].join("\n");

    try {

      const response = await fetch(`${API}/api/notifications/send`, {

        method: "POST",

        headers: { "Content-Type": "application/json" },

        body: JSON.stringify({

          channel,

          title: `GridGuard ${predictedLabel} - ${selected}`,

          message,

          fault_probability: faultProbability,

          source: "CSV dataset demo",

        }),

      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {

        throw new Error(result.detail || `Notification API returned ${response.status}`);

      }

      setNotificationMessage(result.message || `${channel} notification submitted successfully.`);

    } catch (err) {

      setNotificationMessage(err.message || `Could not send ${channel} notification.`);

    } finally {

      setNotificationBusy(false);

    }

  }

  // Apply simulation controls

  async function applyControls() {

    setBusy(true);

    setActionMessage("");

    try {

      const response = await fetch(

        `${API}/api/assets/${selected}/controls`,

        {

          method: "POST",

          headers: {

            "Content-Type": "application/json",

          },

          body: JSON.stringify(controls[selected]),

        }

      );

      const result = await response.json();

      if (!response.ok) {

        throw new Error(

          JSON.stringify(result.detail || result)

        );

      }

      setActionMessage(

        "Simulation controls updated successfully."

      );

      await refresh();

      await refreshHistory(selected);

    } catch (err) {

      setActionMessage(

        `Could not apply controls: ${err.message}`

      );

    } finally {

      setBusy(false);

    }

  }

  // Reset the selected virtual asset

  async function resetAsset() {

    setBusy(true);

    try {

      const response = await fetch(

        `${API}/api/assets/${selected}/reset`,

        { method: "POST" }

      );

      if (!response.ok) {

        throw new Error("Reset failed");

      }

      setControls((old) => ({

        ...old,

        [selected]: {

          load_factor: 0.75,

          fault: "none",

        },

      }));

      setActionMessage(`${selected} simulator reset.`);

      await refresh();

      await refreshHistory(selected);

    } catch (err) {

      setActionMessage(err.message);

    } finally {

      setBusy(false);

    }

  }

  const chartData = history.map((item, index) => ({

    ...item,

    sample: index + 1,

  }));

  return (

    <div className="app-shell">

      {/* Sidebar */}

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">

            <Zap size={24} fill="currentColor" />

          </div>

          <div>

            <strong>GridGuard</strong>

            <span>AI TWIN PLATFORM</span>

          </div>

        </div>

        <div className="nav-label">WORKSPACE</div>

        <button className="nav-item active">

          <LayoutDashboard size={18} />

          Overview

        </button>

        <button

          className="nav-item"

          onClick={() =>

            document

              .getElementById("assets")

              ?.scrollIntoView({ behavior: "smooth" })

          }

        >

          <Network size={18} />

          Grid assets

        </button>

        <button className="nav-item" onClick={() => document.getElementById("digital-twin")?.scrollIntoView({ behavior: "smooth" })}>
          <Network size={18} /> Digital substation
        </button>

        <button className="nav-item" onClick={() => document.getElementById("sensor-analytics")?.scrollIntoView({ behavior: "smooth" })}>
          <Activity size={18} /> Sensor analytics
        </button>

        <button className="nav-item" onClick={() => document.getElementById("ai-evaluation")?.scrollIntoView({ behavior: "smooth" })}>
          <BrainCircuit size={18} /> AI evaluation
        </button>

        <button
          className="nav-item"
          onClick={() => document.getElementById("trends")?.scrollIntoView({ behavior: "smooth" })}
        >
          <Activity size={18} />
          Sensor trends
        </button>

        <button

          className="nav-item"

          onClick={() => document.getElementById("alerts")?.scrollIntoView({ behavior: "smooth" })}

        >

          <AlertTriangle size={18} />

          AI alerts

        </button>

        <button

          className="nav-item"

          onClick={() => document.getElementById("key-factors")?.scrollIntoView({ behavior: "smooth" })}

        >

          <Clock3 size={18} />

          Key factors &amp; RUL

        </button>

        <button

          className="nav-item"

          onClick={() =>

            document

              .getElementById("controls")

              ?.scrollIntoView({ behavior: "smooth" })

          }

        >

          <Settings2 size={18} />

          Simulation controls

        </button>

        <div className="sidebar-spacer" />

        <div className="system-card">

          <div className="system-heading">

            <span className="live-dot" />

            SYSTEM STATUS

          </div>

          <strong>

            {error ? "Disconnected" : "Simulator online"}

          </strong>

          <p>

            {error

              ? "Backend connection required"

              : "Synthetic data stream active"}

          </p>

          <div className="system-line">

            <span>API</span>

            <span className={error ? "text-red" : "text-green"}>

              {error ? "Offline" : "Connected"}

            </span>

          </div>

          <div className="system-line">

            <span>AI model</span>

            <span

              className={

                aiPrediction ? "text-green" : "text-amber"

              }

            >

              {aiLoading

                ? "Loading..."

                : aiPrediction

                  ? "Dataset demo loaded"

                  : "Unavailable"}

            </span>

          </div>

        </div>

        <div className="sidebar-footer">

          GRIDGUARD AI TWIN <span>v0.2.0</span>

        </div>

      </aside>

      {/* Main content */}

      <main className="main-area">

        <header className="topbar">

          <div className="breadcrumb">

            Workspace <span>/</span> <strong>Overview</strong>

          </div>

          <div className="top-actions">

            <span className="environment">

              <span className="live-dot" />

              DEMO ENVIRONMENT

            </span>

            <button

              className="icon-button"

              title="Refresh data"

              onClick={() => {

                refresh();

                refreshAiPrediction();

              }}

            >

              <RefreshCw size={17} />

            </button>

            <div className="avatar">DG</div>

          </div>

        </header>

        <div className="page-content">

          <section className="page-heading">

            <div>

              <div className="eyebrow">

                INDUSTRIAL MONITORING / SUBSTATION

              </div>

              <h1>

                Grid overview <span className="heading-dot">.</span>

              </h1>

              <p>

                Monitor transformer health, inspect sensor trends,

                and simulate fault scenarios.

              </p>

            </div>

            <div className="update-label">

              <Clock3 size={15} />

              {lastUpdated

                ? `Updated ${lastUpdated.toLocaleTimeString()}`

                : "Waiting for data"}

            </div>

          </section>

          {error && (

            <div className="error-banner">

              <AlertTriangle size={19} />

              <div>

                <strong>Backend unavailable</strong>

                <p>{error}</p>

              </div>

              <button onClick={refresh}>Retry</button>

            </div>

          )}

          {actionMessage && (

            <div className="message-banner">

              {actionMessage}

              <button onClick={() => setActionMessage("")}>

                <XCircle size={16} />

              </button>

            </div>

          )}

          {/* CNN + LSTM alert status */}

          <section

            className="section-block"

            aria-live="polite"

            style={{ marginBottom: 22 }}

          >

            <div

              style={{

                display: "flex",

                alignItems: "center",

                gap: 14,

                flexWrap: "wrap",

                padding: 18,

                borderRadius: 14,

                border: `1px solid ${aiPrediction?.alert ? "#fecaca" : "#bbf7d0"}`,

                background: aiPrediction?.alert ? "#fff1f2" : "#f0fdf4",

              }}

            >

              {aiPrediction?.alert ? (

                <AlertTriangle size={26} color="#b91c1c" />

              ) : (

                <CheckCircle2 size={26} color="#15803d" />

              )}

              <div style={{ flex: 1, minWidth: 220 }}>

                <strong style={{ color: aiPrediction?.alert ? "#991b1b" : "#166534" }}>

                  {aiLoading

                    ? "Checking CNN + LSTM prediction…"

                    : aiError

                      ? "AI alert unavailable"

                      : aiPrediction?.alert

                        ? "FAULT ALERT — model threshold exceeded"

                        : "NORMAL — no dataset-demo alert"}

                </strong>

                <p style={{ margin: "5px 0 0", color: "#475569", fontSize: 13 }}>

                  {aiError

                    ? aiError

                    : `Fault probability: ${aiPrediction ? (Number(aiPrediction.fault_probability) * 100).toFixed(1) : "--"}% · Source: CSV dataset demo, not live telemetry.`}

                </p>

              </div>

              <button

                className="secondary-button"

                onClick={refreshAiPrediction}

                disabled={aiLoading}

              >

                {aiLoading ? <LoaderCircle size={16} className="spin" /> : <RefreshCw size={16} />}

                Check prediction

              </button>

              <button

                className="secondary-button"

                onClick={() => sendNotification("email")}

                disabled={notificationBusy || aiLoading || !aiPrediction}

              >

                {notificationBusy ? "Sending…" : "Send email"}

              </button>

              <button

                className="secondary-button"

                onClick={() => sendNotification("whatsapp")}

                disabled={notificationBusy || aiLoading || !aiPrediction}

              >

                {notificationBusy ? "Sending…" : "Send WhatsApp"}

              </button>

              {notificationMessage && (

                <p role="status" aria-live="polite" style={{ width: "100%", margin: "4px 0 0", fontSize: 13, color: notificationMessage.toLowerCase().includes("success") || notificationMessage.toLowerCase().includes("submitted") ? "#166534" : "#b45309" }}>

                  {notificationMessage}

                </p>

              )}

            </div>

          </section>

          {/* Key factors and visible RUL */}

          <section className="section-block" id="key-factors">

            <div className="section-heading">

              <div>

                <h2>Key factors &amp; Remaining Useful Life</h2>

                <p>Current selected asset: {selected}. RUL shown here is a simulator demo value, not a CNN + LSTM output.</p>

              </div>

            </div>

            <div className="metrics-grid">

              <MetricCard title="Remaining Useful Life" value={active?.demo_rul_hours ?? "--"} unit="hours" icon={Clock3} color="blue" note="Demo placeholder — not AI-predicted" />

              <MetricCard title="Voltage" value={active ? Number(active.voltage_kV).toFixed(2) : "--"} unit="kV" icon={Zap} color="blue" note="Selected asset telemetry" />

              <MetricCard title="Temperature" value={active ? Number(active.temperature_C).toFixed(1) : "--"} unit="°C" icon={Thermometer} color="orange" note="Selected asset telemetry" />

              <MetricCard title="Vibration" value={active ? Number(active.vibration_mm_s).toFixed(2) : "--"} unit="mm/s" icon={Waves} color="green" note="Selected asset telemetry" />

            </div>

          </section>

          {/* Summary cards */}

          <section className="summary-grid">

            <div className="summary-card">

              <div className="summary-icon blue">

                <Network size={20} />

              </div>

              <div>

                <span>Monitored assets</span>

                <strong>

                  {summary.asset_count ?? 0}

                  <small> transformers</small>

                </strong>

                <p>Across simulated substation</p>

              </div>

            </div>

            <div className="summary-card">

              <div className="summary-icon green">

                <ShieldCheck size={20} />

              </div>

              <div>

                <span>Normal</span>

                <strong>

                  {summary.normal ?? 0}

                  <small> assets</small>

                </strong>

                <p>Within demo thresholds</p>

              </div>

            </div>

            <div className="summary-card">

              <div className="summary-icon amber">

                <AlertTriangle size={20} />

              </div>

              <div>

                <span>Warnings</span>

                <strong>

                  {summary.warning ?? 0}

                  <small> assets</small>

                </strong>

                <p>Require investigation</p>

              </div>

            </div>

            <div className="summary-card">

              <div className="summary-icon red">

                <Zap size={20} />

              </div>

              <div>

                <span>Critical</span>

                <strong>

                  {summary.critical ?? 0}

                  <small> assets</small>

                </strong>

                <p>Demo threshold exceeded</p>

              </div>

            </div>

          </section>

          {/* Interactive digital substation — shares backend asset state */}
          <DigitalSubstation assets={assets} selected={selected} onSelect={setSelected} />

          {/* Virtual grid assets */}

          <section className="section-block" id="assets">

            <div className="section-heading">

              <div>

                <h2>Substation assets</h2>

                <p>

                  Choose a transformer to inspect its readings

                  and controls.

                </p>

              </div>

              <span className="section-count">

                {assets.length} ASSETS

              </span>

            </div>

            <div className="asset-grid">

              {ASSETS.map((id, index) => {

                const asset = assets.find(

                  (item) => item.asset_id === id

                );

                const isSelected = selected === id;

                return (

                  <button

                    key={id}

                    className={`asset-card ${

                      isSelected ? "selected" : ""

                    }`}

                    onClick={() => setSelected(id)}

                  >

                    <div className="asset-card-top">

                      <div className="asset-symbol">

                        <Zap size={21} />

                      </div>

                      <StatusBadge status={asset?.status} />

                    </div>

                    <div className="asset-name">

                      {id}

                      <span>

                        {[

                          "Main transformer",

                          "Feeder transformer",

                          "Reserve transformer",

                        ][index]}

                      </span>

                    </div>

                    <div className="asset-values">

                      <div>

                        <span>Voltage</span>

                        <strong>

                          {asset

                            ? Number(asset.voltage_kV).toFixed(2)

                            : "--"}{" "}

                          <small>kV</small>

                        </strong>

                      </div>

                      <div>

                        <span>Temperature</span>

                        <strong>

                          {asset

                            ? Number(asset.temperature_C).toFixed(1)

                            : "--"}{" "}

                          <small>°C</small>

                        </strong>

                      </div>

                    </div>

                    <div className="asset-bottom">

                      <span>Load factor</span>

                      <strong>

                        {asset

                          ? Number(asset.load_factor).toFixed(2)

                          : "--"}

                        ×

                      </strong>

                    </div>

                    <div className="asset-bottom">

                      <span>Demo RUL</span>

                      <strong>

                        {asset?.demo_rul_hours != null

                          ? `${asset.demo_rul_hours} h`

                          : "--"}

                      </strong>

                    </div>

                    <div className="load-track">

                      <div

                        style={{

                          width: `${Math.min(

                            100,

                            ((asset?.load_factor || 0) / 1.5) * 100

                          )}%`,

                        }}

                      />

                    </div>

                  </button>

                );

              })}

            </div>

          </section>

          {/* AI model evaluation — outside the asset grid */}
          <section className="section-block" id="ai-evaluation">
            <AIEvaluationPanel />
          </section>

          {/* Fault injection demo — applies to the selected asset */}
          <section className="section-block" id="fault-demo">
            <FaultDemoPanel assetId={selected} />
          </section>

          {/* Live telemetry */}

          <section className="section-block" id="readings">

            <div className="section-heading">

              <div>

                <h2>Live telemetry</h2>

                <p>

                  Selected asset: <strong>{selected}</strong> ·

                  Automatically refreshed every 3 seconds.

                </p>

              </div>

              <span className="live-pill">

                <span className="live-dot" />

                LIVE SIMULATION

              </span>

            </div>

            <div className="metrics-grid">

              <MetricCard

                title="Voltage"

                value={

                  active

                    ? Number(active.voltage_kV).toFixed(2)

                    : "--"

                }

                unit="kV"

                icon={Zap}

                color="blue"

                note="Simulated voltage"

              />

              <MetricCard

                title="Current"

                value={

                  active

                    ? Number(active.current_A).toFixed(2)

                    : "--"

                }

                unit="A"

                icon={Activity}

                color="purple"

                note="Simulated current"

              />

              <MetricCard

                title="Temperature"

                value={

                  active

                    ? Number(active.temperature_C).toFixed(1)

                    : "--"

                }

                unit="°C"

                icon={Thermometer}

                color="orange"

                note="Thermal reading"

              />

              <MetricCard

                title="Vibration"

                value={

                  active

                    ? Number(active.vibration_mm_s).toFixed(2)

                    : "--"

                }

                unit="mm/s"

                icon={Waves}

                color="green"

                note="Vibration reading"

              />

            </div>

          </section>

          {/* Multi-sensor analytics */}
          <section className="section-block" id="sensor-analytics">
            <div className="section-heading">
              <div>
                <div className="eyebrow">TELEMETRY ANALYTICS</div>
                <h2>Sensor analytics</h2>
                <p>Recent backend history for {selected}. Synthetic readings for demonstration.</p>
              </div>
              <span className="section-count">{chartData.length} SAMPLES</span>
            </div>
            <div className="sensor-chart-grid">
              {[
                { key: "voltage_kV", title: "Voltage", unit: "kV", color: "#38bdf8" },
                { key: "current_A", title: "Current", unit: "A", color: "#a78bfa" },
                { key: "temperature_C", title: "Temperature", unit: "°C", color: "#fbbf24" },
                { key: "vibration_mm_s", title: "Vibration", unit: "mm/s", color: "#34d399" },
              ].map((metric) => (
                <article className="panel sensor-chart-card" key={metric.key}>
                  <div className="sensor-chart-heading">
                    <div><span>{metric.title}</span><strong>{active && Number.isFinite(Number(active[metric.key])) ? Number(active[metric.key]).toFixed(metric.key === "temperature_C" ? 1 : 2) : "—"} <small>{metric.unit}</small></strong></div>
                    <span className="sensor-chart-dot" style={{ background: metric.color }} />
                  </div>
                  <div className="sensor-chart">
                    {chartData.length ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                          <defs><linearGradient id={`fill-${metric.key}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={metric.color} stopOpacity={0.25}/><stop offset="100%" stopColor={metric.color} stopOpacity={0.01}/></linearGradient></defs>
                          <CartesianGrid stroke="#24364c" strokeDasharray="3 4" vertical={false}/>
                          <XAxis dataKey="sample" hide/>
                          <YAxis hide domain={["auto","auto"]}/>
                          <Tooltip contentStyle={{ background: "#0d1a2b", border: "1px solid #2b4058", borderRadius: 9, color: "#e7eef8", fontSize: 12 }} formatter={(value) => [`${Number(value).toFixed(2)} ${metric.unit}`, metric.title]}/>
                          <Area type="monotone" dataKey={metric.key} stroke={metric.color} strokeWidth={2.3} fill={`url(#fill-${metric.key})`} isAnimationActive={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : <div className="empty-chart">Collecting samples…</div>}
                  </div>
                  <div className="sensor-chart-foot"><span>History window</span><span>{chartData.length} samples</span></div>
                </article>
              ))}
            </div>
          </section>

          {/* CNN-LSTM AI prediction panel */}

          <section className="section-block" id="ai-model">

            <div className="section-heading">

              <div>

                <h2>CNN-LSTM AI Fault Prediction</h2>

                <p>

                  Experimental inference using the saved model

                  and training dataset.

                </p>

              </div>

              <span className="section-count">AI DEMO</span>

            </div>

            <article className="panel" style={{ padding: 24 }}>

              {aiLoading ? (

                <div className="empty-chart">

                  <LoaderCircle className="spin" />

                  Loading AI prediction...

                </div>

              ) : aiError ? (

                <div className="error-banner">

                  <AlertTriangle size={19} />

                  <div>

                    <strong>AI prediction unavailable</strong>

                    <p>{aiError}</p>

                  </div>

                  <button onClick={refreshAiPrediction}>

                    Retry

                  </button>

                </div>

              ) : (

                <>

                  <div

                    style={{

                      display: "flex",

                      gap: 16,

                      alignItems: "center",

                      flexWrap: "wrap",

                    }}

                  >

                    <div

                      style={{

                        width: 52,

                        height: 52,

                        borderRadius: 14,

                        display: "grid",

                        placeItems: "center",

                        background: "#eaf1ff",

                        color: "#3768e8",

                      }}

                    >

                      <BrainCircuit size={27} />

                    </div>

                    <div style={{ flex: 1, minWidth: 180 }}>

                      <div

                        style={{

                          color: "#7b879b",

                          fontSize: 12,

                          letterSpacing: 1,

                          fontWeight: 700,

                        }}

                      >

                        MODEL OUTPUT · DATASET DEMO

                      </div>

                      <h3 style={{ margin: "5px 0", fontSize: 23 }}>

                        {aiPrediction.predicted_label} class

                      </h3>

                      <div

                        style={{

                          color: "#75839a",

                          fontSize: 13,

                        }}

                      >

                        This is not a prediction from the live

                        virtual grid.

                      </div>

                    </div>

                  </div>

                  <div className="metrics-grid" style={{ marginTop: 20 }}>

                    <MetricCard

                      title="Fault probability"

                      value={(

                        aiPrediction.fault_probability * 100

                      ).toFixed(1)}

                      unit="%"

                      icon={AlertTriangle}

                      color="orange"

                      note="Model output"

                    />

                    <MetricCard

                      title="Normal probability"

                      value={(

                        aiPrediction.normal_probability * 100

                      ).toFixed(1)}

                      unit="%"

                      icon={CheckCircle2}

                      color="green"

                      note="Model output"

                    />

                  </div>

                  <div

                    style={{

                      display: "grid",

                      gridTemplateColumns:

                        "repeat(auto-fit, minmax(150px, 1fr))",

                      gap: 12,

                      marginTop: 18,

                    }}

                  >

                    <div className="summary-card">

                      <div>

                        <span>Sequence length</span>

                        <strong>

                          {aiPrediction.sequence_length} rows

                        </strong>

                      </div>

                    </div>

                    <div className="summary-card">

                      <div>

                        <span>Input features</span>

                        <strong>

                          {aiPrediction.features_used}

                        </strong>

                      </div>

                    </div>

                    <div className="summary-card">

                      <div>

                        <span>Live input</span>

                        <strong>No</strong>

                      </div>

                    </div>

                  </div>

                  <p

                    style={{

                      marginTop: 16,

                      color: "#75839a",

                      fontSize: 13,

                      lineHeight: 1.6,

                    }}

                  >

                    {aiPrediction.note}

                  </p>

                  <button

                    className="secondary-button"

                    onClick={refreshAiPrediction}

                    disabled={aiLoading}

                  >

                    Run prediction again

                  </button>

                </>

              )}

            </article>

          </section>

          {/* Recent AI alert checks */}

          <section className="section-block" id="alerts">

            <div className="section-heading">

              <div>

                <h2>Recent AI alert checks</h2>

                <p>Recent manual/initial CNN + LSTM prediction requests. These are dataset-demo results, not live grid alarms.</p>

              </div>

              <span className="section-count">{alertEvents.length} EVENTS</span>

            </div>

            <article className="panel" style={{ padding: 18 }}>

              {alertEvents.length === 0 ? (

                <p style={{ color: "#75839a", margin: 0 }}>No prediction checks recorded yet. Run a prediction to populate this list.</p>

              ) : (

                <div style={{ display: "grid", gap: 10 }}>

                  {alertEvents.map((event) => (

                    <div key={event.id} style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", padding: 12, border: "1px solid #e5eaf1", borderRadius: 10 }}>

                      {event.label === "FAULT" ? <AlertTriangle size={19} color="#b91c1c" /> : <CheckCircle2 size={19} color="#15803d" />}

                      <div style={{ flex: 1, minWidth: 180 }}>

                        <strong>{event.label}</strong>

                        <div style={{ fontSize: 12, color: "#75839a", marginTop: 3 }}>{event.time}</div>

                      </div>

                      <strong>{(event.probability * 100).toFixed(1)}% fault probability</strong>

                    </div>

                  ))}

                </div>

              )}

            </article>

          </section>

          {/* Sensor history */}

          <section className="content-grid" id="trends">

            <article className="panel chart-panel">

              <div className="panel-heading">

                <div>

                  <h2>Sensor history</h2>

                  <p>Recent samples for {selected}</p>

                </div>

                <div className="chart-legend">

                  <span className="legend-dot" />

                  Temperature °C

                </div>

              </div>

              <div className="chart-wrap">

                {chartData.length > 0 ? (

                  <ResponsiveContainer width="100%" height="100%">

                    <AreaChart data={chartData}>

                      <defs>

                        <linearGradient

                          id="temperatureFill"

                          x1="0"

                          y1="0"

                          x2="0"

                          y2="1"

                        >

                          <stop

                            offset="0%"

                            stopColor="#f59e0b"

                            stopOpacity={0.22}

                          />

                          <stop

                            offset="100%"

                            stopColor="#f59e0b"

                            stopOpacity={0.01}

                          />

                        </linearGradient>

                      </defs>

                      <CartesianGrid

                        stroke="#e8edf4"

                        strokeDasharray="4 4"

                        vertical={false}

                      />

                      <XAxis

                        dataKey="sample"

                        tick={{ fill: "#8490a3", fontSize: 11 }}

                        axisLine={false}

                        tickLine={false}

                      />

                      <YAxis

                        tick={{ fill: "#8490a3", fontSize: 11 }}

                        axisLine={false}

                        tickLine={false}

                        width={42}

                      />

                      <Tooltip

                        contentStyle={{

                          borderRadius: 12,

                          border: "1px solid #e2e8f0",

                          fontSize: 12,

                        }}

                      />

                      <Area

                        type="monotone"

                        dataKey="temperature_C"

                        name="Temperature °C"

                        stroke="#f59e0b"

                        strokeWidth={2.5}

                        fill="url(#temperatureFill)"

                      />

                    </AreaChart>

                  </ResponsiveContainer>

                ) : (

                  <div className="empty-chart">

                    {loading ? (

                      <LoaderCircle className="spin" />

                    ) : (

                      "Collecting sensor samples..."

                    )}

                  </div>

                )}

              </div>

              <div className="chart-foot">

                <span>

                  <span className="live-dot" />

                  Data from synthetic simulator

                </span>

                <span>{chartData.length} samples</span>

              </div>

            </article>

            {/* Simulation controls */}

            <article className="panel controls-panel" id="controls">

              <div className="panel-heading">

                <div>

                  <h2>Simulation controls</h2>

                  <p>Inject a fault into {selected}</p>

                </div>

                <div className="control-icon">

                  <Settings2 size={19} />

                </div>

              </div>

              <label className="field-label">Selected asset</label>

              <div className="selected-asset-field">

                <CircleGauge size={17} />

                <strong>{selected}</strong>

                <ChevronDown size={16} />

              </div>

              <label className="field-label range-label">

                Load factor

                <strong>

                  {controls[selected].load_factor.toFixed(2)}×

                </strong>

              </label>

              <input

                className="range-input"

                type="range"

                min="0.1"

                max="1.5"

                step="0.05"

                value={controls[selected].load_factor}

                onChange={(e) =>

                  updateControl("load_factor", Number(e.target.value))

                }

              />

              <div className="range-labels">

                <span>0.10× · Low</span>

                <span>1.50× · High</span>

              </div>

              <label className="field-label">Fault scenario</label>

              <select

                className="fault-select"

                value={controls[selected].fault}

                onChange={(e) =>

                  updateControl("fault", e.target.value)

                }

              >

                <option value="none">No fault</option>

                <option value="overload">Overload</option>

                <option value="overheating">Overheating</option>

                <option value="vibration">Excessive vibration</option>

                <option value="voltage_sag">Voltage sag</option>

              </select>

              <div className="control-buttons">

                <button

                  className="secondary-button"

                  onClick={resetAsset}

                  disabled={busy}

                >

                  Reset

                </button>

                <button

                  className="primary-button"

                  onClick={applyControls}

                  disabled={busy}

                >

                  {busy ? (

                    <LoaderCircle size={16} className="spin" />

                  ) : (

                    <Activity size={16} />

                  )}

                  Apply scenario

                </button>

              </div>

              <div className="demo-note">

                <AlertTriangle size={15} />

                <span>

                  Controls affect synthetic data only. No real

                  electrical equipment is controlled.

                </span>

              </div>

            </article>

          </section>

          {/* Health assessment */}

          <section className="section-block">

            <div className="section-heading">

              <div>

                <h2>Health assessment</h2>

                <p>

                  Rule-based demonstration status, not a trained

                  model prediction.

                </p>

              </div>

            </div>

            <div className="health-panel">

              <div className="health-left">

                <div

                  className={`health-emblem ${

                    active?.status || "normal"

                  }`}

                >

                  {active?.status === "critical" ||

                  active?.status === "warning" ? (

                    <AlertTriangle size={25} />

                  ) : (

                    <CheckCircle2 size={25} />

                  )}

                </div>

                <div>

                  <span className="muted-label">

                    CURRENT ASSET · {selected}

                  </span>

                  <h3>

                    {active?.status === "critical"

                      ? "Critical condition"

                      : active?.status === "warning"

                        ? "Attention required"

                        : "Operating normally"}

                  </h3>

                  <p>

                    Status calculated using simulator demonstration

                    thresholds.

                  </p>

                </div>

              </div>

              <div className="health-divider" />

              <div className="health-stat">

                <span>Demo RUL</span>

                <strong>

                  {active?.demo_rul_hours ?? "--"} <small>hours</small>

                </strong>

                <p>Placeholder rule-based value</p>

              </div>

              <div className="health-stat">

                <span>Model status</span>

                <strong className="model-not-ready">

                  <Cpu size={17} />

                  {aiLoading

                    ? "Loading..."

                    : aiPrediction

                      ? "Dataset demo loaded"

                      : "Unavailable"}

                </strong>

                <p>Not connected to live simulator inputs</p>

              </div>

            </div>

          </section>

          <footer className="page-footer">

            <span>

              © 2026 GridGuard AI Twin · Academic prototype

            </span>

            <span>

              <span className="live-dot" />

              Synthetic data · Demo thresholds · Not for operational

              decisions

            </span>

          </footer>

        </div>

      </main>

      <Chatbot

        asset={active}

        dashboard={dashboard}

        aiPrediction={aiPrediction}

       />

    </div>

  );

}
