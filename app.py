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
from modules.data_loader import cargar_proyectos, cargar_todos_proyectos
from modules.calculo_cartera import rankear_proyectos, CalculadoraCartera
from modules.formateo_datos import preparar_proyectos_para_paso4
from modules.pdf_generator import generar_pdf_cartera

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

# ========== FUNCIONES AUXILIARES OTC ==========
def cargar_ofertas_otc():
    """Carga ofertas OTC del Google Sheets del compañero"""
    try:
        from modules import otc_storage
        ofertas = otc_storage.read_list("Ofertas")
        return ofertas if ofertas else []
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar ofertas OTC: {str(e)}")
        return []

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
        st.warning(f"⚠️ No se pudieron cargar las operaciones P2P: {e}")
        return []

def cargar_todas_ofertas_secundario():
    """Carga TODAS las ofertas del mercado secundario: OTC + P2P"""
    ofertas_otc = cargar_ofertas_otc()
    ofertas_p2p = cargar_ofertas_p2p()
    
    # Combinar ambos canales
    todas_ofertas = (ofertas_otc or []) + (ofertas_p2p or [])
    
    return todas_ofertas

def agrupar_ofertas_por_proyecto(ofertas):
    """Agrupa ofertas OTC por proyecto_id o token_address - SIN filtro de estado"""
    ofertas_por_proyecto = {}
    
    for oferta in ofertas:
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
            "Nombre completo *",
            value=st.session_state.datos_cliente.get('nombre', ''),
            key="input_nombre"
        )
        email = st.text_input(
            "Email *",
            value=st.session_state.datos_cliente.get('email', ''),
            key="input_email"
        )
        divisa = st.selectbox(
            "Divisa *",
            ["EUR", "USD"],
            index=None,
            placeholder="Selecciona una divisa",
            key="select_divisa"
        )
    
    with col2:
        ya_inversor = st.selectbox(
            "¿Eres ya inversor en Reental? *",
            ["No", "Sí"],
            index=None,
            placeholder="Selecciona una opción",
            key="select_inversor"
        )
        capital = st.selectbox(
            "Capital a invertir *",
            ["Menos de 5.000", "Entre 5.000 y 10.000", "Entre 10.000 y 50.000", "Más de 50.000"],
            index=None,
            placeholder="Selecciona tu rango de capital",
            key="select_capital"
        )
    
    st.markdown("")
    st.markdown("---")
    st.markdown("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col3:
        if st.button("Siguiente >", use_container_width=True, key="btn_paso1_next"):
            if nombre and email and divisa is not None and capital is not None and ya_inversor is not None:
                st.session_state.datos_cliente = {
                    'nombre': nombre,
                    'email': email,
                    'divisa': divisa,
                    'ya_inversor': ya_inversor,
                    'capital': capital
                }
                st.session_state.paso_actual = 2
                st.rerun()
            else:
                st.error("Por favor completa todos los campos marcados con *")

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
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
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
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
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
        <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 180px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
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
            💡 ¿Quieres más información sobre qué es el estatus RNT y cómo puede ayudarte a maximizar tu rentabilidad inmobiliaria? Agenda con nuestro equipo de Onboarding <b style="color: #ff8c00;">aquí</b>.
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
            ["Maximizar rentabilidad - quiero invertir en los proyectos con mayor rentabilidad anualizada", "Ingresos pasivos regulares - quiero invertir en proyectos que me den rentas periódicas"],
            index=None,
            placeholder="Selecciona tu objetivo",
            key="select_objetivo"
        )
    
    with col2:
        distribucion = st.selectbox(
            "Distribución de capital *",
            ["Distribuir en partes iguales", "Elegir cuánto invertir en cada uno"],
            index=None,
            placeholder="Selecciona tu estrategia",
            key="select_distribucion"
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
        if objetivo is not None and mercados_seleccionados and distribucion is not None and estatus_seleccionado is not None:
            if st.button("Siguiente >", use_container_width=True, key="btn_paso3_next"):
                st.session_state.datos_cliente['objetivo'] = objetivo
                st.session_state.datos_cliente['mercados'] = mercados_seleccionados
                st.session_state.datos_cliente['distribucion'] = distribucion
                
                # Cargar TODOS los proyectos (incluidos cerrados con OTC)
                try:
                    st.session_state.df_proyectos = cargar_todos_proyectos()
                    st.session_state.paso_actual = 4
                    st.rerun()
                except Exception as e:
                    st.error(f"Error cargando proyectos: {e}")
        else:
            st.button("Siguiente >", use_container_width=True, disabled=True, key="btn_paso3_next_disabled")

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
        distribucion_type = st.session_state.datos_cliente.get('distribucion', 'Distribuir en partes iguales')
        
        criterios = {
            'ubicaciones': mercados_seleccionados,
            'duracion': 'Largo plazo' if 'maximizar' in objetivo.lower() else 'Corto plazo'
        }
        
        # Cargar ofertas OTC + P2P
        ofertas_otc_list = cargar_todas_ofertas_secundario()
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
        
        # IDs marcados en cualquiera de las tablas
        ids_seleccionados = []
        
        # ========== TABLAS PRIMERA EMISIÓN ==========
        st.markdown("### 📊 Proyectos disponibles en primera emisión (Reental)")
        
        if len(df_matchean) > 0:
            df_display_matchean = preparar_proyectos_para_paso4(df_matchean, estatus)
            ids_seleccionados += tabla_seleccionable(df_display_matchean, "tabla_primera_emision")
        
        if len(df_no_matchean) > 0:
            st.markdown("#### Proyectos adicionales que podrían interesarte")
            df_display_no_matchean = preparar_proyectos_para_paso4(df_no_matchean, estatus)
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
        
        if len(df_con_otc) > 0:
            st.success(f"✅ {len(df_con_otc)} proyecto(s) con ofertas OTC/P2P disponibles")
            
            try:
                df_con_otc = rankear_proyectos(df_con_otc, criterios, estatus)
            except:
                pass
            
            # Precio OTC más bajo por proyecto
            precio_min_por_id = {}
            for idx, row in df_con_otc.iterrows():
                clave = str(row.get('ID', '')).lower() or str(row.get('Token Address', '')).lower()
                precios = []
                for oferta in ofertas_por_proy.get(clave, []):
                    try:
                        precio = float(oferta.get('precio_venta', 0))
                        if precio > 0:
                            precios.append(precio)
                    except:
                        pass
                precio_min_por_id[row['ID']] = min(precios) if precios else row.get('Precio Emisión', 0)
            
            df_display_otc = preparar_proyectos_para_paso4(df_con_otc, estatus)
            df_display_otc['Precio OTC Más Bajo'] = df_display_otc['ID'].map(
                lambda pid: f"€{float(precio_min_por_id.get(pid, 0) or 0):.2f}"
            )
            ids_seleccionados += tabla_seleccionable(df_display_otc, "tabla_otc")
        elif ofertas_por_proy:
            st.info("📭 Hay ofertas OTC, pero ninguna coincide con un proyecto del Master")
        else:
            st.info("📭 No hay ofertas OTC disponibles en este momento")
        
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
        aviso_distribucion = st.empty()  # mensaje de estado (se rellena al final)
        
        proyectos_seleccionados = []
        suma_porcentajes = 0
        reparto_igual = distribucion_type == 'Distribuir en partes iguales'
        ids_validos = [pid for pid in ids_seleccionados if pid in filas_por_id]
        porcentaje_igual = 100 / len(ids_validos) if ids_validos else 0
        
        if ids_validos:
            col_h1, col_h2 = st.columns(2)
            col_h1.markdown("**Precio de compra**")
            col_h2.markdown("**Distribución de capital (%)**")
        
        for proyecto_id in ids_validos:
            row = filas_por_id[proyecto_id]
            
            proyecto_nombre = row['Nombre del proyecto']
            token_address = row.get('Token Address', '')
            es_primera_emision = str(row.get('ESTADO', '')).upper() == 'FINANCIÁNDOSE'
            precio_emision = row.get('Precio Emisión', 0)
            
            proyectos_seleccionados.append({
                'id': proyecto_id,
                'nombre': proyecto_nombre,
                'ubicacion': row['Ubicación'],
                'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0),
                'address': token_address,
                'precio_emision': precio_emision
            })
            
            # Opciones de precio
            clave_otc = str(proyecto_id).lower() or str(token_address).lower()
            ofertas_proyecto = ofertas_por_proy.get(clave_otc, [])
            
            # Precio de emisión solo si el proyecto sigue en primera emisión
            opciones_precio = [f"Emisión: {precio_emision:.2f} EUR"] if es_primera_emision else []
            mejores_ofertas = []
            
            for oferta in ofertas_proyecto:
                try:
                    precio = float(oferta.get('precio_venta', 0))
                    divisa = oferta.get('divisa', 'EUR')
                    n_tokens = oferta.get('n_tokens', 0)
                    if precio > 0:
                        label = f"OTC: {precio:.2f} {divisa} · {n_tokens} tokens disponibles"
                        opciones_precio.append(label)
                        mejores_ofertas.append({
                            'label': label,
                            'precio': precio,
                            'divisa': divisa,
                            'n_tokens': n_tokens
                        })
                except:
                    continue
            
            # Seguridad: si no hay ninguna opción válida, usar el precio de emisión
            if not opciones_precio:
                opciones_precio = [f"Emisión: {precio_emision:.2f} EUR"]
            
            # Fila del proyecto: precio (izquierda) y % (derecha) a la misma altura
            st.markdown(f"**{proyecto_nombre}**")
            col_precio, col_pct = st.columns(2)
            
            with col_precio:
                precio_seleccionado = st.selectbox(
                    "Elige precio",
                    opciones_precio,
                    key=f"precio_{proyecto_id}",
                    label_visibility="collapsed"
                )
                
                if "OTC:" in precio_seleccionado:
                    for oferta in mejores_ofertas:
                        if oferta['label'] == precio_seleccionado:
                            st.session_state.precios_compra[proyecto_id] = {
                                'precio': oferta['precio'],
                                'divisa': oferta['divisa'],
                                'tipo': 'OTC'
                            }
                            break
                else:
                    st.session_state.precios_compra[proyecto_id] = {
                        'precio': precio_emision,
                        'divisa': 'EUR',
                        'tipo': 'Emisión'
                    }
            
            with col_pct:
                if reparto_igual:
                    porcentaje = porcentaje_igual
                    st.text_input(
                        f"pct_{proyecto_id}",
                        value=f"{porcentaje:.1f}%",
                        disabled=True,
                        label_visibility="collapsed"
                    )
                else:
                    porcentaje = st.number_input(
                        f"{proyecto_nombre} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=round(float(st.session_state.cartera_selecciones[proyecto_id].get('porcentaje', 0.0)), 1),
                        step=0.1,
                        key=f"input_{proyecto_id}",
                        label_visibility="collapsed"
                    )
                st.session_state.cartera_selecciones[proyecto_id]['porcentaje'] = porcentaje
                suma_porcentajes += porcentaje
        
        # Mensaje de estado justo debajo de "Construye tu cartera"
        if not ids_validos:
            aviso_distribucion.info("Marca en las tablas de arriba los proyectos que quieras incluir")
        elif reparto_igual:
            suma_porcentajes = 100
            aviso_distribucion.info(f"Se distribuirá {porcentaje_igual:.1f}% en cada proyecto")
        else:
            suma_porcentajes = round(suma_porcentajes, 1)
            if suma_porcentajes == 100:
                aviso_distribucion.success(f"✓ Total: {suma_porcentajes}%")
            elif suma_porcentajes > 0:
                aviso_distribucion.warning(f"⚠ Total: {suma_porcentajes}% (Falta {100 - suma_porcentajes:.1f}%)")
            else:
                aviso_distribucion.info("Asigna porcentajes a los proyectos")
        
        st.markdown("")
        st.markdown("---")
        st.markdown("")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso4_back"):
                st.session_state.paso_actual = 3
                st.rerun()
        
        with col3:
            if len(proyectos_seleccionados) > 0 and suma_porcentajes == 100:
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
            return f"{importe:,.2f} {s}"
        
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
            st.write(f"**Estatus elegido:** {estatus}")
        with col2:
            st.write(f"**Capital a invertir:** {datos.get('capital', 'N/A')} {divisa_cliente}")
            st.write(f"**Objetivo:** {datos.get('objetivo', 'N/A')}")
            st.write(f"**Distribución de la cartera:** {datos.get('distribucion', 'N/A')}")
        
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
            ("💱 TIPO DE CAMBIO", f"{tipo_cambio:.4f}", "USD por 1 € · referencia BCE"),
            ("🪙 PRECIO DEL RNT", f"{precio_rnt:.4f} USDT", "pool RNT/USDT · SushiSwap"),
            ("🔒 STAKING DE RNT", f"{staking_rnt:.2f} %", "rendimiento anual"),
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
        
        capital_map = {
            "Menos de 5.000": 2500,
            "Entre 5.000 y 10.000": 7500,
            "Entre 10.000 y 50.000": 30000,
            "Más de 50.000": 100000
        }
        importe_inmuebles = capital_map.get(datos.get('capital'), 30000)  # en la divisa del cliente
        
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
            
            rent_anual = a_numero(row.get(col_anual, 0))
            rent_total = a_numero(row.get(col_total, 0))
            rentabilidad_media += rent_anual * peso / 100
            
            tipologia = str(row.get(col_tipologia, '') or '').strip() if col_tipologia else ''
            
            filas_tabla.append({
                'Proyecto': proyecto['nombre'],
                'Ubicación': row.get('Ubicación', ''),
                'Precio de compra': f"{fmt(precio_conv)} ({tipo_precio})",
                'Tipo de dividendo': tipologia or '-',
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
                'rent_anu_rnt': a_numero(row.get('Rentabilidad_Anualizada_Reentel', 0)),
                'rent_tot_rnt': a_numero(row.get('Rentabilidad_Total_Reentel', 0)),
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
            ("⭐ COSTE DEL ESTATUS", fmt(coste_estatus), f"{rnt_estatus:,} RNT · {estatus}"),
            ("💰 CAPITAL TOTAL", fmt(capital_total), "inmuebles + estatus"),
            ("📈 RENT. ANUALIZADA", f"{rentabilidad_media:.2f} %", f"media ponderada · {estatus}"),
        ]
        cols = st.columns(5)
        for col, (titulo, valor, sub) in zip(cols, tarjetas):
            col.markdown(tarjeta(titulo, valor, sub), unsafe_allow_html=True)
        
        st.caption("Las rentabilidades se ponderan por el % de la cartera invertido en cada proyecto.")
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
                f"<span style='color:#e08900;'>■</span> {r.ubicacion} — {r.pct:.1f}%"
                for r in reparto_pais.sort_values('pct').itertuples()
            )
            st.markdown(f"<div style='font-size:13px; color:#666666;'>{leyenda}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== COMPARATIVA POR ESTATUS (36 MESES) ==========
        st.markdown("### Comparativa por estatus")
        
        MESES_COMPARATIVA = 36
        
        def rentabilidad_media_estatus(est):
            """Rentabilidad anualizada media de la cartera con las columnas de ese estatus."""
            total = 0.0
            for proyecto in proyectos_cartera:
                fila = df_proy[df_proy['ID'] == proyecto['id']]
                if len(fila) == 0:
                    continue
                peso = distribuciones.get(proyecto['id'], {}).get('porcentaje', 0)
                total += a_numero(fila.iloc[0].get(f'Rentabilidad_Anualizada_{est}', 0)) * peso / 100
            return total
        
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
        
        def media_columna(prefijo, est):
            total = 0.0
            for proyecto in proyectos_cartera:
                fila = df_proy[df_proy['ID'] == proyecto['id']]
                if len(fila) == 0:
                    continue
                peso = distribuciones.get(proyecto['id'], {}).get('porcentaje', 0)
                total += a_numero(fila.iloc[0].get(f'{prefijo}_{est}', 0)) * peso / 100
            return total
        
        rent_anual_media_pdf = {est: media_columna('Rentabilidad_Anualizada', est) for est in {'Reentel', estatus}}
        rent_total_media_pdf = {est: media_columna('Rentabilidad_Total', est) for est in {'Reentel', estatus}}
        
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
        
        pdf_buffer = generar_pdf_cartera(
            st.session_state.datos_cliente,
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
                st.rerun()
    else:
        st.error("No hay cartera para mostrar")


# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666666; font-size: 0.9em; margin-top: 30px;'>
    <p><b>© 2024 Reental Wealth Services</b> | Simulador de Cartera v3.0</p>
    <p>Para más información: <a href='https://reental.com' target='_blank'>www.reental.com</a></p>
    <p style='font-size: 0.85em; margin-top: 15px;'>
        <i>Este simulador es una herramienta educativa. Las proyecciones mostradas son estimaciones basadas en datos históricos 
        y parámetros actuales. La rentabilidad pasada no garantiza resultados futuros. 
        Consulte con un asesor financiero independiente antes de invertir.</i>
    </p>
</div>
""", unsafe_allow_html=True)
