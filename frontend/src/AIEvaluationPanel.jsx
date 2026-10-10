import { useEffect, useState } from "react";
import { RefreshCw, BrainCircuit, AlertTriangle } from "lucide-react";

const API = "http://127.0.0.1:8000";

function Metric({ label, value }) {
  return <div className="gg-eval-metric"><span>{label}</span><strong>{value == null ? "—" : `${(value * 100).toFixed(1)}%`}</strong></div>;
}

export default function AIEvaluationPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadEvaluation() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API}/api/ai/evaluation`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Could not load evaluation results.");
      setData(body);
    } catch (err) {
      setError(err.message || "Evaluation API unavailable.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const id = setTimeout(() => { void loadEvaluation(); }, 0);
    return () => clearTimeout(id);
  }, []);

  const cm = data?.confusion_matrix?.matrix;

  return (
    <section className="panel gg-evaluation-panel" id="ai-evaluation">
      <div className="gg-eval-heading">
        <div>
          <h2><BrainCircuit size={20} /> AI model evaluation</h2>
          <p>Saved 1D CNN + LSTM · held-out evaluation output</p>
        </div>
        <button type="button" onClick={loadEvaluation} disabled={loading}>
          <RefreshCw size={15} /> Refresh
        </button>
      </div>

      {loading && <p>Loading evaluation metrics…</p>}
      {error && <div className="gg-eval-error"><AlertTriangle size={17} /><div><strong>Evaluation not available</strong><p>{error}</p><p>Run <code>python ml\evaluate_cnn_lstm.py</code> from the project root first.</p></div></div>}

      {data && !loading && (
        <>
          <div className="gg-eval-metrics">
            <Metric label="Accuracy" value={data.accuracy} />
            <Metric label="Balanced accuracy" value={data.balanced_accuracy} />
            <Metric label="Fault precision" value={data.fault_precision} />
            <Metric label="Fault recall" value={data.fault_recall} />
            <Metric label="Fault F1-score" value={data.fault_f1} />
          </div>

          <h3>Confusion matrix</h3>
          {cm && cm.length === 2 && (
            <div className="gg-confusion-wrap">
              <table className="gg-confusion">
                <thead><tr><th>Actual ↓ / Predicted →</th><th>Normal</th><th>Fault</th></tr></thead>
                <tbody>
                  <tr><th>Normal</th><td>{cm[0][0]}</td><td>{cm[0][1]}</td></tr>
                  <tr><th>Fault</th><td>{cm[1][0]}</td><td>{cm[1][1]}</td></tr>
                </tbody>
              </table>
            </div>
          )}

          <p className="gg-eval-sample">Test samples: {data.test_samples} · Window: {data.sequence_length} samples · Features: {data.features}</p>
          <div className="gg-eval-caveat"><strong>Evaluation caveat</strong><p>{data.caveat}</p></div>
          {data.classification_report && <details><summary>Classification report</summary><pre>{data.classification_report}</pre></details>}
        </>
      )}
    </section>
  );
}
