"""
SIMULADOR DE CARTERA INMOBILIARIA REENTAL
Layout: Sidebar 3 pasos + Diseño PDF (azul marino + naranja)
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Importar módulos
from modules.data_loader import cargar_proyectos
from modules.calculo_cartera import CalculadoraCartera, rankear_proyectos
from modules.distribucion_capital import distribuir_capital, normalizar_cartera

# ============================================================================
# CONFIG PÁGINA Y DISEÑO
# ============================================================================

st.set_page_config(
    page_title="Simulador Cartera Reental",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados (colores PDF: azul marino #1a2332 + naranja #ff8c00)
st.markdown("""
<style>
    /* Colores principales */
    :root {
        --azul-marino: #1a2332;
        --naranja: #ff8c00;
        --gris-oscuro: #2c3e50;
    }
    
    /* Background */
    .stApp {
        background-color: #1a2332;
        color: #ffffff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f1419;
        border-right: 2px solid #ff8c00;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
    }
    
    /* Titles naranja */
    .sidebar-title {
        color: #ff8c00;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 15px;
    }
    
    /* Labels */
    label {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 14px;
    }
    
    /* Botones */
    .stButton > button {
        background-color: #ff8c00;
        color: #1a2332;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
    }
    
    .stButton > button:hover {
        background-color: #e67e00;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #ff8c00;
    }
    
    /* Radio buttons */
    .stRadio > div {
        background-color: #0f1419;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div {
        background-color: #2c3e50;
        border: 1px solid #ff8c00;
    }
    
    /* Cards */
    .stContainer {
        background-color: #0f1419;
        border: 1px solid #ff8c00;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    /* Info/Warning boxes */
    .stInfo, .stWarning {
        background-color: #2c3e50;
        border: 1px solid #ff8c00;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INICIALIZAR SESSION STATE
# ============================================================================

if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 1

if 'datos_cliente' not in st.session_state:
    st.session_state.datos_cliente = {
        'nombre': '',
        'email': '',
        'divisa': 'EUR',
        'es_inversor': 'No',
        'capital': 'Entre 10.000 y 50.000',
        'estatus': 'SuperReentel',
        'objetivo': 'Busco rentas periódicas, ver cómo periódicamente voy recibiendo rendimientos',
        'mercados': ['España'],
    }

if 'df_proyectos' not in st.session_state:
    st.session_state.df_proyectos = None

if 'proyectos_seleccionados' not in st.session_state:
    st.session_state.proyectos_seleccionados = []

# ============================================================================
# SIDEBAR - FORMULARIO (3 PASOS)
# ============================================================================

with st.sidebar:
    st.markdown("# 🏠 SIMULADOR DE CARTERA")
    st.markdown("**INMOBILIARIA**")
    st.markdown("---")
    
    # ========== PASO 1 ==========
    if st.session_state.paso_actual == 1:
        st.markdown('<div class="sidebar-title">PASO 1: CUÉNTANOS SOBRE TI</div>', unsafe_allow_html=True)
        st.markdown("")
        
        st.session_state.datos_cliente['nombre'] = st.text_input(
            "Nombre completo",
            value=st.session_state.datos_cliente['nombre'],
            placeholder="Juan Pérez",
            key="input_nombre"
        )
        
        st.session_state.datos_cliente['email'] = st.text_input(
            "Email",
            value=st.session_state.datos_cliente['email'],
            placeholder="juan@example.com",
            key="input_email"
        )
        
        st.session_state.datos_cliente['divisa'] = st.selectbox(
            "Divisa preferida",
            ["EUR", "USD"],
            index=0 if st.session_state.datos_cliente['divisa'] == 'EUR' else 1,
            key="select_divisa"
        )
        
        st.session_state.datos_cliente['es_inversor'] = st.radio(
            "¿Ya eres inversor en Reental?",
            ["Sí", "No"],
            index=0 if st.session_state.datos_cliente['es_inversor'] == 'Sí' else 1,
            key="radio_inversor"
        )
        
        capital_options = [
            "Menos de 5.000",
            "Entre 5.000 y 10.000",
            "Entre 10.000 y 50.000",
            "Más de 50.000"
        ]
        
        idx_capital = capital_options.index(st.session_state.datos_cliente['capital'])
        st.session_state.datos_cliente['capital'] = st.selectbox(
            "Capital disponible (orientativo)",
            capital_options,
            index=idx_capital,
            key="select_capital"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("Continuar →", use_container_width=True, key="btn_paso1_next"):
                st.session_state.paso_actual = 2
                st.rerun()
    
    # ========== PASO 2 ==========
    elif st.session_state.paso_actual == 2:
        st.markdown('<div class="sidebar-title">PASO 2: ¿QUÉ ESTATUS RNT QUIERES CONSIDERAR?</div>', unsafe_allow_html=True)
        st.markdown("")
        
        estatus_options = {
            'SuperReentel': 'SuperReentel: quiero conseguir hasta un 50% más de rentabilidad en mis inversiones inmobiliarias y acceso prioritario a los proyectos.',
            'ReentelPro': 'ReentelPro: quiero conseguir hasta un 25% más de rentabilidad en mis inversiones inmobiliarias y acceder a los proyectos tras los SuperReentel.',
            'Reentel': 'Reentel: por ahora no quiero estatus.'
        }
        
        estatus_idx = 0 if st.session_state.datos_cliente['estatus'] == 'SuperReentel' else (
            1 if st.session_state.datos_cliente['estatus'] == 'ReentelPro' else 2
        )
        
        estatus_seleccionado = st.radio(
            "Elige tu estatus",
            list(estatus_options.keys()),
            index=estatus_idx,
            format_func=lambda x: estatus_options[x],
            key="radio_estatus"
        )
        
        st.session_state.datos_cliente['estatus'] = estatus_seleccionado
        
        st.markdown("")
        st.info("💡 **¿Quieres más información sobre qué es el estatus RNT y cómo puede ayudarte a maximizar tu rentabilidad inmobiliaria?** Agenda con nuestro equipo de Onboarding.")
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Atrás", use_container_width=True, key="btn_paso2_back"):
                st.session_state.paso_actual = 1
                st.rerun()
        
        with col2:
            if st.button("Continuar →", use_container_width=True, key="btn_paso2_next"):
                st.session_state.paso_actual = 3
                st.rerun()
    
    # ========== PASO 3 ==========
    elif st.session_state.paso_actual == 3:
        st.markdown('<div class="sidebar-title">PASO 3: ¿QUÉ CARACTERIZA TU CARTERA?</div>', unsafe_allow_html=True)
        st.markdown("")
        
        # Objetivo
        st.markdown("**Objetivo**")
        objetivo_options = [
            "Busco rentas periódicas, ver cómo periódicamente voy recibiendo rendimientos",
            "Busco maximizar la rentabilidad. No me importa esperar más, si eso me permite tener más rendimiento."
        ]
        
        idx_objetivo = 0 if "periódicas" in st.session_state.datos_cliente['objetivo'] else 1
        st.session_state.datos_cliente['objetivo'] = st.radio(
            "¿Qué objetivo buscas?",
            objetivo_options,
            index=idx_objetivo,
            key="radio_objetivo",
            label_visibility="collapsed"
        )
        
        st.markdown("")
        st.markdown("**Mercados**")
        
        mercado_options = [
            "Todos",
            "España",
            "EE.UU.",
            "México",
            "República Dominicana",
            "Argentina",
            "EUA (Emiratos Árabes Unidos)"
        ]
        
        # Lógica: si "Todos" está seleccionado, no mostrar otros
        mercados_default = st.session_state.datos_cliente['mercados']
        mercados_seleccionados = st.multiselect(
            "¿En qué mercados quieres operar?",
            mercado_options,
            default=mercados_default,
            key="select_mercados",
            label_visibility="collapsed"
        )
        
        if "Todos" in mercados_seleccionados:
            st.session_state.datos_cliente['mercados'] = ["Todos"]
        else:
            st.session_state.datos_cliente['mercados'] = mercados_seleccionados if mercados_seleccionados else ['España']
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("← Atrás", use_container_width=True, key="btn_paso3_back"):
                st.session_state.paso_actual = 2
                st.rerun()
        
        with col2:
            if st.button("Continuar →", use_container_width=True, key="btn_paso3_next"):
                with st.spinner("Buscando proyectos..."):
                    try:
                        st.session_state.df_proyectos = cargar_proyectos()
                        if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
                            st.session_state.paso_actual = 4
                            st.rerun()
                        else:
                            st.error("No se encontraron proyectos")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ============================================================================
# CONTENIDO PRINCIPAL
# ============================================================================

# PORTADA (Pasos 1-3)
if st.session_state.paso_actual in [1, 2, 3]:
    st.markdown("# 🏠 SIMULADOR DE CARTERA INMOBILIARIA")
    st.markdown("**Reental Wealth**", help="Elaborado por el servicio Reental Wealth")
    st.markdown("---")
    
    # Mostrar resumen según paso
    if st.session_state.paso_actual == 1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("## Paso 1: Cuéntanos sobre ti")
            if st.session_state.datos_cliente['nombre']:
                st.success(f"✅ {st.session_state.datos_cliente['nombre']}")
            else:
                st.warning("⏳ Ingresa tu nombre")
    
    elif st.session_state.paso_actual == 2:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("## Paso 2: ¿Qué estatus RNT?")
            st.info(f"📊 Estatus seleccionado: **{st.session_state.datos_cliente['estatus']}**")
    
    elif st.session_state.paso_actual == 3:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("## Paso 3: Caracteriza tu cartera")
            st.info(f"""
            **Objetivo:** {st.session_state.datos_cliente['objetivo'][:60]}...
            
            **Mercados:** {', '.join(st.session_state.datos_cliente['mercados'])}
            """)

# PASO 4: Selección de proyectos
elif st.session_state.paso_actual == 4:
    st.markdown("# 🏠 SIMULADOR DE CARTERA INMOBILIARIA")
    st.markdown("**Paso 4: Selecciona tus proyectos**")
    st.markdown("---")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        st.markdown("### Proyectos disponibles (ordenados por relevancia)")
        st.dataframe(st.session_state.df_proyectos, use_container_width=True, hide_index=True)
    else:
        st.error("No se cargaron proyectos")

# ============================================================================
# FOOTER
# ============================================================================

if st.session_state.paso_actual <= 3:
    st.markdown("---")
    st.markdown("<small>Elaborado por el servicio Reental Wealth | " + datetime.now().strftime("%d de %B de %Y") + "</small>", unsafe_allow_html=True)
