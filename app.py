"""
SIMULADOR DE CARTERA INMOBILIARIA REENTAL
Layout final con todos los ajustes de diseño - VERSIÓN CORREGIDA
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Importar módulos
from modules.data_loader import cargar_proyectos
from modules.calculo_cartera import CalculadoraCartera, rankear_proyectos
from modules.distribucion_capital import distribuir_capital, normalizar_cartera
from modules.formateo_datos import preparar_proyectos_para_paso4

# ============================================================================
# CONFIG PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Simulador Cartera Reental",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados - VERSIÓN FINAL CORREGIDA
st.markdown("""
<style>
    /* Fuente Segoe UI - TODA LA HERRAMIENTA */
    html, body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    .stApp, .stApp div, .stApp span, .stApp p, .stApp label, .stApp button, .stApp input, .stApp select, .stApp textarea {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* CORREGIDO: SVG e íconos de Streamlit - NO forzar font */
    .stApp svg, .stApp svg * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
    }
    
    /* Background BLANCO */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Sidebar BLANCO */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 3px solid #ff8c00;
    }
    
    /* Sidebar header - SUBIDO A 40px */
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 40px !important;
        margin-top: 0 !important;
    }
    
    /* Main content BLANCO */
    .main {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Títulos secciones (Pasos) - NARANJA #ff8c00 + 26px */
    h2 {
        color: #ff8c00 !important;
        font-weight: 700 !important;
        font-size: 26px !important;
        margin-top: 30px !important;
        margin-bottom: 30px !important;
        line-height: 1.2 !important;
    }
    
    /* Títulos generales - NEGRO + 22px */
    h1 {
        color: #000000;
        font-weight: 800;
        font-size: 22px;
        margin-bottom: 10px;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Labels - Preguntas EN NEGRO + NEGRITA + 22px */
    label {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 22px !important;
        margin-bottom: 12px !important;
    }
    
    /* Botones - LETRAS NEGRITA + 18px */
    .stButton > button {
        background-color: #ff8c00;
        color: #ffffff;
        font-weight: 700 !important;
        border: none;
        border-radius: 8px;
        padding: 14px 28px;
        font-size: 18px !important;
    }
    
    .stButton > button:hover {
        background-color: #e67e00;
    }
    
    /* Input fields - BLANCO CON BORDE GRIS #cccccc + 20px */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 20px !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #999999 !important;
    }
    
    /* Selectbox - BLANCO CON BORDE GRIS #cccccc + 20px */
    .stSelectbox > div > div > select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        padding: 12px !important;
        font-size: 20px !important;
    }
    
    /* Radio buttons - TEXTO NEGRO + 20px */
    .stRadio > div {
        background-color: transparent;
    }
    
    .stRadio > div > label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 20px !important;
        margin-left: 10px !important;
        padding: 12px 10px !important;
        line-height: 1.6 !important;
    }
    
    .stRadio > div > label > div {
        color: #000000 !important;
        font-size: 20px !important;
    }
    
    .stRadio > div > label > div:first-child {
        background-color: transparent !important;
    }
    
    /* Multiselect - BLANCO CON BORDE GRIS */
    .stMultiSelect > div > div {
        background-color: #ffffff !important;
        border: 2px solid #cccccc !important;
        border-radius: 8px !important;
        font-size: 20px !important;
    }
    
    .stMultiSelect > div > div > input {
        font-size: 20px !important;
        color: #000000 !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #ff8c00 !important;
        color: #ffffff !important;
        font-size: 16px !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: #fff3e0;
        border: 2px solid #ff8c00;
        color: #000000;
        border-radius: 8px;
        padding: 15px;
        font-size: 16px;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 12px;
        color: #666666;
    }
    
    /* Ocultar iconos de enlace externos */
    a[target="_blank"]::after {
        display: none !important;
    }
    
    a svg {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INICIALIZAR SESSION STATE
# ============================================================================

if 'error_paso1' not in st.session_state:
    st.session_state.error_paso1 = False

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
        'objetivo': 'Busco generar ingresos pasivos periódicos',
        'mercados': [],
    }

if 'df_proyectos' not in st.session_state:
    st.session_state.df_proyectos = None

if 'proyectos_seleccionados' not in st.session_state:
    st.session_state.proyectos_seleccionados = []

# ============================================================================
# SIDEBAR - BRANDING FIJO CON LOGO SVG
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; margin-bottom: 30px;">
        <svg width="180" height="40" viewBox="0 0 688 154" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin: 0 auto;">
            <g clip-path="url(#clip0_2206_1070)">
                <path d="M662.231 150.391V7.48199C662.231 5.99671 663.281 4.71853 664.738 4.42984L687.094 0V4.92654V150.391H662.231Z" fill="#FCA311"/>
                <path d="M600.359 37.9688C615.781 37.9688 627.817 42.436 636.465 51.3721C645.113 60.164 649.437 72.6318 649.437 88.7744V150.391H629.647C628.398 150.39 627.384 149.377 627.384 148.127V136.478C627.241 136.648 627.098 136.817 626.952 136.986C622.484 142.031 617.079 146.066 610.737 149.093C604.54 152.12 597.621 153.634 589.982 153.634C582.488 153.634 575.785 152.192 569.876 149.31C564.111 146.427 559.571 142.391 556.256 137.202C552.941 132.014 551.283 126.104 551.283 119.475C551.283 109.241 554.815 101.097 561.877 95.0439C568.939 88.8465 579.101 85.2433 592.36 84.2344L625.136 81.5586C624.683 75.6434 622.407 70.6981 618.304 66.7227C613.692 62.1105 607.638 59.8047 600.144 59.8047C593.802 59.8047 588.541 61.3897 584.361 64.5605C580.965 67.1079 578.589 70.6429 577.234 74.4482C576.814 75.6283 575.592 76.3705 574.378 76.0635L574.2 76.0186L555.253 71.3789C554.023 71.0776 553.274 69.8224 553.657 68.6152C556.45 59.8282 561.64 52.6395 569.228 47.0488C577.587 40.9954 587.964 37.9688 600.359 37.9688ZM596.036 104.557C589.118 105.133 584.145 106.575 581.118 108.881C578.092 111.187 576.578 114.285 576.578 118.177C576.578 122.068 578.308 125.239 581.767 127.689C585.226 130.14 589.622 131.365 594.955 131.365C600.576 131.365 605.621 129.996 610.089 127.258C614.701 124.375 618.376 120.699 621.114 116.231C623.789 111.868 625.156 107.161 625.219 102.11L596.036 104.557Z" fill="#FCA311"/>
                <path d="M516.731 41.3149H542.438V63.5835H516.731V110.714C516.731 116.479 518.173 120.803 521.056 123.686C524.082 126.569 528.406 128.01 534.027 128.01H538.549C540.267 128.01 541.66 129.403 541.66 131.122V150.495H526.893C516.227 150.495 507.724 147.179 501.382 140.549C495.04 133.775 491.869 124.694 491.869 113.308V63.5835H476.967V42.8706C476.967 42.0115 477.664 41.3149 478.523 41.3149H491.869V11.9272C491.869 11.0681 492.566 10.3717 493.425 10.3716H516.731V41.3149Z" fill="#FCA311"/>
                <path d="M392.95 56.6924C394.081 55.1551 395.306 53.7047 396.625 52.3418C400.949 47.7296 405.994 44.1983 411.759 41.748C417.524 39.1537 423.794 37.8564 430.568 37.8564C438.351 37.8565 445.342 39.5858 451.539 43.0449C457.881 46.3599 462.853 51.3329 466.456 57.9629C470.203 64.4487 472.077 72.5918 472.077 82.3926V150.278H449.479C448.228 150.278 447.215 149.265 447.215 148.015V89.96C447.215 83.0418 446.278 77.4206 444.404 73.0967C442.531 68.7729 439.793 65.6018 436.189 63.584C432.73 61.5662 428.694 60.5566 424.082 60.5566C419.758 60.5566 415.29 61.6378 410.678 63.7998C406.21 65.9617 402.391 69.565 399.22 74.6094C396.049 79.654 394.463 86.5006 394.463 95.1484V150.278H372.712C370.994 150.278 369.601 148.885 369.601 147.167V40.9678C369.601 39.2495 370.994 37.8565 372.712 37.8564H392.95V56.6924Z" fill="#FCA311"/>
                <path fill-rule="evenodd" clip-rule="evenodd" d="M182.668 37.9688C193.478 37.9688 202.847 40.4907 210.774 45.5352C218.845 50.4356 225.115 57.3539 229.583 66.29C234.196 75.2261 236.501 85.6758 236.501 97.6387V101.878C236.501 103.596 235.108 104.989 233.39 104.989H152.773C153.348 108.911 154.593 112.587 156.509 116.016C159.392 120.772 163.211 124.591 167.967 127.474C172.724 130.356 177.984 131.798 183.75 131.798C189.226 131.798 194.199 130.356 198.667 127.474C203.28 124.447 206.524 121.466 209.119 116.422C209.691 115.135 211.2 114.559 212.484 115.138L229.316 122.725C230.892 123.435 231.594 125.3 230.783 126.827C226.517 134.852 220.569 141.193 212.936 145.851C204.576 151.039 194.848 153.634 183.75 153.634C172.651 153.634 162.851 151.183 154.347 146.282C145.988 141.382 139.43 134.608 134.673 125.96C129.917 117.312 127.539 107.223 127.539 95.6924C127.539 84.3063 129.844 74.2893 134.457 65.6416C139.213 56.8497 145.699 50.0757 153.915 45.3193C162.274 40.4189 171.859 37.9688 182.668 37.9688ZM302.72 37.9688C313.53 37.9688 322.899 40.4907 330.826 45.5352C338.897 50.4356 345.167 57.3539 349.635 66.29C354.247 75.2261 356.553 85.6758 356.553 97.6387V101.878C356.553 103.596 355.16 104.989 353.442 104.989H272.825C273.4 108.911 274.645 112.587 276.561 116.016C279.444 120.772 283.263 124.591 288.019 127.474C292.775 130.356 298.036 131.798 303.801 131.798C309.278 131.798 314.251 130.356 318.719 127.474C323.331 124.447 326.576 121.466 329.17 116.422L329.284 116.168C329.793 115.021 331.139 114.508 332.283 115.023L350.147 123.076C351.294 123.593 351.804 124.949 351.231 126.069C346.941 134.454 340.859 141.048 332.988 145.851C324.628 151.039 314.899 153.634 303.801 153.634C292.703 153.634 282.903 151.183 274.399 146.282C266.039 141.382 259.481 134.608 254.725 125.96C249.969 117.312 247.59 107.223 247.59 95.6924C247.59 84.3063 249.896 74.2893 254.508 65.6416C259.265 56.8497 265.751 50.0757 273.966 45.3193C282.326 40.4189 291.911 37.9688 302.72 37.9688ZM183.101 59.8047C177.336 59.8047 172.075 61.1736 167.319 63.9121C162.563 66.5064 158.887 70.1813 156.292 74.9375C154.714 77.7429 153.618 80.8423 153 84.2344H211.63C210.998 80.2617 209.704 76.7303 207.748 73.6406C205.153 69.1726 201.694 65.7856 197.37 63.4795C193.19 61.0294 188.434 59.8047 183.101 59.8047ZM303.153 59.8047C297.388 59.8047 292.127 61.1736 287.371 63.9121C282.614 66.5064 278.939 70.1813 276.344 74.9375C274.766 77.7429 273.669 80.8423 273.051 84.2344H331.682C331.05 80.2617 329.756 76.7303 327.799 73.6406C325.205 69.1726 321.745 65.7856 317.421 63.4795C313.242 61.0294 308.486 59.8047 303.153 59.8047Z" fill="#FCA311"/>
                <path fill-rule="evenodd" clip-rule="evenodd" d="M0 1.77641C0 0.508935 1.02749 -0.518555 2.29496 -0.518555H63.8873C67.4307 -0.518555 71.9146 -0.35804 76.5345 0.818092C86.9093 3.4593 100.884 10.2327 109.146 22.3638C120.391 40.5824 121.139 62.901 106.677 83.1283C105.889 84.2302 104.314 84.3554 103.326 83.4289L90.0531 70.9841C89.2685 70.2484 89.1061 69.0667 89.6252 68.1248C97.8869 53.1352 93.9631 44.3505 90.4095 37.1959C86.7092 29.7458 78.7141 24.5806 71.966 22.3638C64.8511 19.1709 51.7534 19.7031 48.8425 19.7031H26.5321C25.2647 19.7031 24.2372 20.7306 24.2372 21.9981V112.559C24.2372 113.325 23.855 114.041 23.2184 114.467L3.57114 127.612C2.04626 128.632 0 127.539 0 125.705V1.77641Z" fill="#FCA311"/>
                <path fill-rule="evenodd" clip-rule="evenodd" d="M66.5305 88.3229C67.0743 87.9435 67.81 87.9996 68.29 88.4571L130.644 147.882C131.555 148.75 130.941 150.285 129.682 150.285H101.039C99.5853 150.285 98.1896 149.718 97.1484 148.704L65.2603 117.655L55.1186 107.513L49.6812 102.076C49.0676 101.463 49.1577 100.443 49.8693 99.947L66.5305 88.3229Z" fill="#FCA311"/>
            </g>
            <defs>
                <clipPath id="clip0_2206_1070">
                    <rect width="687.123" height="153.76" fill="white"/>
                </clipPath>
            </defs>
        </svg>
        <div style="color: #000000; font-weight: 700; font-size: 28px; line-height: 1.4; margin-top: 20px; text-transform: uppercase;">
            SIMULADOR DE<br>CARTERA<br>INMOBILIARIA
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT - CENTRO
# ============================================================================

col_main = st.container()

with col_main:
    # ========== PASO 1 ==========
    if st.session_state.paso_actual == 1:
        st.markdown("## Paso 1: Cuéntanos sobre ti")
        st.markdown("")
        
        # Mostrar error si se intentó continuar sin llenar
        if st.session_state.error_paso1:
            st.error("❌ Por favor, rellena todos los campos antes de continuar.")
        
        # Nombre completo
        st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
        st.markdown('<label style="color: #000000 !important;">**Nombre completo**</label>', unsafe_allow_html=True)
        
        nombre_input = st.text_input(
            "Nombre",
            value=st.session_state.datos_cliente['nombre'],
            placeholder="Juan Pérez",
            key="input_nombre",
            label_visibility="collapsed"
        )
        if nombre_input != st.session_state.datos_cliente['nombre']:
            st.session_state.datos_cliente['nombre'] = nombre_input
            st.session_state.error_paso1 = False  # Limpiar error al escribir
        
        # Email
        st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
        st.markdown('<label style="color: #000000 !important;">**Email**</label>', unsafe_allow_html=True)
        
        email_input = st.text_input(
            "Email",
            value=st.session_state.datos_cliente['email'],
            placeholder="juan@example.com",
            key="input_email",
            label_visibility="collapsed"
        )
        if email_input != st.session_state.datos_cliente['email']:
            st.session_state.datos_cliente['email'] = email_input
            st.session_state.error_paso1 = False  # Limpiar error al escribir
        
        st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
        st.markdown('<label style="color: #000000 !important;">**Divisa preferida**</label>', unsafe_allow_html=True)
        st.session_state.datos_cliente['divisa'] = st.selectbox(
            "Divisa",
            ["EUR", "USD"],
            index=0 if st.session_state.datos_cliente['divisa'] == 'EUR' else 1,
            key="select_divisa",
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        st.markdown('<label style="color: #000000 !important;">**¿Ya eres inversor en Reental?**</label>', unsafe_allow_html=True)
        st.session_state.datos_cliente['es_inversor'] = st.radio(
            "Inversor",
            ["Sí", "No"],
            index=0 if st.session_state.datos_cliente['es_inversor'] == 'Sí' else 1,
            key="radio_inversor",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)
        capital_options = [
            "Menos de 5.000",
            "Entre 5.000 y 10.000",
            "Entre 10.000 y 50.000",
            "Más de 50.000"
        ]
        
        st.markdown('<label style="color: #000000 !important;">**Capital disponible (orientativo)**</label>', unsafe_allow_html=True)
        idx_capital = capital_options.index(st.session_state.datos_cliente['capital'])
        st.session_state.datos_cliente['capital'] = st.selectbox(
            "Capital",
            capital_options,
            index=idx_capital,
            key="select_capital",
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button("Continuar >", use_container_width=True, key="btn_paso1_next"):
                # Validar solo al hacer clic
                campos_vacios = []
                if not st.session_state.datos_cliente['nombre'].strip():
                    campos_vacios.append('nombre')
                if not st.session_state.datos_cliente['email'].strip():
                    campos_vacios.append('email')
                
                if campos_vacios:
                    st.session_state.error_paso1 = True
                    st.rerun()
                else:
                    st.session_state.error_paso1 = False
                    st.session_state.paso_actual = 2
                    st.rerun()

    # ========== PASO 2 - ESTATUS EN 3 COLUMNAS ==========
    elif st.session_state.paso_actual == 2:
        st.markdown("## Paso 2: ¿Qué estatus RNT quieres considerar?")
        st.markdown("")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # SuperReentel seleccionado
            if st.session_state.datos_cliente['estatus'] == 'SuperReentel':
                bg_color = "#f0f9f3"
                border_color = "#16a34a"
                border_width = "3px"
            else:
                bg_color = "#ffffff"
                border_color = "#cccccc"
                border_width = "2px"
            
            st.markdown(f"""
            <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 160px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
                <div style="color: #16a34a; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                    SUPERREENTEL
                </div>
                <div style="color: #000000; font-size: 16px; line-height: 1.6; flex-grow: 1;">
                    quiero conseguir hasta un <b>50% más de rentabilidad</b> en mis inversiones inmobiliarias y <b>acceso prioritario</b> a los proyectos.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Seleccionar SuperReentel", key="btn_super", use_container_width=True):
                st.session_state.datos_cliente['estatus'] = 'SuperReentel'
                st.rerun()
        
        with col2:
            # ReentelPro seleccionado
            if st.session_state.datos_cliente['estatus'] == 'ReentelPro':
                bg_color = "#faf5ff"
                border_color = "#a855f7"
                border_width = "3px"
            else:
                bg_color = "#ffffff"
                border_color = "#cccccc"
                border_width = "2px"
            
            st.markdown(f"""
            <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 160px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
                <div style="color: #a855f7; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                    REENTELPRO
                </div>
                <div style="color: #000000; font-size: 16px; line-height: 1.6; flex-grow: 1;">
                    quiero conseguir hasta un <b>25% más de rentabilidad</b> en mis inversiones inmobiliarias y acceder a los proyectos tras los SuperReentel.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Seleccionar ReentelPro", key="btn_pro", use_container_width=True):
                st.session_state.datos_cliente['estatus'] = 'ReentelPro'
                st.rerun()
        
        with col3:
            # Reentel seleccionado
            if st.session_state.datos_cliente['estatus'] == 'Reentel':
                bg_color = "#feedcf"
                border_color = "#ca820e"
                border_width = "3px"
            else:
                bg_color = "#ffffff"
                border_color = "#cccccc"
                border_width = "2px"
            
            st.markdown(f"""
            <div style="border: {border_width} solid {border_color}; border-radius: 12px; padding: 20px; background-color: {bg_color}; min-height: 160px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer;">
                <div style="color: #ca820e; font-weight: 700; font-size: 16px; margin-bottom: 15px;">
                    REENTEL
                </div>
                <div style="color: #000000; font-size: 16px; line-height: 1.6; flex-grow: 1;">
                    por ahora no quiero estatus.
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Seleccionar Reentel", key="btn_reen", use_container_width=True):
                st.session_state.datos_cliente['estatus'] = 'Reentel'
                st.rerun()
        
        st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <a href="https://api.leadconnectorhq.com/widget/booking/kAzM5NH9hFxtc88sTQKy" target="_blank" style="text-decoration: none; color: inherit;">
            <div style="background-color: #fff3e0; border: 2px solid #ff8c00; color: #000000; border-radius: 8px; padding: 15px; font-size: 16px; cursor: pointer;">
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
            if st.button("Continuar >", use_container_width=True, key="btn_paso2_next"):
                st.session_state.paso_actual = 3
                st.rerun()

    # ========== PASO 3 - OBJETIVO Y MERCADOS ==========
    elif st.session_state.paso_actual == 3:
        st.markdown("## Paso 3: ¿Qué debe caracterizar tu cartera?")
        st.markdown("")
        
        st.markdown("**¿Qué objetivo buscas?**")
        objetivo_options = [
            "Busco generar ingresos pasivos periódicos",
            "Busco maximizar la rentabilidad. No me importa esperar más tiempo, si eso me permite tener más rendimiento"
        ]
        
        idx_objetivo = 0 if "ingresos pasivos" in st.session_state.datos_cliente['objetivo'] else 1
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
            "España",
            "USA",
            "México",
            "República Dominicana",
            "Argentina",
            "Emiratos Árabes",
            "Global"
        ]
        
        mercados_default = st.session_state.datos_cliente['mercados']
        mercados_seleccionados = st.multiselect(
            "Mercados",
            mercado_options,
            default=mercados_default,
            key="select_mercados",
            label_visibility="collapsed"
        )
        
        st.session_state.datos_cliente['mercados'] = mercados_seleccionados
        
        st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
        st.markdown("**¿Cómo quieres distribuir tu cartera?**")
        
        distribucion_options = [
            "Distribuir en partes iguales",
            "Elegir cuánto invertir en cada proyecto"
        ]
        
        idx_distribucion = 0 if st.session_state.datos_cliente.get('distribucion', 'Distribuir en partes iguales') == 'Distribuir en partes iguales' else 1
        st.session_state.datos_cliente['distribucion'] = st.radio(
            "Distribución",
            distribucion_options,
            index=idx_distribucion,
            key="radio_distribucion",
            label_visibility="collapsed"
        )
        
        st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso3_back"):
                st.session_state.paso_actual = 2
                st.rerun()
        
        with col3:
            if st.button("Continuar >", use_container_width=True, key="btn_paso3_next"):
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

    # ========== PASO 4: PROYECTOS ==========
    elif st.session_state.paso_actual == 4:
        st.markdown("## Paso 4: Crea tu cartera de inversión")
        st.markdown("")
        
        if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
            df_proyectos = st.session_state.df_proyectos.copy()
            
            # Obtener parámetros
            mercados_seleccionados = st.session_state.datos_cliente.get('mercados', [])
            objetivo = st.session_state.datos_cliente.get('objetivo', '')
            estatus = st.session_state.datos_cliente.get('estatus', '')
            distribucion_type = st.session_state.datos_cliente.get('distribucion', 'Distribuir en partes iguales')
            
            # Separar proyectos: que matchean con mercados vs que no
            df_matchean = df_proyectos[df_proyectos['Ubicación'].isin(mercados_seleccionados)].copy()
            df_no_matchean = df_proyectos[~df_proyectos['Ubicación'].isin(mercados_seleccionados)].copy()
            
            # Rankear proyectos que matchean
            if len(df_matchean) > 0:
                try:
                    criterios = {
                        'ubicaciones': mercados_seleccionados,
                        'duracion': 'Largo plazo' if 'maximizar' in objetivo.lower() else 'Corto plazo'
                    }
                    df_matchean = rankear_proyectos(df_matchean, criterios, estatus)
                except Exception as e:
                    st.warning(f"No se pudieron rankear proyectos: {e}")
            
            # ========== SECCIÓN 1: TABLA DE PROYECTOS ==========
            st.markdown("### Proyectos disponibles")
            
            # Mostrar proyectos recomendados
            if len(df_matchean) > 0:
                df_display_matchean = preparar_proyectos_para_paso4(df_matchean, estatus)
                column_config = {
                    'Rentabilidad Total': st.column_config.NumberColumn(format='%.2f%%'),
                    'Rentabilidad Anualizada': st.column_config.NumberColumn(format='%.2f%%')
                }
                st.dataframe(df_display_matchean, use_container_width=True, hide_index=True, column_config=column_config)
            
            # Mostrar proyectos adicionales
            if len(df_no_matchean) > 0:
                st.markdown("#### Proyectos adicionales que podrían interesarte")
                df_display_no_matchean = preparar_proyectos_para_paso4(df_no_matchean, estatus)
                column_config = {
                    'Rentabilidad Total': st.column_config.NumberColumn(format='%.2f%%'),
                    'Rentabilidad Anualizada': st.column_config.NumberColumn(format='%.2f%%')
                }
                st.dataframe(df_display_no_matchean, use_container_width=True, hide_index=True, column_config=column_config)
            
            # ========== SECCIÓN 2: SELECCIONAR Y DISTRIBUIR ==========
            st.markdown("### Construye tu cartera")
            st.markdown("")
            
            # Inicializar session state para cartera si no existe
            if 'cartera_selecciones' not in st.session_state:
                st.session_state.cartera_selecciones = {}
            
            # Combinar proyectos para selección
            df_todos = pd.concat([df_matchean, df_no_matchean], ignore_index=True)
            
            # Crear dos columnas para mejor layout
            col_selector, col_distribuir = st.columns([1, 2])
            
            with col_selector:
                st.markdown("**Selecciona proyectos:**")
                proyectos_seleccionados = []
                
                for idx, row in df_todos.iterrows():
                    proyecto_id = row['ID']
                    proyecto_nombre = row['Nombre del proyecto']
                    
                    # Checkbox para seleccionar
                    seleccionado = st.checkbox(
                        f"{proyecto_nombre}",
                        value=st.session_state.cartera_selecciones.get(proyecto_id, {}).get('seleccionado', False),
                        key=f"check_{proyecto_id}"
                    )
                    
                    if seleccionado:
                        proyectos_seleccionados.append({
                            'id': proyecto_id,
                            'nombre': proyecto_nombre,
                            'ubicacion': row['Ubicación'],
                            'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0)
                        })
                        
                        # Guardar en session state
                        if proyecto_id not in st.session_state.cartera_selecciones:
                            st.session_state.cartera_selecciones[proyecto_id] = {'seleccionado': True, 'porcentaje': 0}
                        else:
                            st.session_state.cartera_selecciones[proyecto_id]['seleccionado'] = True
                    else:
                        # Marcar como no seleccionado
                        if proyecto_id in st.session_state.cartera_selecciones:
                            st.session_state.cartera_selecciones[proyecto_id]['seleccionado'] = False
            
            with col_distribuir:
                st.markdown("**Distribución de capital:**")
                
                if len(proyectos_seleccionados) == 0:
                    st.info("Selecciona al menos un proyecto")
                else:
                    if distribucion_type == 'Distribuir en partes iguales':
                        # Distribución automática
                        porcentaje_por_proyecto = 100 / len(proyectos_seleccionados)
                        
                        st.markdown(f"Se distribuirá **{porcentaje_por_proyecto:.1f}%** en cada proyecto:")
                        
                        for proyecto in proyectos_seleccionados:
                            st.session_state.cartera_selecciones[proyecto['id']]['porcentaje'] = porcentaje_por_proyecto
                            st.write(f"• {proyecto['nombre']}: {porcentaje_por_proyecto:.1f}%")
                        
                        suma_porcentajes = 100
                    
                    else:  # Elegir cuánto invertir
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
                        
                        # Validación
                        if suma_porcentajes == 100:
                            st.success(f"✓ Total: {suma_porcentajes}%")
                        elif suma_porcentajes > 0:
                            st.warning(f"⚠ Total: {suma_porcentajes}% (Falta {100 - suma_porcentajes}%)")
                        else:
                            st.info("Asigna porcentajes a los proyectos")
            
            # ========== BOTÓN GENERAR CARTERA ==========
            st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("< Atrás", use_container_width=True, key="btn_paso4_back"):
                    st.session_state.paso_actual = 3
                    st.rerun()
            
            with col3:
                if len(proyectos_seleccionados) > 0 and suma_porcentajes == 100:
                    if st.button("Generar cartera >", use_container_width=True, key="btn_paso4_next"):
                        # Guardar cartera
                        st.session_state.datos_cliente['cartera'] = {
                            'proyectos': proyectos_seleccionados,
                            'distribuciones': st.session_state.cartera_selecciones
                        }
                        
                        # Generar PDF
                        from modules.pdf_generator import generar_pdf_cartera
                        
                        pdf_buffer = generar_pdf_cartera(
                            st.session_state.datos_cliente,
                            proyectos_seleccionados,
                            st.session_state.cartera_selecciones,
                            df_todos
                        )
                        
                        # Mostrar PDF en pantalla
                        st.success("✓ Cartera generada exitosamente")
                        st.markdown("---")
                        st.markdown("### Tu cartera está lista para descargar")
                        
                        # Botón descargar
                        st.download_button(
                            label="📥 Descargar cartera (PDF)",
                            data=pdf_buffer,
                            file_name=f"Cartera_{st.session_state.datos_cliente['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.button("Generar cartera >", use_container_width=True, disabled=True)
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
