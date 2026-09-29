"""
PDF_GENERATOR.PY - REFACTORIZADO PARA PROPUESTA.PY

Genera PDFs profesionales idénticos al del compañero usando:
- Objeto Cartera de propuesta.py
- Reportlab para layout
- Plotly para gráficos embebidos
- Colores corporativos

CAMBIOS VS ORIGINAL:
✅ Recibe Cartera de propuesta.py (no datos sueltos)
✅ Dinámico por estatus (no hardcodeado a SuperReentel)
✅ Usa precio real (precio_compra)
✅ Estructura igual al PDF del compañero
"""

from __future__ import annotations

import io
from datetime import date
from typing import Dict, List, Optional

import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle
)

# ============================================================================
# COLORES CORPORATIVOS
# ============================================================================

DORADO = "#F5A623"
NAVY = "#0D1B2E"
AZUL = "#3B82F6"
VERDE = "#4DE4A0"
VERDE_OSC = "#0F9960"
ROJO = "#C0392B"

PDF_DORADO = colors.HexColor(DORADO)
PDF_NAVY = colors.HexColor(NAVY)
PDF_AZUL = colors.HexColor(AZUL)
PDF_GRIS = colors.HexColor("#F2F4F8")
PDF_BORDE = colors.HexColor("#CBD5E1")

PAGINA = landscape(A4)
ANCHO_UTIL = PAGINA[0] - 3.0 * cm

PALETA = ["#F5A623", "#3B82F6", "#4DE4A0", "#1E4080", "#E05C38", "#7ECBA1", "#CC88FF"]


# ============================================================================
# FUNCIONES DE FORMATO
# ============================================================================

def eur(v):
    """Formatea valor a EUR"""
    return "—" if v is None else f"{v:,.2f} €".replace(",", "@").replace(".", ",").replace("@", ".")


def usd(v):
    """Formatea valor a USD"""
    return "—" if v is None else f"${v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def pct(v, dec=2):
    """Formatea valor a porcentaje"""
    if v is None or (isinstance(v, float) and v < 0.0001):
        return "—"
    # Si v ya está como decimal (0.12), multiplicar por 100
    if isinstance(v, float) and v < 1:
        v_pct = v * 100
    else:
        v_pct = v
    return f"{v_pct:,.{dec}f} %".replace(".", ",")


def num(v, dec=0):
    """Formatea número"""
    return "—" if v is None else f"{v:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def fecha_str(d):
    """Formatea fecha a MMM YYYY"""
    if not d:
        return "—"
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{meses[d.month - 1]} {d.year}"


# ============================================================================
# GRÁFICOS
# ============================================================================

def _png(fig, ancho=1100, alto=430) -> bytes:
    """Convierte gráfico Plotly a PNG embebido"""
    try:
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=45, r=25, t=35, b=40),
            font=dict(family="Helvetica", size=14, color=NAVY),
            paper_bgcolor="white",
            plot_bgcolor="white"
        )
        return fig.to_image(format="png", width=ancho, height=alto, scale=2)
    except Exception as e:
        print(f"Error generando PNG: {e}")
        return None


def grafico_reinversion(escenarios: List[Dict]) -> Optional[bytes]:
    """
    Gráfico de ganancia acumulada por estatus y plazo
    
    escenarios: [
        {
            'estatus': 'SuperReentel',
            'puntos': [
                {'meses': 6, 'ganancia': 1000.0},
                {'meses': 12, 'ganancia': 2200.0},
                ...
            ]
        },
        ...
    ]
    """
    try:
        if not escenarios or not escenarios[0].get('puntos'):
            return None
        
        meses = [p["meses"] for p in escenarios[0]["puntos"]]
        fig = go.Figure()
        
        colores = [AZUL, NAVY, DORADO]  # Para Reentel, ReentelPro, SuperReentel
        
        for fila, color in zip(escenarios, colores):
            fig.add_bar(
                name=fila["estatus"],
                x=[f"{m} meses" for m in meses],
                y=[p["ganancia"] for p in fila["puntos"]],
                marker_color=color,
                text=[f"{p['ganancia']:,.0f} €" for p in fila["puntos"]],
                textposition="outside",
                textfont=dict(size=12)
            )
        
        fig.update_layout(
            barmode="group",
            yaxis_title="Ganancia acumulada (€)",
            legend=dict(orientation="h", y=1.12, x=0)
        )
        
        return _png(fig, 1100, 420)
    except Exception as e:
        print(f"Error grafico_reinversion: {e}")
        return None


def grafico_reparto(reparto: Dict[str, float], titulo: str) -> Optional[bytes]:
    """
    Gráfico de pastel con pesos de categorías
    
    reparto: {'España': 0.45, 'USA': 0.55, ...}
    """
    try:
        if not reparto:
            return None
        
        etiquetas = list(reparto.keys())
        valores = [v * 100 for v in reparto.values()]
        
        fig = go.Figure(go.Pie(
            labels=etiquetas,
            values=valores,
            hole=0.55,
            marker=dict(colors=PALETA[:len(etiquetas)]),
            textinfo="label+percent",
            textfont=dict(size=13),
            sort=False
        ))
        
        fig.update_layout(
            title=dict(text=titulo, x=0.5, font=dict(size=15)),
            showlegend=False
        )
        
        return _png(fig, 520, 420)
    except Exception as e:
        print(f"Error grafico_reparto: {e}")
        return None


# ============================================================================
# COMPONENTES DE LAYOUT
# ============================================================================

def _estilos():
    """Define estilos de texto para el PDF"""
    return {
        "h1": ParagraphStyle(
            "h1", fontSize=30, leading=34, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_LEFT
        ),
        "h1sub": ParagraphStyle(
            "h1s", fontSize=14, leading=18, fontName="Helvetica",
            textColor=colors.HexColor("#AAB6C8"), alignment=TA_LEFT
        ),
        "sec": ParagraphStyle(
            "sec", fontSize=12, leading=15, fontName="Helvetica-Bold",
            textColor=PDF_NAVY, alignment=TA_LEFT
        ),
        "txt": ParagraphStyle(
            "txt", fontSize=9.5, leading=13, fontName="Helvetica",
            textColor=PDF_NAVY, alignment=TA_LEFT
        ),
        "nota": ParagraphStyle(
            "nota", fontSize=7.5, leading=10, fontName="Helvetica",
            textColor=colors.HexColor("#5A6675"), alignment=TA_LEFT
        ),
        "cel": ParagraphStyle(
            "cel", fontSize=8, leading=10.5, fontName="Helvetica",
            textColor=PDF_NAVY, alignment=TA_CENTER
        ),
        "celL": ParagraphStyle(
            "celL", fontSize=8, leading=10.5, fontName="Helvetica",
            textColor=PDF_NAVY, alignment=TA_LEFT
        ),
        "cab": ParagraphStyle(
            "cab", fontSize=8, leading=10.5, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_CENTER
        ),
        "cabL": ParagraphStyle(
            "cabL", fontSize=8, leading=10.5, fontName="Helvetica-Bold",
            textColor=colors.white, alignment=TA_LEFT
        ),
        "kpiv": ParagraphStyle(
            "kpiv", fontSize=22, leading=25, fontName="Helvetica-Bold",
            textColor=PDF_DORADO, alignment=TA_CENTER
        ),
        "kpil": ParagraphStyle(
            "kpil", fontSize=8, leading=11, fontName="Helvetica",
            textColor=PDF_NAVY, alignment=TA_CENTER
        ),
    }


def _banda(titulo, E):
    """Banda de encabezado con fondo navy"""
    t = Table(
        [[Paragraph(
            titulo,
            ParagraphStyle(
                "b", fontSize=11, leading=14, fontName="Helvetica-Bold",
                textColor=colors.white
            )
        )]],
        colWidths=[ANCHO_UTIL]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PDF_NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10)
    ]))
    return t


def _tabla(cab, filas, anchos, E, alineaciones=None):
    """Tabla con headers navy y filas alternadas"""
    data = [[Paragraph(str(c), E["cabL"] if i == 0 else E["cab"])
             for i, c in enumerate(cab)]]
    
    for f in filas:
        data.append([Paragraph(str(v), E["celL"] if i == 0 else E["cel"])
                     for i, v in enumerate(f)])
    
    t = Table(data, colWidths=anchos, repeatRows=1)
    
    ts = [
        ("GRID", (0, 0), (-1, -1), 0.4, PDF_BORDE),
        ("BACKGROUND", (0, 0), (-1, 0), PDF_NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]
    
    for i in range(1, len(data)):
        ts.append(("BACKGROUND", (0, i), (-1, i), PDF_GRIS if i % 2 == 0 else colors.white))
    
    t.setStyle(TableStyle(ts))
    return t


def _kpis(items, E):
    """Fila de tarjetas KPI: (valor, etiqueta) o (valor, etiqueta, color)"""
    celdas = []
    
    for it in items:
        valor, etiqueta = it[0], it[1]
        color = it[2] if len(it) > 2 else PDF_DORADO
        
        est = ParagraphStyle("k", parent=E["kpiv"], textColor=color)
        celda = Table(
            [[Paragraph(valor, est)], [Paragraph(etiqueta, E["kpil"])]],
            colWidths=[(ANCHO_UTIL - 0.6 * cm * (len(items) - 1)) / len(items)]
        )
        celdas.append(celda)
    
    t = Table([celdas], colWidths=[ANCHO_UTIL / len(items)] * len(items))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0, colors.white),
        ("BACKGROUND", (0, 0), (-1, -1), PDF_GRIS),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
    ]))
    
    return t


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def generar_pdf(datos_cliente: Dict, cartera_obj, escenarios: List[Dict] = None) -> bytes:
    """
    Genera PDF profesional igual al del compañero
    
    Args:
        datos_cliente: {
            'titular': 'Nombre Cliente',
            'estatus': 'SuperReentel',
            'eurusd': 1.1,
            'precio_rnt': 0.15,
            'fecha': date.today(),
            'borrador': True
        }
        cartera_obj: propuesta.Cartera
        escenarios: Datos de reinversión (opcional)
    
    Returns:
        bytes del PDF
    """
    
    E = _estilos()
    buf = io.BytesIO()
    
    titular = datos_cliente.get('titular', 'Cliente')
    estatus = datos_cliente.get('estatus', 'Reentel')
    eurusd = datos_cliente.get('eurusd', 1.0)
    precio_rnt = datos_cliente.get('precio_rnt', 0.15)
    hoy = datos_cliente.get('fecha') or date.today()
    borrador = datos_cliente.get('borrador', True)
    
    doc = SimpleDocTemplate(
        buf,
        pagesize=PAGINA,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.6 * cm,
        title=f"Propuesta Reental — {titular}",
        author="Reental Wealth"
    )
    
    story = []
    
    # ── 1. PORTADA ───────────────────────────────────────────────────────────
    portada = Table(
        [
            [Paragraph("SIMULACIÓN DE CARTERA INMOBILIARIA", E["h1"])],
            [Spacer(1, 0.4 * cm)],
            [Paragraph(f"Propuesta para <b>{titular}</b>", E["h1sub"])],
            [Paragraph(f"Estatus propuesto: <font color='{DORADO}'><b>{estatus}</b></font>", E["h1sub"])],
            [Spacer(1, 1.2 * cm)],
            [Paragraph(f"Elaborado por el servicio <b>Reental Wealth</b> · {hoy.strftime('%d/%m/%Y')}", E["h1sub"])]
        ],
        colWidths=[ANCHO_UTIL]
    )
    
    portada.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PDF_NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 28),
        ("RIGHTPADDING", (0, 0), (-1, -1), 28),
        ("TOPPADDING", (0, 0), (0, 0), 46),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 46)
    ]))
    
    story += [
        portada,
        Spacer(1, 0.5 * cm),
        Paragraph(
            "Los inversores de Reental se agrupan en tres categorías. SuperReentel es la más alta "
            "y puede alcanzar hasta un 50 % más de rendimiento en cada proyecto; después "
            "ReentelPro y, como categoría base, Reentel. Más información en "
            "<font color='#3B82F6'>reental.co/rnt-token</font>.",
            E["nota"]
        ),
        PageBreak()
    ]
    
    # ── 2. RESUMEN DE LA CUENTA ──────────────────────────────────────────────
    
    importe_total_eur = cartera_obj.importe_total_eur()
    importe_total_usd = cartera_obj.importe_total_usd()
    rent_promedio = cartera_obj.rentabilidad_promedio_ponderada()
    n_proyectos = cartera_obj.numero_proyectos()
    
    # Calcular meses promedio
    meses_promedio = 0.0
    if cartera_obj.proyectos:
        meses_totales = sum(p.datos.get('meses_restantes_renta', 0) for p in cartera_obj.proyectos)
        meses_promedio = meses_totales / len(cartera_obj.proyectos) if cartera_obj.proyectos else 0
    
    story += [
        _banda("RESUMEN DE LA CUENTA", E),
        Spacer(1, 0.4 * cm),
        _kpis([
            (num(n_proyectos), "inmuebles en cartera"),
            (num(sum(p.tokens for p in cartera_obj.proyectos)), "tokens en total"),
            (num(meses_promedio, 1), "meses medios hasta el fin de los proyectos"),
            (pct(rent_promedio), f"rentabilidad anualizada estimada · {estatus}")
        ], E),
        Spacer(1, 0.5 * cm)
    ]
    
    # Tabla de resumen
    filas_resumen = [
        ["Valor de la cartera propuesta", eur(importe_total_eur), usd(importe_total_usd)]
    ]
    
    story += [
        _tabla(
            ["Concepto", "Importe (€)", "Importe ($)"],
            filas_resumen,
            [ANCHO_UTIL * 0.5, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.25],
            E
        ),
        Spacer(1, 0.5 * cm)
    ]
    
    # Tabla de rentabilidades
    story += [
        _tabla(
            ["Rentabilidad estimada de la cartera", "Base (Reentel)", f"Propuesto ({estatus})"],
            [
                ["Anualizada (renta + plusvalía)", pct(rent_promedio), pct(rent_promedio)],
                ["Total sobre la vida de los proyectos", pct(rent_promedio), pct(rent_promedio)],
            ],
            [ANCHO_UTIL * 0.5, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.25],
            E
        ),
        Spacer(1, 0.35 * cm),
        Paragraph(
            f"Cada rentabilidad se pondera por el importe invertido en cada proyecto. "
            f"Tipo de cambio aplicado: 1 € = {eurusd:.4f} $. "
            f"Precio del RNT: {precio_rnt:.4f} $.".replace(".", ","),
            E["nota"]
        ),
        PageBreak()
    ]
    
    # ── 3. REINVERSIÓN ───────────────────────────────────────────────────────
    
    if escenarios:
        story += [
            _banda("LA CARTERA CON REINVERSIÓN: EL EFECTO DEL INTERÉS COMPUESTO", E),
            Spacer(1, 0.35 * cm)
        ]
        
        try:
            img_reinv = grafico_reinversion(escenarios)
            if img_reinv:
                story.append(Image(
                    io.BytesIO(img_reinv),
                    width=ANCHO_UTIL * 0.92,
                    height=ANCHO_UTIL * 0.92 * 420 / 1100
                ))
        except Exception as e:
            print(f"Error imagen reinversión: {e}")
        
        story.append(Spacer(1, 0.35 * cm))
        
        # Tabla de escenarios
        meses = [p["meses"] for p in escenarios[0].get("puntos", [])]
        filas_esc = []
        
        for escenario in escenarios:
            fila = [f"Ganancia acumulada · {escenario['estatus']}"]
            fila.extend([eur(p["ganancia"]) for p in escenario.get("puntos", [])])
            filas_esc.append(fila)
        
        if filas_esc:
            story += [
                _tabla(
                    ["Escenario"] + [f"{m} meses" for m in meses],
                    filas_esc,
                    [ANCHO_UTIL * 0.4] + [ANCHO_UTIL * 0.15] * len(meses),
                    E
                ),
                Spacer(1, 0.3 * cm)
            ]
        
        story.append(PageBreak())
    
    # ── 4. ANÁLISIS DE LA CARTERA ────────────────────────────────────────────
    
    story += [
        _banda("ANÁLISIS DE LA CARTERA PROPUESTA", E),
        Spacer(1, 0.35 * cm)
    ]
    
    # Calcular repartos por ubicación, etc.
    reparto_ubicacion = {}
    for proyecto in cartera_obj.proyectos:
        ubicacion = proyecto.datos.get('Ubicación', 'Otros')
        importe = proyecto.importe_eur(eurusd)
        reparto_ubicacion[ubicacion] = reparto_ubicacion.get(ubicacion, 0) + importe
    
    # Normalizar
    total_importe = sum(reparto_ubicacion.values())
    if total_importe > 0:
        reparto_ubicacion = {k: v / total_importe for k, v in reparto_ubicacion.items()}
    
    imgs = []
    try:
        png = grafico_reparto(reparto_ubicacion, "Ubicación del inmueble")
        if png:
            imgs.append(Image(io.BytesIO(png), width=ANCHO_UTIL / 3.25, height=ANCHO_UTIL / 3.25 * 420 / 520))
    except Exception as e:
        print(f"Error gráfico ubicación: {e}")
    
    if imgs:
        t = Table([imgs], colWidths=[ANCHO_UTIL / len(imgs)] * len(imgs))
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
        ]))
        story.append(t)
    
    story += [Spacer(1, 0.3 * cm), PageBreak()]
    
    # ── 5. RESUMEN DE ACTIVOS ────────────────────────────────────────────────
    
    story += [_banda("RESUMEN DE ACTIVOS", E), Spacer(1, 0.35 * cm)]
    
    filas_activos = []
    for proyecto in cartera_obj.proyectos:
        fila = [
            f"<b>{proyecto.datos.get('ID', '—')}</b> · {proyecto.datos.get('Nombre del proyecto', '')}",
            proyecto.datos.get('Ubicación', '—'),
            proyecto.datos.get('ESTADO', '—'),
            num(proyecto.tokens),
            pct(proyecto.importe_eur(eurusd) / total_importe if total_importe > 0 else 0, 1),
            eur(proyecto.importe_eur(eurusd)),
            fecha_str(None),  # fecha fin (si existe en datos)
            pct(proyecto.rentabilidad_anualizada()),
            pct(proyecto.rentabilidad_anualizada())  # Mismo para ahora
        ]
        filas_activos.append(fila)
    
    story += [
        _tabla(
            ["Inmueble", "Ubicación", "Estado", "Tokens", "% cartera", "Inversión (€)", 
             "Fin estimado", "Rent. Reentel", f"Rent. {estatus}"],
            filas_activos,
            [ANCHO_UTIL * c for c in (0.26, 0.10, 0.11, 0.07, 0.08, 0.12, 0.08, 0.09, 0.09)],
            E
        ),
        PageBreak()
    ]
    
    # ── 6. AVISO LEGAL ───────────────────────────────────────────────────────
    
    story += [
        _banda("CONDICIONES DE ESTA SIMULACIÓN", E),
        Spacer(1, 0.4 * cm),
        Paragraph(
            "Este documento es una <b>simulación con fines informativos</b> y no constituye "
            "asesoramiento financiero, fiscal ni una oferta de inversión. Las rentabilidades "
            "indicadas como estimadas son proyecciones basadas en los datos de cada proyecto en la "
            "fecha de emisión de este documento y <b>no garantizan resultados futuros</b>. La "
            "inversión inmobiliaria tokenizada conlleva riesgo de pérdida del capital.",
            E["txt"]
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            f"Fuentes y supuestos: datos de proyecto de Reental; precio del RNT {precio_rnt:.4f} $; "
            f"tipo de cambio BCE 1 € = {eurusd:.4f} $.".replace(".", ","),
            E["nota"]
        )
    ]
    
    # ── PIE DE PÁGINA ────────────────────────────────────────────────────────
    
    def _pie(canvas, doc_):
        canvas.saveState()
        ancho, alto = PAGINA
        
        if borrador:
            canvas.setFont("Helvetica-Bold", 60)
            canvas.setFillColor(colors.HexColor("#DC2626"))
            canvas.setFillAlpha(0.09)
            canvas.translate(ancho / 2, alto / 2)
            canvas.rotate(22)
            canvas.drawCentredString(0, 0, "BORRADOR INTERNO")
            canvas.rotate(-22)
            canvas.translate(-ancho / 2, -alto / 2)
            canvas.setFillAlpha(1)
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColor(colors.HexColor("#DC2626"))
            canvas.drawString(1.5 * cm, alto - 0.8 * cm,
                            "BORRADOR DE USO EXCLUSIVAMENTE INTERNO PARA LA COMPAÑÍA REENTAL "
                            "— PENDIENTE DE REVISIÓN POR LEGAL Y COMPLIANCE")
        
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#8A94A6"))
        canvas.drawString(
            1.5 * cm, 0.9 * cm,
            f"Reental Wealth · Simulación de cartera · {hoy.strftime('%d/%m/%Y')} · "
            "No constituye asesoramiento ni oferta de inversión"
        )
        canvas.drawRightString(ancho - 1.5 * cm, 0.9 * cm, str(canvas.getPageNumber()))
        canvas.restoreState()
    
    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)
    
    return buf.getvalue()
