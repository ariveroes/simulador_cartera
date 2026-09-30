"""
PDF_GENERATOR.PY - Propuesta de cartera con el formato del documento de Reental Wealth.

Reproduce el documento que genera el Google Sheet del equipo (fondo navy,
cabeceras doradas, tarjetas y páginas en formato presentación 16:9):

  1. Portada
  2. Resumen de la cuenta
  3. La cartera con reinversión
  4. I Análisis de la cartera (distribución geográfica y estado)
  5. II Análisis de la cartera (tipologías en anillo)
  6. Resumen de activos
  7. Análisis por ubicación (fichas de proyecto)
  8. Beneficios de ser Wealth
  9. Beneficios de ser SuperReentel (solo si es el estatus propuesto)

Todo se dibuja con reportlab. Las cifras llegan ya calculadas desde el
Paso 5 de la app en `resumen`, para que coincidan con la pantalla.
"""

from io import BytesIO
from datetime import date

from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.doughnut import Doughnut
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph, Table, TableStyle

# ─── Página y colores ────────────────────────────────────────────────────────

W, H = 960, 540          # formato presentación 16:9
M = 45                   # margen

C = colors.HexColor
BG = C("#0d1b2e")
BG_PORTADA = C("#08111f")
BG_BENEF = C("#0d1420")
CARD = C("#16263b")
CARD_BENEF = C("#1a2235")
BORDE = C("#26374f")
PISTA = C("#1c2a40")
ORO = C("#f5a623")
AZUL = C("#1e4080")
AZUL2 = C("#2a5299")
AZUL_CLARO = C("#7ab0f0")
VERDE = C("#7ecba1")
BLANCO = colors.white
TXT = C("#d3d9e2")
MUTED = C("#8592a6")
TENUE = C("#4f5c70")

PALETA = ["#f5a623", "#4a7fc1", "#1e4080", "#5b7fa6", "#e05c38", "#7ecba1", "#cc88ff"]

ESTADO_COLORES = {  # (fondo, texto)
    "EN EXPLOTACIÓN": ("#123d33", "#4de4a0"),
    "EN REFORMA": ("#3a3220", "#f5a623"),
    "EN CONSTRUCCIÓN": ("#1f3150", "#7ab0f0"),
    "PRELANZAMIENTO": ("#2f2448", "#cc88ff"),
    "FINANCIÁNDOSE": ("#173a4a", "#60d0f0"),
}
ESTADO_BARRA = {"EN EXPLOTACIÓN": ORO, "EN REFORMA": C("#3b4a60"), "EN CONSTRUCCIÓN": AZUL,
                "PRELANZAMIENTO": C("#5b7fa6"), "FINANCIÁNDOSE": C("#5b7fa6")}


# ─── Formato ─────────────────────────────────────────────────────────────────

def _eur(v):
    return "—" if v is None else f"{v:,.2f} €"


def _usd(v):
    return "—" if v is None else f"${v:,.2f}"


def _dinero(v, divisa):
    return _usd(v) if divisa == "USD" else _eur(v)


def _pct(v, dec=2):
    """v en unidades de porcentaje (10.22 -> '10.22%')."""
    return "—" if v is None else f"{v:.{dec}f}%"


def _norm_estado(e):
    s = str(e or "").upper()
    for clave, nombre in (("EXPLOT", "EN EXPLOTACIÓN"), ("REFORM", "EN REFORMA"),
                          ("CONST", "EN CONSTRUCCIÓN"), ("PRELA", "PRELANZAMIENTO"),
                          ("FINAN", "FINANCIÁNDOSE")):
        if clave in s:
            return nombre
    return str(e or "—").upper()


# ─── Primitivas de dibujo ────────────────────────────────────────────────────

def _fondo(c, color):
    c.setFillColor(color)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def _texto(c, x, y, s, size=10, color=TXT, bold=False, anchor="l"):
    fuente = "Helvetica-Bold" if bold else "Helvetica"
    c.setFont(fuente, size)
    c.setFillColor(color)
    if anchor == "c":
        c.drawCentredString(x, y, str(s))
    elif anchor == "r":
        c.drawRightString(x, y, str(s))
    else:
        c.drawString(x, y, str(s))
    return stringWidth(str(s), fuente, size)


def _caja(c, x, y, w, h, fill=CARD, stroke=BORDE, r=8):
    c.setFillColor(fill)
    if stroke is not None:
        c.setStrokeColor(stroke)
        c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke is not None else 0, fill=1)


def _parrafo(c, x, y_top, w, html, size=9, color=TXT, leading=None, align=TA_LEFT, bold=False):
    est = ParagraphStyle("p", fontName="Helvetica-Bold" if bold else "Helvetica", fontSize=size,
                         leading=leading or size * 1.35, textColor=color, alignment=align)
    p = Paragraph(html, est)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def _cabecera(c, titulo):
    """Banda dorada de sección. Devuelve la y disponible debajo."""
    y = H - M - 30
    _caja(c, M, y, W - 2 * M, 30, fill=ORO, stroke=None, r=5)
    _texto(c, M + 16, y + 10, titulo, 12, BG, bold=True)
    return y - 14


def _numero_pagina(c, n):
    _texto(c, W - 28, 16, str(n), 8, TENUE, anchor="r")


def _etiqueta_estado(c, x, y, estado, size=6.5):
    nombre = _norm_estado(estado)
    fondo, color = ESTADO_COLORES.get(nombre, ("#26374f", "#d3d9e2"))
    ancho = stringWidth(nombre, "Helvetica-Bold", size) + 12
    _caja(c, x, y, ancho, size + 7, fill=C(fondo), stroke=None, r=(size + 7) / 2)
    _texto(c, x + 6, y + 3.6, nombre, size, C(color), bold=True)
    return ancho


def _pastilla(c, x, y, texto, fondo, color, size=8):
    ancho = stringWidth(texto, "Helvetica-Bold", size) + 16
    _caja(c, x, y, ancho, size + 9, fill=fondo, stroke=None, r=(size + 9) / 2)
    _texto(c, x + 8, y + 4.5, texto, size, color, bold=True)
    return ancho


def _tabla(c, x, y_top, filas, anchos, cabecera=True, size=8):
    """Tabla oscura. `filas` puede llevar HTML de Paragraph. Devuelve su alto."""
    est = ParagraphStyle("cel", fontName="Helvetica", fontSize=size, leading=size * 1.3,
                         textColor=TXT, alignment=TA_CENTER)
    est_l = ParagraphStyle("celL", parent=est, alignment=TA_LEFT)
    est_cab = ParagraphStyle("cab", parent=est, fontName="Helvetica-Bold", textColor=MUTED)
    est_cab_l = ParagraphStyle("cabL", parent=est_cab, alignment=TA_LEFT)
    data = []
    for i, fila in enumerate(filas):
        es_cab = cabecera and i == 0
        data.append([Paragraph(str(v), (est_cab_l if es_cab else est_l) if j == 0 else (est_cab if es_cab else est))
                     for j, v in enumerate(fila)])
    t = Table(data, colWidths=anchos)
    estilo = [("BACKGROUND", (0, 0), (-1, -1), CARD),
              ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDE),
              ("BOX", (0, 0), (-1, -1), 0.8, BORDE),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 5),
              ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]
    if cabecera:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), C("#1f3048")))
    t.setStyle(TableStyle(estilo))
    _, h = t.wrapOn(c, sum(anchos), 1000)
    t.drawOn(c, x, y_top - h)
    return h


def _barras_h(c, x, y_top, w, items, alto=20, ancho_nombre=130):
    """Barras horizontales: items = [(nombre, pct 0-100, color, texto)]."""
    y = y_top
    pista = w - ancho_nombre - 10
    for nombre, pct, color, texto in items:
        y -= alto
        _texto(c, x + ancho_nombre, y + alto / 2 - 3.5, nombre[:26], 8.5, MUTED, anchor="r")
        _caja(c, x + ancho_nombre + 10, y + 2, pista, alto - 4, fill=PISTA, stroke=None, r=3)
        largo = max(pista * min(pct, 100) / 100, 4)
        _caja(c, x + ancho_nombre + 10, y + 2, largo, alto - 4, fill=color, stroke=None, r=3)
        color_txt = BG if color in (ORO,) else BLANCO
        _texto(c, x + ancho_nombre + 16, y + alto / 2 - 3.2, texto, 8, color_txt, bold=True)
        y -= 5
    return y_top - y


def _tarjeta_donut(c, x, y, w, h, titulo, reparto):
    _caja(c, x, y, w, h)
    _texto(c, x + 16, y + h - 22, titulo.upper(), 10, BLANCO, bold=True)
    items = [(k, v) for k, v in (reparto or {}).items() if v and v > 0]
    if not items:
        _texto(c, x + 16, y + h / 2, "Sin datos", 9, MUTED)
        return
    lado = min(h - 50, 130)
    d = Drawing(lado, lado)
    dn = Doughnut()
    dn.x = dn.y = 0
    dn.width = dn.height = lado
    dn.data = [v for _, v in items]
    dn.innerRadiusFraction = 0.6
    dn.slices.strokeWidth = 0
    dn.slices.strokeColor = CARD
    for i in range(len(items)):
        dn.slices[i].fillColor = C(PALETA[i % len(PALETA)])
    d.add(dn)
    renderPDF.draw(d, c, x + 20, y + (h - 34 - lado) / 2)

    lx = x + 20 + lado + 22
    ly = y + h - 50
    for i, (k, v) in enumerate(items):
        c.setFillColor(C(PALETA[i % len(PALETA)]))
        c.circle(lx + 5, ly + 3, 5, stroke=0, fill=1)
        ancho = _texto(c, lx + 16, ly, str(k)[:28], 9, BLANCO)
        _texto(c, lx + 20 + ancho, ly, f"({v:.1f}%)", 9, ORO, bold=True)
        ly -= 17


def _icono_check(c, x, y, r=12):
    c.setFillColor(C("#2e2a1f"))
    c.circle(x, y, r, stroke=0, fill=1)
    c.setStrokeColor(ORO)
    c.setLineWidth(1.8)
    c.line(x - r * 0.4, y, x - r * 0.1, y - r * 0.3)
    c.line(x - r * 0.1, y - r * 0.3, x + r * 0.45, y + r * 0.35)


# ─── Páginas ─────────────────────────────────────────────────────────────────

def _portada(c, R, datos_cliente, hoy):
    _fondo(c, BG_PORTADA)
    c.setStrokeColor(C("#0e1a2a"))
    c.setLineWidth(0.6)
    for gx in range(0, W, 48):
        c.line(gx, 0, gx, H)
    for gy in range(0, H, 48):
        c.line(0, gy, W, gy)

    y = H - 120
    for linea, color in (("SIMULACIÓN DE", BLANCO), ("CARTERA", BLANCO), ("INMOBILIARIA", ORO)):
        _texto(c, M + 15, y, linea, 46, color, bold=True)
        y -= 50

    _texto(c, M + 15, y - 12, f"Propuesta para {R.get('titular') or datos_cliente.get('nombre') or '—'}", 14, TXT)

    _caja(c, M + 15, 150, 320, 64, fill=C("#101b2b"), stroke=C("#1f2b3d"))
    c.setFillColor(C("#16202f"))
    c.rect(M + 16, 184, 318, 29, stroke=0, fill=1)
    _texto(c, M + 32, 194, "Estatus*", 11, TXT, bold=True)
    _texto(c, M + 32, 162, f"{R.get('estatus', 'Reentel')} RNT", 13, ORO, bold=True)

    w1 = _texto(c, M + 15, 92, "Elaborado por el servicio ", 14, MUTED)
    _texto(c, M + 15 + w1, 92, "Reental Wealth", 14, ORO, bold=True)
    _texto(c, W - M - 15, 92, hoy.strftime("%d/%m/%Y"), 12, MUTED, anchor="r")

    _parrafo(c, M + 15, 64, W - 2 * M - 30,
             "*Los inversores en Reental cuentan con 3 categorías: SuperReentel (hasta un 50% más de "
             "rendimiento), ReentelPro y Reentel. Más info: https://www.reental.co/rnt-token. "
             "Este documento es una simulación informativa: no constituye asesoramiento ni oferta de inversión "
             "y las rentabilidades estimadas no garantizan resultados futuros.", 7.5, TENUE)


def _resumen(c, R):
    _fondo(c, BG)
    y = _cabecera(c, "RESUMEN DE LA CUENTA")
    ancho = W - 2 * M
    ep = R.get("estatus", "Reentel")
    tc = R.get("tipo_cambio") or 1
    divisa = R.get("divisa", "EUR")

    def en(importe, hacia):
        if importe is None:
            return None
        if hacia == divisa:
            return importe
        return importe * tc if divisa == "EUR" else importe / tc

    # Nº de inmuebles
    y -= 48
    _caja(c, M, y, ancho, 48)
    _texto(c, W / 2, y + 30, "Número de inmuebles propuestos en cartera", 9, MUTED, anchor="c")
    _texto(c, W / 2, y + 9, str(R.get("n_inmuebles", 0)), 18, BLANCO, bold=True, anchor="c")

    # Importes en € y en $
    y -= 10 + 88
    mitad = (ancho - 12) / 2
    for i, (moneda, fmt) in enumerate((("EUR", _eur), ("USD", _usd))):
        x = M + i * (mitad + 12)
        _caja(c, x, y, mitad, 88)
        filas = [(f"Valor inversión estimada ({'€' if moneda == 'EUR' else '$'}) en inmuebles",
                  fmt(en(R.get("importe_inmuebles"), moneda)), 11, TXT),
                 ("Adquisición de estatus", fmt(en(R.get("coste_estatus"), moneda)), 11, TXT),
                 ("Valor total inversión (incl. estatus)", fmt(en(R.get("capital_total"), moneda)), 14, ORO)]
        fy = y + 64
        for j, (etq, val, tam, col) in enumerate(filas):
            _texto(c, x + 16, fy, etq, 9, BLANCO if j == 2 else MUTED, bold=(j == 2))
            _texto(c, x + mitad - 16, fy - (2 if j == 2 else 0), val, tam, col, bold=True, anchor="r")
            if j < 2:
                c.setStrokeColor(BORDE)
                c.setLineWidth(0.6 if j == 0 else 1.2)
                c.line(x + 16, fy - 9, x + mitad - 16, fy - 9)
            fy -= 24

    # % cartera por divisa del proyecto
    y -= 10 + 46
    _caja(c, M, y, ancho, 46)
    _texto(c, M + 16, y + 30, "% Cartera según divisa del proyecto", 9, BLANCO, bold=True)
    reparto = R.get("repartos", {}).get("Divisa del inmueble", {})
    usd = sum(v for k, v in reparto.items() if str(k).upper() in ("USD", "$"))
    eur = sum(v for k, v in reparto.items() if str(k).upper() in ("EUR", "€"))
    pista_x, pista_w = M + 230, ancho - 250
    _caja(c, pista_x, y + 10, pista_w, 18, fill=PISTA, stroke=None, r=3)
    px = pista_x
    for valor, color, etq in ((usd, AZUL, "$"), (eur, ORO, "€")):
        if valor > 0:
            largo = pista_w * valor / 100
            _caja(c, px, y + 10, largo, 18, fill=color, stroke=None, r=3)
            _texto(c, px + 6, y + 15, f"{valor:.1f}% ({etq})", 8, BG if color == ORO else BLANCO, bold=True)
            px += largo
    _texto(c, M + 16, y + 12, f"{R.get('n_inmuebles', 0)} inmuebles", 8.5, MUTED)

    # Rentabilidades Reentel vs propuesto
    y -= 10 + 100
    rent_anual = R.get("rent_anual_media", {})
    rent_total = R.get("rent_total_media", {})
    esc36 = (R.get("escenarios") or [{}])[-1]
    for i, (nombre, color, fondo_badge, color_badge, clave) in enumerate((
            ("Reentel (Base)", AZUL_CLARO, C("#1e3a6e"), AZUL_CLARO, "Reentel"),
            (f"{ep} (Propuesto)", ORO, C("#c17f00"), BG, ep))):
        x = M + i * (mitad + 12)
        _caja(c, x, y, mitad, 100)
        _pastilla(c, x + 16, y + 74, nombre, fondo_badge, color_badge, 8.5)
        ganancia = esc36.get("g_rnt") if clave == "Reentel" else esc36.get("g_est_staking")
        filas = [("Rentabilidad anualizada media", _pct(rent_anual.get(clave))),
                 ("Rentabilidad total cartera", _pct(rent_total.get(clave))),
                 (f"Ganancia a {esc36.get('meses', 36)} meses", _dinero(ganancia, divisa))]
        fy = y + 52
        for j, (etq, val) in enumerate(filas):
            _texto(c, x + 16, fy, etq, 9, MUTED)
            _texto(c, x + mitad - 16, fy - 1, val, 13, color, bold=True, anchor="r")
            if j < 2:
                c.setStrokeColor(BORDE)
                c.setLineWidth(0.5)
                c.line(x + 16, fy - 7, x + mitad - 16, fy - 7)
            fy -= 20

    _parrafo(c, M, y - 8, ancho,
             f"Tipo de cambio aplicado: 1 € = {tc:.4f} $ (referencia BCE). Precio del RNT: "
             f"{(R.get('precio_rnt') or 0):.4f} USDT (pool RNT/USDT). Las rentabilidades se ponderan por el % de la "
             "cartera invertido en cada proyecto.", 7.5, TENUE)


def _reinversion(c, R):
    _fondo(c, BG)
    y = _cabecera(c, "LA CARTERA CON REINVERSIÓN: EL PODER DEL INTERÉS COMPUESTO")
    ancho = W - 2 * M
    ep = R.get("estatus", "Reentel")
    divisa = R.get("divisa", "EUR")
    esc = R.get("escenarios") or []
    if not esc:
        return

    series = [("Ganancia Reentel", [e["g_rnt"] for e in esc], AZUL2)]
    if ep != "Reentel":
        series += [(f"Ganancia {ep}", [e["g_est"] for e in esc], ORO),
                   (f"Ganancia {ep} incl. staking", [e["g_est_staking"] for e in esc], VERDE)]

    alto_graf = 205
    y -= alto_graf + 34
    _caja(c, M, y, ancho, alto_graf + 34)
    _texto(c, M + 16, y + alto_graf + 14, f"★ Ganancia total — Reentel vs {ep}", 10, ORO, bold=True)

    d = Drawing(ancho - 40, alto_graf - 30)
    bc = VerticalBarChart()
    bc.x, bc.y = 60, 18
    bc.width, bc.height = ancho - 110, alto_graf - 58
    bc.data = [s[1] for s in series]
    bc.categoryAxis.categoryNames = [f"{e['meses']} meses" for e in esc]
    for eje in (bc.categoryAxis, bc.valueAxis):
        eje.strokeColor = BORDE
        eje.labels.fillColor = MUTED
        eje.labels.fontName = "Helvetica"
        eje.labels.fontSize = 8
    bc.valueAxis.valueMin = 0
    bc.valueAxis.visibleGrid = 1
    bc.valueAxis.gridStrokeColor = C("#1f2d44")
    bc.valueAxis.labelTextFormat = lambda v: f"{v:,.0f}"
    bc.groupSpacing = 14
    bc.barSpacing = 2
    bc.barLabelFormat = lambda v: f"{v:,.0f}"
    bc.barLabels.fontName = "Helvetica-Bold"
    bc.barLabels.fontSize = 6.5
    bc.barLabels.fillColor = TXT
    bc.barLabels.nudge = 6
    for i, (_, _, color) in enumerate(series):
        bc.bars[i].fillColor = color
        bc.bars[i].strokeColor = None
    d.add(bc)
    renderPDF.draw(d, c, M + 10, y + 24)

    lx = M + 20
    for nombre, _, color in series:
        c.setFillColor(color)
        c.roundRect(lx, y + 11, 9, 9, 2, stroke=0, fill=1)
        lx += 14 + _texto(c, lx + 14, y + 12, f"{nombre} ({'€' if divisa == 'EUR' else '$'})", 8, TXT) + 18

    # Tabla
    oro, verde, azul = "#f5a623", "#7ecba1", "#7ab0f0"
    filas = [["Escenario"] + [f"{e['meses']} meses" for e in esc],
             ["<b>Ganancia Reentel</b>"] + [_dinero(e["g_rnt"], divisa) for e in esc]]
    if ep != "Reentel":
        filas += [[f"<font color='{oro}'><b>Ganancia {ep} ★</b></font>"] +
                  [f"<font color='{oro}'><b>{_dinero(e['g_est'], divisa)}</b></font>" for e in esc],
                  [f"<font color='{verde}'><b>Ganancia {ep} (incl. staking) ★</b></font>"] +
                  [f"<font color='{verde}'><b>{_dinero(e['g_est_staking'], divisa)}</b></font>" for e in esc]]
    filas += [["Rent. acumulada Reentel"] + [_pct(e["rent_rnt"]) for e in esc]]
    if ep != "Reentel":
        filas += [[f"<font color='{oro}'>Rent. acumulada {ep} ★</font>"] +
                  [f"<font color='{oro}'><b>{_pct(e['rent_est'])}</b></font>" for e in esc]]
    n = len(esc)
    y -= 10
    alto = _tabla(c, M, y, filas, [ancho * 0.32] + [ancho * 0.68 / n] * n)
    y -= alto + 10

    # Mensaje destacado
    ult = esc[-1]
    _caja(c, M, y - 34, ancho, 34, fill=C("#241f17"), stroke=C("#5a4520"))
    if ep != "Reentel":
        msg = (f"Con <font color='{oro}'><b>{ep}</b></font>, la ganancia a {ult['meses']} meses alcanza "
               f"<font color='{oro}'><b>{_dinero(ult['g_est_staking'], divisa)}</b></font> (incl. staking) vs "
               f"{_dinero(ult['g_rnt'], divisa)} del estatus base. Rentabilidad acumulada: "
               f"<font color='{oro}'><b>{_pct(ult['rent_est'])}</b></font> vs {_pct(ult['rent_rnt'])}.")
    else:
        msg = (f"La ganancia a {ult['meses']} meses alcanza <font color='{oro}'><b>{_dinero(ult['g_rnt'], divisa)}"
               f"</b></font>, una rentabilidad acumulada del <font color='{oro}'><b>{_pct(ult['rent_rnt'])}</b></font>.")
    _parrafo(c, M + 16, y - 11, ancho - 32, msg, 9, TXT)


def _analisis_1(c, R):
    _fondo(c, BG)
    y = _cabecera(c, "I ANÁLISIS CARTERA PROPUESTA")
    ancho = W - 2 * M

    y -= 48
    _caja(c, M, y, ancho, 48)
    _texto(c, W / 2, y + 30, "Número de inmuebles en cartera propuesta", 9, MUTED, anchor="c")
    _texto(c, W / 2, y + 9, str(R.get("n_inmuebles", 0)), 18, BLANCO, bold=True, anchor="c")

    # Distribución geográfica
    geo = sorted((R.get("repartos", {}).get("Distribución geográfica") or {}).items(), key=lambda kv: -kv[1])
    items = [(k, v, ORO if v >= 50 else C("#c98a22") if v >= 10 else C("#9c6d20"), f"{v:.1f}%") for k, v in geo]
    alto_geo = 44 + len(items) * 25
    y -= 12 + alto_geo
    _caja(c, M, y, ancho, alto_geo)
    _texto(c, M + 16, y + alto_geo - 22, "DISTRIBUCIÓN GEOGRÁFICA DE LA INVERSIÓN", 10, BLANCO, bold=True)
    _barras_h(c, M + 16, y + alto_geo - 34, ancho - 32, items, alto=20, ancho_nombre=150)

    # Estado de los proyectos
    conteo = {}
    for p in R.get("proyectos", []):
        k = _norm_estado(p.get("estado"))
        conteo[k] = conteo.get(k, 0) + 1
    total = sum(conteo.values()) or 1
    items = [(k, n / total * 100, ESTADO_BARRA.get(k, C("#3b4a60")),
              f"{n} inmueble{'s' if n > 1 else ''} — {round(n / total * 100)}%") for k, n in conteo.items()]
    alto_est = 44 + len(items) * 25
    y -= 12 + alto_est
    if y > 30:
        _caja(c, M, y, ancho, alto_est)
        _texto(c, M + 16, y + alto_est - 22, "ESTADO DE LOS PROYECTOS", 10, BLANCO, bold=True)
        _barras_h(c, M + 16, y + alto_est - 34, ancho - 32, items, alto=20, ancho_nombre=150)


def _analisis_2(c, R):
    _fondo(c, BG)
    y = _cabecera(c, "II ANÁLISIS CARTERA PROPUESTA")
    ancho = W - 2 * M
    rep = R.get("repartos", {})
    tipo_precio = {}
    for p in R.get("proyectos", []):
        k = "Mercado secundario (OTC)" if p.get("tipo_precio") == "OTC" else "Primera emisión"
        tipo_precio[k] = tipo_precio.get(k, 0) + (p.get("pct") or 0)

    tarjetas = [("Tipología de dividendos", rep.get("Tipología de dividendo")),
                ("Distribución por región", rep.get("Distribución geográfica")),
                ("Divisa del inmueble", rep.get("Divisa del inmueble")),
                ("Origen del precio de compra", tipo_precio)]
    mitad = (ancho - 14) / 2
    alto = (y - 40 - 14) / 2
    for i, (titulo, reparto) in enumerate(tarjetas):
        x = M + (i % 2) * (mitad + 14)
        yy = y - alto - (i // 2) * (alto + 14)
        _tarjeta_donut(c, x, yy, mitad, alto, titulo, reparto)


def _activos(c, R, proyectos, con_barras):
    _fondo(c, BG)
    ep = R.get("estatus", "Reentel")
    divisa = R.get("divisa", "EUR")
    y = _cabecera(c, "RESUMEN DE ACTIVOS — RENTABILIDADES POR ESTATUS")
    ancho = W - 2 * M
    oro = "#f5a623"

    filas = [["Nombre", "Estado", "Ubicación", "Inversión", "Rent. total Reentel", f"Rent. total {ep} ★",
              "Rent. anual Reentel", f"Rent. anual {ep} ★", "Fin est."]]
    for p in proyectos:
        estado = _norm_estado(p.get("estado"))
        fondo, color = ESTADO_COLORES.get(estado, ("#26374f", "#d3d9e2"))
        filas.append([
            f"<font color='#ffffff'><b>{p['nombre']}</b></font><br/><font size='7' color='#8592a6'>{p.get('id', '')}</font>",
            f"<font size='6.5' color='{color}'><b>{estado}</b></font>",
            p.get("ubicacion", "—"),
            _dinero(p.get("importe"), divisa),
            _pct(p.get("rent_tot_rnt")),
            f"<font color='{oro}'><b>{_pct(p.get('rent_tot_est'))}</b></font>",
            _pct(p.get("rent_anu_rnt")),
            f"<font color='{oro}'><b>{_pct(p.get('rent_anu_est'))}</b></font>",
            p.get("fecha_fin") or "—",
        ])
    alto = _tabla(c, M, y, filas, [ancho * k for k in (0.19, 0.12, 0.11, 0.11, 0.1, 0.1, 0.09, 0.09, 0.09)])
    y -= alto + 14

    if con_barras and proyectos:
        _barras_rentabilidad(c, R, proyectos, y)


def _barras_rentabilidad(c, R, proyectos, y_top):
    ep = R.get("estatus", "Reentel")
    ancho = W - 2 * M
    mitad = (ancho - 14) / 2
    for i, (titulo, k_rnt, k_est) in enumerate((
            (f"Rentabilidad total — Reentel + incremento {ep}", "rent_tot_rnt", "rent_tot_est"),
            (f"Rentabilidad anualizada — Reentel + incremento {ep}", "rent_anu_rnt", "rent_anu_est"))):
        x = M + i * (mitad + 14)
        orden = sorted(proyectos, key=lambda p: -(p.get(k_est) or 0))
        alto = 40 + len(orden) * 25
        y = y_top - alto
        _caja(c, x, y, mitad, alto, fill=C("#1a2a42"))
        _texto(c, x + 14, y + alto - 20, titulo, 9, BLANCO, bold=True)
        maximo = max([p.get(k_est) or 0 for p in orden] + [0.01])
        pista = mitad - 28 - 100
        fy = y + alto - 32
        for p in orden:
            fy -= 20
            base, est = p.get(k_rnt) or 0, p.get(k_est) or 0
            dif = max(est - base, 0)
            _texto(c, x + 104, fy + 6, p["nombre"][:16], 8, MUTED, anchor="r")
            _caja(c, x + 110, fy + 1, pista, 17, fill=PISTA, stroke=None, r=3)
            l_base = max(pista * base / maximo * 0.78, 38)
            l_dif = max(pista * dif / maximo * 0.78, 30) if ep != "Reentel" else 0
            _caja(c, x + 110, fy + 1, l_base, 17, fill=AZUL, stroke=None, r=3)
            _texto(c, x + 115, fy + 6, _pct(base), 7.5, BLANCO, bold=True)
            if l_dif:
                _caja(c, x + 110 + l_base, fy + 1, l_dif, 17, fill=ORO, stroke=None, r=3)
                _texto(c, x + 114 + l_base, fy + 6, f"+{dif:.2f}%", 7.5, BG, bold=True)
            fy -= 5


def _ficha(c, R, p, x, y, w, h):
    ep = R.get("estatus", "Reentel")
    divisa = R.get("divisa", "EUR")
    _caja(c, x, y, w, h)
    izq = x + 20
    yy = y + h - 30
    _texto(c, izq, yy, p["nombre"], 16, BLANCO, bold=True)
    yy -= 20
    _pastilla(c, izq, yy - 2, str(p.get("id", "")), C("#26374f"), MUTED, 7.5)
    yy -= 22
    lineas = [("Ubicación", p.get("ubicacion")), ("Inicio renta", p.get("fecha_inicio")),
              ("Fin estimado", p.get("fecha_fin")), ("Precio de compra", p.get("precio")),
              ("Inversión", _dinero(p.get("importe"), divisa)), ("Dividendo", str(p.get("tipodiv") or "—").capitalize()),
              ("Peso en la cartera", _pct(p.get("pct"), 1))]
    for etq, val in lineas:
        if not val:
            continue
        ancho_etq = _texto(c, izq, yy, f"{etq}: ", 9, MUTED)
        _texto(c, izq + ancho_etq, yy, str(val), 9, BLANCO, bold=True)
        yy -= 15
    _etiqueta_estado(c, izq, yy - 4, p.get("estado"))

    der = x + w / 2 + 10
    yy = y + h - 30
    _texto(c, der, yy, "Rentabilidad total estimada", 8, MUTED)
    yy -= 22
    ancho_b = _pastilla(c, der, yy, f"{ep}: {_pct(p.get('rent_tot_est'))}", ORO, BG, 8.5)
    if ep != "Reentel":
        _pastilla(c, der + ancho_b + 6, yy, f"Reentel: {_pct(p.get('rent_tot_rnt'))}", C("#26374f"), TXT, 8.5)
    yy -= 26
    _texto(c, der, yy, f"Rent. anualizada ({ep})", 8, MUTED)
    _texto(c, der, yy - 18, _pct(p.get("rent_anu_est")), 16, ORO, bold=True)
    if ep != "Reentel":
        yy -= 42
        _texto(c, der, yy, "Rent. anualizada (Reentel)", 8, MUTED)
        _texto(c, der, yy - 15, _pct(p.get("rent_anu_rnt")), 12, AZUL_CLARO, bold=True)


def _beneficios_wealth(c):
    _fondo(c, BG_BENEF)
    _texto(c, M, H - M - 36, "Beneficios de ser", 32, BLANCO, bold=True)
    _texto(c, M + stringWidth("Beneficios de ser ", "Helvetica-Bold", 32), H - M - 36, "Wealth", 32, BLANCO)
    columnas = [
        ["Acceso a oportunidades exclusivas con antelación.",
         "Atención personalizada con un equipo dedicado. Optimización de estrategias.",
         "Reporte detallado de cartera de inversión.",
         "Personalización en las comunicaciones según preferencias."],
        ["Cartera inicial de inmuebles ya en activo con rentabilidades ciertas.",
         "Acompañamiento y facilidades para los procesos de liquidez en la venta de tokens de la cartera.",
         "Análisis recurrentes de oportunidades en el mercado secundario y mercado de colateralización.",
         "Toma de decisiones eficientes en nuevos lanzamientos en base a objetivos."],
    ]
    ancho = W - 2 * M
    mitad = (ancho - 14) / 2
    alto = 290
    y = H - M - 70 - alto
    for i, items in enumerate(columnas):
        x = M + i * (mitad + 14)
        _caja(c, x, y, mitad, alto, fill=CARD_BENEF, stroke=None, r=10)
        yy = y + alto - 30
        for item in items:
            _icono_check(c, x + 34, yy - 6)
            h = _parrafo(c, x + 60, yy + 3, mitad - 80, item, 11, TXT, leading=15)
            yy -= max(h, 30) + 34
    y -= 14 + 58
    _caja(c, M, y, ancho, 58, fill=CARD_BENEF, stroke=None, r=10)
    _icono_check(c, M + 34, y + 29)
    _texto(c, M + 60, y + 34, "Condición para acceder a servicio Reental Wealth:", 11, ORO, bold=True)
    _texto(c, M + 60, y + 17, "Tener en cartera inversión mínima en 500 tokens de proyectos inmobiliarios.", 10.5, TXT)


def _beneficios_superreentel(c, R):
    _fondo(c, BG_BENEF)
    ep = R.get("estatus", "SuperReentel")
    _texto(c, M, H - M - 36, "Beneficios de ser", 32, BLANCO, bold=True)
    _texto(c, M + stringWidth("Beneficios de ser ", "Helvetica-Bold", 32), H - M - 36, ep, 32, BLANCO)
    columnas = [
        ("Ventajas en proyectos Real Estate:",
         ["Acceso prioritario a proyectos antes de ser comunicados al resto de la comunidad.",
          "Acceso privado a proyectos exclusivos únicamente para este grupo de inversores.",
          "Rentabilidad de hasta un <b>8% extra anual</b> en inmuebles."]),
        ("Ventajas en Reental Club:",
         ["Estancias gratuitas en inmuebles.",
          "Invitaciones gratuitas a eventos de Reental.",
          "Formaciones gratuitas por los centros más punteros en tokenización, blockchain, cripto…",
          "Descuentos en partners."]),
        ("Ventajas en el protocolo de Reental:",
         ["Fees del protocolo: Real Yield generado por el uso de las funcionalidades del protocolo "
          "(ventas RNT, claims RNT, fees Buy back, fees colateralización).",
          "Acceso prioritario a Reenlever: mercado de colateralización. Mejores condiciones RL V2.",
          "Voto en la DAO, mejores condiciones de liquidez 24h."]),
    ]
    ancho = W - 2 * M
    tercio = (ancho - 28) / 3
    alto = 300
    y = H - M - 70 - alto
    for i, (titulo, items) in enumerate(columnas):
        x = M + i * (tercio + 14)
        _caja(c, x, y, tercio, alto, fill=CARD_BENEF, stroke=None, r=10)
        _texto(c, x + 18, y + alto - 28, titulo, 10.5, ORO, bold=True)
        yy = y + alto - 50
        for item in items:
            _texto(c, x + 18, yy - 9, "✓", 11, ORO, bold=True)
            h = _parrafo(c, x + 34, yy, tercio - 52, item, 9.5, TXT, leading=13)
            yy -= h + 12
    y -= 14 + 58
    rnt = R.get("rnt_estatus") or 28000
    _caja(c, M, y, ancho, 58, fill=CARD_BENEF, stroke=None, r=10)
    _icono_check(c, M + 34, y + 29)
    _texto(c, M + 60, y + 34, "Condiciones para obtener estatus:", 11, ORO, bold=True)
    _parrafo(c, M + 60, y + 25, ancho - 90,
             f"Adquirir al menos <b>{rnt:,.0f} xRNT</b> (esto es, staking de {rnt:,.0f} RNT a 2 años) para {ep}.",
             10.5, TXT)


# ─── Función principal ───────────────────────────────────────────────────────

def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_proyectos,
                        precios_compra=None, resumen=None):
    """Genera el PDF y devuelve sus bytes. `resumen` lo prepara el Paso 5 de la app."""
    R = dict(resumen or {})
    R.setdefault("estatus", datos_cliente.get("estatus") or "Reentel")
    R.setdefault("divisa", (datos_cliente.get("divisa") or "EUR").upper())
    R.setdefault("titular", datos_cliente.get("nombre"))
    R.setdefault("proyectos", [])
    R.setdefault("repartos", {})
    R.setdefault("n_inmuebles", len(R["proyectos"]))
    hoy = date.today()

    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(f"Propuesta Reental — {R.get('titular') or ''}")
    c.setAuthor("Reental Wealth")
    pagina = [0]

    def nueva(dibujar, *args):
        if pagina[0]:
            c.showPage()
        pagina[0] += 1
        dibujar(c, *args)
        _numero_pagina(c, pagina[0])

    nueva(_portada, R, datos_cliente, hoy)
    nueva(_resumen, R)
    if R.get("escenarios"):
        nueva(_reinversion, R)
    nueva(_analisis_1, R)
    nueva(_analisis_2, R)

    proyectos = R["proyectos"]
    if len(proyectos) <= 5:
        nueva(_activos, R, proyectos, True)
    else:
        for i in range(0, len(proyectos), 10):
            nueva(_activos, R, proyectos[i:i + 10], False)
        for i in range(0, len(proyectos), 8):
            def _pag_barras(c_, R_, grupo):
                _fondo(c_, BG)
                y = _cabecera(c_, "RESUMEN DE ACTIVOS — COMPARATIVA DE RENTABILIDADES")
                _barras_rentabilidad(c_, R_, grupo, y)
            nueva(_pag_barras, R, proyectos[i:i + 8])

    # Fichas agrupadas por ubicación, dos por página
    por_region = {}
    for p in proyectos:
        por_region.setdefault(p.get("ubicacion") or "Otros", []).append(p)
    for region, grupo in por_region.items():
        for i in range(0, len(grupo), 2):
            def _pag_fichas(c_, R_, region_, fichas):
                _fondo(c_, BG)
                y = _cabecera(c_, f"ANÁLISIS POR UBICACIÓN: {str(region_).upper()}")
                alto = (y - 30 - 12) / 2
                for j, p in enumerate(fichas):
                    _ficha(c_, R_, p, M, y - alto - j * (alto + 12), W - 2 * M, alto)
            nueva(_pag_fichas, R, region, grupo[i:i + 2])

    nueva(_beneficios_wealth)
    if R["estatus"] == "SuperReentel":
        nueva(_beneficios_superreentel, R)

    c.save()
    return buf.getvalue()
