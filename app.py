"""
SIMULADOR DE CARTERA INMOBILIARIA REENTAL
Layout: Centrado mejorado con mejor UX/UI
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Importar módulos
from modules.data_loader import cargar_proyectos
from modules.calculo_cartera import CalculadoraCartera, rankear_proyectos
from modules.distribucion_capital import distribuir_capital, normalizar_cartera

# ============================================================================
# CONFIG PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Simulador Cartera Reental",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos personalizados mejorados
st.markdown("""
<style>
    /* Background */
    .stApp {
        background-color: #1a2332;
        color: #ffffff;
    }
    
    /* Títulos principales */
    h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 42px;
        margin-bottom: 10px;
    }
    
    h2 {
        color: #ffffff;
        font-weight: 700;
        font-size: 28px;
        margin-top: 30px;
        margin-bottom: 30px;
    }
    
    /* Subtítulo naranja */
    .subtitle-orange {
        color: #ff8c00;
        font-weight: 800;
        font-size: 36px;
        margin-bottom: 50px;
    }
    
    /* Labels - Preguntas EN NARANJA + NEGRITA */
    label {
        color: #ff8c00 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        margin-bottom: 12px !important;
    }
    
    /* Botones */
    .stButton > button {
        background-color: #ff8c00;
        color: #1a2332;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 14px 28px;
        font-size: 16px;
    }
    
    .stButton > button:hover {
        background-color: #e67e00;
    }
    
    /* Input fields - GRIS CLARO */
    .stTextInput > div > div > input {
        background-color: #4a5a6a !important;
        color: #ffffff !important;
        border: 2px solid #ff8c00 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 15px !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #999999 !important;
    }
    
    /* Selectbox - GRIS CLARO */
    .stSelectbox > div > div > select {
        background-color: #4a5a6a !important;
        color: #ffffff !important;
        border: 2px solid #ff8c00 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 15px !important;
    }
    
    /* Radio buttons - MÁS VISIBLES */
    .stRadio > div {
        background-color: transparent;
    }
    
    .stRadio > div > label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        margin-left: 10px !important;
        padding: 10px !important;
    }
    
    .stRadio > div > label > div:first-child {
        background-color: transparent !important;
    }
    
    /* Multiselect - GRIS CLARO */
    .stMultiSelect > div > div > input {
        background-color: #4a5a6a !important;
        border: 2px solid #ff8c00 !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #ff8c00 !important;
        color: #1a2332 !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #2c3e50;
        border: 2px solid #ff8c00;
        color: #ffffff;
        border-radius: 8px;
        padding: 15px;
    }
    
    /* Espaciado */
    .spacer {
        margin: 25px 0;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 12px;
        color: #999999;
    }
    
    /* Spinner */
    .stSpinner {
        color: #ff8c00;
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
# HEADER
# ============================================================================

st.markdown("""
<div style="text-align: center; margin-bottom: 50px; margin-top: 30px;">
    <div style="color: #ff8c00; font-weight: 800; font-size: 32px; margin-bottom: 5px;">Reental</div>
    <h1>SIMULADOR DE CARTERA</h1>
    <div class="subtitle-orange">INMOBILIARIA</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# PASO 1
# ============================================================================

if st.session_state.paso_actual == 1:
    st.markdown("## Paso 1: Cuéntanos sobre ti")
    st.markdown("")
    
    st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
    st.session_state.datos_cliente['nombre'] = st.text_input(
        "**Nombre completo**",
        value=st.session_state.datos_cliente['nombre'],
        placeholder="Juan Pérez",
        key="input_nombre"
    )
    
    st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
    st.session_state.datos_cliente['email'] = st.text_input(
        "**Email**",
        value=st.session_state.datos_cliente['email'],
        placeholder="juan@example.com",
        key="input_email"
    )
    
    st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
    st.session_state.datos_cliente['divisa'] = st.selectbox(
        "**Divisa preferida**",
        ["EUR", "USD"],
        index=0 if st.session_state.datos_cliente['divisa'] == 'EUR' else 1,
        key="select_divisa"
    )
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    st.session_state.datos_cliente['es_inversor'] = st.radio(
        "**¿Ya eres inversor en Reental?**",
        ["Sí", "No"],
        index=0 if st.session_state.datos_cliente['es_inversor'] == 'Sí' else 1,
        key="radio_inversor",
        horizontal=True
    )
    
    st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
    capital_options = [
        "Menos de 5.000",
        "Entre 5.000 y 10.000",
        "Entre 10.000 y 50.000",
        "Más de 50.000"
    ]
    
    idx_capital = capital_options.index(st.session_state.datos_cliente['capital'])
    st.session_state.datos_cliente['capital'] = st.selectbox(
        "**Capital disponible (orientativo)**",
        capital_options,
        index=idx_capital,
        key="select_capital"
    )
    
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Continuar →", use_container_width=True, key="btn_paso1_next"):
            st.session_state.paso_actual = 2
            st.rerun()

# ============================================================================
# PASO 2
# ============================================================================

elif st.session_state.paso_actual == 2:
    st.markdown("## Paso 2: ¿Qué estatus RNT quieres considerar?")
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
        "**Elige tu estatus**",
        list(estatus_options.keys()),
        index=estatus_idx,
        format_func=lambda x: estatus_options[x],
        key="radio_estatus"
    )
    
    st.session_state.datos_cliente['estatus'] = estatus_seleccionado
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    st.info("💡 ¿Quieres más información sobre qué es el estatus RNT y cómo puede ayudarte a maximizar tu rentabilidad inmobiliaria? Agenda con nuestro equipo de Onboarding.")
    
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Atrás", use_container_width=True, key="btn_paso2_back"):
            st.session_state.paso_actual = 1
            st.rerun()
    
    with col3:
        if st.button("Continuar →", use_container_width=True, key="btn_paso2_next"):
            st.session_state.paso_actual = 3
            st.rerun()

# ============================================================================
# PASO 3
# ============================================================================

elif st.session_state.paso_actual == 3:
    st.markdown("## Paso 3: ¿Qué debe caracterizar tu cartera?")
    st.markdown("")
    
    st.markdown("**¿Qué objetivo buscas?**")
    objetivo_options = [
        "Busco rentas periódicas, ver cómo periódicamente voy recibiendo rendimientos",
        "Busco maximizar la rentabilidad. No me importa esperar más, si eso me permite tener más rendimiento."
    ]
    
    idx_objetivo = 0 if "periódicas" in st.session_state.datos_cliente['objetivo'] else 1
    st.session_state.datos_cliente['objetivo'] = st.radio(
        "Objetivo",
        objetivo_options,
        index=idx_objetivo,
        key="radio_objetivo",
        label_visibility="collapsed"
    )
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    st.markdown("**¿En qué mercados quieres operar?**")
    
    mercado_options = [
        "Todos",
        "España",
        "EE.UU.",
        "México",
        "República Dominicana",
        "Argentina",
        "EUA (Emiratos Árabes Unidos)"
    ]
    
    mercados_default = st.session_state.datos_cliente['mercados']
    mercados_seleccionados = st.multiselect(
        "Mercados",
        mercado_options,
        default=mercados_default,
        key="select_mercados",
        label_visibility="collapsed"
    )
    
    if "Todos" in mercados_seleccionados:
        st.session_state.datos_cliente['mercados'] = ["Todos"]
    else:
        st.session_state.datos_cliente['mercados'] = mercados_seleccionados if mercados_seleccionados else ['España']
    
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Atrás", use_container_width=True, key="btn_paso3_back"):
            st.session_state.paso_actual = 2
            st.rerun()
    
    with col3:
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
# PASO 4: PROYECTOS
# ============================================================================

elif st.session_state.paso_actual == 4:
    st.markdown("## Paso 4: Selecciona tus proyectos")
    st.markdown("")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        st.markdown("### Proyectos disponibles (ordenados por relevancia)")
        st.dataframe(st.session_state.df_proyectos, use_container_width=True, hide_index=True)
    else:
        st.error("No se cargaron proyectos")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div class="footer">
    <p>Elaborado por el servicio Reental Wealth</p>
</div>
""", unsafe_allow_html=True)
