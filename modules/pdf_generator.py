"""
PDF_GENERATOR.PY - Dossier comercial de la cartera simulada.

Sigue el guion y el diseño del documento de propuesta del equipo:
portada, resumen de la cuenta, comparativa por estatus, análisis de la
cartera, resumen de activos y condiciones de la simulación.

Todo se dibuja con reportlab (también los gráficos), así que no necesita
librerías adicionales.

Los datos llegan ya calculados desde el Paso 5 de la app en `resumen`,
para que el PDF muestre exactamente las mismas cifras que la pantalla.
"""

from io import BytesIO
from datetime import date

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.doughnut import Doughnut
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ─── Colores y página ────────────────────────────────────────────────────────

DORADO = "#F5A623"
NAVY = "#0D1B2E"
AZUL = "#3B82F6"

PDF_DORADO = colors.HexColor(DORADO)
PDF_NAVY = colors.HexColor(NAVY)
PDF_GRIS = colors.HexColor("#F2F4F8")
PDF_BORDE = colors.HexColor("#CBD5E1")

PALETA = ["#F5A623", "#3B82F6", "#4DE4A0", "#1E4080", "#E05C38", "#7ECBA1", "#CC88FF"]

PAGINA = landscape(A4)
ANCHO_UTIL = PAGINA[0] - 3.0 * cm

ESTATUS_ORDEN = ["Reentel", "ReentelPro", "SuperReentel"]


# ─── Formato (estilo español: 1.234,56) ──────────────────────────────────────

def _num(v, dec=2):
    if v is None:
        return "—"
    return f"{v:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _dinero(v, divisa="EUR"):
    if v is None:
        return "—"
    return f"${_num(v)}" if divisa == "USD" else f"{_num(v)} €"


def _pct(v, dec=2):
    """v en unidades de porcentaje (10.22 -> '10,22 %')."""
    return "—" if v is None else f"{_num(v, dec)} %"


# ─── Estilos y piezas ────────────────────────────────────────────────────────

def _estilos():
    return {
        "h1": ParagraphStyle("h1", fontSize=30, leading=34, fontName="Helvetica-Bold",
                             textColor=colors.white, alignment=TA_LEFT),
        "h1sub": ParagraphStyle("h1s", fontSize=14, leading=18, fontName="Helvetica",
                                textColor=colors.HexColor("#AAB6C8"), alignment=TA_LEFT),
        "txt": ParagraphStyle("txt", fontSize=9.5, leading=13, fontName="Helvetica",
                              textColor=PDF_NAVY, alignment=TA_LEFT),
        "nota": ParagraphStyle("nota", fontSize=7.5, leading=10, fontName="Helvetica",
                               textColor=colors.HexColor("#5A6675"), alignment=TA_LEFT),
        "cel": ParagraphStyle("cel", fontSize=8, leading=10.5, fontName="Helvetica",
                              textColor=PDF_NAVY, alignment=TA_CENTER),
        "celL": ParagraphStyle("celL", fontSize=8, leading=10.5, fontName="Helvetica",
                               textColor=PDF_NAVY, alignment=TA_LEFT),
        "cab": ParagraphStyle("cab", fontSize=8, leading=10.5, fontName="Helvetica-Bold",
                              textColor=colors.white, alignment=TA_CENTER),
        "cabL": ParagraphStyle("cabL", fontSize=8, leading=10.5, fontName="Helvetica-Bold",
                               textColor=colors.white, alignment=TA_LEFT),
        "kpiv": ParagraphStyle("kpiv", fontSize=20, leading=24, fontName="Helvetica-Bold",
                               textColor=PDF_DORADO, alignment=TA_CENTER),
        "kpil": ParagraphStyle("kpil", fontSize=8, leading=11, fontName="Helvetica",
                               textColor=PDF_NAVY, alignment=TA_CENTER),
    }


def _banda(titulo):
    t = Table([[Paragraph(titulo, ParagraphStyle("b", fontSize=11, leading=14,
                                                 fontName="Helvetica-Bold",
                                                 textColor=colors.white))]],
              colWidths=[ANCHO_UTIL])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PDF_NAVY),
                           ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    return t


def _tabla(cab, filas, anchos, E):
    data = [[Paragraph(str(c), E["cabL"] if i == 0 else E["cab"]) for i, c in enumerate(cab)]]
    for f in filas:
        data.append([Paragraph(str(v), E["celL"] if i == 0 else E["cel"]) for i, v in enumerate(f)])
    t = Table(data, colWidths=anchos, repeatRows=1)
    ts = [("GRID", (0, 0), (-1, -1), 0.4, PDF_BORDE),
          ("BACKGROUND", (0, 0), (-1, 0), PDF_NAVY),
          ("TOPPADDING", (0, 0), (-1, -1), 4),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for i in range(1, len(data)):
        ts.append(("BACKGROUND", (0, i), (-1, i), PDF_GRIS if i % 2 == 0 else colors.white))
    t.setStyle(TableStyle(ts))
    return t


def _kpis(items, E):
    """Fila de tarjetas (valor, etiqueta)."""
    ancho = ANCHO_UTIL / len(items)
    celdas = [Table([[Paragraph(v, E["kpiv"])], [Paragraph(l, E["kpil"])]], colWidths=[ancho - 0.4 * cm])
              for v, l in items]
    t = Table([celdas], colWidths=[ancho] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PDF_GRIS),
                           ("INNERGRID", (0, 0), (-1, -1), 2, colors.white),
                           ("TOPPADDING", (0, 0), (-1, -1), 10),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return t


# ─── Gráficos (reportlab) ────────────────────────────────────────────────────

def _donut(reparto, titulo, ancho, alto=7.5 * cm):
    """Anillo con el peso (%) de cada categoría y su leyenda debajo."""
    d = Drawing(ancho, alto)
    d.add(String(ancho / 2, alto - 12, titulo, fontName="Helvetica-Bold",
                 fontSize=10, fillColor=PDF_NAVY, textAnchor="middle"))

    items = [(k, v) for k, v in reparto.items() if v and v > 0]
    if not items:
        return d

    radio = min(ancho, alto) * 0.30
    dn = Doughnut()
    dn.x = ancho / 2 - radio
    dn.y = alto - 22 - 2 * radio
    dn.width = dn.height = 2 * radio
    dn.data = [v for _, v in items]
    dn.labels = [f"{_num(v, 0)} %" for _, v in items]
    dn.innerRadiusFraction = 0.55
    dn.slices.strokeColor = colors.white
    dn.slices.strokeWidth = 1
    dn.slices.fontName = "Helvetica"
    dn.slices.fontSize = 7
    dn.slices.fontColor = PDF_NAVY
    dn.slices.labelRadius = 1.25
    for i in range(len(items)):
        dn.slices[i].fillColor = colors.HexColor(PALETA[i % len(PALETA)])
    d.add(dn)

    ley = Legend()
    ley.x = 10
    ley.y = dn.y - 14
    ley.fontName = "Helvetica"
    ley.fontSize = 7
    ley.alignment = "right"
    ley.columnMaximum = 3
    ley.deltax = ancho / 2 - 10
    ley.dxTextSpace = 4
    ley.boxAnchor = "nw"
    ley.colorNamePairs = [(colors.HexColor(PALETA[i % len(PALETA)]), f"{k} — {_num(v, 1)} %")
                          for i, (k, v) in enumerate(items)]
    d.add(ley)
    return d


def _barras_estatus(comparativa, divisa, meses, ancho, alto=6.5 * cm):
    """Ganancia a N meses por estatus."""
    d = Drawing(ancho, alto)
    filas = [c for c in comparativa if c.get("ganancia") is not None]
    if not filas:
        return d

    bc = VerticalBarChart()
    bc.x, bc.y = 55, 30
    bc.width, bc.height = ancho - 80, alto - 55
    bc.data = [[c["ganancia"] for c in filas]]
    bc.categoryAxis.categoryNames = [c["estatus"] for c in filas]
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 8
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.labelTextFormat = lambda v: _num(v, 0)
    bc.barWidth = 18
    bc.barLabelFormat = lambda v: _dinero(v, divisa)
    bc.barLabels.fontName = "Helvetica-Bold"
    bc.barLabels.fontSize = 7
    bc.barLabels.nudge = 7
    colores = [AZUL, "#1E4080", DORADO]
    for i in range(len(filas)):
        bc.bars[(0, i)].fillColor = colors.HexColor(colores[i % 3])
        bc.bars[(0, i)].strokeColor = None
    d.add(bc)
    d.add(String(ancho / 2, alto - 10, f"Ganancia a {meses} meses por estatus",
                 fontName="Helvetica-Bold", fontSize=10, fillColor=PDF_NAVY, textAnchor="middle"))
    return d


# ─── Resumen mínimo si la app no lo envía ────────────────────────────────────

def _resumen_basico(datos_cliente, proyectos_cartera, distribuciones, df_proyectos, precios_compra):
    filas = []
    for p in proyectos_cartera:
        fila = df_proyectos[df_proyectos["ID"] == p["id"]]
        ub = fila.iloc[0].get("Ubicación", "") if len(fila) else ""
        info = precios_compra.get(p["id"], {})
        filas.append({
            "Proyecto": p["nombre"], "Ubicación": ub,
            "Precio de compra": f"{_num(info.get('precio', 0))} {info.get('divisa', 'EUR')} ({info.get('tipo', 'Emisión')})",
            "Tipo de dividendo": "-", "Rentabilidad anualizada": None, "Rentabilidad total": None,
            "% cartera": distribuciones.get(p["id"], {}).get("porcentaje", 0), "Importe": None,
        })
    return {"divisa": (datos_cliente.get("divisa") or "EUR").upper(), "estatus": datos_cliente.get("estatus") or "Reentel",
            "n_inmuebles": len(filas), "proyectos": filas, "repartos": {}, "comparativa": [],
            "tipo_cambio": None, "precio_rnt": None, "staking": None, "rnt_estatus": 0,
            "importe_inmuebles": None, "coste_estatus": None, "capital_total": None,
            "rentabilidad_media": None, "meses": 36}


# ─── Documento ───────────────────────────────────────────────────────────────

def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_proyectos,
                        precios_compra=None, resumen=None):
    """Genera el PDF y devuelve sus bytes.

    `resumen` lo prepara el Paso 5 de la app con todas las cifras ya calculadas.
    """
    precios_compra = precios_compra or {}
    R = resumen or _resumen_basico(datos_cliente, proyectos_cartera, distribuciones,
                                   df_proyectos, precios_compra)
    E = _estilos()
    hoy = date.today()

    divisa = R.get("divisa", "EUR")
    estatus = R.get("estatus", "Reentel")
    tc = R.get("tipo_cambio")

    def en(importe, hacia):
        """Convierte un importe de la divisa del cliente a EUR o USD."""
        if importe is None or tc is None:
            return importe if hacia == divisa else None
        if hacia == divisa:
            return importe
        return importe * tc if divisa == "EUR" else importe / tc

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=PAGINA,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.3 * cm, bottomMargin=1.6 * cm,
                            title=f"Propuesta Reental — {datos_cliente.get('nombre', '')}",
                            author="Reental Wealth")
    story = []

    # ── 1. Portada ───────────────────────────────────────────────────────────
    portada = Table(
        [[Paragraph("SIMULACIÓN DE CARTERA INMOBILIARIA", E["h1"])],
         [Spacer(1, 0.4 * cm)],
         [Paragraph(f"Propuesta para <b>{datos_cliente.get('nombre') or '—'}</b>", E["h1sub"])],
         [Paragraph(f"Estatus propuesto: <font color='{DORADO}'><b>{estatus}</b></font>", E["h1sub"])],
         [Spacer(1, 1.2 * cm)],
         [Paragraph(f"Elaborado por el servicio <b>Reental Wealth</b> · {hoy.strftime('%d/%m/%Y')}",
                    E["h1sub"])]],
        colWidths=[ANCHO_UTIL])
    portada.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PDF_NAVY),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 28),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 28),
                                 ("TOPPADDING", (0, 0), (0, 0), 46),
                                 ("BOTTOMPADDING", (0, -1), (-1, -1), 46)]))
    inversor = [
        ["Titular", datos_cliente.get("nombre", "—"), "Capital a invertir", f"{datos_cliente.get('capital', '—')} {divisa}"],
        ["Email", datos_cliente.get("email", "—"), "Objetivo", datos_cliente.get("objetivo", "—")],
        ["Estatus elegido", estatus, "Distribución de la cartera", datos_cliente.get("distribucion", "—")],
    ]
    story += [portada, Spacer(1, 0.5 * cm),
              _tabla(["Inversor", "", "", ""], inversor,
                     [ANCHO_UTIL * c for c in (0.14, 0.30, 0.18, 0.38)], E),
              Spacer(1, 0.4 * cm),
              Paragraph("Los inversores de Reental se agrupan en tres categorías. SuperReentel es la más alta "
                        "y puede alcanzar hasta un 50 % más de rendimiento en cada proyecto; después ReentelPro "
                        "y, como categoría base, Reentel.", E["nota"]),
              PageBreak()]

    # ── 2. Resumen de la cuenta ──────────────────────────────────────────────
    story += [_banda("RESUMEN DE LA CUENTA"), Spacer(1, 0.4 * cm),
              _kpis([(_num(R.get("n_inmuebles"), 0), "inmuebles en cartera"),
                     (_dinero(R.get("importe_inmuebles"), divisa), "invertido en inmuebles"),
                     (_dinero(R.get("coste_estatus"), divisa), f"coste del estatus {estatus}"),
                     (_pct(R.get("rentabilidad_media")), f"rentabilidad anualizada estimada · {estatus}")], E),
              Spacer(1, 0.5 * cm)]

    filas_cuenta = [
        ["Inversión en inmuebles", _dinero(en(R.get("importe_inmuebles"), "EUR")),
         _dinero(en(R.get("importe_inmuebles"), "USD"), "USD")],
        [f"Adquisición del estatus {estatus} ({_num(R.get('rnt_estatus'), 0)} RNT)",
         _dinero(en(R.get("coste_estatus"), "EUR")), _dinero(en(R.get("coste_estatus"), "USD"), "USD")],
        ["<b>Capital total desplegado</b>", f"<b>{_dinero(en(R.get('capital_total'), 'EUR'))}</b>",
         f"<b>{_dinero(en(R.get('capital_total'), 'USD'), 'USD')}</b>"],
    ]
    story += [_tabla(["Concepto", "Importe (€)", "Importe ($)"], filas_cuenta,
                     [ANCHO_UTIL * 0.5, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.25], E),
              Spacer(1, 0.5 * cm)]

    comp = {c["estatus"]: c for c in R.get("comparativa", [])}
    if comp:
        base, prop = comp.get("Reentel", {}), comp.get(estatus, {})
        story.append(_tabla(
            ["Rentabilidad estimada de la cartera", "Reentel (base)", f"{estatus} (propuesto)"],
            [["Anualizada media", _pct(base.get("rent_anual")), _pct(prop.get("rent_anual"))],
             [f"Ganancia a {R.get('meses', 36)} meses", _dinero(base.get("ganancia"), divisa),
              _dinero(prop.get("ganancia"), divisa)]],
            [ANCHO_UTIL * 0.5, ANCHO_UTIL * 0.25, ANCHO_UTIL * 0.25], E))
        story.append(Spacer(1, 0.35 * cm))

    story += [Paragraph(
        "Cada rentabilidad se pondera por el porcentaje de la cartera invertido en cada proyecto. "
        f"Tipo de cambio aplicado: 1 € = {_num(tc, 4)} $. Precio del RNT tomado del pool RNT/USDT: "
        f"{_num(R.get('precio_rnt'), 4)} $.", E["nota"]),
        PageBreak()]

    # ── 3. Comparativa por estatus ───────────────────────────────────────────
    if R.get("comparativa"):
        meses = R.get("meses", 36)
        story += [_banda("COMPARATIVA POR ESTATUS"), Spacer(1, 0.35 * cm),
                  _barras_estatus(R["comparativa"], divisa, meses, ANCHO_UTIL * 0.9),
                  Spacer(1, 0.35 * cm)]
        filas = [[c["estatus"], _dinero(c.get("ganancia"), divisa), _pct(c.get("rent_cartera")),
                  _pct(c.get("rent_total")), _dinero(c.get("coste"), divisa)]
                 for c in R["comparativa"]]
        story += [_tabla(["Estatus", f"Ganancia a {meses} meses", "Rent. sobre la cartera",
                          "Rent. sobre el capital total", "Coste del estatus"], filas,
                         [ANCHO_UTIL * c for c in (0.24, 0.19, 0.19, 0.19, 0.19)], E),
                  Spacer(1, 0.3 * cm),
                  Paragraph(
                      "La ganancia incluye lo que producen los inmuebles con la rentabilidad de cada estatus y "
                      f"el rendimiento del staking de los RNT del estatus ({_pct(R.get('staking'))} anual). "
                      "La rentabilidad sobre el capital total incluye la compra del estatus: el RNT adquirido "
                      "no se consume, se conserva y además genera rendimiento en staking.", E["nota"]),
                  PageBreak()]

    # ── 4. Análisis de la cartera ────────────────────────────────────────────
    repartos = R.get("repartos") or {}
    if repartos:
        story += [_banda("ANÁLISIS DE LA CARTERA PROPUESTA"), Spacer(1, 0.5 * cm)]
        n = len(repartos)
        graficos = [_donut(rep, titulo, ANCHO_UTIL / n - 0.3 * cm) for titulo, rep in repartos.items()]
        t = Table([graficos], colWidths=[ANCHO_UTIL / n] * n)
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story += [t, PageBreak()]

    # ── 5. Resumen de activos ────────────────────────────────────────────────
    story += [_banda("RESUMEN DE ACTIVOS"), Spacer(1, 0.35 * cm)]
    filas = []
    for p in R.get("proyectos", []):
        filas.append([f"<b>{p.get('Proyecto', '')}</b>", p.get("Ubicación", "—"),
                      p.get("Precio de compra", "—"), p.get("Tipo de dividendo", "—"),
                      _pct(p.get("Rentabilidad anualizada")), _pct(p.get("Rentabilidad total")),
                      _pct(p.get("% cartera"), 1), _dinero(p.get("Importe"), divisa)])
    story += [_tabla(["Inmueble", "Ubicación", "Precio de compra", "Tipo de dividendo",
                      f"Rent. anualizada ({estatus})", "Rent. total", "% cartera", "Inversión"],
                     filas, [ANCHO_UTIL * c for c in (0.19, 0.10, 0.17, 0.14, 0.11, 0.09, 0.08, 0.12)], E),
              Spacer(1, 0.3 * cm),
              Paragraph("<b>Emisión</b> = precio oficial del token en su lanzamiento · <b>OTC</b> = precio de "
                        "una oferta real en el mercado secundario en la fecha de este documento.", E["nota"]),
              PageBreak()]

    # ── 6. Condiciones ───────────────────────────────────────────────────────
    story += [_banda("CONDICIONES DE ESTA SIMULACIÓN"), Spacer(1, 0.4 * cm),
              Paragraph(
                  "Este documento es una <b>simulación con fines informativos</b> y no constituye "
                  "asesoramiento financiero, fiscal ni una oferta de inversión. Las rentabilidades indicadas "
                  "como estimadas son proyecciones basadas en los datos de cada proyecto en la fecha de "
                  "emisión de este documento y <b>no garantizan resultados futuros</b>. La inversión "
                  "inmobiliaria tokenizada conlleva riesgo de pérdida del capital. El mercado OTC es menos "
                  "líquido que el mercado primario.", E["txt"]),
              Spacer(1, 0.3 * cm),
              Paragraph(
                  "Fuentes y supuestos: datos de proyecto del maestro de inmuebles de Reental; precio del RNT "
                  f"tomado del pool RNT/USDT ({_num(R.get('precio_rnt'), 4)} $); tipo de cambio de referencia "
                  f"del Banco Central Europeo (1 € = {_num(tc, 4)} $); rendimiento de staking del RNT "
                  f"{_pct(R.get('staking'))}. Los importes en una divisa distinta a la elegida son conversiones "
                  "a la fecha de emisión y variarán con el tipo de cambio.", E["nota"])]

    # ── Pie de página ────────────────────────────────────────────────────────
    def _pie(canvas, doc_):
        canvas.saveState()
        ancho, _alto = PAGINA
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#8A94A6"))
        canvas.drawString(1.5 * cm, 0.9 * cm,
                          f"Reental Wealth · Simulación de cartera · {hoy.strftime('%d/%m/%Y')} · "
                          "No constituye asesoramiento ni oferta de inversión")
        canvas.drawRightString(ancho - 1.5 * cm, 0.9 * cm, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)
    return buf.getvalue()
