"""
SIMULADOR DE CARTERA INMOBILIARIA REENTAL - FASE 3 COMPLETA
Streamlit App - Versión FASE 3 con Precios OTC Reales

Pasos:
1. Datos cliente (nombre, email, capital, divisa)
2. Estatus (Reentel, ReentelPro, SuperReentel)
3. Parámetros (objetivo, mercados, distribución)
4. Cartera (seleccionar proyectos + PRECIOS OTC)
5. Resumen (tabla cartera + proyecciones + descargar PDF)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import math
import re
import traceback
import uuid
from modules.data_loader import cargar_proyectos, cargar_todos_proyectos
from modules.calculo_cartera import rankear_proyectos, CalculadoraCartera
from modules.formateo_datos import preparar_proyectos_para_paso4
from modules.pdf_generator import generar_pdf_cartera
from modules import leads

# ========== CONFIGURACIÓN STREAMLIT ==========
st.set_page_config(
    page_title="Simulador de Cartera - Reental",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== CSS PERSONALIZADO ==========
# Paleta del informe mensual de Reental Wealth: ámbar, navy y fondo gris claro,
# con la tipografía Fustat.
COLOR_AMBAR = "#fca311"
COLOR_AMBAR_OSCURO = "#d97706"      # ámbar legible sobre blanco (textos, avisos)
COLOR_AMBAR_CLARO = "#feedcf"
COLOR_NAVY = "#1f2937"
COLOR_GRIS = "#6d737c"
COLOR_GRIS_CLARO = "#9ca1aa"
COLOR_BORDE = "#e5e7eb"
COLOR_FONDO = "#f9fafb"
COLOR_VERDE = "#15803d"
COLOR_ROJO = "#dc2626"
PALETA_GRAFICOS = ["#fca311", "#1f2937", "#15803d", "#fcd287", "#9ca1aa", "#f5a11f", "#3e4753"]

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fustat:wght@400;500;600;700;800&display=swap');

    html, body, .stApp, .stApp div, .stApp p, .stApp label, .stApp input, .stApp textarea,
    .stApp button, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp span:not([data-testid="stIconMaterial"]) {{
        font-family: 'Fustat', 'Segoe UI', sans-serif;
    }}
    /* Los iconos de Streamlit usan su propia fuente: si se les cambia, en vez
       del icono aparece su nombre en texto (p. ej. «keyboard_double»). */
    [data-testid="stIconMaterial"], .material-symbols-rounded {{
        font-family: 'Material Symbols Rounded' !important;
    }}

    .stApp {{ background-color: {COLOR_FONDO}; color: {COLOR_NAVY}; }}

    /* Títulos */
    h1 {{ color: {COLOR_NAVY}; font-weight: 800; }}
    h2 {{
        color: {COLOR_NAVY};
        font-size: 1.7em;
        font-weight: 800;
        margin-top: 10px;
        padding-bottom: 6px;
        border-bottom: 3px solid {COLOR_AMBAR};
        display: inline-block;
    }}
    h3 {{ color: {COLOR_NAVY}; font-size: 1.25em; font-weight: 700; margin-top: 10px; }}
    h4 {{ color: {COLOR_GRIS}; font-weight: 600; }}

    /* Botones: ámbar con texto navy (más legible que el blanco sobre ámbar) */
    .stButton button, .stDownloadButton button {{
        background-color: {COLOR_AMBAR};
        color: {COLOR_NAVY};
        border: none;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.2s ease;
    }}
    .stButton button:hover, .stDownloadButton button:hover {{
        background-color: #f5a11f;
        color: {COLOR_NAVY};
        border: none;
    }}
    .stButton button:focus:not(:active) {{ color: {COLOR_NAVY}; border: none; }}
    .stButton button:disabled {{
        background-color: {COLOR_BORDE};
        color: {COLOR_GRIS_CLARO};
    }}

    /* Campos de formulario sobre blanco */
    div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {{
        background-color: #ffffff;
        border-color: {COLOR_BORDE};
        border-radius: 8px;
    }}

    /* Barra de progreso */
    .stProgress > div > div > div > div {{ background-color: {COLOR_AMBAR}; }}

    /* Tablas */
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{
        border: 1px solid {COLOR_BORDE};
        border-radius: 12px;
        background-color: #ffffff;
    }}

    hr {{ border-color: {COLOR_BORDE}; }}
</style>
""", unsafe_allow_html=True)

# ========== INICIALIZAR SESSION STATE ==========
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 1

if 'datos_cliente' not in st.session_state:
    st.session_state.datos_cliente = {}

if 'df_proyectos' not in st.session_state:
    st.session_state.df_proyectos = None

if 'cartera_selecciones' not in st.session_state:
    st.session_state.cartera_selecciones = {}

if 'precios_compra' not in st.session_state:
    st.session_state.precios_compra = {}

if 'sel_tablas' not in st.session_state:
    st.session_state.sel_tablas = {}

# Construye tu cartera: tokens a comprar y oferta elegida por proyecto
for _clave, _defecto in (('tokens_compra', {}), ('oferta_elegida', {}),
                         ('tokens_manual', False), ('version_editor', 0)):
    if _clave not in st.session_state:
        st.session_state[_clave] = _defecto

# ========== FUNCIONES AUXILIARES OTC ==========
# Los módulos OTC de la herramienta del compañero (otc_inventario, otc_saldos,
# aave_lend, utils, reental_tokens) se importan entre sí sin el prefijo
# "modules.", así que la carpeta modules/ tiene que estar en la ruta de Python.
import os
import sys
_DIR_MODULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if _DIR_MODULES not in sys.path:
    sys.path.insert(0, _DIR_MODULES)


def _num(valor, defecto=0.0):
    try:
        return float(str(valor).replace(',', '.'))
    except (TypeError, ValueError):
        return defecto


def _proyectos_para_catalogo(df):
    """Tupla (hashable, para la caché) con lo que el catálogo OTC necesita de cada proyecto."""
    filas = []
    for _, r in df.iterrows():
        addr = str(r.get('Token Address', '') or '').strip().lower()
        if not (addr.startswith('0x') and len(addr) == 42):
            continue
        filas.append((addr, str(r.get('ID', '') or '').strip(),
                      str(r.get('Nombre del proyecto', '') or ''),
                      str(r.get('Divisa', '') or 'EUR'),
                      _num(r.get('Precio Emisión', 0)),
                      str(r.get('Ubicación', '') or ''),
                      str(r.get('ESTADO', '') or '')))
    return tuple(filas)


# Wallet de custodia de Reental: la misma que usan pages/02_OTC.py y
# pages/06_Constructor_Propuestas.py de la herramienta OTC (OTC_WALLET).
OTC_WALLET_CUSTODIA = "0xce0719ec1bda336ba069c6961ad167767829301a"


@st.cache_data(ttl=900, show_spinner="Consultando en la blockchain qué hay disponible en OTC…")
def catalogo_otc(proyectos):
    """Lo disponible hoy en OTC, calculado con los MISMOS módulos que la herramienta
    OTC del compañero (otc_inventario.catalogo): stock propio de Reental en la
    wallet de custodia + ofertas activas de terceros, ambos contrastados con la
    cadena y descontando reservas y entregas. Se cachea 15 minutos."""
    import otc_inventario
    from modules import otc_storage

    try:
        api_key = str(st.secrets["etherscan"]["api_key"]).strip()
    except Exception:
        api_key = ""
    if not api_key:
        return {"catalogo": {}, "precios": {}, "error": "falta_clave"}
    try:
        custodia = str(st.secrets["otc"]["custodia"]).strip().lower()
    except Exception:
        custodia = OTC_WALLET_CUSTODIA

    por_addr, por_id = {}, {}
    for addr, pid, nombre, divisa, precio, ubic, estado in proyectos:
        p = {"id": pid, "nombre": nombre, "token_address": addr, "divisa": divisa,
             "precio_emision": precio, "ubicacion": ubic, "estado": estado,
             "fecha_fin": None, "tipo_renta": "—"}
        por_addr[addr] = p
        if pid:
            por_id[pid.lower()] = p

    reservas = otc_storage.read_list("Reservas")
    ofertas = otc_storage.read_list("Ofertas")

    balances, entradas = {}, {}
    if custodia:
        balances, _envios, entradas, _ = otc_inventario.balances_de_wallet(
            custodia, api_key, por_addr, por_id)

    cat = otc_inventario.catalogo(balances, reservas, ofertas, api_key,
                                  otc_inventario.saldo_en_wallet, entradas, custodia)
    try:
        precios = otc_storage.read_dict("precios_otc")
    except Exception:
        precios = {}
    return {"catalogo": cat, "precios": precios, "error": ""}


def _precio_stock_reental(precios, addr):
    """Precio de venta del stock propio de Reental: el de la pestaña precios_otc
    y, si no hay, el de emisión (mismo criterio que pages/02_OTC.py)."""
    v = (precios.get(addr) or {}).get("precio_otc") if isinstance(precios.get(addr), dict) else None
    valor = _num(v, None)
    return valor if valor and valor > 0 else None


def cargar_ofertas_otc(df_proyectos=None):
    """Ofertas OTC disponibles, en el formato que usa el resto de la app."""
    if df_proyectos is None or len(df_proyectos) == 0:
        return []
    try:
        res = catalogo_otc(_proyectos_para_catalogo(df_proyectos))
    except Exception as e:
        print(f"❌ Error calculando la disponibilidad OTC: {e}")
        traceback.print_exc()
        st.warning("⚠️ Ahora mismo no hemos podido cargar las ofertas del mercado secundario. "
                   "Inténtalo de nuevo en unos minutos.")
        return []

    proyecto_de = {str(r.get('Token Address', '')).strip().lower(): r
                   for _, r in df_proyectos.iterrows()}
    ofertas = []
    for addr, d in (res.get("catalogo") or {}).items():
        fila = proyecto_de.get(addr)
        pid = str(fila.get('ID', '')) if fila is not None else str(d.get('id', ''))
        nombre = str(fila.get('Nombre del proyecto', '')) if fila is not None else d.get('nombre', '')

        # Stock propio de Reental
        if (d.get('reental') or 0) > 0.001:
            precio = _precio_stock_reental(res.get("precios") or {}, addr)
            origen_precio = 'precio OTC' if precio is not None else 'precio de emisión'
            if precio is None:
                precio = _num(fila.get('Precio Emisión', 0)) if fila is not None else 0
            ofertas.append({
                'proyecto_id': pid.lower(), 'token_address': addr, 'proyecto_nombre': nombre,
                'n_tokens': round(d['reental'], 4), 'precio_venta': precio,
                'divisa': str(fila.get('Divisa', 'EUR')) if fila is not None else 'EUR',
                'estado': 'activa', 'canal': 'Stock Reental',
                'origen_precio': origen_precio,
            })

        # Ofertas de terceros (ya filtradas por la cadena)
        for t in d.get('terceros', []):
            ofertas.append({
                'proyecto_id': pid.lower(), 'token_address': addr, 'proyecto_nombre': nombre,
                'n_tokens': round(t['disponible'], 4), 'precio_venta': t['precio'],
                'divisa': t.get('divisa', 'USD'), 'estado': 'activa',
                'canal': 'Oferta de tercero', 'origen_precio': 'precio de la oferta',
            })

    if res.get("error") == "falta_clave":
        print("❌ Falta la clave de Etherscan en los Secrets ([etherscan] api_key)")
        st.warning("⚠️ Ahora mismo no hemos podido cargar las ofertas del mercado secundario. "
                   "Inténtalo de nuevo en unos minutos.")
    return ofertas

def cargar_ofertas_p2p():
    """Carga operaciones P2P cerradas (como ofertas del mercado secundario)"""
    try:
        from modules import p2p_mercado
        df_p2p = p2p_mercado.cargar()
        
        if df_p2p is None or df_p2p.empty:
            return []
        
        # Convertir a lista de dicts compatible con OTC
        # P2P contiene operaciones CERRADAS, las mostramos como "ofertas históricas"
        ofertas_p2p = []
        for idx, row in df_p2p.iterrows():
            oferta = {
                'id': row.get('hash', f"P2P-{idx}"),
                'proyecto_id': row.get('proyecto', '').lower() if pd.notna(row.get('proyecto')) else '',
                'token_address': row.get('token_address', '').lower() if pd.notna(row.get('token_address')) else '',
                'proyecto_nombre': row.get('proyecto', ''),
                'n_tokens': row.get('tokens', 0),
                'precio_venta': row.get('precio_unitario', 0),
                'divisa': 'USD',
                'inversor': row.get('vendedor', 'Desconocido'),
                'estado': 'cerrada',  # P2P son operaciones ya cerradas
                'canal': 'P2P',
                'fecha': row.get('fecha', '')
            }
            ofertas_p2p.append(oferta)
        
        return ofertas_p2p
    except Exception as e:
        print(f"❌ Error cargando P2P: {e}")
        return []

def cargar_todas_ofertas_secundario(df_proyectos=None):
    """Carga TODAS las ofertas del mercado secundario: OTC + P2P"""
    ofertas_otc = cargar_ofertas_otc(df_proyectos)
    ofertas_p2p = cargar_ofertas_p2p()
    
    # Combinar ambos canales
    todas_ofertas = (ofertas_otc or []) + (ofertas_p2p or [])
    
    return todas_ofertas

# Mínimo de tokens disponibles para que una oferta OTC (o el stock de Reental)
# aparezca en el simulador. Las que tengan esta cantidad o menos no se muestran.
MIN_TOKENS_OTC = 10


def agrupar_ofertas_por_proyecto(ofertas):
    """Agrupa por proyecto_id o token_address las ofertas ACTIVAS
    (mismo criterio que otc_inventario.catalogo de la herramienta OTC)."""
    ofertas_por_proyecto = {}

    for oferta in ofertas:
        # Solo ofertas vivas: las eliminadas, vendidas, etc. no son comprables
        if str(oferta.get('estado', '')).strip().lower() != 'activa':
            continue
        # Solo ofertas con un mínimo de tokens disponibles
        if _num(oferta.get('n_tokens'), 0.0) <= MIN_TOKENS_OTC:
            continue

        # Usar proyecto_id o token_address como clave
        proyecto_id = (oferta.get('proyecto_id') or '').lower()
        token_address = (oferta.get('token_address') or '').lower()
        
        clave = proyecto_id or token_address or None
        
        if not clave:
            continue
        
        if clave not in ofertas_por_proyecto:
            ofertas_por_proyecto[clave] = []
        
        ofertas_por_proyecto[clave].append(oferta)
    
    return ofertas_por_proyecto

# ========== ANCHOS Y FORMATOS DE COLUMNAS (TABLAS PASO 4) ==========
# Para cambiar el ancho de una columna, edita solo su línea aquí.
# width admite "small", "medium", "large" o un número de píxeles (ej. 90).
CONFIG_COLUMNAS_PASO4 = {
    'ID': st.column_config.Column(width="small"),
    'Nombre del proyecto': st.column_config.Column(width=170),
    'Tipología de dividendo': st.column_config.Column(width="medium"),
    'ESTADO': st.column_config.Column('Estado', width=145),
    'Fecha Inicio Estimada': st.column_config.Column(width="small"),
    'Fecha Fin Estimada': st.column_config.Column(width="small"),
    'Ubicación': st.column_config.Column(width="small"),
    'Rentabilidad Total': st.column_config.NumberColumn('Rentabilidad total', format='%.2f%%', width=90),
    'Rentabilidad Anualizada': st.column_config.NumberColumn('Rentabilidad anualizada', format='%.2f%%', width=90),
    'Precio OTC Más Bajo': st.column_config.TextColumn('Precio OTC', width=90),
    'Tokens disponibles': st.column_config.NumberColumn('Tokens disponibles', format='%.2f', width=110),
}

# ========== SUPUESTOS DE MERCADO POR DEFECTO (Paso 5) ==========
# Se usan si no se puede leer el valor real. No son editables por el usuario.
TIPO_CAMBIO_DEFECTO = 1.14      # USD por 1 €
PRECIO_RNT_DEFECTO = 0.32       # USDT por 1 RNT
STAKING_RNT = 3.5               # % anual del staking de RNT (fijo)
# RNT necesarios para cada estatus
RNT_POR_ESTATUS = {'SuperReentel': 28000, 'ReentelPro': 14000, 'Reentel': 0}

# Código ISO numérico de cada país (para pintarlo en el mapa del Paso 5).
# Si aparece un mercado nuevo en el Master, basta con añadirlo aquí.
CODIGOS_PAIS = {
    'espana': 724, 'mexico': 484, 'usa': 840, 'eeuu': 840, 'estados unidos': 840,
    'republica dominicana': 214, 'argentina': 32, 'emiratos arabes': 784,
    'emiratos arabes unidos': 784, 'dubai': 784, 'portugal': 620, 'francia': 250,
    'italia': 380, 'alemania': 276, 'suecia': 752, 'polonia': 616, 'panama': 591,
    'colombia': 170, 'costa rica': 188, 'reino unido': 826, 'andorra': 20,
}



@st.cache_data(ttl=86400)
def tipo_cambio_actual():
    """USD por 1 € según el BCE (se consulta una vez al día). Si falla, valor por defecto."""
    try:
        from modules import divisas
        tipo = divisas.usd_por_euro()
        return round(tipo, 4) if tipo else TIPO_CAMBIO_DEFECTO
    except Exception:
        return TIPO_CAMBIO_DEFECTO


@st.cache_data(ttl=3600)
def precio_rnt_actual():
    """Precio del RNT en USDT según el pool (se consulta como mucho una vez por hora)."""
    try:
        from modules import pool_rnt
        precio = pool_rnt.precio_actual(st.secrets["etherscan"]["api_key"])
        return round(precio, 4) if precio else PRECIO_RNT_DEFECTO
    except Exception:
        return PRECIO_RNT_DEFECTO


from modules.rentabilidad_compra import rentabilidad_ajustada


def divisa_proyecto(row):
    """'USD' o 'EUR' según la divisa del proyecto en el Master."""
    return 'USD' if str(row.get('Divisa', '') or '').strip().upper() in ('USD', '$', 'USDT') else 'EUR'


def convertir_divisa(importe, desde, hacia):
    """Convierte entre EUR y USD (USDT cuenta como USD) con el tipo del BCE."""
    desde = 'USD' if str(desde).upper() in ('USD', 'USDT', '$') else 'EUR'
    hacia = 'USD' if str(hacia).upper() in ('USD', 'USDT', '$') else 'EUR'
    if desde == hacia:
        return importe
    tc = tipo_cambio_actual()
    return importe * tc if desde == 'EUR' else importe / tc


def aplicar_rentabilidad_ajustada(df_display, df_origen, estatus, precio_por_id=None):
    """Sustituye 'Rentabilidad Total' y 'Rentabilidad Anualizada' de una tabla del
    Paso 4 por las calculadas con el precio de compra y los meses que quedan
    (mismas fórmulas que la plantilla de propuestas). `precio_por_id` va en la
    divisa de cada proyecto; si un proyecto no está, se usa su precio de emisión."""
    if df_display is None or len(df_display) == 0:
        return df_display
    filas = {row['ID']: row for _, row in df_origen.iterrows()}
    totales, anuales = [], []
    for pid in df_display['ID']:
        row = filas.get(pid)
        if row is None:
            totales.append(None); anuales.append(None)
            continue
        r = rentabilidad_ajustada(row, estatus, (precio_por_id or {}).get(pid))
        totales.append(round(r['total'], 2))
        anuales.append(round(r['anual'], 2) if r['anual'] is not None else None)
    df_display = df_display.copy()
    df_display['Rentabilidad Total'] = totales
    df_display['Rentabilidad Anualizada'] = anuales
    return df_display


# Importe con el que se simula cada rango de capital del Paso 1 (punto medio del
# rango; para "Más de 50.000", que no tiene techo, se usan 100.000).
CAPITAL_SIMULADO = {
    "Menos de 5.000": 2500,
    "Entre 5.000 y 10.000": 7500,
    "Entre 10.000 y 50.000": 30000,
    "Más de 50.000": 100000,
}

def _indice(opciones, valor):
    """Posición de `valor` en `opciones` (para recordar lo elegido al volver atrás)."""
    return opciones.index(valor) if valor in opciones else None


def importe_simulado(capital_texto):
    return CAPITAL_SIMULADO.get(capital_texto, 30000)


def importe_cliente(datos):
    """Capital con el que se simula: el ajustado en el Paso 4 si lo hay; si no,
    el punto medio del rango elegido en el Paso 1."""
    return datos.get('capital_ajustado') or importe_simulado(datos.get('capital'))


def capital_mostrado(datos, simbolo):
    """Texto del capital para la pantalla y el PDF: el importe con el que se simula."""
    return f"{es(importe_cliente(datos), 0)} {simbolo}"


def md(texto):
    """Escapa el símbolo $ para st.markdown/avisos: Streamlit lo interpreta como
    inicio de fórmula matemática y descoloca el texto (pasaba con la divisa USD)."""
    return str(texto).replace("$", "\\$")


def html_seguro(texto):
    """Lo mismo para fragmentos HTML: el $ se escribe como entidad."""
    return str(texto).replace("$", "&#36;")


def ajustar_capital(importe_repartido):
    """Fija el capital en lo que suman los tokens elegidos, para que el reparto sea
    exactamente el 100 %. Los tokens de cada proyecto no cambian."""
    if importe_repartido and importe_repartido > 0:
        st.session_state.datos_cliente['capital_ajustado'] = importe_repartido


def _formato_euro():
    """True si el cliente invierte en euros (o aún no lo ha elegido)."""
    try:
        return (st.session_state.get('datos_cliente') or {}).get('divisa', 'EUR') != 'USD'
    except Exception:
        return True


def es(valor, decimales=2):
    """Número según la divisa del cliente:
    en euros  → 257.109,50 (punto para miles, coma para decimales)
    en dólares → 257,109.50 (coma para miles, punto para decimales)"""
    try:
        texto = f"{float(valor):,.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)
    if not _formato_euro():
        return texto
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


OBJETIVOS = [
    "Maximizar rentabilidad - quiero invertir en los proyectos con mayor rentabilidad anualizada",
    "Ingresos pasivos regulares - quiero invertir en proyectos que me den rentas periódicas",
]


def priorizar_rentas(df):
    """Para el objetivo de ingresos pasivos: primero los proyectos con rendimientos
    mensuales, luego trimestrales y al final los que solo pagan al terminar.
    Dentro de cada grupo se respeta el orden que ya tenían."""
    if df is None or len(df) == 0:
        return df
    try:
        from modules.formateo_datos import _buscar_columna_tipologia
        col = _buscar_columna_tipologia(df)
    except Exception:
        col = None
    if not col:
        return df
    def _grupo(t):
        t = str(t or "").lower()
        return 0 if "mensual" in t else 1 if "trimestral" in t else 2
    orden = df[col].map(_grupo)
    return df.assign(_orden=orden).sort_values("_orden", kind="stable").drop(columns="_orden")


def tabla_seleccionable(df_display, key):
    """
    Muestra una tabla con una casilla 'Incluir' en cada fila
    y devuelve la lista de IDs de los proyectos marcados.
    """
    if df_display is None or len(df_display) == 0:
        return []
    
    df_editor = df_display.copy()
    marcados_antes = st.session_state.sel_tablas.get(key, set())
    df_editor.insert(0, 'Incluir', df_editor['ID'].isin(marcados_antes))
    
    editado = st.data_editor(
        df_editor,
        hide_index=True,
        key=key,
        column_config={
            **CONFIG_COLUMNAS_PASO4,
            'Incluir': st.column_config.CheckboxColumn('Incluir', width=60),
        },
        disabled=[c for c in df_editor.columns if c != 'Incluir'],
    )
    
    marcados = editado.loc[editado['Incluir'] == True, 'ID'].tolist()
    st.session_state.sel_tablas[key] = set(marcados)
    return marcados


# ========== DIAGNÓSTICO DE LEADS (solo con ?diagnostico=leads en la URL) ==========
try:
    if st.query_params.get("diagnostico") == "leads":
        st.info(leads.diagnostico())
except Exception:
    pass

# ========== HEADER ==========
st.markdown(f"""
<div style="padding: 4px 0 10px 0;">
    <div style="font-size: 22px; font-weight: 800; color: {COLOR_AMBAR};">Reental
        <span style="color: {COLOR_NAVY}; font-weight: 500;">Wealth</span></div>
    <div style="font-size: 38px; font-weight: 800; color: {COLOR_NAVY}; line-height: 1.15; margin-top: 10px;">
        Simulador de <span style="color: {COLOR_AMBAR};">cartera inmobiliaria</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== PROGRESS BAR ==========
progress_value = (st.session_state.paso_actual - 1) / 4
col1, col2 = st.columns([3, 1])
with col1:
    st.progress(progress_value)
with col2:
    st.write(f"**Paso {st.session_state.paso_actual}/5**")

st.markdown("")

# ========== PASO 1: DATOS CLIENTE ==========
if st.session_state.paso_actual == 1:
    st.markdown("## Paso 1: Cuéntanos sobre ti")
    st.markdown("Información básica para personalizar tu simulación")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input(
            "¿Cómo te llamas? *",
            value=st.session_state.datos_cliente.get('nombre', ''),
            key="input_nombre"
        )
        email = st.text_input(
            "¿Cuál es tu email? *",
            value=st.session_state.datos_cliente.get('email', ''),
            key="input_email"
        )
        telefono = st.text_input(
            "¿Cuál es tu número de teléfono? *",
            value=st.session_state.datos_cliente.get('telefono', ''),
            placeholder="Ej.: +34 600 123 456",
            key="input_telefono"
        )
        divisa = st.selectbox(
            "¿En qué divisa prefieres invertir? *",
            ["EUR", "USD"],
            index=_indice(["EUR", "USD"], st.session_state.datos_cliente.get('divisa')),
            placeholder="Selecciona una divisa",
            key="select_divisa"
        )
    
    with col2:
        ya_inversor = st.selectbox(
            "¿Eres ya inversor en Reental? *",
            ["No", "Sí"],
            index=_indice(["No", "Sí"], st.session_state.datos_cliente.get('ya_inversor')),
            placeholder="Selecciona una opción",
            key="select_inversor"
        )
        capital = st.selectbox(
            "¿Cuánto capital tienes disponible para invertir? *",
            list(CAPITAL_SIMULADO.keys()),
            index=_indice(list(CAPITAL_SIMULADO.keys()), st.session_state.datos_cliente.get('capital')),
            placeholder="Selecciona tu rango de capital",
            key="select_capital"
        )
    
    st.markdown("")
    st.markdown("---")
    st.markdown("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col3:
        if st.button("Siguiente >", use_container_width=True, key="btn_paso1_next"):
            email_valido = bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (email or "").strip()))
            digitos_tel = re.sub(r"\D", "", telefono or "")
            telefono_valido = (bool(re.match(r"^[\d\s().+-]+$", (telefono or "").strip()))
                               and 6 <= len(digitos_tel) <= 15)
            if not (nombre and email and telefono and divisa is not None and capital is not None
                    and ya_inversor is not None):
                st.error("Por favor completa todos los campos marcados con *")
            elif not email_valido:
                st.error("Revisa el email: no parece una dirección válida.")
            elif not telefono_valido:
                st.error("Revisa el teléfono: escribe solo números (puedes empezar por + y el prefijo del país).")
            else:
                anteriores = st.session_state.datos_cliente
                nuevos = {
                    'nombre': nombre.strip(),
                    'email': email.strip(),
                    'telefono': telefono.strip(),
                    'divisa': divisa,
                    'ya_inversor': ya_inversor,
                    'capital': capital,
                }
                # Se conservan las respuestas de los pasos siguientes; el capital
                # ajustado solo vale mientras no se cambie el rango ni la divisa.
                if anteriores.get('capital') != capital or anteriores.get('divisa') != divisa:
                    anteriores.pop('capital_ajustado', None)
                st.session_state.datos_cliente = {**anteriores, **nuevos}
                # Guardar el lead (si falla, la app sigue igual)
                if 'lead_id' not in st.session_state:
                    st.session_state.lead_id = uuid.uuid4().hex[:10]
                leads.guardar(st.session_state.lead_id, "Datos de contacto", st.session_state.datos_cliente)
                st.session_state.paso_actual = 2
                st.rerun()

# ========== PASO 2: ESTATUS ==========
elif st.session_state.paso_actual == 2:
    st.markdown("## Paso 2: ¿Qué estatus RNT quieres considerar?")
    st.markdown("")
    
    col1, col2, col3 = st.columns(3)
    
    estatus_seleccionado = st.session_state.datos_cliente.get('estatus', None)
    
    # ========== SUPERREENTEL ==========
    with col1:
        if estatus_seleccionado == 'SuperReentel':
            bg_color = COLOR_AMBAR_CLARO
            border_color = COLOR_AMBAR
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = COLOR_BORDE
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 14px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: {COLOR_NAVY}; font-weight: 800; font-size: 16px; margin-bottom: 15px;">
                🏛️ SUPERREENTEL
            </div>
            <div style="color: {COLOR_NAVY}; font-size: 15px; line-height: 1.6; flex-grow: 1;">
                quiero conseguir hasta un <b>50% más de rentabilidad</b> en mis inversiones inmobiliarias y <b>acceso prioritario</b> a los proyectos.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar SuperReentel", key="btn_super", use_container_width=True):
            st.session_state.datos_cliente['estatus'] = 'SuperReentel'
            st.rerun()
    
    # ========== REENTELPRO ==========
    with col2:
        if estatus_seleccionado == 'ReentelPro':
            bg_color = COLOR_AMBAR_CLARO
            border_color = COLOR_AMBAR
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = COLOR_BORDE
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 14px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: {COLOR_NAVY}; font-weight: 800; font-size: 16px; margin-bottom: 15px;">
                🏢 REENTELPRO
            </div>
            <div style="color: {COLOR_NAVY}; font-size: 15px; line-height: 1.6; flex-grow: 1;">
                quiero conseguir hasta un <b>25% más de rentabilidad</b> en mis inversiones inmobiliarias y acceder a los proyectos tras los SuperReentel.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar ReentelPro", key="btn_pro", use_container_width=True):
            st.session_state.datos_cliente['estatus'] = 'ReentelPro'
            st.rerun()
    
    # ========== REENTEL ==========
    with col3:
        if estatus_seleccionado == 'Reentel':
            bg_color = COLOR_AMBAR_CLARO
            border_color = COLOR_AMBAR
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = COLOR_BORDE
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 14px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: {COLOR_NAVY}; font-weight: 800; font-size: 16px; margin-bottom: 15px;">
                🏠 REENTEL
            </div>
            <div style="color: {COLOR_NAVY}; font-size: 15px; line-height: 1.6; flex-grow: 1;">
                por ahora no quiero estatus.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar Reentel", key="btn_reen", use_container_width=True):
            st.session_state.datos_cliente['estatus'] = 'Reentel'
            st.rerun()
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    # ========== BOTÓN "¿QUIERES MÁS INFO?" ==========
    st.markdown(f"""
    <a href="https://api.leadconnectorhq.com/widget/booking/kAzM5NH9hFxtc88sTQKy" target="_blank" style="text-decoration: none; color: inherit;">
        <div style="background-color: {COLOR_AMBAR_CLARO}; border: 2px solid {COLOR_AMBAR}; color: {COLOR_NAVY}; border-radius: 12px; padding: 15px; font-size: 15px; cursor: pointer; text-align: center;">
            💡 ¿Quieres más información sobre <b> qué es el estatus RNT</b> y cómo puede ayudarte a <b>maximizar tu rentabilidad inmobiliaria</b>? Agenda con nuestro equipo de Onboarding <b style="color: {COLOR_AMBAR_OSCURO};">aquí</b>.
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("< Atrás", use_container_width=True, key="btn_paso2_back"):
            st.session_state.paso_actual = 1
            st.rerun()
    with col3:
        # Validar que estatus esté seleccionado (no None)
        if estatus_seleccionado is not None:
            if st.button("Siguiente >", use_container_width=True, key="btn_paso2_next"):
                st.session_state.paso_actual = 3
                st.rerun()
        else:
            st.button("Siguiente >", use_container_width=True, disabled=True, key="btn_paso2_next_disabled")

# ========== PASO 3: PARÁMETROS ==========
elif st.session_state.paso_actual == 3:
    st.markdown("## Paso 3: Define tu estrategia de inversión")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        objetivo = st.selectbox(
            "Objetivo de inversión *",
            OBJETIVOS,
            index=_indice(OBJETIVOS, st.session_state.datos_cliente.get('objetivo')),
            placeholder="Selecciona tu objetivo",
            key="select_objetivo"
        )
    

    st.markdown("")
    st.markdown("**Selecciona los mercados de interés:** *")
    
    # Obtener todos los mercados únicos del Master Inmuebles (incluyendo cerrados)
    try:
        from modules.maestro import proyectos
        todos_los_proyectos = proyectos()
        if todos_los_proyectos:
            mercados_disponibles = sorted(list(set([p.get('ubicacion', '').strip() for p in todos_los_proyectos if p.get('ubicacion', '').strip()])))
        else:
            mercados_disponibles = ["España", "Portugal", "Francia", "Italia", "Alemania", "Suecia", "Polonia"]
    except:
        mercados_disponibles = ["España", "Portugal", "Francia", "Italia", "Alemania", "Suecia", "Polonia"]
    
    mercados_seleccionados = st.multiselect(
        "Mercados",
        mercados_disponibles,
        default=st.session_state.datos_cliente.get('mercados', []),
        key="multiselect_mercados",
        label_visibility="collapsed"
    )
    
    st.markdown("")
    st.markdown("---")
    st.markdown("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("< Atrás", use_container_width=True, key="btn_paso3_back"):
            st.session_state.paso_actual = 2
            st.rerun()
    
    with col3:
        estatus_seleccionado = st.session_state.datos_cliente.get('estatus')
        
        # Validar que TODOS los campos estén completos (no None)
        if objetivo is not None and mercados_seleccionados and estatus_seleccionado is not None:
            if st.button("Siguiente >", use_container_width=True, key="btn_paso3_next"):
                st.session_state.datos_cliente['objetivo'] = objetivo
                st.session_state.datos_cliente['mercados'] = mercados_seleccionados
                
                # Cargar TODOS los proyectos (incluidos cerrados con OTC)
                try:
                    st.session_state.df_proyectos = cargar_todos_proyectos()
                    st.session_state.paso_actual = 4
                    st.rerun()
                except Exception as e:
                    print(f"❌ Error cargando proyectos: {e}")
                    traceback.print_exc()
                    st.error("No hemos podido cargar los proyectos. Inténtalo de nuevo en unos minutos.")
        else:
            st.button("Siguiente >", use_container_width=True, disabled=True, key="btn_paso3_next_disabled")
            faltan = [n for n, ok in (("el objetivo de inversión", objetivo is not None),
                                      ("al menos un mercado", bool(mercados_seleccionados))) if not ok]
            if faltan:
                st.caption("Para continuar, elige " + " y ".join(faltan) + ".")

# ========== PASO 4: PROYECTOS Y PRECIOS ==========
elif st.session_state.paso_actual == 4:
    st.markdown("## Paso 4: Crea tu cartera de inversión")
    st.markdown("Selecciona aquellos proyectos que quieras incluir en tu cartera")
    st.markdown("")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        # SEPARAR: Para Primera Emisión solo FINANCIÁNDOSE, para OTC todos
        df_proyectos_todos = st.session_state.df_proyectos.copy()
        
        # Filtrar solo FINANCIÁNDOSE para la sección de Primera Emisión
        df_proyectos = df_proyectos_todos[
            df_proyectos_todos['ESTADO'].str.upper() == 'FINANCIÁNDOSE'
        ].copy()
        
        # Obtener parámetros
        mercados_seleccionados = st.session_state.datos_cliente.get('mercados', [])
        objetivo = st.session_state.datos_cliente.get('objetivo', '')
        estatus = st.session_state.datos_cliente.get('estatus', None)
        
        criterios = {
            'ubicaciones': mercados_seleccionados,
            'duracion': 'Largo plazo' if 'maximizar' in objetivo.lower() else 'Corto plazo'
        }
        
        # Cargar ofertas OTC + P2P
        ofertas_otc_list = cargar_todas_ofertas_secundario(df_proyectos_todos)
        ofertas_por_proy = agrupar_ofertas_por_proyecto(ofertas_otc_list)

        # Separar proyectos ACTIVOS (FINANCIÁNDOSE)
        df_matchean = df_proyectos[df_proyectos['Ubicación'].isin(mercados_seleccionados)].copy()
        df_no_matchean = df_proyectos[~df_proyectos['Ubicación'].isin(mercados_seleccionados)].copy()
        
        # Rankear
        if len(df_matchean) > 0:
            try:
                df_matchean = rankear_proyectos(df_matchean, criterios, estatus)
            except:
                pass
        
        ingresos_pasivos = 'ingresos' in (objetivo or '').lower()
        if ingresos_pasivos:
            df_matchean = priorizar_rentas(df_matchean)
            df_no_matchean = priorizar_rentas(df_no_matchean)
        
        # IDs marcados en cualquiera de las tablas
        ids_seleccionados = []
        
        # ========== TABLAS PRIMERA EMISIÓN ==========
        st.markdown("### 📊 Proyectos disponibles en primera emisión (Reental)")
        
        if len(df_matchean) == 0:
            st.info("No hay proyectos en primera emisión en los mercados que has elegido"
                    + (". Debajo tienes otros proyectos que podrían interesarte." if len(df_no_matchean) > 0 else "."))
        else:
            df_display_matchean = preparar_proyectos_para_paso4(df_matchean, estatus)
            df_display_matchean = aplicar_rentabilidad_ajustada(df_display_matchean, df_matchean, estatus)
            ids_seleccionados += tabla_seleccionable(df_display_matchean, "tabla_primera_emision")
        
        if len(df_no_matchean) > 0:
            st.markdown("#### Proyectos adicionales que podrían interesarte")
            df_display_no_matchean = preparar_proyectos_para_paso4(df_no_matchean, estatus)
            df_display_no_matchean = aplicar_rentabilidad_ajustada(df_display_no_matchean, df_no_matchean, estatus)
            ids_seleccionados += tabla_seleccionable(df_display_no_matchean, "tabla_adicionales")
        
        # ========== TABLA OTC ==========
        st.markdown("---")
        st.markdown("### 💰 Proyectos disponibles en OTC (Mercado Secundario)")
        
        df_con_otc = pd.DataFrame()
        
        if ofertas_por_proy:
            # Mapas de proyectos por ID y Token Address (incluidos cerrados)
            proyectos_por_id = {}
            proyectos_por_token = {}
            for idx, row in df_proyectos_todos.iterrows():
                proyecto_id = str(row.get('ID', '')).lower()
                token_addr = str(row.get('Token Address', '')).lower()
                if proyecto_id:
                    proyectos_por_id[proyecto_id] = row
                if token_addr:
                    proyectos_por_token[token_addr] = row
            
            # Encontrar proyectos con ofertas
            proyectos_con_otc = []
            for clave_otc in ofertas_por_proy.keys():
                proyecto_data = proyectos_por_id.get(clave_otc)
                if proyecto_data is None:
                    proyecto_data = proyectos_por_token.get(clave_otc)
                if proyecto_data is not None:
                    proyectos_con_otc.append(proyecto_data)
            
            if proyectos_con_otc:
                df_con_otc = pd.DataFrame(proyectos_con_otc)
        
        # Solo los mercados elegidos en el Paso 3
        otc_fuera_de_mercado = 0
        if len(df_con_otc) > 0 and mercados_seleccionados:
            en_mercado = df_con_otc['Ubicación'].isin(mercados_seleccionados)
            otc_fuera_de_mercado = int((~en_mercado).sum())
            df_con_otc = df_con_otc[en_mercado]
        
        if len(df_con_otc) > 0:
            n_otc = len(df_con_otc)
            st.success(f"✅ {n_otc} proyecto{'s' if n_otc != 1 else ''} con tokens disponibles en el mercado secundario")
            
            try:
                df_con_otc = rankear_proyectos(df_con_otc, criterios, estatus)
            except:
                pass
            if ingresos_pasivos:
                df_con_otc = priorizar_rentas(df_con_otc)
            
            # Precio OTC más bajo por proyecto, en la divisa del proyecto
            precio_min_por_id = {}
            for idx, row in df_con_otc.iterrows():
                clave = str(row.get('ID', '')).lower() or str(row.get('Token Address', '')).lower()
                div_proy = divisa_proyecto(row)
                precios = []
                for oferta in ofertas_por_proy.get(clave, []):
                    try:
                        precio = float(oferta.get('precio_venta', 0))
                        if precio > 0:
                            precios.append(convertir_divisa(precio, oferta.get('divisa', 'USD'), div_proy))
                    except:
                        pass
                if precios:
                    precio_min_por_id[row['ID']] = min(precios)
            
            simbolo_por_id = {row['ID']: ('$' if divisa_proyecto(row) == 'USD' else '€')
                              for _, row in df_con_otc.iterrows()}
            df_display_otc = preparar_proyectos_para_paso4(df_con_otc, estatus)
            # Rentabilidad comprando a la oferta más barata
            df_display_otc = aplicar_rentabilidad_ajustada(df_display_otc, df_con_otc, estatus, precio_min_por_id)
            # Tokens disponibles: stock de Reental + todas las ofertas de terceros del proyecto
            tokens_por_id = {}
            for _, row in df_con_otc.iterrows():
                clave = str(row.get('ID', '')).lower() or str(row.get('Token Address', '')).lower()
                tokens_por_id[row['ID']] = round(sum(_num(o.get('n_tokens'), 0.0)
                                                     for o in ofertas_por_proy.get(clave, [])), 2)
            df_display_otc['Tokens disponibles'] = df_display_otc['ID'].map(tokens_por_id)
            df_display_otc['Precio OTC Más Bajo'] = df_display_otc['ID'].map(
                lambda pid: (f"{es(precio_min_por_id[pid], 2)} {simbolo_por_id.get(pid, '€')}"
                             if pid in precio_min_por_id else "-")
            )
            ids_seleccionados += tabla_seleccionable(df_display_otc, "tabla_otc")
        elif otc_fuera_de_mercado:
            st.info("📭 Ahora mismo no hay tokens disponibles en el mercado secundario en los mercados que has elegido.")
        else:
            st.info("📭 Ahora mismo no hay tokens disponibles en el mercado secundario.")
        if otc_fuera_de_mercado:
            st.caption(f"Hay {otc_fuera_de_mercado} proyecto{'s' if otc_fuera_de_mercado != 1 else ''} más con tokens "
                       "disponibles en otros mercados. Puedes añadir esos mercados en el Paso 3.")
        
        # ========== GUARDAR SELECCIÓN ==========
        ids_seleccionados = list(dict.fromkeys(ids_seleccionados))  # sin duplicados, en orden
        
        for pid in list(st.session_state.cartera_selecciones.keys()):
            st.session_state.cartera_selecciones[pid]['seleccionado'] = pid in ids_seleccionados
        for pid in ids_seleccionados:
            if pid not in st.session_state.cartera_selecciones:
                st.session_state.cartera_selecciones[pid] = {'seleccionado': True, 'porcentaje': 0}
        
        filas_por_id = {row['ID']: row for _, row in df_proyectos_todos.iterrows()}
        
        # ========== CONSTRUIR CARTERA ==========
        st.markdown("---")
        st.markdown("### Construye tu cartera")

        MODOS_REPARTO = ["Por cantidad de tokens", "Por % de mi cartera", "Por igual"]
        if st.session_state.get('modo_reparto') not in MODOS_REPARTO:
            st.session_state.modo_reparto = "Por igual"
        if not isinstance(st.session_state.get('oferta_elegida'), dict):
            st.session_state.oferta_elegida = {}

        proyectos_seleccionados = []
        divisa_cliente_p4 = (st.session_state.datos_cliente.get('divisa') or 'EUR').upper()
        simbolo_cliente_p4 = '€' if divisa_cliente_p4 == 'EUR' else '$'
        ids_validos = [pid for pid in ids_seleccionados if pid in filas_por_id]
        tokens_compra = st.session_state.tokens_compra
        for pid in ids_validos:
            tokens_compra.setdefault(pid, 0.0)

        def _simbolo(div):
            return '$' if str(div).upper() in ('USD', 'USDT', '$') else '€'

        def _etiqueta(o):
            texto = f"{es(o['precio'], 2)} {_simbolo(o['divisa'])}"
            if _simbolo(o['divisa']) != simbolo_cliente_p4:
                texto += (f" (aprox. {es(convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4), 2)} "
                          f"{simbolo_cliente_p4})")
            return texto

        # ----- Opciones de compra de cada proyecto (la más barata primero) -----
        opciones_por_id = {}
        for pid in ids_validos:
            row = filas_por_id[pid]
            precio_em = _num(row.get('Precio Emisión', 0))
            opciones = []
            if str(row.get('ESTADO', '')).upper() == 'FINANCIÁNDOSE':
                opciones.append({'tipo': 'Emisión', 'precio': precio_em,
                                 'divisa': divisa_proyecto(row), 'n_tokens': None})
            clave_otc = str(pid).lower() or str(row.get('Token Address', '')).lower()
            for oferta in ofertas_por_proy.get(clave_otc, []):
                precio = _num(oferta.get('precio_venta'), 0.0)
                if precio > 0:
                    opciones.append({'tipo': 'OTC', 'precio': precio,
                                     'divisa': oferta.get('divisa', 'EUR'),
                                     'n_tokens': _num(oferta.get('n_tokens'), 0.0)})
            if not opciones:
                opciones.append({'tipo': 'Emisión', 'precio': precio_em,
                                 'divisa': divisa_proyecto(row), 'n_tokens': None})
            opciones.sort(key=lambda o: convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4))
            opciones_por_id[pid] = opciones

        def _oferta(pid):
            opciones = opciones_por_id[pid]
            try:
                i = int(st.session_state.oferta_elegida.get(pid, 0))
            except (TypeError, ValueError):
                i = 0
            return opciones[i] if 0 <= i < len(opciones) else opciones[0]

        def _precio_cliente(o):
            """Precio de un token en la divisa del cliente."""
            return convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4)

        def _olvidar_widgets(pid):
            """Las casillas se vuelven a rellenar desde tokens_compra en la siguiente vuelta."""
            for prefijo in ("tk_", "pct_"):
                st.session_state.pop(f"{prefijo}{pid}", None)

        # ----- Estado de partida -----
        importe_total_p4 = importe_cliente(st.session_state.datos_cliente)
        def _texto_importe(valor):
            """Importe con separador de miles y el símbolo dentro de la casilla: «50.000 €»."""
            return f"{es(valor, 0)} {simbolo_cliente_p4}"
        
        def _leer_importe(texto):
            """Convierte lo escrito («50.000 €», «50000», «50,000 $»…) en número. None si no se entiende."""
            limpio = re.sub(r"[^\d.,]", "", str(texto or ""))
            if not limpio:
                return None
            if _formato_euro():
                limpio = limpio.replace(".", "").replace(",", ".")
            else:
                limpio = limpio.replace(",", "")
            try:
                return float(limpio)
            except ValueError:
                return None
        
        if 'input_importe' not in st.session_state:
            st.session_state.input_importe = _texto_importe(importe_total_p4)
        modo = st.session_state.modo_reparto
        estatus_p4 = st.session_state.datos_cliente.get('estatus') or 'Reentel'

        def _cambiar_importe():
            anterior = importe_cliente(st.session_state.datos_cliente)
            nuevo = _leer_importe(st.session_state.input_importe)
            if nuevo is None or nuevo <= 0:
                # No se entiende lo escrito: se deja el importe que había
                st.session_state.input_importe = _texto_importe(anterior)
                return
            st.session_state.datos_cliente['capital_ajustado'] = nuevo
            st.session_state.input_importe = _texto_importe(nuevo)
            # Repartiendo por %, se mantienen los % y cambian los tokens
            if st.session_state.modo_reparto == "Por % de mi cartera" and anterior:
                for p in list(st.session_state.tokens_compra):
                    st.session_state.tokens_compra[p] *= nuevo / anterior
                    _olvidar_widgets(p)

        def _cambiar_modo():
            valor = st.session_state.get("selector_modo")
            if valor in MODOS_REPARTO:          # si se deselecciona, se mantiene el anterior
                st.session_state.modo_reparto = valor
            for p in list(st.session_state.tokens_compra):
                _olvidar_widgets(p)

        # Reparto por igual respetando los tokens disponibles: si un proyecto no
        # llega a su parte, se le asigna todo lo que hay y el resto se reparte
        # entre los demás.
        if modo == "Por igual" and ids_validos and importe_total_p4 > 0:
            restante, abiertos, asignado = importe_total_p4, list(ids_validos), {}
            while abiertos:
                parte = restante / len(abiertos)
                limitados = [p for p in abiertos if _oferta(p)['n_tokens'] is not None
                             and _oferta(p)['n_tokens'] * _precio_cliente(_oferta(p)) < parte]
                if not limitados:
                    for p in abiertos:
                        asignado[p] = parte
                    break
                for p in limitados:
                    asignado[p] = _oferta(p)['n_tokens'] * _precio_cliente(_oferta(p))
                    restante -= asignado[p]
                    abiertos.remove(p)
            for p in ids_validos:
                precio = _precio_cliente(_oferta(p))
                tokens_compra[p] = round(asignado.get(p, 0.0) / precio, 4) if precio else 0.0

        # ----- Cálculos a partir de los tokens -----
        filas_calc = []
        importe_repartido = 0.0
        for pid in ids_validos:
            o = _oferta(pid)
            tokens = max(0.0, _num(tokens_compra.get(pid), 0.0))
            importe = tokens * _precio_cliente(o)
            importe_repartido += importe
            row = filas_por_id[pid]
            precio_proy = convertir_divisa(o['precio'], o['divisa'], divisa_proyecto(row))
            rent = rentabilidad_ajustada(row, estatus_p4, precio_proy)
            filas_calc.append((pid, o, tokens, importe, rent))
        pendiente = importe_total_p4 - importe_repartido
        tolerancia = max(1.0, importe_total_p4 * 0.0005)
        tokens_totales = sum(f[2] for f in filas_calc)
        rent_media = (sum((f[4]['anual'] or 0.0) * f[3] for f in filas_calc) / importe_repartido
                      if importe_repartido > 0 else 0.0)

        # ----- Estilos de esta sección -----
        st.markdown(f"""
        <style>
        [class*="st-key-kpi_"] {{
            background: #ffffff; border: 1px solid {COLOR_BORDE} !important; border-radius: 12px;
            padding: 12px 14px 10px 14px; min-height: 118px;
        }}
        [class*="st-key-kpi_"] div[data-testid="stVerticalBlock"] {{ gap: 0.15rem; }}
        .kpi-titulo {{ font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.5px; }}
        .kpi-valor {{ font-size: 26px; font-weight: 800; color: {COLOR_NAVY}; line-height: 1.25; }}
        .kpi-sub {{ font-size: 12px; color: {COLOR_GRIS_CLARO}; }}
        .st-key-kpi_importe div[data-baseweb="input"] {{ min-height: 38px; }}
        .st-key-kpi_importe input {{ font-size: 22px; font-weight: 800; color: {COLOR_NAVY}; padding: 2px 8px; }}
        .st-key-kpi_pendiente button {{ padding: 2px 10px; min-height: 28px; font-size: 12px; }}

        .st-key-tabla_cartera {{
            background: #ffffff; border: 1px solid {COLOR_BORDE}; border-radius: 12px; padding: 4px 6px;
        }}
        .st-key-tabla_cartera div[data-testid="stVerticalBlock"] {{ gap: 0; }}
        .st-key-tabla_cartera div[data-testid="stHorizontalBlock"] {{ gap: 0.75rem; }}
        .st-key-tabla_cartera p {{ margin-bottom: 0; }}
        .st-key-tabla_cartera [data-testid="stMarkdownContainer"],
        [class*="st-key-kpi_"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
        .nota-gris {{ display: block; margin-top: 2px; }}
        [class*="st-key-fila_"] {{ padding: 8px 10px; border-radius: 8px; }}
        [class*="st-key-fila_par_"] {{ background: {COLOR_FONDO}; }}
        .st-key-tabla_cartera div[data-baseweb="input"],
        .st-key-tabla_cartera div[data-baseweb="select"] > div {{ min-height: 32px; }}
        .st-key-tabla_cartera input {{ padding: 4px 8px; }}
        .st-key-tabla_cartera button[data-testid="stNumberInputStepUp"],
        .st-key-tabla_cartera button[data-testid="stNumberInputStepDown"] {{ display: none; }}
        .st-key-tabla_cartera .stButton button {{ padding: 2px 10px; min-height: 32px; }}
        .fila-cab {{ font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.4px; padding: 6px 10px 2px 10px; }}
        .proy-nombre {{ font-weight: 700; color: {COLOR_NAVY}; }}
        .proy-sub, .nota-gris {{ font-size: 12px; color: {COLOR_GRIS}; }}
        .barra-pct {{ background: #f1f3f5; border-radius: 4px; height: 8px; width: 100%; }}
        .barra-pct > div {{ background: {COLOR_AMBAR}; border-radius: 4px; height: 8px; }}
        </style>
        """, unsafe_allow_html=True)

        def _kpi(clave):
            try:
                return st.container(key=f"kpi_{clave}")
            except TypeError:
                return st.container(border=True)

        # ----- 1) Franja de indicadores -----
        k1, k2, k3, k4 = st.columns(4)
        with k1, _kpi("importe"):
            st.markdown("<div class='kpi-titulo'>IMPORTE A INVERTIR</div>", unsafe_allow_html=True)
            st.text_input("Importe a invertir", key="input_importe", on_change=_cambiar_importe,
                          label_visibility="collapsed")
            rango = st.session_state.datos_cliente.get('capital', '')
            st.markdown(html_seguro(f"<div class='kpi-sub'>En el Paso 1 elegiste «{rango}». Te proponemos el "
                                    "punto medio de ese rango; puedes cambiarlo por el importe exacto que "
                                    "quieras invertir.</div>"), unsafe_allow_html=True)
        importe_total_p4 = importe_cliente(st.session_state.datos_cliente)

        with k2, _kpi("repartido"):
            st.markdown(html_seguro(
                f"<div class='kpi-titulo'>REPARTIDO</div>"
                f"<div class='kpi-valor'>{es(importe_repartido, 0)} {simbolo_cliente_p4}</div>"
                f"<div class='kpi-sub'>{es(tokens_totales, 2)} tokens · {len(ids_validos)} "
                f"proyecto{'s' if len(ids_validos) != 1 else ''}</div>"), unsafe_allow_html=True)

        with k3, _kpi("pendiente"):
            if not ids_validos:
                titulo, valor, color = "PENDIENTE", "—", COLOR_GRIS_CLARO
            elif abs(pendiente) <= tolerancia:
                titulo, valor, color = "PENDIENTE", "✓ Todo repartido", COLOR_VERDE
            elif pendiente > 0:
                titulo, valor, color = "PENDIENTE", f"{es(pendiente, 0)} {simbolo_cliente_p4}", COLOR_AMBAR_OSCURO
            else:
                titulo, valor, color = "TE HAS PASADO EN", f"{es(-pendiente, 0)} {simbolo_cliente_p4}", COLOR_ROJO
            st.markdown(html_seguro(f"<div class='kpi-titulo'>{titulo}</div>"
                                    f"<div class='kpi-valor' style='color:{color};'>{valor}</div>"),
                        unsafe_allow_html=True)
            if ids_validos and abs(pendiente) > tolerancia and importe_repartido > 0:
                def _usar_repartido(valor):
                    st.session_state.datos_cliente['capital_ajustado'] = valor
                    st.session_state.input_importe = _texto_importe(valor)
                    for p in list(st.session_state.tokens_compra):
                        _olvidar_widgets(p)
                st.button(md(f"Usar {es(importe_repartido, 0)} {simbolo_cliente_p4} como importe"),
                          key="btn_ajustar_capital", on_click=_usar_repartido, args=(importe_repartido,),
                          help="Cambia el importe a invertir para que coincida con lo que has repartido")

        with k4, _kpi("rentabilidad"):
            st.markdown(html_seguro(
                f"<div class='kpi-titulo'>RENT. ANUALIZADA</div>"
                f"<div class='kpi-valor'>{es(rent_media, 2) + ' %' if importe_repartido > 0 else '—'}</div>"
                f"<div class='kpi-sub'>estimada · {estatus_p4} · al precio elegido</div>"),
                unsafe_allow_html=True)

        # ----- 2) Barra de reparto -----
        if ids_validos and importe_total_p4 > 0:
            base = max(importe_total_p4, importe_repartido)
            tramos = []
            for i, (pid, o, tokens, importe, rent) in enumerate(filas_calc):
                if importe <= 0:
                    continue
                ancho = importe / base * 100
                nombre = str(filas_por_id[pid]['Nombre del proyecto']).replace("'", "&#39;")
                color = PALETA_GRAFICOS[i % len(PALETA_GRAFICOS)]
                texto_color = "#ffffff" if color in ("#1f2937", "#15803d", "#3e4753") else COLOR_NAVY
                etiqueta = nombre if ancho >= 9 else ""
                tramos.append(
                    f"<div title='{nombre}: {es(importe / importe_total_p4 * 100, 1)} %' "
                    f"style='width:{ancho:.3f}%;background:{color};color:{texto_color};"
                    f"overflow:hidden;white-space:nowrap;text-overflow:ellipsis;padding:0 6px;'>{etiqueta}</div>")
            if pendiente > tolerancia:
                ancho = pendiente / base * 100
                tramos.append(f"<div title='Pendiente' style='width:{ancho:.3f}%;background:{COLOR_BORDE};"
                              f"color:{COLOR_GRIS};overflow:hidden;white-space:nowrap;padding:0 6px;'>"
                              f"{'pendiente' if ancho >= 9 else ''}</div>")
            st.markdown(
                "<div style='display:flex;height:26px;border-radius:8px;overflow:hidden;margin:12px 0 4px 0;"
                f"font-size:12px;font-weight:700;line-height:26px;border:1px solid {COLOR_BORDE};"
                f"background:{COLOR_BORDE};'>" + "".join(tramos) + "</div>",
                unsafe_allow_html=True)
            if pendiente < -tolerancia:
                st.markdown(html_seguro(f"<div class='nota-gris' style='color:{COLOR_ROJO};'>Lo repartido supera "
                                        f"tu importe a invertir en {es(-pendiente, 0)} {simbolo_cliente_p4}.</div>"),
                            unsafe_allow_html=True)

        # ----- 3) Modo de reparto (píldoras) -----
        st.markdown("")
        if st.session_state.get('selector_modo') not in MODOS_REPARTO:
            st.session_state.selector_modo = modo
        if hasattr(st, "segmented_control"):
            st.segmented_control("¿Cómo quieres repartir tu cartera?", MODOS_REPARTO, key="selector_modo",
                                 on_change=_cambiar_modo)
        else:
            st.radio("¿Cómo quieres repartir tu cartera?", MODOS_REPARTO, horizontal=True,
                     key="selector_modo", on_change=_cambiar_modo)

        # ----- 4) Tabla: una fila por proyecto -----
        proyectos_sin_tokens = []
        if not ids_validos:
            st.info("Marca en las tablas de arriba los proyectos que quieras incluir")
        else:
            def _contenedor(clave):
                try:
                    return st.container(key=clave)
                except TypeError:
                    return st.container()

            def _columnas():
                anchos = [2.6, 2.5, 2.0, 0.7, 2.4]
                try:
                    return st.columns(anchos, vertical_alignment="center")
                except TypeError:
                    return st.columns(anchos)

            titulo_entrada = {"Por cantidad de tokens": "TOKENS A COMPRAR",
                              "Por % de mi cartera": "% DE LA CARTERA",
                              "Por igual": "TOKENS A COMPRAR"}[modo]

            def _cambiar_oferta(pid, opciones):
                anterior = _oferta(pid)
                try:
                    nueva_i = int(st.session_state[f"of_{pid}"])
                except (TypeError, ValueError, KeyError):
                    nueva_i = 0
                nueva = opciones[nueva_i]
                # Repartiendo por %, se mantiene el importe y se recalculan los tokens
                if st.session_state.modo_reparto == "Por % de mi cartera" and _precio_cliente(nueva):
                    importe = st.session_state.tokens_compra.get(pid, 0.0) * _precio_cliente(anterior)
                    st.session_state.tokens_compra[pid] = importe / _precio_cliente(nueva)
                st.session_state.oferta_elegida[pid] = nueva_i
                _olvidar_widgets(pid)

            def _guardar_tokens(pid):
                st.session_state.tokens_compra[pid] = max(0.0, float(st.session_state.get(f"tk_{pid}") or 0.0))

            def _guardar_pct(pid, precio_cliente, importe_total):
                pct = max(0.0, float(st.session_state.get(f"pct_{pid}") or 0.0))
                st.session_state.tokens_compra[pid] = (importe_total * pct / 100 / precio_cliente
                                                       if precio_cliente else 0.0)

            def _maximo(pid, tokens_max):
                st.session_state.tokens_compra[pid] = tokens_max
                _olvidar_widgets(pid)

            def _dividendo_corto(texto):
                t = str(texto or "").lower()
                partes = []
                if "mensual" in t:
                    partes.append("mensual")
                if "trimestral" in t:
                    partes.append("trimestral")
                if "final" in t:
                    partes.append("al final")
                return " + ".join(partes) if partes else (str(texto) if texto else "")

            try:
                from modules.formateo_datos import _buscar_columna_tipologia
                col_tipo = _buscar_columna_tipologia(df_proyectos_todos)
            except Exception:
                col_tipo = None

            with _contenedor("tabla_cartera"):
                c = _columnas()
                for col, titulo in zip(c, ["PROYECTO", "PRECIO DE COMPRA", titulo_entrada, "", "% DE TU CARTERA"]):
                    col.markdown(f"<div class='fila-cab'>{titulo or '&nbsp;'}</div>", unsafe_allow_html=True)

                for n_fila, (pid, o, tokens, importe, rent) in enumerate(filas_calc):
                    row = filas_por_id[pid]
                    nombre = row['Nombre del proyecto']
                    opciones = opciones_por_id[pid]
                    precio_cli = _precio_cliente(o)
                    pct = importe / importe_total_p4 * 100 if importe_total_p4 else 0.0

                    with _contenedor(f"fila_{'par' if n_fila % 2 else 'impar'}_{n_fila}"):
                        c_nom, c_precio, c_entrada, c_max, c_pct = _columnas()

                        # Proyecto + ubicación · dividendo · rentabilidad al precio elegido
                        detalles = [str(row.get('Ubicación', '') or '')]
                        if col_tipo:
                            detalles.append(_dividendo_corto(row.get(col_tipo)))
                        if rent['anual'] is not None:
                            detalles.append(f"{es(rent['anual'], 1)} % anual")
                        c_nom.markdown(f"<div class='proy-nombre'>{nombre}</div>"
                                       f"<div class='proy-sub'>{' · '.join(d for d in detalles if d)}</div>",
                                       unsafe_allow_html=True)

                        # Precio: desplegable solo si hay varias ofertas
                        if len(opciones) > 1:
                            if f"of_{pid}" not in st.session_state:
                                st.session_state[f"of_{pid}"] = opciones.index(o)
                            c_precio.selectbox(
                                "Precio de compra", list(range(len(opciones))), key=f"of_{pid}",
                                format_func=lambda i, opciones=opciones: (
                                    _etiqueta(opciones[i]) + (f" · {es(opciones[i]['n_tokens'], 2)} tk"
                                                              if opciones[i]['n_tokens'] is not None else "")),
                                on_change=_cambiar_oferta, args=(pid, opciones), label_visibility="collapsed")
                        else:
                            c_precio.markdown(md(_etiqueta(o)))

                        # Entrada según el modo de reparto + disponibles debajo
                        with c_entrada:
                            if modo == "Por cantidad de tokens":
                                if f"tk_{pid}" not in st.session_state:
                                    st.session_state[f"tk_{pid}"] = round(tokens, 2)
                                st.number_input("Tokens", min_value=0.0, step=1.0, format="%.2f",
                                                key=f"tk_{pid}", on_change=_guardar_tokens, args=(pid,),
                                                label_visibility="collapsed")
                            elif modo == "Por % de mi cartera":
                                if f"pct_{pid}" not in st.session_state:
                                    st.session_state[f"pct_{pid}"] = round(pct, 1)
                                st.number_input("%", min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
                                                key=f"pct_{pid}", on_change=_guardar_pct,
                                                args=(pid, precio_cli, importe_total_p4),
                                                label_visibility="collapsed")
                            else:
                                st.markdown(f"<div class='proy-nombre'>{es(tokens, 2)} tokens</div>",
                                            unsafe_allow_html=True)
                            if o['n_tokens'] is not None:
                                nota = f"de {es(o['n_tokens'], 2)} disponibles"
                                if modo == "Por % de mi cartera":
                                    nota = f"{es(tokens, 2)} tokens " + nota
                                st.markdown(f"<div class='nota-gris'>{nota}</div>", unsafe_allow_html=True)
                            elif modo == "Por % de mi cartera":
                                st.markdown(f"<div class='nota-gris'>{es(tokens, 2)} tokens</div>",
                                            unsafe_allow_html=True)

                        # Máx: todos los tokens disponibles, sin pasar del importe a invertir
                        if o['n_tokens'] is not None and modo != "Por igual" and precio_cli:
                            tokens_max = round(min(o['n_tokens'], importe_total_p4 / precio_cli), 4)
                            c_max.button("Máx", key=f"max_{pid}", on_click=_maximo, args=(pid, tokens_max),
                                         help=(f"Comprar {es(tokens_max, 2)} tokens: todos los disponibles "
                                               "en esta oferta, sin pasar de tu importe a invertir"))

                        # % de tu cartera: barrita + importe
                        falta = o['n_tokens'] is not None and tokens > o['n_tokens'] + 0.01
                        if falta:
                            proyectos_sin_tokens.append(nombre)
                        color_barra = COLOR_ROJO if falta else COLOR_AMBAR
                        sub = (f"<span style='color:{COLOR_ROJO};'>⚠ faltan {es(tokens - o['n_tokens'], 2)} tk</span>"
                               f" · {es(importe, 0)} {simbolo_cliente_p4}" if falta
                               else f"{es(importe, 0)} {simbolo_cliente_p4}")
                        c_pct.markdown(html_seguro(
                            "<div style='display:flex;align-items:center;gap:8px;'>"
                            f"<div class='barra-pct' style='flex:1;'><div style='width:{min(pct, 100):.2f}%;"
                            f"background:{color_barra};'></div></div>"
                            f"<div style='font-weight:700;color:{COLOR_NAVY};min-width:52px;text-align:right;'>"
                            f"{es(pct, 1)} %</div></div>"
                            f"<div class='nota-gris'>{sub}</div>"), unsafe_allow_html=True)

                    # Datos para el Paso 5
                    st.session_state.precios_compra[pid] = {'precio': o['precio'], 'divisa': o['divisa'],
                                                            'tipo': o['tipo'], 'n_tokens': o['n_tokens']}
                    st.session_state.cartera_selecciones.setdefault(pid, {'seleccionado': True})['porcentaje'] = pct
                    proyectos_seleccionados.append({
                        'id': pid, 'nombre': nombre, 'ubicacion': row['Ubicación'],
                        'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0),
                        'address': row.get('Token Address', ''), 'precio_emision': _num(row.get('Precio Emisión', 0)),
                    })

            if modo == "Por igual":
                st.caption("Para ajustar algún proyecto a mano, elige «Por cantidad de tokens» "
                           "o «Por % de mi cartera».")
            if proyectos_sin_tokens:
                st.warning(md(f"⚠ No hay tokens suficientes en: {', '.join(proyectos_sin_tokens)}. "
                              "Baja la cantidad, pulsa «Máx» o elige otra oferta."))

        suma_porcentajes = 100 if (ids_validos and abs(pendiente) <= tolerancia) else (
            round(importe_repartido / importe_total_p4 * 100, 1) if importe_total_p4 else 0.0)

        st.markdown("")
        st.markdown("---")
        st.markdown("")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso4_back"):
                st.session_state.paso_actual = 3
                st.rerun()
        
        with col3:
            if len(proyectos_seleccionados) > 0 and suma_porcentajes == 100 and not proyectos_sin_tokens:
                if st.button("Generar cartera >", use_container_width=True, key="btn_paso4_next"):
                    # Si queda una diferencia mínima por redondeo, el importe pasa a ser
                    # exactamente lo repartido para que los % sumen 100.
                    if abs(pendiente) > 0.01 and importe_repartido > 0:
                        st.session_state.datos_cliente['capital_ajustado'] = importe_repartido
                        for pid, o, tokens, importe, _rent in filas_calc:
                            st.session_state.cartera_selecciones[pid]['porcentaje'] = importe / importe_repartido * 100
                    st.session_state.datos_cliente['cartera'] = {
                        'proyectos': proyectos_seleccionados,
                        'distribuciones': st.session_state.cartera_selecciones
                    }
                    st.session_state.paso_actual = 5
                    st.rerun()
            else:
                st.button("Generar cartera >", use_container_width=True, disabled=True)
    else:
        st.error("No se cargaron proyectos")


# ========== PASO 5: RESUMEN Y PDF ==========
elif st.session_state.paso_actual == 5:
    import altair as alt
    
    st.markdown("## Paso 5: Tu cartera está lista")
    st.markdown("")
    
    datos = st.session_state.datos_cliente
    cartera = datos.get('cartera', {})
    proyectos_cartera = cartera.get('proyectos', [])
    distribuciones = cartera.get('distribuciones', {})
    precios_compra = st.session_state.precios_compra
    df_proy = st.session_state.df_proyectos
    
    if len(proyectos_cartera) > 0:
        estatus = datos.get('estatus') or 'Reentel'
        divisa_cliente = (datos.get('divisa') or 'EUR').upper()
        simbolo = '€' if divisa_cliente == 'EUR' else '$'
        otra_divisa = 'USD' if divisa_cliente == 'EUR' else 'EUR'
        otro_simbolo = '$' if divisa_cliente == 'EUR' else '€'
        
        def fmt(importe, s=simbolo):
            return f"{es(importe, 2)} {s}"
        
        def a_numero(valor):
            try:
                return float(str(valor).replace('%', '').replace(',', '.').strip())
            except:
                return 0.0
        
        # ========== 1) INVERSOR ==========
        st.markdown("### Inversor")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Titular:** {datos.get('nombre', 'N/A')}")
            st.write(f"**Email:** {datos.get('email', 'N/A')}")
            st.write(f"**Teléfono:** {datos.get('telefono', 'N/A')}")
            st.write(f"**Estatus elegido:** {estatus}")
        with col2:
            st.write(f"**Capital a invertir:** {capital_mostrado(datos, simbolo)}")
            st.write(f"**Objetivo:** {datos.get('objetivo', 'N/A')}")
        
        st.markdown("---")
        
        # Tarjeta de resumen (se usa en supuestos y en la cartera)
        def tarjeta(titulo, valor, sub):
            valor, sub = html_seguro(valor), html_seguro(sub)
            return f"""
            <div style="border: 1px solid {COLOR_BORDE}; border-radius: 12px; padding: 14px 16px; background: #ffffff; min-height: 105px;">
                <div style="font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.5px;">{titulo}</div>
                <div style="font-size: 26px; font-weight: 800; color: {COLOR_NAVY}; margin: 4px 0;">{valor}</div>
                <div style="font-size: 12px; color: {COLOR_GRIS_CLARO};">{sub}</div>
            </div>
            """
        
        # ========== 2) SUPUESTOS DE MERCADO ==========
        st.markdown("### Supuestos de mercado")
        tipo_cambio = tipo_cambio_actual()
        precio_rnt = precio_rnt_actual()
        staking_rnt = STAKING_RNT
        
        tarjetas_supuestos = [
            ("💱 TIPO DE CAMBIO", f"{es(tipo_cambio, 4)}", "USD por 1 € · referencia BCE"),
            ("🪙 PRECIO DEL RNT", f"{es(precio_rnt, 4)} USDT", "pool RNT/USDT · SushiSwap"),
            ("🔒 STAKING DE RNT", f"{es(staking_rnt, 2)} %", "rendimiento anual"),
        ]
        cols = st.columns(3)
        for col, (titulo, valor, sub) in zip(cols, tarjetas_supuestos):
            col.markdown(tarjeta(titulo, valor, sub), unsafe_allow_html=True)
        
        def convertir(importe, desde, hacia):
            desde = 'USD' if str(desde).upper() in ('USD', 'USDT') else 'EUR'
            hacia = 'USD' if str(hacia).upper() in ('USD', 'USDT') else 'EUR'
            if desde == hacia:
                return importe
            return importe * tipo_cambio if desde == 'EUR' else importe / tipo_cambio
        
        st.markdown("---")
        
        # ========== 3) TU CARTERA DE INVERSIÓN ==========
        st.markdown("### Tu cartera de inversión")
        
        importe_inmuebles = importe_cliente(datos)  # en la divisa del cliente
        
        rnt_estatus = RNT_POR_ESTATUS.get(estatus, 0)
        coste_estatus = convertir(rnt_estatus * precio_rnt, 'USD', divisa_cliente)
        capital_total = importe_inmuebles + coste_estatus
        
        # Columnas de rentabilidad según estatus
        col_anual = f'Rentabilidad_Anualizada_{estatus}'
        col_total = f'Rentabilidad_Total_{estatus}'
        
        # Columna de tipología de dividendo
        try:
            from modules.formateo_datos import _buscar_columna_tipologia
            col_tipologia = _buscar_columna_tipologia(df_proy)
        except Exception:
            col_tipologia = next((c for c in df_proy.columns if 'tipolog' in c.lower()), None)
        
        filas_tabla = []
        filas_graficos = []
        proyectos_pdf = []
        
        # Precio de compra de cada proyecto, convertido a la divisa del propio
        # proyecto: es lo que necesita el cálculo de rentabilidad ajustada.
        def precio_compra_en_divisa_proyecto(pid, row):
            info = precios_compra.get(pid, {})
            precio = a_numero(info.get('precio', row.get('Precio Emisión', 0)))
            return convertir(precio, info.get('divisa', divisa_proyecto(row)), divisa_proyecto(row))
        
        def rent_proyecto(pid, est):
            fila = df_proy[df_proy['ID'] == pid]
            if len(fila) == 0:
                return None
            row = fila.iloc[0]
            return rentabilidad_ajustada(row, est, precio_compra_en_divisa_proyecto(pid, row))
        
        def media_cartera(est, campo):
            """Media de la cartera ponderada por el % invertido en cada proyecto."""
            total = 0.0
            for proyecto in proyectos_cartera:
                r = rent_proyecto(proyecto['id'], est)
                if r is None:
                    continue
                peso = distribuciones.get(proyecto['id'], {}).get('porcentaje', 0)
                total += (r[campo] or 0.0) * peso / 100
            return total
        rentabilidad_media = 0.0
        
        for proyecto in proyectos_cartera:
            proyecto_id = proyecto['id']
            fila = df_proy[df_proy['ID'] == proyecto_id]
            if len(fila) == 0:
                continue
            row = fila.iloc[0]
            
            peso = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            
            info_precio = precios_compra.get(proyecto_id, {})
            precio = a_numero(info_precio.get('precio', row.get('Precio Emisión', 0)))
            divisa_precio = info_precio.get('divisa', 'EUR')
            tipo_precio = info_precio.get('tipo', 'Emisión')
            precio_conv = convertir(precio, divisa_precio, divisa_cliente)
            
            r_est = rent_proyecto(proyecto_id, estatus)
            r_rnt = rent_proyecto(proyecto_id, 'Reentel')
            rent_anual = r_est['anual'] or 0.0
            rent_total = r_est['total']
            rentabilidad_media += rent_anual * peso / 100
            
            tipologia = str(row.get(col_tipologia, '') or '').strip() if col_tipologia else ''
            
            filas_tabla.append({
                'Proyecto': proyecto['nombre'],
                'Ubicación': row.get('Ubicación', ''),
                'Precio de compra': f"{fmt(precio_conv)} ({tipo_precio})",
                'Tipo de dividendo': tipologia or '-',
                'Tokens': round(_num(st.session_state.tokens_compra.get(proyecto_id), 0.0), 2),
                'Rentabilidad anualizada': rent_anual,
                'Rentabilidad total': rent_total,
                '% cartera': peso,
            })
            
            proyectos_pdf.append({
                'id': str(proyecto_id),
                'nombre': proyecto['nombre'],
                'ubicacion': str(row.get('Ubicación', '') or ''),
                'estado': str(row.get('ESTADO', '') or ''),
                'tipodiv': tipologia or '-',
                'precio': f"{fmt(precio_conv)} ({tipo_precio})",
                'tipo_precio': tipo_precio,
                'pct': peso,
                'importe': importe_inmuebles * peso / 100,
                'tokens': _num(st.session_state.tokens_compra.get(proyecto_id), 0.0),
                'rent_anu_rnt': r_rnt['anual'] or 0.0,
                'rent_tot_rnt': r_rnt['total'],
                'rent_anu_est': rent_anual,
                'rent_tot_est': rent_total,
                'fecha_inicio': str(row.get('Fecha Inicio Estimada', '') or ''),
                'fecha_fin': str(row.get('Fecha Fin Estimada', '') or ''),
            })
            
            filas_graficos.append({
                'ubicacion': str(row.get('Ubicación', '') or 'Sin dato'),
                'tipologia': tipologia or 'Sin dato',
                'divisa': str(row.get('Divisa', '') or 'Sin dato'),
                'peso': peso,
            })
        
        # ----- Tarjetas resumen -----
        tarjetas = [
            ("🏠 INMUEBLES", f"{len(filas_tabla)}", "proyectos en cartera"),
            ("💶 EN INMUEBLES", fmt(importe_inmuebles),
             fmt(convertir(importe_inmuebles, divisa_cliente, otra_divisa), otro_simbolo)),
            ("⭐ COSTE DEL ESTATUS", fmt(coste_estatus), f"{es(rnt_estatus, 0)} RNT · {estatus}"),
            ("💰 CAPITAL TOTAL", fmt(capital_total), "inmuebles + estatus"),
            ("📈 RENT. ANUALIZADA", f"{es(rentabilidad_media, 2)} %", f"media ponderada · {estatus}"),
        ]
        cols = st.columns(5)
        for col, (titulo, valor, sub) in zip(cols, tarjetas):
            col.markdown(tarjeta(titulo, valor, sub), unsafe_allow_html=True)
        
        st.caption("Las rentabilidades se calculan con el precio de compra de cada proyecto y los meses de renta que le quedan, y se ponderan por el % de la cartera invertido en cada uno.")
        st.markdown("")
        
        # ----- Tabla de proyectos -----
        if filas_tabla:
            st.dataframe(
                pd.DataFrame(filas_tabla),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Rentabilidad anualizada': st.column_config.NumberColumn(format='%.2f%%'),
                    'Rentabilidad total': st.column_config.NumberColumn(format='%.2f%%'),
                    '% cartera': st.column_config.NumberColumn(format='%.1f%%'),
                    'Tokens': st.column_config.NumberColumn(format='%.2f'),
                }
            )
        
        # ----- Gráficos -----
        if filas_graficos:
            df_graf = pd.DataFrame(filas_graficos)
            colores = PALETA_GRAFICOS
            
            def donut(campo, titulo):
                datos_g = df_graf.groupby(campo, as_index=False)['peso'].sum()
                datos_g = datos_g[datos_g['peso'] > 0]
                total = datos_g['peso'].sum()
                datos_g['pct'] = datos_g['peso'] / total if total else 0
                datos_g = datos_g.rename(columns={campo: 'categoria'})
                
                base = alt.Chart(datos_g).encode(
                    theta=alt.Theta('peso:Q', stack=True),
                    color=alt.Color('categoria:N', scale=alt.Scale(range=colores),
                                    legend=alt.Legend(orient='bottom', title=None)),
                    tooltip=[alt.Tooltip('categoria:N', title=titulo),
                             alt.Tooltip('pct:Q', format='.0%', title='Peso')]
                )
                arco = base.mark_arc(innerRadius=55, outerRadius=95)
                texto = base.mark_text(radius=112, size=11).encode(text=alt.Text('pct:Q', format='.0%'))
                return (arco + texto).properties(title=titulo, height=290)
            
            st.markdown("")
            g1, g2, g3 = st.columns(3)
            g1.altair_chart(donut('ubicacion', 'Distribución geográfica'), use_container_width=True)
            g2.altair_chart(donut('tipologia', 'Tipología de dividendo'), use_container_width=True)
            g3.altair_chart(donut('divisa', 'Divisa del inmueble'), use_container_width=True)
            
            # ----- Mapa de distribución geográfica -----
            import unicodedata
            def _norm(t):
                return unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode().lower().strip()
            
            reparto_pais = df_graf.groupby('ubicacion', as_index=False)['peso'].sum()
            reparto_pais = reparto_pais[reparto_pais['peso'] > 0]
            total_peso = reparto_pais['peso'].sum()
            reparto_pais['pct'] = reparto_pais['peso'] / total_peso * 100 if total_peso else 0
            reparto_pais['id'] = reparto_pais['ubicacion'].map(lambda u: CODIGOS_PAIS.get(_norm(u)))
            en_mapa = reparto_pais.dropna(subset=['id']).astype({'id': int})
            
            if len(en_mapa) > 0:
                paises = alt.topo_feature(
                    'https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json', 'countries')
                
                fondo = alt.Chart(paises).mark_geoshape(
                    fill=COLOR_BORDE, stroke='#ffffff', strokeWidth=0.5
                ).transform_filter('datum.id != 10')   # sin la Antártida
                
                invertidos = alt.Chart(paises).mark_geoshape(
                    stroke='#ffffff', strokeWidth=0.5
                ).transform_lookup(
                    lookup='id',
                    from_=alt.LookupData(en_mapa, 'id', ['ubicacion', 'pct'])
                ).transform_filter(
                    'isValid(datum.pct)'
                ).encode(
                    color=alt.Color('pct:Q', scale=alt.Scale(range=['#fcd287', '#f5a11f']), legend=None),
                    tooltip=[alt.Tooltip('ubicacion:N', title='País'),
                             alt.Tooltip('pct:Q', format='.1f', title='% de la inversión')]
                )
                
                mapa = (fondo + invertidos).project('equalEarth').properties(
                    title='Distribución geográfica de la inversión', height=420
                )
                st.altair_chart(mapa, use_container_width=True)
            
            leyenda = " · ".join(
                f"<span style='color:{COLOR_AMBAR};'>■</span> {r.ubicacion} — {es(r.pct, 1)}%"
                for r in reparto_pais.sort_values('pct').itertuples()
            )
            st.markdown(f"<div style='font-size:13px; color:{COLOR_GRIS};'>{leyenda}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== COMPARATIVA POR ESTATUS (36 MESES) ==========
        st.markdown("### Comparativa por estatus")
        
        MESES_COMPARATIVA = 36
        
        def rentabilidad_media_estatus(est):
            """Rentabilidad anualizada media de la cartera para ese estatus, al precio de compra."""
            return media_cartera(est, 'anual')
        
        filas_comparativa = []
        comparativa_pdf = []
        for est in ['Reentel', 'ReentelPro', 'SuperReentel']:
            rent_est = rentabilidad_media_estatus(est) / 100
            capital_final = CalculadoraCartera(est).calcular_proyeccion(importe_inmuebles, rent_est, MESES_COMPARATIVA)
            ganancia_inmuebles = capital_final - importe_inmuebles
            
            rnt_est = RNT_POR_ESTATUS.get(est, 0)
            coste_est = convertir(rnt_est * precio_rnt, 'USD', divisa_cliente)
            # Rendimiento del staking de los RNT del estatus durante el mismo plazo
            ganancia_staking = coste_est * (staking_rnt / 100) * (MESES_COMPARATIVA / 12)
            
            ganancia = ganancia_inmuebles + ganancia_staking
            capital_total_est = importe_inmuebles + coste_est
            
            comparativa_pdf.append({
                'estatus': est,
                'rent_anual': rent_est * 100,
                'ganancia': ganancia,
                'rent_cartera': (ganancia / importe_inmuebles * 100) if importe_inmuebles else 0,
                'rent_total': (ganancia / capital_total_est * 100) if capital_total_est else 0,
                'coste': coste_est,
            })
            filas_comparativa.append({
                'Estatus': est,
                f'Ganancia a {MESES_COMPARATIVA} meses': fmt(ganancia),
                'Rent. sobre la cartera': (ganancia / importe_inmuebles * 100) if importe_inmuebles else 0,
                'Rent. sobre el capital total': (ganancia / capital_total_est * 100) if capital_total_est else 0,
                'Coste del estatus': fmt(coste_est),
            })
        
        rent_anual_media_pdf = {est: media_cartera(est, 'anual') for est in {'Reentel', estatus}}
        rent_total_media_pdf = {est: media_cartera(est, 'total') for est in {'Reentel', estatus}}
        
        escenarios_pdf = []
        for meses in [6, 12, 24, 36]:
            g_rnt = CalculadoraCartera('Reentel').calcular_proyeccion(
                importe_inmuebles, rent_anual_media_pdf['Reentel'] / 100, meses) - importe_inmuebles
            g_est = CalculadoraCartera(estatus).calcular_proyeccion(
                importe_inmuebles, rent_anual_media_pdf[estatus] / 100, meses) - importe_inmuebles
            g_est_staking = g_est + coste_estatus * (staking_rnt / 100) * (meses / 12)
            escenarios_pdf.append({
                'meses': meses,
                'g_rnt': g_rnt,
                'g_est': g_est,
                'g_est_staking': g_est_staking,
                'rent_rnt': (g_rnt / importe_inmuebles * 100) if importe_inmuebles else 0,
                'rent_est': (g_est_staking / capital_total * 100) if capital_total else 0,
            })
        
        st.dataframe(
            pd.DataFrame(filas_comparativa),
            use_container_width=True,
            hide_index=True,
            column_config={
                'Rent. sobre la cartera': st.column_config.NumberColumn(format='%.2f %%'),
                'Rent. sobre el capital total': st.column_config.NumberColumn(format='%.2f %%'),
            }
        )
        
        st.markdown("---")
        
        # ========== DESCARGAR PDF ==========
        st.markdown("### Descarga tu cartera")
        
        repartos_pdf = {}
        if filas_graficos:
            for campo, titulo in (('ubicacion', 'Distribución geográfica'),
                                  ('tipologia', 'Tipología de dividendo'),
                                  ('divisa', 'Divisa del inmueble')):
                serie = df_graf.groupby(campo)['peso'].sum()
                total = serie.sum()
                repartos_pdf[titulo] = (serie / total * 100).to_dict() if total else {}
        
        resumen_pdf = {
            'divisa': divisa_cliente,
            'estatus': estatus,
            'tipo_cambio': tipo_cambio,
            'precio_rnt': precio_rnt,
            'staking': staking_rnt,
            'rnt_estatus': rnt_estatus,
            'n_inmuebles': len(filas_tabla),
            'importe_inmuebles': importe_inmuebles,
            'coste_estatus': coste_estatus,
            'capital_total': capital_total,
            'rentabilidad_media': rentabilidad_media,
            'titular': datos.get('nombre'),
            'proyectos': proyectos_pdf,
            'escenarios': escenarios_pdf,
            'rent_anual_media': rent_anual_media_pdf,
            'rent_total_media': rent_total_media_pdf,
            'repartos': repartos_pdf,
            'comparativa': comparativa_pdf,
            'meses': MESES_COMPARATIVA,
        }
        
        # Guardar el lead con la cartera simulada (una sola vez por cartera)
        cartera_txt = "; ".join(
            f"{f['Proyecto']} ({es(f['% cartera'], 1)}% · {f['Precio de compra']})" for f in filas_tabla)
        firma_cartera = f"{st.session_state.get('lead_id', '')}|{estatus}|{cartera_txt}"
        if st.session_state.get('lead_cartera_guardada') != firma_cartera:
            if 'lead_id' not in st.session_state:
                st.session_state.lead_id = uuid.uuid4().hex[:10]
            leads.guardar(st.session_state.lead_id, "Cartera generada", datos,
                          cartera=cartera_txt, importe=fmt(importe_inmuebles))
            st.session_state.lead_cartera_guardada = firma_cartera
        
        datos_pdf = dict(st.session_state.datos_cliente)
        if datos_pdf.get('capital_ajustado'):
            datos_pdf['capital'] = capital_mostrado(datos_pdf, simbolo)
        pdf_buffer = generar_pdf_cartera(
            datos_pdf,
            proyectos_cartera,
            distribuciones,
            st.session_state.df_proyectos,
            precios_compra,
            resumen=resumen_pdf
        )
        
        st.download_button(
            label="📥 Descargar cartera (PDF)",
            data=pdf_buffer,
            file_name=f"Cartera_{datos['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.markdown("")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso5_back"):
                st.session_state.paso_actual = 4
                st.rerun()
        
        with col3:
            if st.button("Crear nueva cartera", use_container_width=True, key="btn_nueva_cartera"):
                st.session_state.paso_actual = 1
                st.session_state.datos_cliente = {}
                st.session_state.cartera_selecciones = {}
                st.session_state.precios_compra = {}
                st.session_state.sel_tablas = {}
                st.session_state.tokens_compra = {}
                st.session_state.oferta_elegida = {}
                st.session_state.tokens_manual = False
                st.session_state.modo_reparto = "Por igual"
                st.session_state.pop('input_importe', None)
                st.rerun()
    else:
        st.error("No hay cartera para mostrar")


# ========== FOOTER ==========
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: {COLOR_GRIS}; font-size: 0.9em; margin-top: 30px;'>
    <p><b>© {datetime.now().year} Reental Wealth Services</b> | Simulador de Cartera</p>
    <p>Para más información: <a href='https://reental.com' target='_blank' style='color: {COLOR_AMBAR_OSCURO};'>www.reental.com</a></p>
    <p style='font-size: 0.85em; margin-top: 15px;'>
        <i>Este simulador es una herramienta educativa. Las proyecciones mostradas son estimaciones basadas en datos históricos 
        y parámetros actuales. La rentabilidad pasada no garantiza resultados futuros.</i>
    </p>
</div>
""", unsafe_allow_html=True)
