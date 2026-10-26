"""
IMAGEN RESUMEN DE LA SIMULACIÓN - Para descargar en el Paso 4 y mandar por WhatsApp.

Muestra las cuatro cifras de la cartera, el gráfico «tu cartera / tu cartera optimizada»
a varios plazos y, si hay cartera optimizada, cuánto más podría conseguir sin invertir
más. Formato 1080 px de ancho; el alto se ajusta al contenido (mínimo 1350, 4:5).
"""
from __future__ import annotations

import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

NAVY = "#1f2937"
AMBAR = "#fca311"
AMBAR_OSCURO = "#d97706"
AMBAR_CLARO = "#fff4de"
FONDO = "#f9fafb"
GRIS = "#6b7280"
BORDE = "#e5e7eb"
BLANCO = "#ffffff"

W, H_MAX = 1080, 2400
M = 64

_AQUI = os.path.dirname(os.path.abspath(__file__))
# Dónde buscar la fuente Fustat (la carpeta «fonts» puede estar en modules/ o en la raíz)
_DIRS_FUENTES = [os.path.join(_AQUI, "fonts"), os.path.join(_AQUI, "..", "fonts"),
                 os.path.join(_AQUI, "..", "static", "fonts")]
# Si no está Fustat, otras con tildes que suelen estar instaladas
_ALTERNATIVAS = {False: ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
                 True: ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]}


_INCRUSTADA = {}


def _fustat_incrustada(negrita):
    """Los bytes de la fuente guardada dentro de fuente_fustat.py (siempre disponible)."""
    if negrita not in _INCRUSTADA:
        import base64
        try:
            from modules import fuente_fustat
        except ImportError:
            import fuente_fustat
        texto = fuente_fustat.BOLD if negrita else fuente_fustat.REGULAR
        _INCRUSTADA[negrita] = base64.b64decode("".join(texto.split()))
    return _INCRUSTADA[negrita]


def _fuente(tam, negrita=False):
    nombre = "Fustat-Bold.ttf" if negrita else "Fustat-Regular.ttf"
    for ruta in [os.path.join(d, nombre) for d in _DIRS_FUENTES]:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    try:
        return ImageFont.truetype(BytesIO(_fustat_incrustada(negrita)), tam)
    except Exception:
        pass
    for ruta in _ALTERNATIVAS[negrita]:
        try:
            return ImageFont.truetype(ruta, tam)
        except OSError:
            continue
    return ImageFont.load_default(size=tam)


def _num(v, dec=0):
    """Formato español: 12.345,67"""
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _ajustar(d, texto, fuente, ancho_max):
    palabras, lineas, actual = [p for p in texto.split(" ") if p], [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if d.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def _parrafo(d, x, y, texto, fuente, color, ancho, interlinea):
    for linea in _ajustar(d, texto, fuente, ancho):
        d.text((x, y), linea, font=fuente, fill=color)
        y += interlinea
    return y


def generar(titular: str, simbolo: str, capital: float, n_inmuebles: int, rent_total: float,
            rent_anual: float, plazos: list, series: list, hay_mejora: bool, extra: float,
            moneda: str) -> bytes:
    """PNG del resumen.

    plazos: [6, 12, 24, 36, 60] (meses). series: [(nombre, color, [ganancia por plazo]), ...]
    con «Tu cartera» primero y, si hay mejora, «Tu cartera optimizada».
    """
    img = Image.new("RGB", (W, H_MAX), FONDO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=AMBAR)

    # Título
    titulo, ft = "Simulación de cartera inmobiliaria en Reental", _fuente(54, True)
    while d.textlength(titulo, font=ft) > W - 2 * M and ft.size > 44:   # mejor en una sola línea
        ft = _fuente(ft.size - 1, True)
    y = _parrafo(d, M, 76, titulo, ft, NAVY, W - 2 * M, int(ft.size * 1.22))
    y += 34

    # Cuatro cifras (2 × 2)
    cifras = [("IMPORTE INVERTIDO", f"{_num(capital)} {simbolo}"),
              ("INMUEBLES", f"{n_inmuebles}"),
              ("RENTABILIDAD TOTAL", f"Hasta {_num(rent_total, 2)} %"),
              ("RENTABILIDAD ANUALIZADA", f"Hasta {_num(rent_anual, 2)} %")]
    hueco = 24
    ancho_t = (W - 2 * M - hueco) // 2
    alto_t = 150
    for i, (titulo, valor) in enumerate(cifras):
        x0 = M + (i % 2) * (ancho_t + hueco)
        y0 = y + (i // 2) * (alto_t + hueco)
        d.rounded_rectangle([x0, y0, x0 + ancho_t, y0 + alto_t], radius=22, fill=BLANCO, outline=BORDE, width=2)
        d.text((x0 + 30, y0 + 28), titulo, font=_fuente(24, True), fill=GRIS)
        fv = _fuente(46, True)
        while d.textlength(valor, font=fv) > ancho_t - 60 and fv.size > 28:
            fv = _fuente(fv.size - 2, True)
        d.text((x0 + 30, y0 + 70), valor, font=fv, fill=NAVY)
    y += 2 * alto_t + hueco + 56

    # Gráfico: ganancia estimada a cada plazo
    d.text((M, y), "¿Cuánto puede ganar tu cartera?", font=_fuente(40, True), fill=NAVY)
    y += 56
    d.text((M, y), f"Ganancia estimada ({simbolo})", font=_fuente(26), fill=GRIS)
    y += 50

    alto_g = 420
    x_ini, x_fin = M + 10, W - M
    y_base = y + alto_g
    maximo = max([max(v) for _, _, v in series] + [1.0])
    escala = (alto_g - 50) / maximo
    # Líneas de referencia
    for k in range(1, 4):
        yy = y_base - (alto_g - 50) * k / 3
        d.line([x_ini, yy, x_fin, yy], fill=BORDE, width=1)
    d.line([x_ini, y_base, x_fin, y_base], fill="#cbd5e1", width=2)

    n_grupos, n_series = len(plazos), len(series)
    ancho_grupo = (x_fin - x_ini) / n_grupos
    ancho_barra = min(74, (ancho_grupo - 36) / n_series)
    f_val = _fuente(18 if n_series > 1 else 22, True)
    for gi, meses in enumerate(plazos):
        centro = x_ini + ancho_grupo * (gi + 0.5)
        izq = centro - ancho_barra * n_series / 2 - 3 * (n_series - 1)
        for si, (_, color, valores) in enumerate(series):
            xb = izq + si * (ancho_barra + 6)
            alto_b = max(2, valores[gi] * escala)
            d.rounded_rectangle([xb, y_base - alto_b, xb + ancho_barra, y_base], radius=6, fill=color)
            etiqueta = _num(valores[gi])
            ancho_e = d.textlength(etiqueta, font=f_val)
            d.text((xb + ancho_barra / 2 - ancho_e / 2, y_base - alto_b - 26), etiqueta, font=f_val,
                   fill=AMBAR_OSCURO if color == AMBAR else NAVY)
        texto_p = f"{meses} meses"
        fp = _fuente(24)
        d.text((centro - d.textlength(texto_p, font=fp) / 2, y_base + 14), texto_p, font=fp, fill=GRIS)
    y = y_base + 64

    # Leyenda
    x = M
    for nombre, color, _ in series:
        d.rounded_rectangle([x, y + 6, x + 26, y + 32], radius=5, fill=color)
        d.text((x + 38, y), nombre, font=_fuente(28), fill=NAVY)
        x += 38 + d.textlength(nombre, font=_fuente(28)) + 48
    y += 70

    # Gancho (solo si hay cartera optimizada)
    if hay_mejora:
        f_t, f_v = _fuente(34, True), _fuente(72, True)
        lineas_ini = _ajustar(d, "Con la misma cartera, podrías conseguir hasta", f_t, W - 2 * M - 88)
        lineas_fin = _ajustar(d, f"en 36 meses, sin invertir ni un solo {moneda} más", f_t, W - 2 * M - 88)
        alto = 36 + 46 * len(lineas_ini) + 100 + 46 * len(lineas_fin) + 34
        d.rounded_rectangle([M, y, W - M, y + alto], radius=28, fill=AMBAR_CLARO, outline=AMBAR, width=4)
        yy = y + 36
        for l in lineas_ini:
            d.text((M + 44, yy), l, font=f_t, fill=NAVY)
            yy += 46
        d.text((M + 44, yy - 2), f"{_num(extra)} {simbolo} más", font=f_v, fill=AMBAR_OSCURO)
        yy += 100
        for l in lineas_fin:
            d.text((M + 44, yy), l, font=f_t, fill=NAVY)
            yy += 46
        y += alto + 30

    # Pie
    pie = ("Simulación informativa. Rentabilidades máximas estimadas, con las mejores condiciones disponibles "
           "en Reental. El cálculo considera la reinversión de los beneficios (interés compuesto). "
           + ("La cartera optimizada tiene los mismos proyectos y el mismo importe total. " if hay_mejora else "")
           + "Las cifras son estimaciones: no constituyen asesoramiento ni oferta de inversión y no garantizan "
             "resultados futuros.")
    y += 20
    d.line([M, y, W - M, y], fill=BORDE, width=2)
    y = _parrafo(d, M, y + 16, pie, _fuente(22), GRIS, W - 2 * M, 29)

    img = img.crop((0, 0, W, max(1350, int(y + 40))))
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
