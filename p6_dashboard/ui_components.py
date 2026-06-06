"""
ui_components.py
Componentes de UI rediseñados al estilo Power BI ejecutivo para el dashboard Primavera P6.
Todos los componentes son funciones que devuelven rx.Component.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple

import reflex as rx

# ---------------------------------------------------------------------------
# Design tokens
# ---------------------------------------------------------------------------

C = dict(
    primary="#0078D4",
    primary_dark="#005A9E",
    primary_light="#2B88D8",
    success="#107C10",
    warning="#FF8C00",
    danger="#D13438",
    purple="#7719AA",
    teal="#038387",
    bg="#F3F4F6",
    bg2="#EAECEE",
    surface="#FFFFFF",
    sidebar="#1B2431",
    sidebar_hover="#243447",
    sidebar_active="#2D3F55",
    border="#E1E4E8",
    border_light="#EEF0F2",
    text="#252423",
    text_sec="#605E5C",
    text_muted="#A19F9D",
    text_inv="#FFFFFF",
    shadow="0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.06)",
    shadow_elevated="0 4px 24px rgba(0,0,0,0.12)",
)

FONT = "'Inter', 'Segoe UI', -apple-system, system-ui, sans-serif"

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class State(rx.State):
    active_tab: str = "resumen"

    def set_tab(self, tab: str):
        self.active_tab = tab


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _pill(text: str, bg: str, color: str = C["text_inv"]) -> rx.Component:
    """Small rounded badge/pill."""
    return rx.box(
        rx.text(text, size="1", weight="medium", color=color),
        background=bg,
        border_radius="4px",
        padding_x="8px",
        padding_y="3px",
        display="inline-flex",
        align_items="center",
    )


def _status_color(status: str) -> str:
    """Map a status string to a semantic color."""
    s = (status or "").lower()
    if s in ("completada", "complete", "completed", "finalizada"):
        return C["success"]
    if s in ("en progreso", "in progress", "activa", "active"):
        return C["primary"]
    if s in ("pendiente", "not started", "no iniciada"):
        return C["text_muted"]
    if s in ("retrasada", "late", "delayed"):
        return C["danger"]
    if s in ("en riesgo", "at risk"):
        return C["warning"]
    return C["text_sec"]


# ---------------------------------------------------------------------------
# 1. sidebar
# ---------------------------------------------------------------------------


def sidebar(tabs: List[Tuple[str, str, str]]) -> rx.Component:
    """
    Sidebar 240 px, fondo oscuro estilo Power BI.

    tabs: list of (key, icon, label)
        key   → identificador lógico
        icon  → nombre de ícono Lucide (ej. "layout-dashboard")
        label → texto visible
    """

    def _nav_item(key: str, icon: str, label: str) -> rx.Component:
        is_active = State.active_tab == key
        return rx.box(
            rx.hstack(
                # Borde izquierdo activo
                rx.box(
                    width="3px",
                    height="100%",
                    background=rx.cond(is_active, C["primary"], "transparent"),
                    border_radius="0 2px 2px 0",
                    position="absolute",
                    left="0",
                    top="0",
                    bottom="0",
                ),
                rx.icon(
                    icon,
                    size=16,
                    color=rx.cond(is_active, C["text_inv"], "#8A9BB4"),
                    flex_shrink="0",
                ),
                rx.text(
                    label,
                    size="2",
                    weight=rx.cond(is_active, "semibold", "regular"),
                    color=rx.cond(is_active, C["text_inv"], "#8A9BB4"),
                    no_of_lines=1,
                ),
                spacing="3",
                align="center",
                padding_left="16px",
                padding_right="12px",
                height="40px",
                position="relative",
            ),
            background=rx.cond(is_active, C["sidebar_active"], "transparent"),
            border_radius="0 6px 6px 0",
            margin_right="12px",
            cursor="pointer",
            on_click=State.set_tab(key),
            _hover={
                "background": rx.cond(is_active, C["sidebar_active"], C["sidebar_hover"]),
            },
            transition="background 0.15s ease",
            position="relative",
            overflow="hidden",
        )

    nav_items = rx.vstack(
        *[_nav_item(key, icon, label) for key, icon, label in tabs],
        spacing="1",
        width="100%",
        align="stretch",
    )

    return rx.box(
        rx.vstack(
            # ── Logo / título ──────────────────────────────────────────────
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("bar-chart-3", size=20, color=C["primary"]),
                            background=C["sidebar_active"],
                            border_radius="8px",
                            padding="8px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.vstack(
                            rx.text(
                                "P6 Dashboard",
                                size="3",
                                weight="bold",
                                color=C["text_inv"],
                                line_height="1.2",
                            ),
                            rx.text(
                                "Primavera P6",
                                size="1",
                                color="#8A9BB4",
                            ),
                            spacing="0",
                            align="start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    spacing="0",
                    align="start",
                ),
                padding_x="16px",
                padding_y="20px",
                border_bottom=f"1px solid {C['sidebar_hover']}",
                width="100%",
            ),
            # ── Separador de sección ───────────────────────────────────────
            rx.box(
                rx.text(
                    "NAVEGACIÓN",
                    size="1",
                    weight="bold",
                    color="#4A5A70",
                    letter_spacing="0.08em",
                ),
                padding_x="16px",
                padding_top="16px",
                padding_bottom="8px",
            ),
            # ── Ítems de navegación ────────────────────────────────────────
            nav_items,
            rx.spacer(),
            # ── Footer ────────────────────────────────────────────────────
            rx.box(
                rx.vstack(
                    rx.divider(color=C["sidebar_hover"]),
                    rx.hstack(
                        rx.icon("calendar", size=12, color="#4A5A70"),
                        rx.text(
                            "Galpon Minero v9.1",
                            size="1",
                            color="#4A5A70",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("clock", size=12, color="#4A5A70"),
                        rx.text(
                            "Proyecto Activo",
                            size="1",
                            color="#4A5A70",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="2",
                    align="start",
                ),
                padding="16px",
                width="100%",
            ),
            spacing="0",
            height="100%",
            align="stretch",
        ),
        width="240px",
        min_width="240px",
        height="100vh",
        background=C["sidebar"],
        position="sticky",
        top="0",
        overflow_y="auto",
        border_right=f"1px solid {C['sidebar_hover']}",
        font_family=FONT,
        display="flex",
        flex_direction="column",
    )


# ---------------------------------------------------------------------------
# 2. kpi_card
# ---------------------------------------------------------------------------


def kpi_card(
    label: str,
    value: str,
    sub: str,
    color: str,
    icon: str,
    trend: Optional[str] = None,
) -> rx.Component:
    """
    Tarjeta KPI estilo Power BI.
    trend: string como "+5%" o "−2%" (positivo → verde, negativo → rojo).
    """
    # Determinar color de tendencia y flecha
    trend_positive = trend is not None and (trend.startswith("+") or trend.startswith("↑"))
    trend_negative = trend is not None and (
        trend.startswith("-") or trend.startswith("−") or trend.startswith("↓")
    )
    trend_color = (
        C["success"]
        if trend_positive
        else C["danger"]
        if trend_negative
        else C["text_muted"]
    )
    trend_arrow = "↑" if trend_positive else "↓" if trend_negative else ""

    trend_component = rx.box()
    if trend is not None:
        trend_component = rx.hstack(
            rx.text(
                trend_arrow,
                size="1",
                color=trend_color,
                weight="bold",
            ),
            rx.text(
                trend,
                size="1",
                color=trend_color,
                weight="medium",
            ),
            spacing="1",
            align="center",
            background=f"{trend_color}14",
            border_radius="4px",
            padding_x="6px",
            padding_y="2px",
        )

    return rx.box(
        # Border-top de color KPI (estilo Power BI)
        rx.box(
            height="3px",
            background=color,
            border_radius="8px 8px 0 0",
            position="absolute",
            top="0",
            left="0",
            right="0",
        ),
        rx.hstack(
            # Contenido principal
            rx.vstack(
                rx.text(
                    label.upper(),
                    size="1",
                    weight="medium",
                    color=C["text_muted"],
                    letter_spacing="0.06em",
                ),
                rx.text(
                    value,
                    size="8",
                    weight="bold",
                    color=C["text"],
                    line_height="1.1",
                    font_family=FONT,
                ),
                rx.hstack(
                    rx.text(sub, size="1", color=C["text_sec"]),
                    trend_component,
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # Ícono a la derecha
            rx.box(
                rx.icon(icon, size=28, color=color),
                background=f"{color}12",
                border_radius="10px",
                padding="10px",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            align="center",
            width="100%",
        ),
        background=C["surface"],
        border_radius="8px",
        border=f"1px solid {C['border_light']}",
        padding="20px",
        padding_top="23px",
        box_shadow=C["shadow"],
        position="relative",
        overflow="hidden",
        font_family=FONT,
        _hover={"box_shadow": C["shadow_elevated"], "transform": "translateY(-1px)"},
        transition="all 0.2s ease",
    )


# ---------------------------------------------------------------------------
# 3. section_label
# ---------------------------------------------------------------------------


def section_label(text: str) -> rx.Component:
    """Label de sección con línea divisora estilo Power BI."""
    return rx.hstack(
        rx.text(
            text.upper(),
            size="1",
            weight="bold",
            color=C["text_muted"],
            letter_spacing="0.08em",
            white_space="nowrap",
        ),
        rx.box(
            flex="1",
            height="1px",
            background=C["border"],
            margin_left="12px",
            align_self="center",
        ),
        spacing="0",
        align="center",
        width="100%",
        padding_y="4px",
        font_family=FONT,
    )


# ---------------------------------------------------------------------------
# 4. chart_card
# ---------------------------------------------------------------------------


def chart_card(fig: Any, height: Optional[str] = None) -> rx.Component:
    """Wrapper de card blanca para un gráfico Plotly."""
    chart_height = height or "400px"
    return rx.box(
        rx.plotly(
            data=fig,
            height=chart_height,
            width="100%",
        ),
        background=C["surface"],
        border_radius="8px",
        border=f"1px solid {C['border_light']}",
        box_shadow=C["shadow"],
        overflow="hidden",
        padding="4px",
        font_family=FONT,
    )


# ---------------------------------------------------------------------------
# 5. phase_summary_card
# ---------------------------------------------------------------------------


def phase_summary_card(
    phase: str,
    total: int,
    critical: int,
    start_str: str,
    end_str: str,
    color: str,
) -> rx.Component:
    """Card compacta de resumen de fase con barra de color izquierda."""
    pct_critical = round(critical / total * 100) if total > 0 else 0

    return rx.box(
        rx.hstack(
            # Barra de color izquierda
            rx.box(
                width="4px",
                min_height="100%",
                background=color,
                border_radius="4px",
                flex_shrink="0",
            ),
            # Contenido
            rx.vstack(
                # Nombre de fase
                rx.text(
                    phase,
                    size="2",
                    weight="bold",
                    color=C["text"],
                    no_of_lines=2,
                    line_height="1.3",
                ),
                # Métricas inline
                rx.hstack(
                    rx.hstack(
                        rx.icon("list-checks", size=12, color=C["primary"]),
                        rx.text(
                            f"{total} actividades",
                            size="1",
                            color=C["text_sec"],
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.box(
                        width="3px",
                        height="3px",
                        border_radius="50%",
                        background=C["border"],
                    ),
                    rx.hstack(
                        rx.icon("alert-triangle", size=12, color=C["danger"]),
                        rx.text(
                            f"{critical} críticas ({pct_critical}%)",
                            size="1",
                            color=C["danger"],
                            weight="medium",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                # Fechas
                rx.hstack(
                    rx.icon("calendar-range", size=11, color=C["text_muted"]),
                    rx.text(
                        f"{start_str} → {end_str}",
                        size="1",
                        color=C["text_muted"],
                    ),
                    spacing="1",
                    align="center",
                ),
                spacing="2",
                align="start",
                flex="1",
            ),
            spacing="3",
            align="stretch",
            width="100%",
            padding="14px",
            min_height="80px",
        ),
        background=C["surface"],
        border_radius="8px",
        border=f"1px solid {C['border_light']}",
        box_shadow=C["shadow"],
        overflow="hidden",
        font_family=FONT,
        _hover={"box_shadow": C["shadow_elevated"]},
        transition="box-shadow 0.15s ease",
    )


# ---------------------------------------------------------------------------
# 6. activity_table
# ---------------------------------------------------------------------------


def activity_table(
    tasks: List[Any],
    phase_name_fn: Optional[Callable[[Any], str]] = None,
) -> rx.Component:
    """
    Tabla de actividades estilo Power BI.
    tasks: lista de objetos o dicts con atributos:
        task_code, task_name, phase (o wbs_id), start, finish, duration, status, is_critical
    phase_name_fn: función que recibe un task y devuelve el nombre de la fase.
    """

    def _get(task: Any, attr: str, default: str = "") -> str:
        if isinstance(task, dict):
            return str(task.get(attr, default))
        return str(getattr(task, attr, default))

    def _is_critical(task: Any) -> bool:
        val = _get(task, "is_critical", "false")
        return val.lower() in ("true", "1", "yes", "sí", "si")

    def _badge_status(status: str) -> rx.Component:
        color = _status_color(status)
        return _pill(status, f"{color}18", color)

    def _critical_badge(critical: bool) -> rx.Component:
        if critical:
            return rx.hstack(
                rx.icon("zap", size=11, color=C["danger"]),
                rx.text("Sí", size="1", color=C["danger"], weight="medium"),
                spacing="1",
                align="center",
            )
        return rx.text("No", size="1", color=C["text_muted"])

    header_style = dict(
        background=C["bg2"],
        padding_x="12px",
        padding_y="10px",
        border_bottom=f"2px solid {C['border']}",
        position="sticky",
        top="0",
        z_index="10",
    )

    def _th(label: str, width: Optional[str] = None) -> rx.Component:
        props = dict(
            **header_style,
            **({"width": width} if width else {}),
        )
        return rx.table.column_header_cell(
            rx.text(
                label.upper(),
                size="1",
                weight="bold",
                color=C["text_muted"],
                letter_spacing="0.05em",
            ),
            **props,
        )

    def _td(content: rx.Component, width: Optional[str] = None) -> rx.Component:
        props = dict(
            padding_x="12px",
            padding_y="9px",
            border_bottom=f"1px solid {C['border_light']}",
            vertical_align="middle",
            **({"width": width} if width else {}),
        )
        return rx.table.cell(content, **props)

    rows = []
    for i, task in enumerate(tasks):
        code = _get(task, "task_code", f"T-{i:04d}")
        name = _get(task, "task_name", "Sin nombre")
        phase = (
            phase_name_fn(task)
            if phase_name_fn
            else _get(task, "phase", _get(task, "wbs_id", "—"))
        )
        start = _get(task, "start", "—")
        finish = _get(task, "finish", "—")
        duration = _get(task, "duration", "—")
        status = _get(task, "status", "Pendiente")
        critical = _is_critical(task)

        row_bg = "#FFF5F5" if critical else C["surface"]

        rows.append(
            rx.table.row(
                _td(
                    rx.text(code, size="1", weight="medium", color=C["primary"], font_family="'Consolas', monospace"),
                    width="100px",
                ),
                _td(
                    rx.text(name, size="2", color=C["text"], no_of_lines=2),
                    width="220px",
                ),
                _td(
                    rx.text(phase, size="1", color=C["text_sec"], no_of_lines=1),
                    width="160px",
                ),
                _td(rx.text(start, size="1", color=C["text_sec"]), width="90px"),
                _td(rx.text(finish, size="1", color=C["text_sec"]), width="90px"),
                _td(
                    rx.text(f"{duration}d" if duration != "—" else "—", size="1", color=C["text_muted"]),
                    width="70px",
                ),
                _td(_badge_status(status), width="110px"),
                _td(_critical_badge(critical), width="70px"),
                background=row_bg,
                _hover={"background": C["bg2"]},
            )
        )

    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _th("Código", "100px"),
                    _th("Nombre", "220px"),
                    _th("Fase", "160px"),
                    _th("Inicio", "90px"),
                    _th("Fin", "90px"),
                    _th("Duración", "70px"),
                    _th("Estado", "110px"),
                    _th("Crítica", "70px"),
                ),
            ),
            rx.table.body(*rows),
            width="100%",
            variant="surface",
        ),
        background=C["surface"],
        border_radius="8px",
        border=f"1px solid {C['border']}",
        box_shadow=C["shadow"],
        overflow="auto",
        max_height="520px",
        font_family=FONT,
    )


# ---------------------------------------------------------------------------
# 7. page_header
# ---------------------------------------------------------------------------


def page_header(title: str, subtitle: str) -> rx.Component:
    """Header de página estilo Power BI con título, subtítulo y branding."""
    return rx.box(
        rx.hstack(
            # Título + subtítulo
            rx.vstack(
                rx.heading(
                    title,
                    size="6",
                    weight="bold",
                    color=C["text"],
                    line_height="1.2",
                    font_family=FONT,
                ),
                rx.text(
                    subtitle,
                    size="2",
                    color=C["text_sec"],
                    font_family=FONT,
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            # Branding derecha
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Galpon Minero",
                            size="2",
                            weight="semibold",
                            color=C["text"],
                            text_align="right",
                        ),
                        rx.text(
                            "Primavera P6 · Power BI",
                            size="1",
                            color=C["text_muted"],
                            text_align="right",
                        ),
                        spacing="0",
                        align="end",
                    ),
                ),
                rx.box(
                    rx.icon("bar-chart-2", size=20, color=C["primary"]),
                    background=f"{C['primary']}12",
                    border_radius="8px",
                    padding="8px",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                spacing="3",
                align="center",
            ),
            align="center",
            width="100%",
        ),
        padding_x="24px",
        padding_top="20px",
        padding_bottom="16px",
        background=C["surface"],
        border_bottom=f"2px solid {C['border']}",
        font_family=FONT,
    )


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "C",
    "FONT",
    "State",
    "sidebar",
    "kpi_card",
    "section_label",
    "chart_card",
    "phase_summary_card",
    "activity_table",
    "page_header",
]
