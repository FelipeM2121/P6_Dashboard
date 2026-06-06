# design.py
# Sistema de diseño estilo Power BI ejecutivo — solo tokens y configuración.
# Sin imports externos. Sin lógica de UI ni charts.

# ---------------------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------------------

COLORS = {
    # Fondos
    "bg":            "#F3F4F6",   # Fondo principal de la app
    "bg_secondary":  "#E9EAEC",   # Fondo secundario / paneles interiores
    "bg_dark":       "#1B2431",   # Sidebar oscuro azul-grisáceo

    # Primary (azul Microsoft)
    "primary":       "#0078D4",
    "primary_dark":  "#005A9E",
    "primary_light": "#C7E0F4",

    # Semáforo / estado
    "success":       "#107C10",   # Verde Microsoft
    "warning":       "#FF8C00",   # Naranja ejecutivo
    "danger":        "#D13438",   # Rojo Microsoft
    "neutral":       "#605E5C",   # Gris neutro
    "purple":        "#8764B8",   # Púrpura acento

    # Texto
    "text":          "#1B1B1B",   # Texto principal (casi negro)
    "text_secondary":"#484644",   # Texto secundario
    "text_muted":    "#8A8886",   # Texto apagado / captions
    "text_inverse":  "#FFFFFF",   # Texto sobre fondos oscuros

    # Bordes y superficie de cards
    "border":        "#D2D0CE",   # Borde estándar
    "border_light":  "#EDEBE9",   # Borde sutil
    "surface":       "#FFFFFF",   # Fondo de cards / panels blancos

    # Grilla de charts
    "chart_grid":    "#F0F0F0",   # Líneas de grilla muy sutiles
}

# ---------------------------------------------------------------------------
# CHART_PALETTE — 10 colores ordenados para series de datos
# ---------------------------------------------------------------------------

CHART_PALETTE = [
    "#0078D4",   # Azul Microsoft — serie principal
    "#107C10",   # Verde éxito
    "#FF8C00",   # Naranja advertencia
    "#D13438",   # Rojo peligro
    "#8764B8",   # Púrpura acento
    "#00B7C3",   # Cyan ejecutivo
    "#E74856",   # Coral
    "#038387",   # Teal oscuro
    "#C239B3",   # Magenta
    "#486860",   # Verde pizarra
]

# ---------------------------------------------------------------------------
# PHASE_COLORS — 6 fases del proyecto Galpon Minero
# ---------------------------------------------------------------------------

PHASE_COLORS = {
    "Preliminares":          "#0078D4",   # Azul principal
    "Fundaciones":           "#107C10",   # Verde
    "Estructura Metálica":   "#FF8C00",   # Naranja
    "Cubierta y Cerramientos": "#8764B8", # Púrpura
    "Instalaciones":         "#00B7C3",   # Cyan
    "Terminaciones":         "#D13438",   # Rojo / cierre
}

# ---------------------------------------------------------------------------
# TYPOGRAPHY
# ---------------------------------------------------------------------------

TYPOGRAPHY = {
    "font_family": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",

    # Tamaños de texto (en px como string para uso en estilos inline)
    "title":    "24px",   # Títulos de sección / KPI grandes
    "subtitle": "16px",   # Subtítulos de cards
    "body":     "14px",   # Texto de cuerpo estándar
    "label":    "12px",   # Etiquetas de ejes / leyendas
    "caption":  "11px",   # Notas al pie / metadata
    "mono":     "'Cascadia Code', 'Consolas', 'Courier New', monospace",

    # Pesos
    "weight_regular": "400",
    "weight_medium":  "500",
    "weight_semibold":"600",
    "weight_bold":    "700",
}

# ---------------------------------------------------------------------------
# SHADOWS
# ---------------------------------------------------------------------------

SHADOWS = {
    "card":     "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
    "elevated": "0 4px 12px rgba(0,0,0,0.12), 0 2px 4px rgba(0,0,0,0.08)",
    "sidebar":  "2px 0 8px rgba(0,0,0,0.25)",
}

# ---------------------------------------------------------------------------
# RADIUS
# ---------------------------------------------------------------------------

RADIUS = {
    "sm":   "4px",
    "md":   "8px",
    "lg":   "12px",
    "pill": "9999px",
}

# ---------------------------------------------------------------------------
# CHART_LAYOUT — kwargs base para fig.update_layout() en todos los charts Plotly
# Uso: fig.update_layout(**CHART_LAYOUT)
# ---------------------------------------------------------------------------

CHART_LAYOUT = {
    "font": {
        "family": "Inter, Segoe UI, system-ui, sans-serif",
        "color":  "#484644",
        "size":   12,
    },
    "paper_bgcolor": "#FFFFFF",   # Fondo externo del chart (surface)
    "plot_bgcolor":  "#FFFFFF",   # Fondo del área de trazado
    "margin":        {"t": 40, "b": 40, "l": 48, "r": 24},
    "showlegend":    True,
    "legend": {
        "bgcolor":     "rgba(255,255,255,0)",
        "bordercolor": "rgba(0,0,0,0)",
        "borderwidth": 0,
        "font":        {"size": 11, "color": "#605E5C"},
        "orientation": "h",
        "yanchor":     "bottom",
        "y":           1.02,
        "xanchor":     "left",
        "x":           0,
    },
    "title": {
        "font": {
            "family": "Inter, Segoe UI, sans-serif",
            "size":   14,
            "color":  "#1B1B1B",
        },
        "x":       0.02,
        "xanchor": "left",
        "pad":     {"t": 4, "b": 8},
    },
    "hoverlabel": {
        "bgcolor":     "#1B2431",
        "bordercolor": "#1B2431",
        "font": {
            "family": "Inter, Segoe UI, sans-serif",
            "size":   12,
            "color":  "#FFFFFF",
        },
    },
    "colorway": CHART_PALETTE,
}

# ---------------------------------------------------------------------------
# CHART_AXES — kwargs para fig.update_xaxes() / fig.update_yaxes()
# Uso: fig.update_xaxes(**CHART_AXES)  |  fig.update_yaxes(**CHART_AXES)
# ---------------------------------------------------------------------------

CHART_AXES = {
    "showgrid":      True,
    "gridcolor":     "#F0F0F0",   # Grilla muy sutil
    "gridwidth":     1,
    "griddash":      "solid",

    "zeroline":      True,
    "zerolinecolor": "#D2D0CE",
    "zerolinewidth": 1,

    "showline":      False,       # Sin líneas de ejes axiales
    "linecolor":     "rgba(0,0,0,0)",

    "ticks":         "",          # Sin marcas de graduación
    "tickcolor":     "#8A8886",
    "tickfont": {
        "family": "Inter, Segoe UI, sans-serif",
        "size":   11,
        "color":  "#8A8886",
    },
    "title_font": {
        "family": "Inter, Segoe UI, sans-serif",
        "size":   12,
        "color":  "#605E5C",
    },
    "automargin": True,
}

# ---------------------------------------------------------------------------
# STATUS_COLORS — estados de actividades P6
# ---------------------------------------------------------------------------

STATUS_COLORS = {
    "TK_NotStart":  "#D2D0CE",   # Gris claro — No iniciada
    "TK_Active":    "#0078D4",   # Azul Microsoft — En progreso
    "TK_Complete":  "#107C10",   # Verde — Completada
}

# ---------------------------------------------------------------------------
# STATUS_LABELS — etiquetas en español para los estados P6
# ---------------------------------------------------------------------------

STATUS_LABELS = {
    "TK_NotStart": "No Iniciada",
    "TK_Active":   "En Progreso",
    "TK_Complete": "Completada",
}
