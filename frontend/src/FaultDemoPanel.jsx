import { useState } from "react";
import { AlertTriangle, Play, RotateCcw, CheckCircle2 } from "lucide-react";

const API = "http://127.0.0.1:8000";

const scenarios = [
  { value: "none", label: "Normal operation", load: 0.75 },
  { value: "overload", label: "Overload", load: 1.25 },
  { value: "overheating", label: "Overheating", load: 1.0 },
  { value: "vibration", label: "High vibration", load: 0.9 },
  { value: "voltage_sag", label: "Voltage sag", load: 0.8 },
];

export default function FaultDemoPanel({ assetId, onApplied }) {
  const [scenario, setScenario] = useState("overload");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function applyScenario(value = scenario) {
    if (!assetId) {
      setError("Select an asset before applying a demo scenario.");
      return;
    }
    const chosen = scenarios.find((item) => item.value === value) || scenarios[1];
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const response = await fetch(`${API}/api/assets/${encodeURIComponent(assetId)}/controls`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ load_factor: chosen.load, fault: chosen.value }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || "Could not apply scenario");
      setMessage(`${assetId}: ${chosen.label} scenario applied.`);
      if (onApplied) onApplied(data);
    } catch (err) {
      setError(err.message || "Failed to apply scenario.");
    } finally {
      setBusy(false);
    }
  }

  async function resetScenario() {
    if (!assetId) return setError("Select an asset before resetting.");
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const response = await fetch(`${API}/api/assets/${encodeURIComponent(assetId)}/reset`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Reset failed");
      setScenario("none");
      setMessage(`${assetId} simulator reset.`);
      if (onApplied) onApplied(data);
    } catch (err) {
      setError(err.message || "Reset failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel gg-fault-demo" aria-label="Interactive fault demonstration">
      <div className="gg-fault-demo-heading">
        <div>
          <h2>Interactive fault demo</h2>
          <p>Inject a synthetic fault and watch the simulator status and readings respond.</p>
        </div>
        <span className="gg-fault-demo-tag">SIMULATION ONLY</span>
      </div>
      <div className="gg-fault-demo-controls">
        <label htmlFor="gg-fault-scenario">Scenario</label>
        <select id="gg-fault-scenario" value={scenario} onChange={(event) => setScenario(event.target.value)} disabled={busy}>
          {scenarios.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <button type="button" onClick={() => applyScenario()} disabled={busy}>
          <Play size={16} /> {busy ? "Applying…" : "Apply scenario"}
        </button>
        <button type="button" className="gg-fault-reset" onClick={resetScenario} disabled={busy}>
          <RotateCcw size={16} /> Reset asset
        </button>
      </div>
      {message && <p className="gg-fault-success"><CheckCircle2 size={16} />{message}</p>}
      {error && <p className="gg-fault-error"><AlertTriangle size={16} />{error}</p>}
      <p className="gg-fault-demo-note">These controls alter synthetic simulator data only. They do not control physical equipment, and they do not make the CSV-based CNN-LSTM prediction live.</p>
    </section>
  );
}
