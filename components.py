# components.py
import streamlit as st
from components import kpi

def kpi(label: str, value: str, delta: str | None = None, help: str | None = None):
    """Small wrapper so KPIs look consistent across pages."""
    st.metric(label, value, delta=delta, help=help)

# components.py
import uuid
from html import escape
import streamlit as st

# ==============================
# Internal helpers & base styles
# ==============================
def _ensure_styles():
    if st.session_state.get("_kpi_css_injected"):
        return
    st.session_state["_kpi_css_injected"] = True

    st.markdown(
        """
        <style>
        /* ---------- Layout helpers ---------- */
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
        }

        /* ---------- KPI Card ---------- */
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

        .kpi-delta {
          font-size: 0.95rem; font-weight: 600;
        }

        .kpi-delta.up { color: #16a34a; }     /* green-600 */
        .kpi-delta.down { color: #dc2626; }   /* red-600 */
        .kpi-delta.neutral { color: #6b7280; }/* gray-500 */

        /* ---------- Accent colors ---------- */
        .accent-blue   { background: #3b82f6; }
        .accent-rose   { background: #f43f5e; }
        .accent-amber  { background: #f59e0b; }
        .accent-emerald{ background: #10b981; }
        .accent-violet { background: #8b5cf6; }

        /* ---------- Progress KPI ---------- */
        .kpi-meta {
          margin-top: 8px;
          font-size: 0.8rem;
          color: var(--label-color, #6b7280);
          display: flex;
          justify-content: space-between;
        }

        .kpi-progress-track {
          position: relative;
          height: 8px;
          border-radius: 999px;
          background: rgba(0,0,0,0.08);
          overflow: hidden;
          margin-top: 6px;
        }

        @media (prefers-color-scheme: dark) {
          .kpi-progress-track { background: rgba(255,255,255,0.12); }
        }

        .kpi-progress-fill {
          height: 100%;
          width: 0%;
          border-radius: 999px;
          transition: width 300ms ease;
        }

        /* Fill colors (match icon accents) */
        .fill-blue   { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
        .fill-rose   { background: linear-gradient(90deg, #f43f5e, #fb7185); }
        .fill-amber  { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .fill-emerald{ background: linear-gradient(90deg, #10b981, #34d399); }
        .fill-violet { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _delta_class(delta: str | None) -> str:
    if not delta:
        return "neutral"
    d = delta.strip()
    if d.startswith("+"):
        return "up"
    if d.startswith("-"):
        return "down"
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

# =================
# Public components
# =================
def kpi(
    label: str,
    value: str | int | float,
    delta: str | None = None,
    *,
    icon: str | None = None,
    color: str = "blue",
    help: str | None = None,
    compact: bool = False,
):
    """Card-style KPI with optional icon and delta."""
    _ensure_styles()

    label_safe = escape(str(label))
    value_safe = escape(f"{value}")
    delta_safe = escape(delta) if delta is not None else None
    icon_safe  = escape(icon) if icon else ""
    uid = uuid.uuid4().hex[:8]

    delta_cls = _delta_class(delta)
    icon_cls  = _accent_class(color)
    compact_cls = "kpi-compact" if compact else ""

    html = f"""
    <div class="kpi-card {compact_cls}" id="kpi-{uid}">
      <div class="kpi-top" title="{escape(help) if help else ''}">
        {"<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>" if icon_safe else ""}
        <div>{label_safe}</div>
      </div>
      <div class="kpi-row">
        <div class="kpi-value">{value_safe}</div>
        {"<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>" if delta_safe else ""}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def kpi_grid(items: list[dict]):
    """Render multiple KPIs in a responsive grid."""
    _ensure_styles()
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    for it in items:
        kpi(
            label=it.get("label", ""),
            value=it.get("value", ""),
            delta=it.get("delta"),
            icon=it.get("icon"),
            color=it.get("color", "blue"),
            help=it.get("help"),
            compact=it.get("compact", False),
        )
    st.markdown("</div>", unsafe_allow_html=True)


def kpi_progress(
    label: str,
    value: float | int,
    target: float | int,
    *,
    units: str | None = None,
    delta: str | None = None,
    icon: str | None = None,
    color: str = "blue",
    help: str | None = None,
    compact: bool = False,
    clamp_overflow: bool = True,
    show_percent: bool = True,
):
    """
    KPI with a mini progress bar for target tracking.

    Args:
      label:   Title (e.g., "Revenue vs Target").
      value:   Actual numeric value.
      target:  Target numeric value (0 handled).
      units:   Optional unit suffix (e.g. "$", "hrs").
      delta:   Optional change indicator (e.g., "+4.2%").
      icon:    Optional emoji/text icon.
      color:   Accent color for bar/icon (blue|rose|amber|emerald|violet).
      help:    Tooltip text.
      compact: Smaller padding.
      clamp_overflow: If True, caps bar at 100% width (still shows >100% in text).
      show_percent: Show `(XX%)` beside the ratio text.
    """
    _ensure_styles()

    uid = uuid.uuid4().hex[:8]
    icon_cls = _accent_class(color)
    fill_cls = _fill_class(color)
    compact_cls = "kpi-compact" if compact else ""

    # Robust ratio calculation
    try:
        v = float(value)
    except Exception:
        v = 0.0
    try:
        t = float(target)
    except Exception:
        t = 0.0

    pct = 0.0 if t == 0 else (v / t * 100.0)
    pct_display = f"{pct:.0f}%"
    pct_bar = max(0.0, min(100.0, pct)) if clamp_overflow else max(0.0, pct)

    # Build label row
    label_safe = escape(str(label))
    units_safe = escape(units) if units else ""
    icon_safe  = escape(icon) if icon else ""
    help_safe  = escape(help) if help else ""
    delta_safe = escape(delta) if delta else None
    delta_cls  = _delta_class(delta)

    value_txt  = f"{v:,.0f}{units_safe}" if units else f"{v:,.0f}"
    target_txt = f"{t:,.0f}{units_safe}" if units else f"{t:,.0f}"
    ratio_txt  = f"{value_txt} / {target_txt}" + (f"  ({pct_display})" if show_percent else "")

    html = f"""
    <div class="kpi-card {compact_cls}" id="kpi-prog-{uid}">
      <div class="kpi-top" title="{help_safe}">
        {"<div class='kpi-icon " + icon_cls + "'>" + icon_safe + "</div>" if icon_safe else ""}
        <div>{label_safe}</div>
      </div>

      <div class="kpi-row">
        <div class="kpi-value">{value_txt}</div>
        {"<div class='kpi-delta " + delta_cls + "'>" + delta_safe + "</div>" if delta_safe else ""}
      </div>

      <div class="kpi-meta">
        <div>{ratio_txt}</div>
        <div>Target</div>
      </div>

      <div class="kpi-progress-track">
        <div class="kpi-progress-fill {fill_cls}" style="width:{pct_bar:.2f}%"></div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
