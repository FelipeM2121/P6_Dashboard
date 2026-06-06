"""
charts.py — Plotly chart builders for Galpon Minero P6 Dashboard.
Power BI Executive style: clean white surfaces, minimal grid, Inter/Segoe UI font.
"""
from __future__ import annotations

import os
from collections import defaultdict
from datetime import timedelta
from typing import Optional

import plotly.graph_objects as go
import plotly.figure_factory as ff

from .xer_parser import parse_xer, P6Project, WBSNode

# ---------------------------------------------------------------------------
# Design tokens (Power BI executive palette) — inline to avoid circular deps
# ---------------------------------------------------------------------------
PRIMARY   = "#0078D4"
SUCCESS   = "#107C10"
WARNING   = "#FF8C00"
DANGER    = "#D13438"
PURPLE    = "#7719AA"
NEUTRAL   = "#605E5C"
BG        = "#F3F4F6"
SURFACE   = "#FFFFFF"
BORDER    = "#E1E4E8"
GRID      = "#F0F0F0"
TEXT      = "#252423"
TEXT_SEC  = "#605E5C"
FONT      = "Inter, Segoe UI, system-ui, sans-serif"

CHART_PALETTE = [
    "#0078D4", "#107C10", "#FF8C00", "#D13438", "#7719AA",
    "#00B4D8", "#038387", "#CA5010", "#8764B8", "#4F6BED",
]

PHASE_COLORS = {
    "FASE 1: INGENIERÍA Y PERMISOS":                       "#0078D4",
    "FASE 2: OBRAS CIVILES - FUNDACIONES Y LOSA":          "#FF8C00",
    "FASE 3: ESTRUCTURA METÁLICA Y CUBIERTA":              "#107C10",
    "FASE 4: INSTALACIONES (EE + SS + CI + VENT)":         "#D13438",
    "FASE 5: EQUIPAMIENTO INTERIOR Y TERMINACIONES":       "#7719AA",
    "FASE 6: GESTIÓN DE PROYECTO Y CIERRE":                "#038387",
}

BASE_LAYOUT = dict(
    plot_bgcolor=SURFACE,
    paper_bgcolor=SURFACE,
    font=dict(family=FONT, color=TEXT, size=12),
    title_font=dict(size=14, color=TEXT, family=FONT),
    margin=dict(l=16, r=16, t=48, b=16),
    hoverlabel=dict(
        bgcolor=SURFACE,
        bordercolor=BORDER,
        font_family=FONT,
        font_size=12,
    ),
)

# ---------------------------------------------------------------------------
# Load project data at module level
# ---------------------------------------------------------------------------
_XER = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "4e3ad98d-Galpon_Minero_v9_1.xer",
)
_project: P6Project = parse_xer(_XER)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _phase_name(wbs_id: str, wbs_dict: dict) -> str:
    """Walk up WBS tree to find the top-level phase name (level 1)."""
    node = wbs_dict.get(wbs_id)
    if not node:
        return "Sin Fase"
    cur = node
    while cur and cur.level > 1:
        cur = wbs_dict.get(cur.parent_id)
    return cur.name if cur else node.name


def _apply_base(fig: go.Figure, height: int = 400) -> go.Figure:
    """Apply BASE_LAYOUT plus common axis defaults to a figure."""
    fig.update_layout(
        height=height,
        **BASE_LAYOUT,
    )
    return fig


def _clean_axis(axis_kwargs: dict | None = None) -> dict:
    """Return a clean Power BI-style axis config."""
    base = dict(
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(family=FONT, color=TEXT_SEC, size=11),
    )
    if axis_kwargs:
        base.update(axis_kwargs)
    return base


def _phase_color(phase: str) -> str:
    for key, color in PHASE_COLORS.items():
        if key in phase or phase in key:
            return color
    return NEUTRAL


# ---------------------------------------------------------------------------
# 1. chart_phase_bar — horizontal bar: activities per phase
# ---------------------------------------------------------------------------

def chart_phase_bar() -> go.Figure:
    """Horizontal bar chart: number of activities per WBS phase."""
    counts: dict[str, int] = defaultdict(int)
    for task in _project.tasks:
        phase = _phase_name(task.wbs_id, _project.wbs)
        counts[phase] += 1

    # Sort by count descending for readability
    sorted_items = sorted(counts.items(), key=lambda x: x[1])
    phases = [p for p, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors = [_phase_color(p) for p in phases]

    # Shorten phase labels for display
    short_labels = []
    for p in phases:
        if ":" in p:
            short_labels.append(p.split(":")[0].strip())
        else:
            short_labels.append(p)

    fig = go.Figure(
        go.Bar(
            y=short_labels,
            x=values,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=values,
            textposition="outside",
            textfont=dict(family=FONT, size=12, color=TEXT),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Actividades: <b>%{x}</b><extra></extra>"
            ),
            cliponaxis=False,
        )
    )

    fig.update_layout(
        title=dict(text="<b>Actividades por Fase</b>", x=0.01),
        xaxis=_clean_axis(dict(
            title=None,
            showgrid=True,
            range=[0, max(values) * 1.18],
        )),
        yaxis=_clean_axis(dict(
            title=None,
            showgrid=False,
            automargin=True,
        )),
        showlegend=False,
        height=380,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 2. chart_status_donut — donut chart of task status
# ---------------------------------------------------------------------------

def chart_status_donut() -> go.Figure:
    """Donut chart showing task status distribution with central total annotation."""
    status_map = {
        "TK_NotStart": ("No Iniciadas", WARNING),
        "TK_Active":   ("En Progreso",  PRIMARY),
        "TK_Complete": ("Completadas",  SUCCESS),
    }

    counts: dict[str, int] = defaultdict(int)
    for task in _project.tasks:
        label, _ = status_map.get(task.status, ("Otro", NEUTRAL))
        counts[label] += 1

    labels = list(counts.keys())
    values = list(counts.values())
    color_map = {v[0]: v[1] for v in status_map.values()}
    color_map["Otro"] = NEUTRAL
    colors = [color_map.get(lbl, NEUTRAL) for lbl in labels]

    total = sum(values)

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(
                colors=colors,
                line=dict(color=SURFACE, width=3),
            ),
            textinfo="label+percent",
            textfont=dict(family=FONT, size=12, color=TEXT),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Tareas: <b>%{value}</b><br>"
                "Porcentaje: <b>%{percent}</b><extra></extra>"
            ),
            direction="clockwise",
            sort=False,
        )
    )

    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:11px;color:{TEXT_SEC}'>Tareas</span>",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(family=FONT, size=20, color=TEXT),
        align="center",
    )

    fig.update_layout(
        title=dict(text="<b>Estado de Tareas</b>", x=0.01),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.02, y=0.5,
            xanchor="left",
            font=dict(family=FONT, size=12, color=TEXT),
        ),
        height=360,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 3. chart_phase_timeline — macro Gantt of phases
# ---------------------------------------------------------------------------

def chart_phase_timeline() -> go.Figure:
    """Horizontal Gantt of phases with duration labels on each bar."""
    phase_bounds: dict[str, dict] = {}

    for task in _project.tasks:
        phase = _phase_name(task.wbs_id, _project.wbs)
        start = task.target_start or task.early_start
        finish = task.target_finish or task.early_finish
        if not start or not finish:
            continue
        if phase not in phase_bounds:
            phase_bounds[phase] = {"start": start, "finish": finish}
        else:
            if start < phase_bounds[phase]["start"]:
                phase_bounds[phase]["start"] = start
            if finish > phase_bounds[phase]["finish"]:
                phase_bounds[phase]["finish"] = finish

    # Sort by start date
    sorted_phases = sorted(phase_bounds.items(), key=lambda x: x[1]["start"])

    fig = go.Figure()

    for i, (phase, bounds) in enumerate(sorted_phases):
        start = bounds["start"]
        finish = bounds["finish"]
        duration_days = (finish - start).days
        color = _phase_color(phase)

        short = phase.split(":")[0].strip() if ":" in phase else phase

        fig.add_trace(
            go.Bar(
                name=short,
                y=[short],
                x=[duration_days],
                base=[start.timestamp() * 1000],
                orientation="h",
                marker=dict(color=color, line=dict(width=0)),
                text=f"{duration_days}d",
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(family=FONT, size=11, color=SURFACE),
                hovertemplate=(
                    f"<b>{phase}</b><br>"
                    f"Inicio: {start.strftime('%d/%m/%Y')}<br>"
                    f"Fin: {finish.strftime('%d/%m/%Y')}<br>"
                    f"Duración: <b>{duration_days} días</b>"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # X axis as dates
    all_starts = [v["start"] for v in phase_bounds.values()]
    all_ends   = [v["finish"] for v in phase_bounds.values()]
    x_min = min(all_starts) - timedelta(days=5)
    x_max = max(all_ends)   + timedelta(days=10)

    fig.update_layout(
        title=dict(text="<b>Cronograma por Fase (Macro)</b>", x=0.01),
        barmode="overlay",
        xaxis=dict(
            type="date",
            range=[x_min.isoformat(), x_max.isoformat()],
            tickformat="%b %Y",
            tickfont=dict(family=FONT, size=11, color=TEXT_SEC),
            showgrid=True,
            gridcolor=GRID,
            gridwidth=1,
            showline=False,
            zeroline=False,
        ),
        yaxis=_clean_axis(dict(
            title=None,
            showgrid=False,
            automargin=True,
            autorange="reversed",
        )),
        showlegend=False,
        height=380,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 4. chart_gantt — detailed Gantt for first N tasks
# ---------------------------------------------------------------------------

def chart_gantt(n: int = 45) -> go.Figure:
    """Detailed Gantt chart for the first N tasks, colored by phase."""
    tasks_with_dates = [
        t for t in _project.tasks
        if (t.target_start or t.early_start) and (t.target_finish or t.early_finish)
    ][:n]

    if not tasks_with_dates:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de fechas disponibles", **BASE_LAYOUT)
        return fig

    fig = go.Figure()

    for task in reversed(tasks_with_dates):
        start  = task.target_start  or task.early_start
        finish = task.target_finish or task.early_finish
        phase  = _phase_name(task.wbs_id, _project.wbs)
        color  = _phase_color(phase)
        dur_d  = max((finish - start).days, 1)
        short_name = task.name[:50] + "…" if len(task.name) > 50 else task.name
        short_phase = phase.split(":")[0].strip() if ":" in phase else phase

        fig.add_trace(
            go.Bar(
                name=short_phase,
                y=[short_name],
                x=[dur_d],
                base=[start.timestamp() * 1000],
                orientation="h",
                marker=dict(
                    color=color,
                    opacity=0.85,
                    line=dict(width=0),
                ),
                hovertemplate=(
                    f"<b>{task.name}</b><br>"
                    f"Código: {task.task_code}<br>"
                    f"Fase: {phase}<br>"
                    f"Inicio: {start.strftime('%d/%m/%Y')}<br>"
                    f"Fin: {finish.strftime('%d/%m/%Y')}<br>"
                    f"Duración: <b>{dur_d} días</b><br>"
                    f"Avance: <b>{task.pct_complete:.0f}%</b>"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    all_starts  = [t.target_start or t.early_start for t in tasks_with_dates]
    all_ends    = [t.target_finish or t.early_finish for t in tasks_with_dates]
    x_min = min(all_starts) - timedelta(days=3)
    x_max = max(all_ends)   + timedelta(days=5)

    fig.update_layout(
        title=dict(text=f"<b>Gantt Detallado — Primeras {len(tasks_with_dates)} Tareas</b>", x=0.01),
        barmode="overlay",
        xaxis=dict(
            type="date",
            range=[x_min.isoformat(), x_max.isoformat()],
            tickformat="%d %b",
            tickfont=dict(family=FONT, size=10, color=TEXT_SEC),
            showgrid=True,
            gridcolor=GRID,
            gridwidth=1,
            showline=False,
            zeroline=False,
        ),
        yaxis=_clean_axis(dict(
            title=None,
            showgrid=False,
            automargin=True,
            tickfont=dict(family=FONT, size=10, color=TEXT),
        )),
        showlegend=False,
        height=max(500, len(tasks_with_dates) * 18 + 80),
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 5. chart_resource_cost — vertical bar: cost per resource
# ---------------------------------------------------------------------------

def chart_resource_cost() -> go.Figure:
    """Vertical bar chart of total planned cost per resource (CLP format)."""
    cost_by_rsrc: dict[str, float] = defaultdict(float)
    for tr in _project.task_resources:
        rsrc = _project.resources.get(tr.rsrc_id)
        name = rsrc.name if rsrc else tr.rsrc_id
        cost_by_rsrc[name] += tr.target_cost

    if not cost_by_rsrc:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de recursos disponibles", **BASE_LAYOUT)
        return fig

    sorted_items = sorted(cost_by_rsrc.items(), key=lambda x: x[1], reverse=True)[:15]
    names  = [n for n, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(names))]

    def clp(v: float) -> str:
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"

    text_labels = [clp(v) for v in values]

    fig = go.Figure(
        go.Bar(
            x=names,
            y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=text_labels,
            textposition="outside",
            textfont=dict(family=FONT, size=11, color=TEXT),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Costo: <b>$%{y:,.0f}</b><extra></extra>"
            ),
            cliponaxis=False,
        )
    )

    max_val = max(values) if values else 1

    fig.update_layout(
        title=dict(text="<b>Costo Planificado por Recurso</b>", x=0.01),
        xaxis=_clean_axis(dict(
            title=None,
            showgrid=False,
            automargin=True,
            tickangle=-35,
        )),
        yaxis=_clean_axis(dict(
            title="CLP",
            range=[0, max_val * 1.2],
            tickformat="$,.0f",
        )),
        showlegend=False,
        height=420,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 6. chart_duration_hist — histogram of task durations
# ---------------------------------------------------------------------------

def chart_duration_hist() -> go.Figure:
    """Histogram of task durations (in working days, assuming 8 h/day)."""
    durations = [
        t.duration_hrs / 8.0
        for t in _project.tasks
        if t.duration_hrs > 0
    ]

    if not durations:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de duración", **BASE_LAYOUT)
        return fig

    fig = go.Figure(
        go.Histogram(
            x=durations,
            nbinsx=20,
            marker=dict(color=PRIMARY, line=dict(color=SURFACE, width=1)),
            hovertemplate=(
                "Duración: <b>%{x:.0f} días</b><br>"
                "Tareas: <b>%{y}</b><extra></extra>"
            ),
            name="Tareas",
        )
    )

    fig.update_layout(
        title=dict(text="<b>Distribución de Duraciones</b>", x=0.01),
        xaxis=_clean_axis(dict(title="Días", showgrid=False)),
        yaxis=_clean_axis(dict(title="Nº de Tareas")),
        showlegend=False,
        bargap=0.05,
        height=340,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 7. chart_critical_path_gauge — gauge of critical path %
# ---------------------------------------------------------------------------

def chart_critical_path_gauge() -> go.Figure:
    """Gauge indicator showing percentage of critical tasks vs total."""
    total    = len(_project.tasks)
    critical = sum(1 for t in _project.tasks if t.is_critical)
    pct      = round(critical / total * 100, 1) if total else 0

    # Colour thresholds: green < 30, orange 30-60, red > 60
    if pct < 30:
        needle_color = SUCCESS
    elif pct < 60:
        needle_color = WARNING
    else:
        needle_color = DANGER

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=pct,
            number=dict(
                suffix="%",
                font=dict(family=FONT, size=36, color=TEXT),
            ),
            delta=dict(
                reference=30,
                increasing=dict(color=DANGER),
                decreasing=dict(color=SUCCESS),
                font=dict(family=FONT, size=14),
            ),
            title=dict(
                text=(
                    f"<b>Ruta Crítica</b><br>"
                    f"<span style='font-size:12px;color:{TEXT_SEC}'>"
                    f"{critical} de {total} tareas</span>"
                ),
                font=dict(family=FONT, size=14, color=TEXT),
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickwidth=1,
                    tickcolor=BORDER,
                    tickfont=dict(family=FONT, size=11, color=TEXT_SEC),
                ),
                bar=dict(color=needle_color, thickness=0.25),
                bgcolor=SURFACE,
                borderwidth=1,
                bordercolor=BORDER,
                steps=[
                    dict(range=[0, 30],  color="#E8F5E9"),
                    dict(range=[30, 60], color="#FFF3E0"),
                    dict(range=[60, 100], color="#FFEBEE"),
                ],
                threshold=dict(
                    line=dict(color=DANGER, width=2),
                    thickness=0.75,
                    value=pct,
                ),
            ),
        )
    )

    fig.update_layout(
        height=320,
        **BASE_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# 8. chart_weekly_workload — weekly activity workload bar chart
# ---------------------------------------------------------------------------

def chart_weekly_workload() -> go.Figure:
    """Bar chart of number of active tasks per ISO week (start–finish window)."""
    from collections import Counter
    import datetime as dt_mod

    week_counts: Counter = Counter()

    for task in _project.tasks:
        start  = task.target_start  or task.early_start
        finish = task.target_finish or task.early_finish
        if not start or not finish:
            continue
        # Walk each week the task spans
        cur = start
        while cur <= finish:
            iso_year, iso_week, _ = cur.isocalendar()
            week_counts[(iso_year, iso_week)] += 1
            cur += timedelta(weeks=1)

    if not week_counts:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de carga semanal", **BASE_LAYOUT)
        return fig

    sorted_weeks = sorted(week_counts.keys())
    # Build ISO week label and a representative Monday date for x-axis
    labels = []
    x_dates = []
    y_vals  = []
    for (yr, wk) in sorted_weeks:
        monday = dt_mod.datetime.fromisocalendar(yr, wk, 1)
        labels.append(monday.strftime("%d %b"))
        x_dates.append(monday)
        y_vals.append(week_counts[(yr, wk)])

    # Colour bars by intensity
    max_y = max(y_vals) if y_vals else 1
    bar_colors = [
        PRIMARY if v < max_y * 0.5
        else WARNING if v < max_y * 0.8
        else DANGER
        for v in y_vals
    ]

    fig = go.Figure(
        go.Bar(
            x=x_dates,
            y=y_vals,
            marker=dict(color=bar_colors, line=dict(width=0)),
            hovertemplate=(
                "Semana del <b>%{x|%d/%m/%Y}</b><br>"
                "Actividades activas: <b>%{y}</b><extra></extra>"
            ),
            name="Actividades",
        )
    )

    fig.update_layout(
        title=dict(text="<b>Carga de Trabajo Semanal</b>", x=0.01),
        xaxis=dict(
            type="date",
            tickformat="%d %b",
            tickfont=dict(family=FONT, size=11, color=TEXT_SEC),
            showgrid=False,
            showline=False,
            zeroline=False,
        ),
        yaxis=_clean_axis(dict(title="Nº de Tareas Activas")),
        showlegend=False,
        bargap=0.15,
        height=360,
        **BASE_LAYOUT,
    )
    return fig
