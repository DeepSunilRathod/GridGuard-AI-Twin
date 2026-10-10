import plotly.graph_objects as go

ASSETS = ["TX-01", "TX-02", "TX-03"]

STATUS_COLORS = {
    "normal": "#22C55E",
    "warning": "#F59E0B",
    "critical": "#EF4444",
    "unknown": "#64748B",
}

BG = "#0B1220"
PANEL = "#111C2E"
WIRE = "#6F829B"
TEXT = "#E5EDF7"
MUTED = "#93A4BA"
CYAN = "#38BDF8"


def _line(fig, x0, y0, x1, y1, color=WIRE, width=3):
    fig.add_shape(
        type="line", x0=x0, y0=y0, x1=x1, y1=y1,
        line=dict(color=color, width=width), layer="below"
    )


def _label(fig, x, y, text, size=10, color=MUTED, bold=False, anchor="center"):
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=False,
        xanchor=anchor, yanchor="middle",
        font=dict(family="Arial, sans-serif", size=size, color=color),
        borderpad=2,
    )


def _panel(fig, x0, y0, x1, y1, fill=PANEL, line="#24344A"):
    fig.add_shape(
        type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
        fillcolor=fill, line=dict(color=line, width=1), layer="below"
    )


def build_grid_figure(status_by_asset=None, readings_by_asset=None,
                      selected_asset=None, breaker_by_asset=None):
    status_by_asset = status_by_asset or {}
    readings_by_asset = readings_by_asset or {}
    breaker_by_asset = breaker_by_asset or {}
    fig = go.Figure()

    _panel(fig, 0.15, 0.35, 12.85, 7.25, fill=BG, line=BG)
    _panel(fig, 0.45, 4.55, 12.55, 6.85, fill="#0E1929", line="#1E3047")
    _panel(fig, 0.45, 0.65, 12.55, 4.15, fill="#0E1929", line="#1E3047")

    _label(fig, 0.75, 6.48, "GRIDGUARD", size=18, color=TEXT, bold=True, anchor="left")
    _label(fig, 2.35, 6.48, "AI TWIN  /  SUBSTATION OVERVIEW", size=10, color=CYAN, bold=True, anchor="left")
    _label(fig, 12.2, 6.48, "SINGLE-LINE DIAGRAM", size=9, color=MUTED, anchor="right")
    _line(fig, 0.75, 6.15, 12.25, 6.15, color="#24344A", width=1)

    _panel(fig, 0.8, 5.05, 2.05, 5.75, fill="#14263B", line="#2A4563")
    _label(fig, 1.425, 5.52, "UTILITY GRID", size=10, color=TEXT, bold=True)
    _label(fig, 1.425, 5.25, "11 kV INCOMING", size=8)
    _line(fig, 2.05, 5.4, 2.75, 5.4, color=CYAN, width=4)

    _panel(fig, 2.75, 5.12, 3.35, 5.68, fill="#14263B", line="#2A4563")
    _label(fig, 3.05, 5.53, "CB-01", size=9, color=TEXT, bold=True)
    _line(fig, 2.82, 5.32, 3.28, 5.62, color=CYAN, width=3)
    _line(fig, 3.35, 5.4, 4.0, 5.4, color=CYAN, width=4)

    _line(fig, 4.0, 5.4, 11.95, 5.4, color=CYAN, width=7)
    for x in [4.75, 7.55, 10.35]:
        fig.add_trace(go.Scatter(
            x=[x], y=[5.4], mode="markers",
            marker=dict(size=10, color="#E0F2FE", line=dict(color=CYAN, width=2)),
            hoverinfo="skip", showlegend=False
        ))
    _label(fig, 8.0, 5.78, "11 kV MAIN BUSBAR", size=10, color=CYAN, bold=True)

    bay_x = {"TX-01": 4.75, "TX-02": 7.55, "TX-03": 10.35}
    for asset, x in bay_x.items():
        status = status_by_asset.get(asset, "unknown")
        if status not in STATUS_COLORS:
            status = "unknown"
        color = STATUS_COLORS[status]
        reading = readings_by_asset.get(asset, {})
        selected = asset == selected_asset
        border = CYAN if selected else "#2A3B52"
        bay_fill = "#142237" if selected else "#101C2D"
        _panel(fig, x - 1.12, 1.0, x + 1.12, 4.65, fill=bay_fill, line=border)

        breaker_closed = bool(breaker_by_asset.get(asset, True))
        _line(fig, x, 5.4, x, 4.12, color=CYAN, width=3)
        _panel(fig, x - 0.28, 3.72, x + 0.28, 4.12, fill="#16263A", line=("#3C506B" if breaker_closed else STATUS_COLORS["critical"]))
        if breaker_closed:
            _line(fig, x - 0.18, 3.78, x + 0.18, 4.04, color=CYAN, width=2)
            _line(fig, x, 3.72, x, 3.33, color=CYAN, width=3)
        else:
            _line(fig, x - 0.18, 3.78, x + 0.10, 3.90, color=STATUS_COLORS["critical"], width=2)
        _label(fig, x, 4.38, f"CB-{asset[-2:]} {'CLOSED' if breaker_closed else 'OPEN'}", size=7, color=(CYAN if breaker_closed else STATUS_COLORS["critical"]))

        fig.add_shape(
            type="circle", x0=x - 0.43, x1=x + 0.02, y0=2.88, y1=3.33,
            fillcolor="#14263A", line=dict(color=color, width=3)
        )
        fig.add_shape(
            type="circle", x0=x - 0.02, x1=x + 0.43, y0=2.88, y1=3.33,
            fillcolor="#14263A", line=dict(color=color, width=3)
        )
        _label(fig, x, 3.10, "T", size=13, color=TEXT, bold=True)
        _label(fig, x, 3.57, asset, size=12, color=TEXT, bold=True)

        fig.add_trace(go.Scatter(
            x=[x - 0.65], y=[2.47], mode="markers",
            marker=dict(size=10, color=color),
            hovertemplate=f"{asset}<br>Status: {status}<extra></extra>",
            showlegend=False,
        ))
        _label(fig, x - 0.48, 2.47, status.upper(), size=8, color=color, bold=True)
        def fmt(value, suffix, digits=1):
            return "—" if value is None else f"{float(value):.{digits}f}{suffix}"

        _line(fig, x - 0.88, 1.88, x + 0.88, 1.88, color="#2A3B52", width=1)
        _label(fig, x - 0.78, 1.58, f"I  {fmt(reading.get('current_A'), ' A')}", size=8, anchor="left")
        _label(fig, x + 0.12, 1.58, f"V  {fmt(reading.get('voltage_kV'), ' kV')}", size=8, anchor="left")
        _label(fig, x - 0.78, 1.30, f"T  {fmt(reading.get('temperature_C'), ' °C')}", size=8, anchor="left")
        _label(fig, x + 0.12, 1.30, f"a  {fmt(reading.get('vibration_mm_s'), ' mm/s')}", size=8, anchor="left")

        _line(fig, x, 2.88, x, 0.82, color=color if status != "unknown" else WIRE, width=3)
        _panel(fig, x - 0.62, 0.77, x + 0.62, 1.02, fill="#14263B", line="#2A4563")
        _label(fig, x, 0.895, f"FEEDER {asset[-2:]}", size=8, color=TEXT, bold=True)

    _line(fig, 0.75, 0.52, 12.25, 0.52, color="#24344A", width=1)
    legend = [("NORMAL", STATUS_COLORS["normal"]), ("WARNING", STATUS_COLORS["warning"]),
              ("CRITICAL", STATUS_COLORS["critical"]), ("UNKNOWN", STATUS_COLORS["unknown"])]
    x0 = 1.0
    for label, color in legend:
        fig.add_trace(go.Scatter(
            x=[x0], y=[0.22], mode="markers",
            marker=dict(size=9, color=color),
            showlegend=False, hoverinfo="skip"
        ))
        _label(fig, x0 + 0.18, 0.22, label, size=8, bold=True, anchor="left")
        x0 += 1.55
    _label(fig, 12.1, 0.22, "SIMULATED DATA", size=8, color="#FBBF24", bold=True, anchor="right")

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Arial, sans-serif", color=TEXT),
        height=760, margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False, hovermode="closest",
        xaxis=dict(visible=False, range=[0, 13], fixedrange=True),
        yaxis=dict(visible=False, range=[0, 7.5], fixedrange=True, scaleanchor="x", scaleratio=1),
    )
    return fig
