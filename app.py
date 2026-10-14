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
st.markdown("""
<style>
    /* Colores Reental */
    :root {
        --color-naranja: #ff8c00;
        --color-gris: #666666;
        --color-blanco: #f9f9f9;
    }
    
    /* Main */
    .main {
        background-color: #ffffff;
    }
    
    /* Headers */
    h1 {
        color: #ff8c00;
        font-size: 2.5em;
        margin-bottom: 10px;
        font-weight: 700;
    }
    
    h2 {
        color: #ff8c00;
        font-size: 1.8em;
        margin-top: 20px;
        margin-bottom: 15px;
        font-weight: 700;
        border-bottom: 2px solid #ff8c00;
        padding-bottom: 10px;
    }
    
    h3 {
        color: #666666;
        font-size: 1.3em;
        margin-top: 15px;
        margin-bottom: 10px;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #ff8c00;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 1.1em;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #e67e00;
        transform: scale(1.02);
    }
    
    .stButton > button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }
    
    /* Info Boxes */
    .stInfo {
        background-color: #e8f4f8;
        border-left: 4px solid #ff8c00;
        padding: 12px;
    }
    
    .stSuccess {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    .stWarning {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    
    .stError {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    
    /* Tables */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
    }
    
    .dataframe th {
        background-color: #ff8c00;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
    }
    
    .dataframe td {
        padding: 10px 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .dataframe tr:hover {
        background-color: #f5f5f5;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #f9f9f9;
    }
    
    /* Progress bar color */
    .stProgress > div > div > div {
        background-color: #ff8c00;
    }
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

def agrupar_ofertas_por_proyecto(ofertas):
    """Agrupa por proyecto_id o token_address las ofertas ACTIVAS
    (mismo criterio que otc_inventario.catalogo de la herramienta OTC)."""
    ofertas_por_proyecto = {}

    for oferta in ofertas:
        # Solo ofertas vivas: las eliminadas, vendidas, etc. no son comprables
        if str(oferta.get('estado', '')).strip().lower() != 'activa':
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
    'Nombre del proyecto': st.column_config.Column(width="large"),
    'Tipología de dividendo': st.column_config.Column(width="medium"),
    'ESTADO': st.column_config.Column(width="small"),
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
    """Texto del capital para la pantalla y el PDF."""
    if datos.get('capital_ajustado'):
        return f"{es(datos['capital_ajustado'], 0)} {simbolo} (ajustado)"
    return f"{datos.get('capital', 'N/A')} ({'EUR' if simbolo == '€' else 'USD'})"


def ajustar_capital(importe_repartido):
    """Fija el capital en lo que suman los tokens elegidos, para que el reparto sea
    exactamente el 100 %. Los tokens de cada proyecto no cambian."""
    if importe_repartido and importe_repartido > 0:
        st.session_state.datos_cliente['capital_ajustado'] = importe_repartido


def es(valor, decimales=2):
    """Número en formato español: 257.109,50 (punto para miles, coma para decimales)."""
    try:
        texto = f"{float(valor):,.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)
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
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<h1 style='text-align: center;'>🏠 SIMULADOR DE CARTERA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666666;'>Inversión Inmobiliaria Reental</h3>", unsafe_allow_html=True)

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
        st.caption("Para simular tu cartera usaremos el punto medio del rango elegido "
                   "(por ejemplo, 30.000 para «Entre 10.000 y 50.000», y 100.000 si eliges «Más de 50.000»).")
    
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
            bg_color = "#f0f9f3"
            border_color = "#16a34a"
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = "#cccccc"
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: #16a34a; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                🏛️ SUPERREENTEL
            </div>
            <div style="color: #000000; font-size: 15px; line-height: 1.6; flex-grow: 1;">
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
            bg_color = "#faf5ff"
            border_color = "#a855f7"
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = "#cccccc"
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: #a855f7; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                🏢 REENTELPRO
            </div>
            <div style="color: #000000; font-size: 15px; line-height: 1.6; flex-grow: 1;">
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
            bg_color = "#feedcf"
            border_color = "#ca820e"
            border_width = "3px"
        else:
            bg_color = "#ffffff"
            border_color = "#cccccc"
            border_width = "2px"
        
        st.markdown(f"""
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="color: #ca820e; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                🏠 REENTEL
            </div>
            <div style="color: #000000; font-size: 15px; line-height: 1.6; flex-grow: 1;">
                por ahora no quiero estatus.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Seleccionar Reentel", key="btn_reen", use_container_width=True):
            st.session_state.datos_cliente['estatus'] = 'Reentel'
            st.rerun()
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    # ========== BOTÓN "¿QUIERES MÁS INFO?" ==========
    st.markdown("""
    <a href="https://api.leadconnectorhq.com/widget/booking/kAzM5NH9hFxtc88sTQKy" target="_blank" style="text-decoration: none; color: inherit;">
        <div style="background-color: #fff3e0; border: 2px solid #ff8c00; color: #000000; border-radius: 8px; padding: 15px; font-size: 15px; cursor: pointer; text-align: center;">
            💡 ¿Quieres más información sobre <b> qué es el estatus RNT</b> y cómo puede ayudarte a <b>maximizar tu rentabilidad inmobiliaria</b>? Agenda con nuestro equipo de Onboarding <b style="color: #ff8c00;">aquí</b>.
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
        
        proyectos_seleccionados = []
        reparto_igual = True   # la tabla arranca repartida por igual hasta que se toque a mano
        divisa_cliente_p4 = (st.session_state.datos_cliente.get('divisa') or 'EUR').upper()
        importe_total_p4 = importe_cliente(st.session_state.datos_cliente)
        simbolo_cliente_p4 = '€' if divisa_cliente_p4 == 'EUR' else '$'
        ids_validos = [pid for pid in ids_seleccionados if pid in filas_por_id]
        tokens_compra = st.session_state.tokens_compra
        
        def _simbolo(div):
            return '$' if str(div).upper() in ('USD', 'USDT', '$') else '€'
        
        def _etiqueta(o):
            texto = f"{es(o['precio'], 2)} {_simbolo(o['divisa'])}"
            if _simbolo(o['divisa']) != simbolo_cliente_p4:
                texto += f" (aprox. {es(convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4), 2)} {simbolo_cliente_p4})"
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
        
        if not isinstance(st.session_state.get('oferta_elegida'), dict):
            st.session_state.oferta_elegida = {}
        
        def _oferta(pid):
            """La oferta elegida del proyecto (la más barata si no se ha cambiado)."""
            opciones = opciones_por_id[pid]
            try:
                i = int(st.session_state.oferta_elegida.get(pid, 0))
            except (TypeError, ValueError):
                i = 0
            return opciones[i] if 0 <= i < len(opciones) else opciones[0]
        
        def _tokens_por_importe(pid, importe):
            o = _oferta(pid)
            return convertir_divisa(importe, divisa_cliente_p4, o['divisa']) / o['precio'] if o['precio'] else 0.0
        
        def _repartir_por_igual():
            if ids_validos:
                parte = importe_total_p4 / len(ids_validos)
                for pid in ids_validos:
                    st.session_state.tokens_compra[pid] = round(_tokens_por_importe(pid, parte), 4)
            st.session_state.tokens_manual = False
            st.session_state.version_editor += 1
        
        # Reparto inicial: en partes iguales mientras no se toque a mano
        if ids_validos and reparto_igual and not st.session_state.tokens_manual:
            parte = importe_total_p4 / len(ids_validos)
            for pid in ids_validos:
                tokens_compra[pid] = round(_tokens_por_importe(pid, parte), 4)
        for pid in ids_validos:
            tokens_compra.setdefault(pid, 0.0)
        
        # ----- Cálculo de importes y % a partir de los tokens -----
        filas_editor, maximos, proyectos_sin_tokens = [], {}, []
        importe_repartido = 0.0
        for pid in ids_validos:
            row = filas_por_id[pid]
            o = _oferta(pid)
            tokens = _num(tokens_compra.get(pid), 0.0)
            importe = convertir_divisa(tokens * o['precio'], o['divisa'], divisa_cliente_p4)
            importe_repartido += importe
            pct = importe / importe_total_p4 * 100 if importe_total_p4 else 0.0
            
            st.session_state.precios_compra[pid] = {'precio': o['precio'], 'divisa': o['divisa'],
                                                    'tipo': o['tipo'], 'n_tokens': o['n_tokens']}
            st.session_state.cartera_selecciones.setdefault(pid, {'seleccionado': True})['porcentaje'] = pct
            proyectos_seleccionados.append({
                'id': pid, 'nombre': row['Nombre del proyecto'], 'ubicacion': row['Ubicación'],
                'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0),
                'address': row.get('Token Address', ''), 'precio_emision': _num(row.get('Precio Emisión', 0)),
            })
            
            disponibles = o['n_tokens']
            if disponibles is not None:
                maximos[pid] = round(disponibles, 4)
            texto_pct = f"{es(pct, 1)}% · {es(importe, 0)} {simbolo_cliente_p4}"
            if disponibles is not None and tokens > disponibles + 0.01:
                proyectos_sin_tokens.append(row['Nombre del proyecto'])
                texto_pct = f"⚠ faltan {es(tokens - disponibles, 2)} tk · {texto_pct}"
            filas_editor.append({
                'Proyecto': row['Nombre del proyecto'],
                'Precio de compra': _etiqueta(o),
                'Tokens disponibles': round(disponibles, 2) if disponibles is not None else None,
                'Máx': disponibles is not None and abs(tokens - disponibles) < 0.005,
                'Tokens a comprar': round(tokens, 2),
                '% de tu cartera': texto_pct,
            })
        
        suma_porcentajes = round(importe_repartido / importe_total_p4 * 100, 1) if importe_total_p4 else 0.0
        
        # ----- Avisos y acciones (encima de la tabla) -----
        if not ids_validos:
            st.info("Marca en las tablas de arriba los proyectos que quieras incluir")
        else:
            st.button("Repartir por igual", key="btn_repartir_igual", on_click=_repartir_por_igual,
                      help="Asigna a cada proyecto el mismo porcentaje de tu capital")
            if proyectos_sin_tokens:
                st.warning(f"⚠ No hay tokens suficientes en: {', '.join(proyectos_sin_tokens)}. "
                           "Baja los tokens, marca «Máx» o elige otra oferta más abajo.")
            if suma_porcentajes == 0:
                st.info("Indica cuántos tokens quieres comprar de cada proyecto.")
            elif suma_porcentajes != 100:
                if suma_porcentajes > 100:
                    st.warning(f"⚠ Has repartido un {es(suma_porcentajes, 1)}% de tu capital: "
                               f"te sobra un {es(suma_porcentajes - 100, 1)}%.")
                else:
                    st.warning(f"⚠ Has repartido un {es(suma_porcentajes, 1)}% de tu capital: "
                               f"te queda un {es(100 - suma_porcentajes, 1)}% por asignar.")
                st.button(
                    f"Ajustar mi capital a {es(importe_repartido, 0)} {simbolo_cliente_p4} "
                    f"para invertir exactamente lo que has elegido",
                    key="btn_ajustar_capital", on_click=ajustar_capital, args=(importe_repartido,),
                )
                st.caption(f"Tu capital pasará de {es(importe_total_p4, 0)} {simbolo_cliente_p4} "
                           f"a {es(importe_repartido, 0)} {simbolo_cliente_p4}.")
        
        # ----- Tabla -----
        if ids_validos:
            clave_editor = f"editor_cartera_{st.session_state.version_editor}"
            
            def _aplicar_edicion(clave, ids, maximos):
                cambios = (st.session_state.get(clave) or {}).get("edited_rows", {})
                for fila, cols in cambios.items():
                    pid = ids[int(fila)]
                    if "Máx" in cols:
                        if cols["Máx"] and maximos.get(pid) is not None:
                            st.session_state.tokens_compra[pid] = maximos[pid]
                        elif not cols["Máx"]:
                            st.session_state.tokens_compra[pid] = 0.0
                    if "Tokens a comprar" in cols and cols["Tokens a comprar"] is not None:
                        st.session_state.tokens_compra[pid] = max(0.0, float(cols["Tokens a comprar"]))
                st.session_state.tokens_manual = True
                st.session_state.version_editor += 1
            
            st.data_editor(
                pd.DataFrame(filas_editor),
                key=clave_editor,
                hide_index=True,
                use_container_width=True,
                on_change=_aplicar_edicion,
                args=(clave_editor, list(ids_validos), maximos),
                disabled=['Proyecto', 'Precio de compra', 'Tokens disponibles', '% de tu cartera'],
                column_config={
                    'Proyecto': st.column_config.TextColumn(width="medium"),
                    'Precio de compra': st.column_config.TextColumn(width="medium"),
                    'Tokens disponibles': st.column_config.NumberColumn(format='%.2f', width="small"),
                    'Máx': st.column_config.CheckboxColumn(
                        width="small", help="Comprar todos los tokens disponibles de la oferta"),
                    'Tokens a comprar': st.column_config.NumberColumn(
                        min_value=0.0, step=0.01, format='%.2f', width="small"),
                    '% de tu cartera': st.column_config.TextColumn(width="medium"),
                },
            )
            st.markdown(f"**Total: {es(suma_porcentajes, 1)}% · {es(importe_repartido, 0)} {simbolo_cliente_p4}** "
                        f"de {es(importe_total_p4, 0)} {simbolo_cliente_p4}")
            
            # ----- Cambiar de oferta (solo proyectos con varias opciones) -----
            con_varias = [pid for pid in ids_validos if len(opciones_por_id[pid]) > 1]
            if con_varias:
                def _cambiar_oferta(pid):
                    try:
                        st.session_state.oferta_elegida[pid] = int(st.session_state[f"sel_oferta_{pid}"])
                    except (TypeError, ValueError, KeyError):
                        st.session_state.oferta_elegida[pid] = 0
                    st.session_state.version_editor += 1
                
                c1, c2, _ = st.columns([2, 3, 3])
                pid_cambio = c1.selectbox(
                    "Cambiar oferta de", con_varias,
                    format_func=lambda p: filas_por_id[p]['Nombre del proyecto'], key="sel_proyecto_oferta")
                opciones = opciones_por_id[pid_cambio]
                c2.selectbox(
                    "Oferta", list(range(len(opciones))),
                    index=min(max(0, int(_num(st.session_state.oferta_elegida.get(pid_cambio, 0), 0))),
                              len(opciones) - 1),
                    format_func=lambda i, opciones=opciones: (
                        _etiqueta(opciones[i]) + (f" · {es(opciones[i]['n_tokens'], 2)} tk"
                                                  if opciones[i]['n_tokens'] is not None else "")),
                    key=f"sel_oferta_{pid_cambio}", on_change=_cambiar_oferta, args=(pid_cambio,))
        
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
            return f"""
            <div style="border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 16px; background: #ffffff; min-height: 105px;">
                <div style="font-size: 12px; font-weight: 700; color: #666666; letter-spacing: 0.5px;">{titulo}</div>
                <div style="font-size: 26px; font-weight: 700; color: #1f2937; margin: 4px 0;">{valor}</div>
                <div style="font-size: 12px; color: #9ca3af;">{sub}</div>
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
            colores = ['#f5a623', '#3b82f6', '#16a34a', '#a855f7', '#ef4444', '#14b8a6', '#6b7280']
            
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
                    fill='#eceef1', stroke='#ffffff', strokeWidth=0.5
                ).transform_filter('datum.id != 10')   # sin la Antártida
                
                invertidos = alt.Chart(paises).mark_geoshape(
                    stroke='#ffffff', strokeWidth=0.5
                ).transform_lookup(
                    lookup='id',
                    from_=alt.LookupData(en_mapa, 'id', ['ubicacion', 'pct'])
                ).transform_filter(
                    'isValid(datum.pct)'
                ).encode(
                    color=alt.Color('pct:Q', scale=alt.Scale(range=['#f7c77a', '#e08900']), legend=None),
                    tooltip=[alt.Tooltip('ubicacion:N', title='País'),
                             alt.Tooltip('pct:Q', format='.1f', title='% de la inversión')]
                )
                
                mapa = (fondo + invertidos).project('equalEarth').properties(
                    title='Distribución geográfica de la inversión', height=420
                )
                st.altair_chart(mapa, use_container_width=True)
            
            leyenda = " · ".join(
                f"<span style='color:#e08900;'>■</span> {r.ubicacion} — {es(r.pct, 1)}%"
                for r in reparto_pais.sort_values('pct').itertuples()
            )
            st.markdown(f"<div style='font-size:13px; color:#666666;'>{leyenda}</div>", unsafe_allow_html=True)
        
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
                st.rerun()
    else:
        st.error("No hay cartera para mostrar")


# ========== FOOTER ==========
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666666; font-size: 0.9em; margin-top: 30px;'>
    <p><b>© {datetime.now().year} Reental Wealth Services</b> | Simulador de Cartera</p>
    <p>Para más información: <a href='https://reental.com' target='_blank'>www.reental.com</a></p>
    <p style='font-size: 0.85em; margin-top: 15px;'>
        <i>Este simulador es una herramienta educativa. Las proyecciones mostradas son estimaciones basadas en datos históricos 
        y parámetros actuales. La rentabilidad pasada no garantiza resultados futuros. 
        Consulte con un asesor financiero independiente antes de invertir.</i>
    </p>
</div>
""", unsafe_allow_html=True)
