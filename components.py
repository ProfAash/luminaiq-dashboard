# --- append to your existing components.py (or replace the file with this full version) ---

import uuid
from html import escape
import streamlit as st

def kpi(label: str, value: str, delta: str | None = None) -> None:
    """
    Thin wrapper around st.metric so pages can `from components import kpi`.
    """
    st.metric(label, value, delta)


# ==============================
# base helpers & styles (same as before; keep or replace your previous block)
# ==============================
def _ensure_styles():
    if st.session_state.get("_kpi_css_injected"):
        return
    st.session_state["_kpi_css_injected"] = True

    st.markdown(
        """
        <style>
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
        }
        .kpi-card {
          border-radius: 14px;
          padding: 14px 16px;
          border: 1px solid var(--border-color, rgba(49, 51, 63, 0.2));
          background: var(--bg-color, rgba(255,255,255,0.6));
          box-shadow: 0 1px 1px rgba(0,0,0,0.04);
        }
        .kpi-compact { padding: 10px 14px; }
        @media (prefers-color-scheme: dark) {
          .kpi-card {
            --bg-color: rgba(255,255,255,0.05);
            --border-color: rgba(250, 250, 250, 0.15);
          }
        }
        .kpi-top {
          display:flex; align-items:center; gap:8px; margin-bottom:6px;
          color: var(--label-color, #6b7280); font-size: 0.80rem;
        }
        .kpi-icon {
          width: 26px; height: 26px; border-radius: 8px;
          display: inline-flex; align-items:center; justify-content:center;
          font-size: 14px; font-weight: 600; color: white;
        }
        .kpi-value {
          font-size: 1.45rem; line-height: 1.2; font-weight: 700;
          letter-spacing: -0.01em;
        }
        .kpi-row {
          display:flex; align-items: baseline; justify-content: space-between; gap: 8px;
        }
        .kpi-delta { font-size: 0.95rem; font-weight: 600; }
        .kpi-delta.up { color: #16a34a; }
        .kpi-delta.down { color: #dc2626; }
        .kpi-delta.neutral { color: #6b7280; }

        /* accents */
        .accent-blue   { background: #3b82f6; }
        .accent-rose   { background: #f43f5e; }
        .accent-amber  { background: #f59e0b; }
        .accent-emerald{ background: #10b981; }
        .accent-violet { background: #8b5cf6; }

        /* progress (single) */
        .kpi-meta {
          margin-top: 8px;
          font-size: 0.8rem;
          color: var(--label-color, #6b7280);
          display: flex; justify-content: space-between;
        }
        .kpi-progress-track {
          position: relative; height: 8px; border-radius: 999px;
          background: rgba(0,0,0,0.08); overflow: hidden; margin-top: 6px;
        }
        @media (prefers-color-scheme: dark) {
          .kpi-progress-track { background: rgba(255,255,255,0.12); }
        }
        .kpi-progress-fill {
          height: 100%; width: 0%; border-radius: 999px; transition: width 300ms ease;
        }
        .fill-blue   { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
        .fill-rose   { background: linear-gradient(90deg, #f43f5e, #fb7185); }
        .fill-amber  { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .fill-emerald{ background: linear-gradient(90deg, #10b981, #34d399); }
        .fill-violet { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }

        /* stacked progress */
        .kpi-progress-track-2 { position: relative; height: 10px; border-radius: 999px;
          background: rgba(0,0,0,0.08); overflow: hidden; margin-top: 6px; }
        @media (prefers-color-scheme: dark) {
          .kpi-progress-track-2 { background: rgba(255,255,255,0.12); }
        }
        .kpi-progress-fill.soft { opacity: 0.45; }
        .kpi-submeta { display:flex; gap:10px; margin-top:6px; font-size:0.78rem; color:#6b7280; }
        .kpi-dot { width:8px; height:8px; border-radius:999px; display:inline-block; transform: translateY(1px);}
        .dot-blue{background:#3b82f6;} .dot-rose{background:#f43f5e;}
        .dot-amber{background:#f59e0b;} .dot-emerald{background:#10b981;} .dot-violet{background:#8b5cf6;}

        /* sparkline */
        .spark-wrap { margin-top: 8px; }
        .spark-legend { display:flex; justify-content: space-between; font-size:0.78rem; color:#6b7280; }
        .spark-svg { width:100%; height:42px; display:block; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _delta_class(delta: str | None) -> str:
    if not delta:
        return "neutral"
    d = delta.strip()
    if d.startswith("+"): return "up"
    if d.startswith("-"): return "down"
    try:
        f = float(d.replace("%",""))
        if f > 0: return "up"
        if f < 0: return "down"
    except Exception:
        pass
    return "neutral"

def _accent_class(color: str) -> str:
    return {
        "blue": "accent-blue",
        "rose": "accent-rose",
        "amber": "accent-amber",
        "emerald": "accent-emerald",
        "violet": "accent-violet",
    }.get(color, "accent-blue")

def _fill_class(color: str) -> str:
    return {
        "blue": "fill-blue",
        "rose": "fill-rose",
        "amber": "fill-amber",
        "emerald": "fill-emerald",
        "violet": "fill-violet",
    }.get(color, "fill-blue")

def _dot_class(color: str) -> str:
    return {
        "blue":"dot-blue","rose":"dot-rose","amber":"dot-amber","emerald":"dot-emerald","violet":"dot-violet"
    }.get(color, "dot-blue")

# =================
# existing exports
# =================
def kpi(label, value, delta=None, *, icon=None, color="blue", help=None, compact=False):
    _ensure_styles()
    label_safe = escape(str(label)); value_safe = escape(f"{value}")
    delta_safe = escape(delta) if delta is not None else None
    icon_safe  = escape(icon) if icon else ""
    uid = uuid.uuid4().hex[:8]
    delta_cls = _delta_class(delta); icon_cls  = _accent_class(color)
    compact_cls = "kpi-compact" if compact else ""
    st.markdown(
        f"""
        <div class="kpi-card {compact_cls}" id="kpi-{uid}">
          <div class="kpi-top" title="{escape(help) if help else ''}">
            {("<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>") if icon_safe else ""}
            <div>{label_safe}</div>
          </div>
          <div class="kpi-row">
            <div class="kpi-value">{value_safe}</div>
            {("<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>") if delta_safe else ""}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def kpi_grid(items: list[dict]):
    _ensure_styles()
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    for it in items:
        kpi(
            it.get("label",""), it.get("value",""), it.get("delta"),
            icon=it.get("icon"), color=it.get("color","blue"),
            help=it.get("help"), compact=it.get("compact",False)
        )
    st.markdown("</div>", unsafe_allow_html=True)

def kpi_progress(label, value, target, *, units=None, delta=None, icon=None,
                 color="blue", help=None, compact=False, clamp_overflow=True, show_percent=True):
    _ensure_styles()
    uid = uuid.uuid4().hex[:8]
    icon_cls = _accent_class(color); fill_cls = _fill_class(color)
    compact_cls = "kpi-compact" if compact else ""

    try: v = float(value)
    except Exception: v = 0.0
    try: t = float(target)
    except Exception: t = 0.0

    pct = 0.0 if t == 0 else (v/t*100.0)
    pct_bar = max(0,min(100,pct)) if clamp_overflow else max(0,pct)
    pct_display = f"{pct:.0f}%"

    label_safe = escape(str(label)); units_safe = escape(units) if units else ""
    icon_safe = escape(icon) if icon else ""; help_safe = escape(help) if help else ""
    delta_safe = escape(delta) if delta else None; delta_cls=_delta_class(delta)
    value_txt = f"{v:,.0f}{units_safe}" if units else f"{v:,.0f}"
    target_txt= f"{t:,.0f}{units_safe}" if units else f"{t:,.0f}"
    ratio_txt = f"{value_txt} / {target_txt}" + (f" ({pct_display})" if show_percent else "")

    st.markdown(
        f"""
        <div class="kpi-card {compact_cls}" id="kpi-prog-{uid}">
          <div class="kpi-top" title="{help_safe}">
            {("<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>") if icon_safe else ""}
            <div>{label_safe}</div>
          </div>
          <div class="kpi-row">
            <div class="kpi-value">{value_txt}</div>
            {("<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>") if delta_safe else ""}
          </div>
          <div class="kpi-meta">
            <div>{ratio_txt}</div><div>Target</div>
          </div>
          <div class="kpi-progress-track">
            <div class="kpi-progress-fill {fill_cls}" style="width:{pct_bar:.2f}%"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================
# NEW: stacked progress (Actual vs Previous)
# =========================================
def kpi_progress_stacked(
    label: str,
    actual: float | int,
    previous: float | int,
    target: float | int,
    *,
    units: str | None = None,
    delta: str | None = None,
    icon: str | None = None,
    color: str = "blue",        # actual color
    prev_color: str = "amber",  # previous color
    help: str | None = None,
    compact: bool = False,
    clamp_overflow: bool = True,
):
    """
    Two progress bars on a single track:
      - top (strong): Actual vs Target
      - bottom (soft): Previous vs Target
    Great for 'This period vs Last period' against a common target.
    """
    _ensure_styles()
    uid = uuid.uuid4().hex[:8]
    icon_cls = _accent_class(color)
    fill_actual = _fill_class(color)
    fill_prev   = _fill_class(prev_color)
    dot_actual  = _dot_class(color)
    dot_prev    = _dot_class(prev_color)
    compact_cls = "kpi-compact" if compact else ""

    def _f(x):
        try: return float(x)
        except Exception: return 0.0

    a = _f(actual); p = _f(previous); t = _f(target)
    pct_a = 0.0 if t == 0 else (a/t*100.0)
    pct_p = 0.0 if t == 0 else (p/t*100.0)
    if clamp_overflow:
        pct_a = max(0,min(100,pct_a))
        pct_p = max(0,min(100,pct_p))

    units_safe = escape(units) if units else ""
    a_txt = f"{a:,.0f}{units_safe}" if units else f"{a:,.0f}"
    p_txt = f"{p:,.0f}{units_safe}" if units else f"{p:,.0f}"
    t_txt = f"{t:,.0f}{units_safe}" if units else f"{t:,.0f}"

    label_safe = escape(label); icon_safe = escape(icon) if icon else ""
    help_safe  = escape(help) if help else ""
    delta_safe = escape(delta) if delta else None; delta_cls=_delta_class(delta)

    st.markdown(
        f"""
        <div class="kpi-card {compact_cls}" id="kpi-prog2-{uid}">
          <div class="kpi-top" title="{help_safe}">
            {("<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>") if icon_safe else ""}
            <div>{label_safe}</div>
          </div>
          <div class="kpi-row">
            <div class="kpi-value">{a_txt}</div>
            {("<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>") if delta_safe else ""}
          </div>

          <div class="kpi-meta"><div>Actual / Target ({a_txt} / {t_txt})</div><div>Target</div></div>
          <div class="kpi-progress-track-2">
            <div class="kpi-progress-fill {fill_prev} soft" style="width:{pct_p:.2f}%"></div>
            <div class="kpi-progress-fill {fill_actual}" style="width:{pct_a:.2f}%"></div>
          </div>

          <div class="kpi-submeta">
            <span><span class="kpi-dot {dot_actual}"></span> Actual</span>
            <span><span class="kpi-dot {dot_prev}"></span> Previous</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================
# NEW: KPI with inline sparkline trend (SVG)
# =========================================
def kpi_sparkline(
    label: str,
    value: float | int | str,
    series: list[float] | tuple[float, ...],
    *,
    delta: str | None = None,
    units: str | None = None,
    icon: str | None = None,
    color: str = "emerald",
    help: str | None = None,
    compact: bool = False,
    area: bool = False,
):
    """
    KPI with a tiny sparkline underneath. No external libs; pure SVG.
    `series` is a sequence of numbers (recent → last).
    """
    _ensure_styles()
    uid = uuid.uuid4().hex[:8]
    icon_cls = _accent_class(color)
    dot_cls  = _dot_class(color)
    compact_cls = "kpi-compact" if compact else ""

    # value text
    try:
        v = float(value) if isinstance(value, (int, float, str)) else value
        v_txt = f"{v:,.0f}{escape(units) if units else ''}" if isinstance(v,(int,float)) else escape(str(v))
    except Exception:
        v_txt = escape(str(value))

    # build sparkline path
    pts = list(series) if series else [0.0, 0.0]
    n = len(pts)
    w, h, pad = 120.0, 30.0, 2.0
    xmin, xmax = 0, max(1, n-1)
    ymin, ymax = min(pts), max(pts)
    yrange = (ymax - ymin) or 1.0

    def sx(i): return pad + (w-2*pad) * (i - xmin) / (xmax - xmin)
    def sy(val): return pad + (h-2*pad) * (1.0 - (val - ymin)/yrange)

    path_d = " ".join([("M" if i==0 else "L") + f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(pts)])

    # area fill path (optional)
    area_d = f"{path_d} L{sx(n-1):.1f},{h-pad:.1f} L{sx(0):.1f},{h-pad:.1f} Z" if area else ""

    label_safe = escape(label)
    icon_safe  = escape(icon) if icon else ""
    help_safe  = escape(help) if help else ""
    delta_safe = escape(delta) if delta else None
    delta_cls  = _delta_class(delta)

    # pick line color (CSS variables not available in SVG; use fixed palette)
    stroke_map = {
        "blue":"#3b82f6","rose":"#f43f5e","amber":"#f59e0b","emerald":"#10b981","violet":"#8b5cf6"
    }
    stroke = stroke_map.get(color, "#10b981")

    st.markdown(
        f"""
        <div class="kpi-card {compact_cls}" id="kpi-spark-{uid}">
          <div class="kpi-top" title="{help_safe}">
            {("<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>") if icon_safe else ""}
            <div>{label_safe}</div>
          </div>
          <div class="kpi-row">
            <div class="kpi-value">{v_txt}</div>
            {("<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>") if delta_safe else ""}
          </div>

          <div class="spark-wrap">
            <svg class="spark-svg" viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none">
              {"<path d='" + area_d + "' fill='" + stroke + "22' stroke='none'/>" if area_d else ""}
              <path d="{path_d}" fill="none" stroke="{stroke}" stroke-width="2.0" stroke-linejoin="round" stroke-linecap="round"/>
            </svg>
            <div class="spark-legend">
              <span><span class="kpi-dot {dot_cls}"></span> Trend</span>
              <span>Last {n}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

