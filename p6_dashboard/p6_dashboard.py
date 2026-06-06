"""Primavera P6 Dashboard - Galpon Minero.
UI inspirada en hospital-buin-paine-public: sidebar marino, fondo cyan claro, accent #00b4d8.
"""
import os
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import reflex as rx

from .xer_parser import P6Project, parse_xer

XER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "4e3ad98d-Galpon_Minero_v9_1.xer")

_project: P6Project = parse_xer(XER_FILE)

# ── Design tokens (hospital-buin-paine palette) ───────────────────────────────
C = dict(
    primary="#00b4d8",
    primary_dark="#0090b0",
    primary_light="#67d9f0",
    green="#10b981",
    orange="#f59e0b",
    red="#ef4444",
    purple="#8b5cf6",
    blue="#1b3a5c",
    cyan="#00b4d8",
    # surfaces
    bg="#f0f6fa",
    sidebar="#0f1e2e",
    sidebar_active="#162b40",
    white="#ffffff",
    card="#ffffff",
    # borders
    border="#d6e8f0",
    border_light="#e8f4fa",
    # text
    text="#0f1e2e",
    text_muted="#4a6580",
    text_light="#8aaec4",
    text_sidebar="#7aa8c4",
    text_sidebar_active="#ffffff",
)

CHART_COLORS = [
    "#00b4d8","#1b3a5c","#10b981","#f59e0b",
    "#8b5cf6","#ef4444","#06d6a0","#e76f51",
    "#457b9d","#a8dadc","#ffd166","#118ab2",
]

PHASE_COLORS = {
    "FASE 1: INGENIERÍA Y PERMISOS": "#1b3a5c",
    "FASE 2: OBRAS CIVILES - FUNDACIONES Y LOSA": "#f59e0b",
    "FASE 3: ESTRUCTURA METÁLICA Y CUBIERTA": "#10b981",
    "FASE 4: INSTALACIONES (EE + SS + CI + VENT)": "#ef4444",
    "FASE 5: EQUIPAMIENTO INTERIOR Y TERMINACIONES": "#8b5cf6",
    "FASE 6: GESTIÓN DE PROYECTO Y CIERRE": "#00b4d8",
}

STATUS_LABEL = {
    "TK_NotStart": "No Iniciada",
    "TK_Active":   "En Progreso",
    "TK_Complete": "Completada",
}

SHADOW = "0 2px 16px rgba(99,102,241,0.07), 0 1px 4px rgba(0,0,0,0.04)"

TABS = [
    ("resumen",   "Resumen",      "📊"),
    ("gantt",     "Gantt",        "📅"),
    ("fases",     "Por Fase",     "🏗️"),
    ("recursos",  "Recursos",     "💰"),
    ("listado",   "Actividades",  "📋"),
]


# ── State ─────────────────────────────────────────────────────────────────────
class State(rx.State):
    active_tab: str = "resumen"

    def set_tab(self, tab: str):
        self.active_tab = tab


# ── Data helpers ──────────────────────────────────────────────────────────────
def _phase_name(wbs_id: str) -> str:
    node = _project.wbs.get(wbs_id)
    if not node:
        return "Sin Fase"
    cur = node
    while cur and cur.level > 1:
        cur = _project.wbs.get(cur.parent_id)
    return cur.name if cur else node.name


def _summary() -> dict:
    total    = len(_project.tasks)
    complete = sum(1 for t in _project.tasks if t.status == "TK_Complete")
    active   = sum(1 for t in _project.tasks if t.status == "TK_Active")
    ns       = sum(1 for t in _project.tasks if t.status == "TK_NotStart")
    critical = sum(1 for t in _project.tasks if t.is_critical)
    cost     = sum(tr.target_cost for tr in _project.task_resources)
    return dict(
        total=total, complete=complete, active=active,
        not_started=ns, critical=critical, total_cost=cost,
        plan_start=_project.plan_start.strftime("%d/%m/%Y") if _project.plan_start else "—",
        plan_end=_project.plan_end.strftime("%d/%m/%Y")   if _project.plan_end   else "—",
    )


_S = _summary()


# ── Chart builders ─────────────────────────────────────────────────────────────
_LAYOUT = dict(
    plot_bgcolor=C["white"], paper_bgcolor=C["white"],
    font_color=C["text"], title_font_size=15,
    margin=dict(l=12, r=12, t=44, b=12),
    font_family="Inter, system-ui, sans-serif",
)


def _chart_phase_bar():
    counts: dict[str, int] = defaultdict(int)
    for t in _project.tasks:
        counts[_phase_name(t.wbs_id)] += 1
    df = pd.DataFrame(list(counts.items()), columns=["Fase", "Actividades"])
    df = df.sort_values("Actividades", ascending=True)
    fig = px.bar(
        df, x="Actividades", y="Fase", orientation="h",
        title="Actividades por Fase",
        color="Fase", color_discrete_map=PHASE_COLORS,
    )
    fig.update_layout(**_LAYOUT, height=300, showlegend=False,
                      coloraxis_showscale=False)
    fig.update_xaxes(gridcolor=C["border_light"], title="")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0)", title="")
    return fig


def _chart_status_donut():
    counts: dict[str, int] = defaultdict(int)
    for t in _project.tasks:
        counts[t.status] += 1
    labels = [STATUS_LABEL.get(k, k) for k in counts]
    values = list(counts.values())
    colors = [C["primary"], C["orange"], C["green"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=colors[:len(values)],
        hole=0.58, textinfo="label+percent",
        textfont_size=12,
    ))
    fig.update_layout(**_LAYOUT, height=300,
                      title="Estado de Actividades", showlegend=False)
    return fig


def _chart_phase_timeline():
    phase_dates: dict[str, dict] = {}
    for t in _project.tasks:
        p = _phase_name(t.wbs_id)
        if t.early_start and t.early_finish:
            if p not in phase_dates:
                phase_dates[p] = {"start": t.early_start, "end": t.early_finish}
            else:
                if t.early_start < phase_dates[p]["start"]:
                    phase_dates[p]["start"] = t.early_start
                if t.early_finish > phase_dates[p]["end"]:
                    phase_dates[p]["end"] = t.early_finish
    df = pd.DataFrame([
        dict(Fase=p, Start=v["start"], Finish=v["end"])
        for p, v in phase_dates.items()
    ])
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Fase",
        color="Fase", color_discrete_map=PHASE_COLORS,
        title="Cronograma por Fase",
    )
    fig.update_layout(**_LAYOUT, height=280, showlegend=False)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    fig.update_xaxes(gridcolor=C["border_light"])
    return fig


def _chart_gantt():
    tasks = [t for t in _project.tasks if t.early_start and t.early_finish][:45]
    df = pd.DataFrame([
        dict(
            Actividad=f"{t.task_code} {t.name[:38]}",
            Start=t.early_start,
            Finish=t.early_finish,
            Fase=_phase_name(t.wbs_id),
        )
        for t in tasks
    ])
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Actividad",
        color="Fase", color_discrete_map=PHASE_COLORS,
        title="Diagrama de Gantt — Primeras 45 Actividades",
    )
    fig.update_layout(**_LAYOUT, height=720,
                      legend=dict(orientation="h", y=-0.04, x=0,
                                  font_size=11, bgcolor="rgba(0,0,0,0)"))
    fig.update_yaxes(autorange="reversed", tickfont_size=9,
                     gridcolor=C["border_light"])
    fig.update_xaxes(gridcolor=C["border_light"])
    return fig


def _chart_resource_cost():
    rsrc_costs: dict[str, float] = defaultdict(float)
    for tr in _project.task_resources:
        rsrc = _project.resources.get(tr.rsrc_id)
        name = rsrc.name if rsrc else tr.rsrc_id
        rsrc_costs[name] += tr.target_cost
    if not rsrc_costs:
        return go.Figure()
    df = pd.DataFrame(list(rsrc_costs.items()), columns=["Recurso", "Costo (CLP)"])
    df = df.sort_values("Costo (CLP)", ascending=False)
    fig = px.bar(
        df, x="Recurso", y="Costo (CLP)",
        title="Costo por Recurso (CLP)",
        color_discrete_sequence=[C["primary"]],
    )
    fig.update_traces(marker_color=C["primary"],
                      marker_line_color=C["primary_dark"],
                      marker_line_width=1,
                      marker_cornerradius=6)
    fig.update_layout(**_LAYOUT, height=320, showlegend=False)
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    fig.update_yaxes(gridcolor=C["border_light"])
    return fig


def _chart_duration_hist():
    durations = [t.duration_hrs / 8 for t in _project.tasks if t.duration_hrs > 0]
    fig = px.histogram(
        x=durations, nbins=20,
        title="Distribución de Duraciones (días)",
        labels={"x": "Días", "y": "Actividades"},
        color_discrete_sequence=[C["primary"]],
    )
    fig.update_traces(marker_color=C["primary"],
                      marker_line_color=C["primary_dark"],
                      marker_line_width=1)
    fig.update_layout(**_LAYOUT, height=300, showlegend=False)
    fig.update_xaxes(gridcolor=C["border_light"])
    fig.update_yaxes(gridcolor=C["border_light"])
    return fig


# ── UI Components ─────────────────────────────────────────────────────────────

def sidebar_item(key: str, label: str, icon: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(icon, font_size="1rem"),
            rx.text(label, font_size="0.875rem", font_weight="500"),
            spacing="3",
            align="center",
        ),
        padding="0.65rem 1.25rem",
        border_radius="8px",
        margin_bottom="2px",
        cursor="pointer",
        color=rx.cond(
            State.active_tab == key,
            C["text_sidebar_active"],
            C["text_sidebar"],
        ),
        background=rx.cond(
            State.active_tab == key,
            C["sidebar_active"],
            "transparent",
        ),
        border_left=rx.cond(
            State.active_tab == key,
            f"3px solid {C['primary']}",
            "3px solid transparent",
        ),
        on_click=State.set_tab(key),
        _hover={"background": C["sidebar_active"], "color": C["text_sidebar_active"]},
        transition="all 0.15s ease",
    )


def sidebar() -> rx.Component:
    return rx.box(
        # Logo / Title
        rx.box(
            rx.vstack(
                rx.text("🏗️", font_size="2rem"),
                rx.text(
                    "P6 Dashboard",
                    font_size="1rem", font_weight="800",
                    color=C["text_sidebar_active"],
                    letter_spacing="-0.3px",
                ),
                rx.text(
                    "Galpon Minero",
                    font_size="0.72rem", color=C["text_sidebar"],
                ),
                spacing="1", align="center",
            ),
            padding="1.75rem 1rem 1.5rem",
            border_bottom=f"1px solid {C['sidebar_active']}",
            text_align="center",
        ),
        # Nav items
        rx.box(
            *[sidebar_item(k, label, icon) for k, label, icon in TABS],
            padding="1rem 0.75rem",
        ),
        # Footer
        rx.box(
            rx.text("Primavera P6", font_size="0.7rem",
                    color=C["text_sidebar"], text_align="center"),
            rx.text(f"{_S['plan_start']} → {_S['plan_end']}",
                    font_size="0.65rem", color=C["text_light"],
                    text_align="center"),
            padding="1rem",
            border_top=f"1px solid {C['sidebar_active']}",
            position="absolute",
            bottom="0",
            width="100%",
        ),
        width="220px",
        min_width="220px",
        background=C["sidebar"],
        height="100vh",
        position="sticky",
        top="0",
        overflow_y="auto",
        box_shadow="4px 0 24px rgba(0,0,0,0.18)",
        flex_shrink="0",
        position_type="relative",
    )


def page_header(title: str, subtitle: str) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.heading(title, size="7", color=C["text"],
                       font_weight="800", letter_spacing="-0.5px"),
            rx.text(subtitle, font_size="0.82rem", color=C["text_muted"],
                    margin_top="4px"),
            spacing="0",
        ),
        rx.spacer(),
        rx.box(
            rx.text("Hospital Buin Paine", font_size="0.72rem",
                    color=C["text_muted"], font_weight="600"),
            rx.text("Sistema P6 — Construcción 2026",
                    font_size="0.68rem", color=C["text_light"]),
            text_align="right",
        ),
        align="center",
        margin_bottom="2rem",
    )


def kpi_card(label: str, value: str, sub: str, color: str, icon: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(label, font_size="0.75rem", font_weight="600",
                        color=C["text_muted"], text_transform="uppercase",
                        letter_spacing="0.04em"),
                rx.text(value, font_size="1.9rem", font_weight="800",
                        color=color, line_height="1.1"),
                rx.text(sub, font_size="0.72rem", color=C["text_light"],
                        margin_top="2px"),
                spacing="1", align_items="flex-start",
            ),
            rx.spacer(),
            rx.box(
                rx.text(icon, font_size="1.6rem"),
                background=f"{color}18",
                border_radius="12px",
                padding="0.65rem",
            ),
            align="center",
        ),
        background=C["card"],
        border_radius="18px",
        border=f"1px solid {C['border_light']}",
        box_shadow=SHADOW,
        padding="1.25rem 1.4rem",
        flex="1",
        min_width="200px",
    )


def chart_card(fig, title: str = "") -> rx.Component:
    return rx.box(
        rx.plotly(data=fig),
        background=C["card"],
        border_radius="18px",
        border=f"1px solid {C['border_light']}",
        box_shadow=SHADOW,
        padding="0.75rem",
    )


def activity_table() -> rx.Component:
    rows = []
    for t in _project.tasks[:60]:
        start  = t.early_start.strftime("%d/%m/%Y") if t.early_start else "—"
        finish = t.early_finish.strftime("%d/%m/%Y") if t.early_finish else "—"
        dur    = f"{t.duration_hrs / 8:.0f}d"
        status = STATUS_LABEL.get(t.status, t.status)
        s_color = {"No Iniciada": C["primary"], "En Progreso": C["orange"],
                   "Completada": C["green"]}.get(status, C["text_muted"])
        rows.append(
            rx.table.row(
                rx.table.cell(
                    rx.text(t.task_code, font_size="0.72rem",
                            color=C["text_muted"], font_family="monospace"),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(t.name[:50], font_size="0.8rem", color=C["text"]),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.box(
                        rx.text(_phase_name(t.wbs_id)[:30],
                                font_size="0.72rem", color=C["text_muted"]),
                    ),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(start, font_size="0.75rem", color=C["text"]),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(finish, font_size="0.75rem", color=C["text"]),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.text(dur, font_size="0.75rem", color=C["text"],
                            text_align="center"),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.box(
                        rx.text(status, font_size="0.7rem",
                                font_weight="600", color=s_color),
                        background=f"{s_color}15",
                        border=f"1px solid {s_color}40",
                        border_radius="999px",
                        padding="2px 10px",
                        display="inline-block",
                    ),
                    padding="0.55rem 0.75rem",
                ),
                rx.table.cell(
                    rx.box(
                        rx.text("Crítica", font_size="0.7rem",
                                font_weight="600", color=C["red"]),
                        background=f"{C['red']}15",
                        border=f"1px solid {C['red']}40",
                        border_radius="999px",
                        padding="2px 10px",
                        display="inline-block",
                    ) if t.is_critical else rx.text("—", color=C["text_light"],
                                                    font_size="0.75rem"),
                    padding="0.55rem 0.75rem",
                ),
                _hover={"background": C["bg"]},
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
                            color=C["text_muted"],
                            font_weight="700",
                            padding="0.65rem 0.75rem",
                            background=C["bg"],
                            text_transform="uppercase",
                            letter_spacing="0.04em",
                        )
                        for h in ["Código", "Nombre", "Fase", "Inicio", "Fin",
                                  "Dur.", "Estado", "Ruta Crítica"]
                    ]
                )
            ),
            rx.table.body(*rows),
            width="100%",
        ),
        overflow_x="auto",
        border_radius="12px",
        border=f"1px solid {C['border']}",
        max_height="520px",
        overflow_y="auto",
        background=C["card"],
        box_shadow=SHADOW,
    )


# ── Tab views ─────────────────────────────────────────────────────────────────
def view_resumen() -> rx.Component:
    cost_fmt = f"CLP {_S['total_cost']:,.0f}" if _S["total_cost"] > 0 else "N/D"
    return rx.vstack(
        page_header(
            "Resumen del Proyecto",
            f"Galpon Minero — Construcción 2026  ·  {_S['plan_start']} → {_S['plan_end']}",
        ),
        # KPIs
        rx.flex(
            kpi_card("Total Actividades", str(_S["total"]),
                     "en el proyecto", C["primary"], "📋"),
            kpi_card("No Iniciadas", str(_S["not_started"]),
                     "pendientes de inicio", C["text_muted"], "⏳"),
            kpi_card("En Progreso", str(_S["active"]),
                     "activas actualmente", C["orange"], "⚡"),
            kpi_card("Completadas", str(_S["complete"]),
                     "finalizadas", C["green"], "✅"),
            kpi_card("Ruta Crítica", str(_S["critical"]),
                     "actividades críticas", C["red"], "🎯"),
            kpi_card("Costo Total", cost_fmt[:14],
                     "presupuesto estimado", C["purple"], "💰"),
            gap="1rem",
            wrap="wrap",
            margin_bottom="1.75rem",
            width="100%",
        ),
        # Charts 2-col
        rx.grid(
            chart_card(_chart_phase_bar()),
            chart_card(_chart_status_donut()),
            columns="2",
            gap="1.25rem",
            margin_bottom="1.25rem",
            width="100%",
        ),
        # Timeline
        rx.box(chart_card(_chart_phase_timeline()),
               width="100%", margin_bottom="1.25rem"),
        # Duration hist
        rx.box(chart_card(_chart_duration_hist()),
               width="100%"),
        spacing="0",
        width="100%",
    )


def view_gantt() -> rx.Component:
    return rx.vstack(
        page_header("Diagrama de Gantt",
                    "Primeras 45 actividades por fecha de inicio temprano"),
        rx.box(
            chart_card(_chart_gantt()),
            width="100%",
        ),
        spacing="0",
        width="100%",
    )


def view_fases() -> rx.Component:
    # Summary cards per phase
    phase_stats: dict[str, dict] = {}
    for t in _project.tasks:
        p = _phase_name(t.wbs_id)
        if p not in phase_stats:
            phase_stats[p] = {"total": 0, "critical": 0, "start": None, "end": None}
        phase_stats[p]["total"] += 1
        if t.is_critical:
            phase_stats[p]["critical"] += 1
        if t.early_start:
            if not phase_stats[p]["start"] or t.early_start < phase_stats[p]["start"]:
                phase_stats[p]["start"] = t.early_start
            if not phase_stats[p]["end"] or (t.early_finish and t.early_finish > phase_stats[p]["end"]):
                phase_stats[p]["end"] = t.early_finish

    cards = []
    for i, (phase, st) in enumerate(phase_stats.items()):
        color = CHART_COLORS[i % len(CHART_COLORS)]
        start_str = st["start"].strftime("%d/%m/%Y") if st["start"] else "—"
        end_str   = st["end"].strftime("%d/%m/%Y")   if st["end"]   else "—"
        cards.append(
            rx.box(
                rx.hstack(
                    rx.box(
                        background=color,
                        width="4px",
                        border_radius="4px",
                        align_self="stretch",
                        min_height="60px",
                    ),
                    rx.vstack(
                        rx.text(phase, font_size="0.82rem", font_weight="700",
                                color=C["text"], line_height="1.3"),
                        rx.hstack(
                            rx.text(f"🗂 {st['total']} actividades",
                                    font_size="0.73rem", color=C["text_muted"]),
                            rx.text(f"🎯 {st['critical']} críticas",
                                    font_size="0.73rem", color=C["red"]),
                            rx.text(f"📅 {start_str} → {end_str}",
                                    font_size="0.73rem", color=C["text_light"]),
                            gap="1.25rem",
                            wrap="wrap",
                        ),
                        spacing="1",
                        align_items="flex_start",
                    ),
                    spacing="3",
                    align="center",
                ),
                background=C["card"],
                border_radius="14px",
                border=f"1px solid {C['border_light']}",
                box_shadow=SHADOW,
                padding="1rem 1.25rem",
            )
        )

    return rx.vstack(
        page_header("Desglose por Fase",
                    "Resumen de actividades, duración y ruta crítica por fase del proyecto"),
        rx.grid(
            chart_card(_chart_phase_bar()),
            chart_card(_chart_phase_timeline()),
            columns="2", gap="1.25rem", margin_bottom="1.75rem",
            width="100%",
        ),
        rx.text("Detalle por Fase", font_size="0.95rem", font_weight="700",
                color=C["text_muted"], text_transform="uppercase",
                letter_spacing="0.05em", margin_bottom="0.75rem"),
        rx.vstack(*cards, spacing="3", width="100%"),
        spacing="0",
        width="100%",
    )


def view_recursos() -> rx.Component:
    return rx.vstack(
        page_header("Costos y Recursos",
                    "Distribución de costos por tipo de recurso asignado"),
        rx.grid(
            chart_card(_chart_resource_cost()),
            chart_card(_chart_duration_hist()),
            columns="2", gap="1.25rem", width="100%",
        ),
        spacing="0",
        width="100%",
    )


def view_listado() -> rx.Component:
    return rx.vstack(
        page_header("Listado de Actividades",
                    "Primeras 60 actividades con estado, fechas y ruta crítica"),
        activity_table(),
        spacing="0",
        width="100%",
    )


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


# ── Root ──────────────────────────────────────────────────────────────────────
def index() -> rx.Component:
    return rx.hstack(
        sidebar(),
        content_area(),
        spacing="0",
        align="stretch",
        min_height="100vh",
        background=C["bg"],
        font_family="'Inter', -apple-system, system-ui, sans-serif",
    )


app = rx.App(
    stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"],
)
app.add_page(index, route="/", title="P6 Dashboard — Galpon Minero")
