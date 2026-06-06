"""Primavera P6 Dashboard - Galpon Minero."""
import os
from collections import defaultdict
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import reflex as rx

from .xer_parser import P6Project, parse_xer

XER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "4e3ad98d-Galpon_Minero_v9_1.xer")

# ── Load data once at module level ──────────────────────────────────────────
_project: P6Project = parse_xer(XER_FILE)

STATUS_LABEL = {
    "TK_NotStart": "No Iniciada",
    "TK_Active": "En Progreso",
    "TK_Complete": "Completada",
}
STATUS_COLOR = {
    "TK_NotStart": "#3B82F6",
    "TK_Active": "#F59E0B",
    "TK_Complete": "#10B981",
}


def _phase_name(wbs_id: str) -> str:
    node = _project.wbs.get(wbs_id)
    if not node:
        return "Sin Fase"
    cur = node
    while cur and cur.level > 1:
        cur = _project.wbs.get(cur.parent_id)
    return cur.name if cur else node.name


def _build_summary() -> dict:
    total = len(_project.tasks)
    complete = sum(1 for t in _project.tasks if t.status == "TK_Complete")
    active = sum(1 for t in _project.tasks if t.status == "TK_Active")
    not_started = sum(1 for t in _project.tasks if t.status == "TK_NotStart")
    critical = sum(1 for t in _project.tasks if t.is_critical)
    total_cost = sum(tr.target_cost for tr in _project.task_resources)
    return dict(
        total=total,
        complete=complete,
        active=active,
        not_started=not_started,
        critical=critical,
        total_cost=total_cost,
        plan_start=_project.plan_start.strftime("%d/%m/%Y") if _project.plan_start else "—",
        plan_end=_project.plan_end.strftime("%d/%m/%Y") if _project.plan_end else "—",
    )


def _tasks_by_phase_chart():
    phase_counts: dict[str, int] = defaultdict(int)
    for t in _project.tasks:
        phase_counts[_phase_name(t.wbs_id)] += 1
    df = pd.DataFrame(list(phase_counts.items()), columns=["Fase", "Actividades"])
    df = df.sort_values("Actividades", ascending=True)
    fig = px.bar(
        df, x="Actividades", y="Fase", orientation="h",
        color="Actividades", color_continuous_scale="Blues",
        title="Actividades por Fase",
    )
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title_font_size=16,
        coloraxis_showscale=False, margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    return fig


def _status_pie_chart():
    counts = defaultdict(int)
    for t in _project.tasks:
        counts[t.status] += 1
    labels = [STATUS_LABEL.get(k, k) for k in counts]
    values = list(counts.values())
    colors = [STATUS_COLOR.get(k, "#94A3B8") for k in counts]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, marker_colors=colors,
        hole=0.55, textinfo="label+percent",
    ))
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title="Estado de Actividades",
        title_font_size=16, margin=dict(l=10, r=10, t=40, b=10),
        height=320, showlegend=False,
    )
    return fig


def _duration_histogram():
    durations = [t.duration_hrs / 8 for t in _project.tasks if t.duration_hrs > 0]
    fig = px.histogram(
        x=durations, nbins=20, title="Distribución de Duraciones (días)",
        labels={"x": "Días", "y": "Actividades"},
    )
    fig.update_traces(marker_color="#3B82F6", marker_line_color="#1E40AF", marker_line_width=1)
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title_font_size=16,
        margin=dict(l=10, r=10, t=40, b=10), height=300,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    return fig


def _gantt_chart():
    tasks = [t for t in _project.tasks if t.early_start and t.early_finish][:40]
    df = pd.DataFrame([
        dict(
            Task=f"{t.task_code} {t.name[:35]}",
            Start=t.early_start,
            Finish=t.early_finish,
            Phase=_phase_name(t.wbs_id),
            Critical="Crítica" if t.is_critical else "Normal",
        )
        for t in tasks
    ])
    color_map = {
        "FASE 1: INGENIERÍA Y PERMISOS": "#6366F1",
        "FASE 2: OBRAS CIVILES - FUNDACIONES Y LOSA": "#F59E0B",
        "FASE 3: ESTRUCTURA METÁLICA Y CUBIERTA": "#10B981",
        "FASE 4: INSTALACIONES (EE + SS + CI + VENT)": "#EF4444",
        "FASE 5: EQUIPAMIENTO INTERIOR Y TERMINACIONES": "#8B5CF6",
        "FASE 6: GESTIÓN DE PROYECTO Y CIERRE": "#06B6D4",
    }
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Task",
        color="Phase", color_discrete_map=color_map,
        title="Diagrama de Gantt - Primeras 40 Actividades",
    )
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title_font_size=16,
        height=700, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=-0.05, x=0),
    )
    fig.update_yaxes(autorange="reversed", tickfont_size=9, gridcolor="#334155")
    fig.update_xaxes(gridcolor="#334155")
    return fig


def _resource_cost_chart():
    rsrc_costs: dict[str, float] = defaultdict(float)
    rsrc_map = _project.resources
    for tr in _project.task_resources:
        rsrc = rsrc_map.get(tr.rsrc_id)
        name = rsrc.name if rsrc else tr.rsrc_id
        rsrc_costs[name] += tr.target_cost
    if not rsrc_costs:
        return go.Figure()
    df = pd.DataFrame(list(rsrc_costs.items()), columns=["Recurso", "Costo (CLP)"])
    df = df.sort_values("Costo (CLP)", ascending=False)
    fig = px.bar(
        df, x="Recurso", y="Costo (CLP)", title="Costo por Recurso (CLP)",
        color="Costo (CLP)", color_continuous_scale="Viridis",
    )
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title_font_size=16,
        coloraxis_showscale=False, margin=dict(l=10, r=10, t=40, b=10), height=320,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    return fig


def _phase_timeline_chart():
    phase_dates: dict[str, dict] = {}
    for t in _project.tasks:
        phase = _phase_name(t.wbs_id)
        if t.early_start and t.early_finish:
            if phase not in phase_dates:
                phase_dates[phase] = {"start": t.early_start, "end": t.early_finish}
            else:
                if t.early_start < phase_dates[phase]["start"]:
                    phase_dates[phase]["start"] = t.early_start
                if t.early_finish > phase_dates[phase]["end"]:
                    phase_dates[phase]["end"] = t.early_finish
    df = pd.DataFrame([
        dict(Phase=p, Start=v["start"], Finish=v["end"])
        for p, v in phase_dates.items()
    ])
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Phase",
        color="Phase", title="Cronograma por Fase",
    )
    fig.update_layout(
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font_color="#E2E8F0", title_font_size=16,
        height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False,
    )
    fig.update_yaxes(autorange="reversed", gridcolor="#334155")
    fig.update_xaxes(gridcolor="#334155")
    return fig


# ── Pre-compute ──────────────────────────────────────────────────────────────
_summary = _build_summary()


# ── UI Components ─────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, color: str = "#3B82F6") -> rx.Component:
    return rx.box(
        rx.text(label, color="#94A3B8", font_size="0.75rem", font_weight="500"),
        rx.text(value, color=color, font_size="1.75rem", font_weight="700"),
        padding="1.25rem",
        background="#1E293B",
        border_radius="12px",
        border=f"1px solid {color}33",
        min_width="150px",
        flex="1",
    )


def section_title(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="1.1rem",
        font_weight="700",
        color="#CBD5E1",
        margin_bottom="0.75rem",
        padding_left="0.25rem",
    )


def task_table() -> rx.Component:
    tasks = _project.tasks[:50]
    rows = []
    for t in tasks:
        start = t.early_start.strftime("%d/%m/%Y") if t.early_start else "—"
        finish = t.early_finish.strftime("%d/%m/%Y") if t.early_finish else "—"
        dur_d = f"{t.duration_hrs / 8:.0f}d"
        status_label = STATUS_LABEL.get(t.status, t.status)
        rows.append(
            rx.table.row(
                rx.table.cell(
                    rx.text(t.task_code, font_size="0.75rem", color="#94A3B8"),
                    padding="0.5rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(t.name[:45], font_size="0.8rem"),
                    padding="0.5rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(_phase_name(t.wbs_id)[:28], font_size="0.75rem", color="#94A3B8"),
                    padding="0.5rem 0.75rem",
                ),
                rx.table.cell(start, font_size="0.75rem", padding="0.5rem 0.75rem"),
                rx.table.cell(finish, font_size="0.75rem", padding="0.5rem 0.75rem"),
                rx.table.cell(dur_d, font_size="0.75rem", padding="0.5rem 0.75rem"),
                rx.table.cell(
                    rx.badge(status_label, color_scheme="blue"),
                    padding="0.5rem 0.75rem",
                ),
                rx.table.cell(
                    rx.badge("Crítica", color_scheme="red") if t.is_critical
                    else rx.text("—", color="#94A3B8", font_size="0.75rem"),
                    padding="0.5rem 0.75rem",
                ),
                background="#1E293B",
                _hover={"background": "#263350"},
            )
        )
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[
                        rx.table.column_header_cell(
                            h,
                            font_size="0.72rem",
                            color="#64748B",
                            font_weight="600",
                            padding="0.6rem 0.75rem",
                            background="#0F172A",
                        )
                        for h in ["Código", "Nombre", "Fase", "Inicio", "Fin", "Dur.", "Estado", "Ruta Crítica"]
                    ]
                )
            ),
            rx.table.body(*rows),
            width="100%",
        ),
        overflow_x="auto",
        border_radius="10px",
        border="1px solid #1E293B",
        max_height="500px",
        overflow_y="auto",
    )


def index() -> rx.Component:
    s = _summary
    total_cost_fmt = f"CLP {s['total_cost']:,.0f}" if s["total_cost"] > 0 else "N/D"

    return rx.box(
        # Header
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        "Dashboard P6 — Galpon Minero",
                        size="7",
                        color="white",
                        font_weight="800",
                    ),
                    rx.text(
                        f"Proyecto: {_project.name}  |  {s['plan_start']} → {s['plan_end']}",
                        color="#94A3B8",
                        font_size="0.9rem",
                    ),
                    spacing="1",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("Primavera P6", color="#3B82F6", font_weight="700", font_size="0.8rem"),
                    rx.text("Reflex Dashboard", color="#64748B", font_size="0.75rem"),
                    align="end",
                    spacing="0",
                ),
                align="center",
                width="100%",
            ),
            padding="1.5rem 2rem",
            background="#0F172A",
            border_bottom="1px solid #1E293B",
        ),

        # Body
        rx.box(
            # KPIs
            rx.flex(
                kpi_card("Total Actividades", str(s["total"]), "#3B82F6"),
                kpi_card("No Iniciadas", str(s["not_started"]), "#94A3B8"),
                kpi_card("En Progreso", str(s["active"]), "#F59E0B"),
                kpi_card("Completadas", str(s["complete"]), "#10B981"),
                kpi_card("Ruta Crítica", str(s["critical"]), "#EF4444"),
                kpi_card("Costo Total", total_cost_fmt, "#8B5CF6"),
                gap="1rem",
                wrap="wrap",
                margin_bottom="1.75rem",
            ),

            # Charts row 1
            rx.grid(
                rx.box(
                    rx.plotly(data=_tasks_by_phase_chart()),
                    background="#1E293B",
                    border_radius="12px",
                    padding="0.75rem",
                    border="1px solid #334155",
                ),
                rx.box(
                    rx.plotly(data=_status_pie_chart()),
                    background="#1E293B",
                    border_radius="12px",
                    padding="0.75rem",
                    border="1px solid #334155",
                ),
                columns="2",
                gap="1rem",
                margin_bottom="1.5rem",
            ),

            # Phase timeline
            rx.box(
                rx.plotly(data=_phase_timeline_chart()),
                background="#1E293B",
                border_radius="12px",
                padding="0.75rem",
                border="1px solid #334155",
                margin_bottom="1.5rem",
            ),

            # Charts row 2
            rx.grid(
                rx.box(
                    rx.plotly(data=_resource_cost_chart()),
                    background="#1E293B",
                    border_radius="12px",
                    padding="0.75rem",
                    border="1px solid #334155",
                ),
                rx.box(
                    rx.plotly(data=_duration_histogram()),
                    background="#1E293B",
                    border_radius="12px",
                    padding="0.75rem",
                    border="1px solid #334155",
                ),
                columns="2",
                gap="1rem",
                margin_bottom="1.5rem",
            ),

            # Gantt
            rx.box(
                rx.plotly(data=_gantt_chart()),
                background="#1E293B",
                border_radius="12px",
                padding="0.75rem",
                border="1px solid #334155",
                margin_bottom="1.5rem",
            ),

            # Activity table
            section_title("Listado de Actividades (primeras 50)"),
            task_table(),

            padding="1.75rem 2rem",
            max_width="1600px",
            margin="0 auto",
        ),

        background="#0F172A",
        min_height="100vh",
        color="#E2E8F0",
        font_family="'Inter', sans-serif",
    )


app = rx.App(
    theme=rx.theme(appearance="dark", accent_color="blue"),
    stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"],
)
app.add_page(index, route="/", title="P6 Dashboard — Galpon Minero")
