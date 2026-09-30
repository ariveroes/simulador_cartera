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
    except Exception:
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
        st.markdown("")
        
        proyectos_seleccionados = []
        suma_porcentajes = 0
        
        col_selector, col_distribuir = st.columns([1, 2])
        
        with col_selector:
            st.markdown("**Precio de compra:**")
            
            if not ids_seleccionados:
                st.info("Marca en las tablas de arriba los proyectos que quieras incluir")
            
            for proyecto_id in ids_seleccionados:
                row = filas_por_id.get(proyecto_id)
                if row is None:
                    continue
                
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
                
                # ========== COMBO DE PRECIOS ==========
                st.markdown(f"**{proyecto_nombre}**")
                
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
                        inversor = oferta.get('inversor', 'Desconocido')
                        
                        if precio > 0:
                            label = f"OTC: {precio:.2f} {divisa} ({n_tokens} tokens) - {inversor}"
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
                
                precio_seleccionado = st.selectbox(
                    "Elige precio",
                    opciones_precio,
                    key=f"precio_{proyecto_id}",
                    label_visibility="collapsed"
                )
                
                # Guardar precio
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
                
                st.markdown("")
        
        with col_distribuir:
            st.markdown("**Distribución de capital:**")
            
            if len(proyectos_seleccionados) == 0:
                st.info("Selecciona al menos un proyecto")
            else:
                if distribucion_type == 'Distribuir en partes iguales':
                    porcentaje_por_proyecto = 100 / len(proyectos_seleccionados)
                    st.markdown(f"Se distribuirá **{porcentaje_por_proyecto:.1f}%** en cada proyecto:")
                    
                    for proyecto in proyectos_seleccionados:
                        st.session_state.cartera_selecciones[proyecto['id']]['porcentaje'] = porcentaje_por_proyecto
                        st.write(f"• {proyecto['nombre']}: {porcentaje_por_proyecto:.1f}%")
                    
                    suma_porcentajes = 100
                
                else:
                    suma_porcentajes = 0
                    
                    for proyecto in proyectos_seleccionados:
                        porcentaje = st.number_input(
                            f"{proyecto['nombre']} (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=round(float(st.session_state.cartera_selecciones[proyecto['id']].get('porcentaje', 0.0)), 1),
                            step=0.1,
                            key=f"input_{proyecto['id']}"
                        )
                        st.session_state.cartera_selecciones[proyecto['id']]['porcentaje'] = porcentaje
                        suma_porcentajes += porcentaje
                    
                    suma_porcentajes = round(suma_porcentajes, 1)
                    if suma_porcentajes == 100:
                        st.success(f"✓ Total: {suma_porcentajes}%")
                    elif suma_porcentajes > 0:
                        st.warning(f"⚠ Total: {suma_porcentajes}% (Falta {100 - suma_porcentajes:.1f}%)")
                    else:
                        st.info("Asigna porcentajes a los proyectos")
        
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
    st.markdown("## Paso 5: Tu cartera está lista")
    st.markdown("")
    
    cartera = st.session_state.datos_cliente.get('cartera', {})
    proyectos_cartera = cartera.get('proyectos', [])
    distribuciones = cartera.get('distribuciones', {})
    precios_compra = st.session_state.precios_compra
    
    if len(proyectos_cartera) > 0:
        # ========== RESUMEN CLIENTE ==========
        st.markdown("### Datos de tu inversión")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nombre:** {st.session_state.datos_cliente.get('nombre', 'N/A')}")
            st.write(f"**Email:** {st.session_state.datos_cliente.get('email', 'N/A')}")
            st.write(f"**Capital:** {st.session_state.datos_cliente.get('capital', 'N/A')}")
        with col2:
            st.write(f"**Estatus:** {st.session_state.datos_cliente.get('estatus', 'N/A')}")
            st.write(f"**Objetivo:** {st.session_state.datos_cliente.get('objetivo', 'N/A')}")
            st.write(f"**Distribución:** {st.session_state.datos_cliente.get('distribucion', 'N/A')}")
        
        st.markdown("---")
        
        # ========== TABLA CARTERA CON PRECIO_COMPRA ==========
        st.markdown("### Tu cartera de inversión")
        
        cartera_data = []
        for proyecto in proyectos_cartera:
            proyecto_id = proyecto['id']
            proyecto_row = st.session_state.df_proyectos[st.session_state.df_proyectos['ID'] == proyecto_id]
            
            if len(proyecto_row) > 0:
                row = proyecto_row.iloc[0]
                porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
                
                # PRECIO_COMPRA REAL
                precio_compra_info = precios_compra.get(proyecto_id, {})
                precio_compra = precio_compra_info.get('precio', row.get('Precio Emisión', 0))
                tipo_precio = precio_compra_info.get('tipo', 'Emisión')
                
                cartera_data.append({
                    'Proyecto': proyecto['nombre'],
                    'Ubicación': row.get('Ubicación', 'N/A'),
                    'Precio Compra': f"€{precio_compra:.2f} ({tipo_precio})",
                    'Rentabilidad Anualizada': f"{row.get('Rentabilidad_Anualizada_SuperReentel', 0):.2f}%",
                    '% Invertido': f"{porcentaje:.1f}%"
                })
        
        if cartera_data:
            df_cartera_display = pd.DataFrame(cartera_data)
            st.dataframe(df_cartera_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ========== PROYECCIONES DE RENTABILIDAD ==========
        st.markdown("### Proyecciones de patrimonio")
        
        capital_map = {
            "Menos de 5.000": 2500,
            "Entre 5.000 y 10.000": 7500,
            "Entre 10.000 y 50.000": 30000,
            "Más de 50.000": 100000
        }
        
        capital_text = st.session_state.datos_cliente.get('capital', 'Entre 10.000 y 50.000')
        capital_estimado = capital_map.get(capital_text, 75000)
        
        estatus = st.session_state.datos_cliente.get('estatus', None)
        calculadora = CalculadoraCartera(estatus or 'Reentel')
        
        # Calcular rentabilidad promedio
        rentabilidad_promedio = 0
        for proyecto in proyectos_cartera:
            proyecto_id = proyecto['id']
            proyecto_row = st.session_state.df_proyectos[st.session_state.df_proyectos['ID'] == proyecto_id]
            if len(proyecto_row) > 0:
                porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0) / 100
                try:
                    rentabilidad_pct = float(str(proyecto_row.iloc[0].get('Rentabilidad_Anualizada_SuperReentel', 0)).replace('%', ''))
                    rentabilidad = rentabilidad_pct / 100
                except:
                    rentabilidad = 0
                rentabilidad_promedio += rentabilidad * porcentaje
        
        proyecciones_data = []
        for meses in [6, 12, 24, 36, 60]:
            capital_final = calculadora.calcular_proyeccion(capital_estimado, rentabilidad_promedio, meses)
            ganancia = capital_final - capital_estimado
            roi = (ganancia / capital_estimado * 100) if capital_estimado > 0 else 0
            
            proyecciones_data.append({
                'Plazo': f"{meses} meses",
                'Capital Inicial': f"€{capital_estimado:,.0f}",
                'Capital Final': f"€{capital_final:,.0f}",
                'Ganancia': f"€{ganancia:,.0f}",
                'ROI': f"{roi:.2f}%"
            })
        
        df_proyecciones = pd.DataFrame(proyecciones_data)
        st.dataframe(df_proyecciones, use_container_width=True, hide_index=True)
        
        st.info(f"📊 Capital Estimado: €{capital_estimado:,.0f} | Rentabilidad Promedio Anual: {rentabilidad_promedio*100:.2f}%")
        
        st.markdown("---")
        
        # ========== DESCARGAR PDF ==========
        st.markdown("### Descarga tu cartera")
        
        pdf_buffer = generar_pdf_cartera(
            st.session_state.datos_cliente,
            proyectos_cartera,
            distribuciones,
            st.session_state.df_proyectos,
            precios_compra
        )
        
        st.download_button(
            label="📥 Descargar cartera (PDF)",
            data=pdf_buffer,
            file_name=f"Cartera_{st.session_state.datos_cliente['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
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
