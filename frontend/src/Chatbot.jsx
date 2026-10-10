import { useState } from "react";
import { Bot, MessageCircle, Send, X, LoaderCircle, UserRound } from "lucide-react";

const API = "http://127.0.0.1:8000";

const suggestions = [
  "Explain the current asset readings",
  "What does the fault probability mean?",
  "How can I reduce transformer overheating?",
];

export default function Chatbot({ asset, dashboard, aiPrediction }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm GridGuard Assistant. I can explain the selected asset's readings, simulator warnings, and the CNN-LSTM dataset-demo prediction. I won't treat demo predictions as confirmed live faults.",
    },
  ]);

  async function sendMessage(text = input) {
    const message = text.trim();
    if (!message || sending) return;

    const nextMessages = [...messages, { role: "user", content: message }];
    setMessages(nextMessages);
    setInput("");
    setError("");
    setSending(true);

    try {
      const response = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          context: {
            selected_asset: asset || null,
            dashboard_summary: dashboard?.summary || null,
            assets: dashboard?.assets || [],
            cnn_lstm_prediction: aiPrediction || null,
            prediction_source: "CSV dataset demo; not live simulator input",
          },
          history: nextMessages
            .filter((item) => item.role === "user" || item.role === "assistant")
            .slice(-8)
            .map(({ role, content }) => ({ role, content })),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `Chat API returned ${response.status}`);
      }

      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.reply },
      ]);
    } catch (err) {
      setError(
        err.message ||
          "Could not reach the assistant. Check the backend and Gemini API key."
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      {open && (
        <section className="gg-chat-window" aria-label="GridGuard AI assistant">
          <header className="gg-chat-header">
            <div className="gg-chat-brand">
              <span className="gg-chat-avatar"><Bot size={20} /></span>
              <div>
                <strong>GridGuard Assistant</strong>
                <small>Asset-aware AI help</small>
              </div>
            </div>
            <button className="gg-chat-icon-button" onClick={() => setOpen(false)} aria-label="Close chatbot">
              <X size={19} />
            </button>
          </header>

          <div className="gg-chat-context">
            Context: {asset?.asset_id || "No asset selected"} · simulator readings + AI demo output
          </div>

          <div className="gg-chat-messages" aria-live="polite">
            {messages.map((item, index) => (
              <div className={`gg-chat-message ${item.role}`} key={`${index}-${item.role}`}>
                <span className="gg-chat-message-icon">
                  {item.role === "assistant" ? <Bot size={15} /> : <UserRound size={15} />}
                </span>
                <div className="gg-chat-bubble">{item.content}</div>
              </div>
            ))}
            {sending && (
              <div className="gg-chat-thinking">
                <LoaderCircle size={15} className="gg-chat-spinner" />
                GridGuard is thinking…
              </div>
            )}
            {error && <div className="gg-chat-error">{error}</div>}
          </div>

          {messages.length === 1 && (
            <div className="gg-chat-suggestions">
              {suggestions.map((suggestion) => (
                <button key={suggestion} onClick={() => sendMessage(suggestion)} disabled={sending}>
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form
            className="gg-chat-input-row"
            onSubmit={(event) => {
              event.preventDefault();
              void sendMessage();
            }}
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about readings or faults…"
              aria-label="Message GridGuard Assistant"
              maxLength={1500}
              disabled={sending}
            />
            <button type="submit" aria-label="Send message" disabled={sending || !input.trim()}>
              {sending ? <LoaderCircle size={18} className="gg-chat-spinner" /> : <Send size={18} />}
            </button>
          </form>
          <footer className="gg-chat-disclaimer">
            Prototype assistant. Verify recommendations before acting.
          </footer>
        </section>
      )}

      <button
        className={`gg-chat-launcher ${open ? "is-open" : ""}`}
        onClick={() => setOpen((value) => !value)}
        aria-label={open ? "Close GridGuard Assistant" : "Open GridGuard Assistant"}
        title="Ask GridGuard Assistant"
      >
        {open ? <X size={23} /> : <MessageCircle size={23} />}
        {!open && <span>Ask AI</span>}
      </button>
    </>
  );
}
