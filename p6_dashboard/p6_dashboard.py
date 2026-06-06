"""P6 Dashboard — Galpon Minero. Orquestador principal.

Módulos:
- design.py       : tokens Power BI
- charts.py       : builders Plotly
- ui_components.py: componentes Reflex + State
- xer_parser.py   : lectura XER
"""
from collections import defaultdict

import reflex as rx

from .charts import (
    _project, _phase_name,
    chart_phase_bar, chart_status_donut, chart_phase_timeline,
    chart_gantt, chart_resource_cost, chart_duration_hist,
    chart_critical_path_gauge, chart_weekly_workload,
)
from .design import COLORS as C, PHASE_COLORS, STATUS_LABELS, STATUS_COLORS
from .ui_components import (
    State,
    sidebar, kpi_card, section_label, chart_card,
    phase_summary_card, activity_table, page_header,
)

# ── Tabs definition ────────────────────────────────────────────────────────────
TABS = [
    ("resumen",   "Resumen",      "📊"),
    ("gantt",     "Gantt",        "📅"),
    ("fases",     "Por Fase",     "🏗️"),
    ("recursos",  "Recursos",     "💰"),
    ("listado",   "Actividades",  "📋"),
]

# ── Pre-compute summary ────────────────────────────────────────────────────────
def _make_summary():
    tasks    = _project.tasks
    total    = len(tasks)
    complete = sum(1 for t in tasks if t.status == "TK_Complete")
    active   = sum(1 for t in tasks if t.status == "TK_Active")
    ns       = sum(1 for t in tasks if t.status == "TK_NotStart")
    critical = sum(1 for t in tasks if t.is_critical)
    cost     = sum(tr.target_cost for tr in _project.task_resources)
    return dict(
        total=total, complete=complete, active=active,
        not_started=ns, critical=critical, total_cost=cost,
        plan_start=_project.plan_start.strftime("%d/%m/%Y") if _project.plan_start else "—",
        plan_end=_project.plan_end.strftime("%d/%m/%Y")     if _project.plan_end   else "—",
        critical_pct=round(critical / total * 100) if total else 0,
    )


def _make_phase_stats():
    stats: dict[str, dict] = {}
    for t in _project.tasks:
        p = _phase_name(t.wbs_id, _project.wbs)
        if p not in stats:
            stats[p] = {"total": 0, "critical": 0, "start": None, "end": None}
        stats[p]["total"] += 1
        if t.is_critical:
            stats[p]["critical"] += 1
        if t.early_start:
            if stats[p]["start"] is None or t.early_start < stats[p]["start"]:
                stats[p]["start"] = t.early_start
            if stats[p]["end"] is None or (t.early_finish and t.early_finish > stats[p]["end"]):
                stats[p]["end"] = t.early_finish
    return stats


_S  = _make_summary()
_PS = _make_phase_stats()


# ── Tab views ──────────────────────────────────────────────────────────────────

def view_resumen() -> rx.Component:
    cost_fmt = f"CLP {_S['total_cost'] / 1_000_000:.1f} M"
    return rx.vstack(
        page_header(
            "Resumen Ejecutivo",
            f"Galpon Minero — Construcción 2026  ·  {_S['plan_start']} → {_S['plan_end']}",
        ),
        # KPI row
        rx.flex(
            kpi_card("Total Actividades", str(_S["total"]),
                     "en el programa", C["primary"], "📋"),
            kpi_card("No Iniciadas", str(_S["not_started"]),
                     "pendientes", C["text_muted"], "⏳"),
            kpi_card("En Progreso", str(_S["active"]),
                     "en ejecución", C["warning"], "⚡"),
            kpi_card("Completadas", str(_S["complete"]),
                     "finalizadas", C["success"], "✅"),
            kpi_card("Ruta Crítica", f"{_S['critical_pct']}%",
                     f"{_S['critical']} actividades", C["danger"], "🎯"),
            kpi_card("Presupuesto", cost_fmt,
                     "costo estimado total", C["purple"], "💰"),
            gap="0.875rem",
            wrap="wrap",
            margin_bottom="1.5rem",
            width="100%",
        ),
        # Charts 2-col
        rx.grid(
            chart_card(chart_phase_bar(), height="380px"),
            chart_card(chart_status_donut(), height="380px"),
            columns="2",
            gap="1rem",
            width="100%",
            margin_bottom="1rem",
        ),
        # Row: timeline + gauge
        rx.grid(
            chart_card(chart_phase_timeline(), height="300px"),
            chart_card(chart_critical_path_gauge(), height="300px"),
            columns="2",
            gap="1rem",
            width="100%",
            margin_bottom="1rem",
        ),
        # Weekly workload full width
        chart_card(chart_weekly_workload(), height="320px"),
        spacing="0",
        width="100%",
    )


def view_gantt() -> rx.Component:
    return rx.vstack(
        page_header(
            "Diagrama de Gantt",
            "Primeras 45 actividades por fecha de inicio temprano · Color por fase",
        ),
        chart_card(chart_gantt(45)),
        spacing="0",
        width="100%",
    )


def view_fases() -> rx.Component:
    phase_cards = []
    for i, (ph, st) in enumerate(_PS.items()):
        colors = list(PHASE_COLORS.values())
        color = colors[i % len(colors)]
        s = st["start"].strftime("%d/%m/%Y") if st["start"] else "—"
        e = st["end"].strftime("%d/%m/%Y")   if st["end"]   else "—"
        phase_cards.append(
            phase_summary_card(ph, st["total"], st["critical"], s, e, color)
        )

    return rx.vstack(
        page_header(
            "Desglose por Fase",
            "Actividades, duración y ruta crítica por fase del proyecto",
        ),
        rx.grid(
            chart_card(chart_phase_bar()),
            chart_card(chart_phase_timeline()),
            columns="2", gap="1rem",
            width="100%", margin_bottom="1.25rem",
        ),
        section_label("Resumen por Fase"),
        rx.grid(
            *phase_cards,
            columns="2", gap="0.875rem", width="100%",
        ),
        spacing="0",
        width="100%",
    )


def view_recursos() -> rx.Component:
    return rx.vstack(
        page_header(
            "Costos y Recursos",
            "Distribución de presupuesto por recurso y análisis de duraciones",
        ),
        rx.grid(
            chart_card(chart_resource_cost()),
            chart_card(chart_duration_hist()),
            columns="2", gap="1rem",
            width="100%", margin_bottom="1rem",
        ),
        chart_card(chart_weekly_workload()),
        spacing="0",
        width="100%",
    )


def view_listado() -> rx.Component:
    return rx.vstack(
        page_header(
            "Listado de Actividades",
            "Primeras 60 actividades · Estado, fechas y ruta crítica",
        ),
        activity_table(
            _project.tasks[:60],
            lambda wid: _phase_name(wid, _project.wbs),
        ),
        spacing="0",
        width="100%",
    )


# ── Root ───────────────────────────────────────────────────────────────────────

def content_area() -> rx.Component:
    return rx.box(
        rx.match(
            State.active_tab,
            ("resumen",  view_resumen()),
            ("gantt",    view_gantt()),
            ("fases",    view_fases()),
            ("recursos", view_recursos()),
            ("listado",  view_listado()),
            view_resumen(),
        ),
        flex="1",
        overflow_y="auto",
        background=C["bg"],
        padding="2rem 2.5rem",
        min_height="100vh",
    )


def index() -> rx.Component:
    return rx.hstack(
        sidebar(TABS),
        content_area(),
        spacing="0",
        align="stretch",
        width="100%",
        min_height="100vh",
        background=C["bg"],
        font_family="'Inter', 'Segoe UI', -apple-system, system-ui, sans-serif",
    )


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap",
    ],
)
app.add_page(index, route="/", title="P6 Dashboard — Galpon Minero")
