"""
SIMULADOR DE CARTERA INMOBILIARIA REENTAL - FASE 3 COMPLETA
Streamlit App - Simulador de cartera inmobiliaria (Reental Wealth)

Pasos:
1. Datos cliente (nombre, email, capital, divisa)
2. Estrategia (objetivo y mercados)
3. Estatus (Reentel, ReentelPro, SuperReentel)
4. Cartera (proyectos disponibles ordenados según las preferencias + reparto)
5. Resumen (tabla cartera + proyecciones + descargar PDF)

ESTRUCTURA DE ARCHIVOS
  app.py                      → este archivo: configuración, cabecera, navegación entre pasos y pie
  modules/comun.py            → colores, constantes y funciones comunes (formatos, divisas, proyectos…)
  modules/estilos.py          → CSS de toda la app
  modules/paso1_datos.py      → Paso 1: datos del cliente
  modules/paso2_preferencias.py → Paso 2: objetivo y mercados
  modules/paso3_estatus.py    → Paso 3: estatus
  modules/paso4_cartera.py    → Paso 4: proyectos y reparto de la cartera
  modules/paso5_resumen.py    → Paso 5: resumen, comparativa y PDF
"""

import streamlit as st

# ========== CONFIGURACIÓN STREAMLIT ==========
st.set_page_config(
    page_title="Simulador de Cartera - Reental",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

from modules.comun import *  # noqa: F401,F403
from modules.estilos import aplicar_estilos
from modules import paso1_datos, paso2_preferencias, paso3_estatus, paso4_cartera, paso5_resumen

aplicar_estilos()

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

# ========== HEADER ==========
st.markdown(f"""
<div style="padding: 4px 0 10px 0;">
    <div class="marca-app" style="font-size: 22px; font-weight: 800; color: {COLOR_AMBAR};">Reental
        <span style="color: {COLOR_NAVY}; font-weight: 500;">Wealth</span></div>
    <div class="titulo-app" style="font-size: 38px; font-weight: 800; color: {COLOR_NAVY}; line-height: 1.15; margin-top: 10px;">
        Simulador de <span style="color: {COLOR_AMBAR};">cartera inmobiliaria</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== INSTRUCCIONES (solo al empezar, antes del Paso 1) ==========
if st.session_state.paso_actual == 1:
    st.markdown(f"""
<div style="background: {COLOR_AMBAR_CLARO}; border: 1px solid #f6c56b;
            border-radius: 12px; padding: 18px 22px; margin: 4px 0 22px 0;">
    <div style="font-size: 20px; font-weight: 700; color: {COLOR_NAVY}; margin-bottom: 8px;">
        Bienvenido al Simulador de cartera inmobiliaria</div>
    <p style="color: {COLOR_NAVY}; font-size: 15px; line-height: 1.55; margin: 0 0 8px 0;">
        Esta herramienta, desarrollada por Reental Wealth, te permitirá simular una cartera inmobiliaria <b>adaptada a tu perfil</b>: tu capital, tu objetivo de inversión y los mercados
        que prefieras.</p>
    <p style="color: {COLOR_NAVY}; font-size: 15px; line-height: 1.55; margin: 0;">
        En solo cinco pasos verás <b>qué proyectos encajan contigo</b> y la rentabilidad estimada de tu cartera. Al final podrás descargar un resumen
        en PDF.</p>
</div>
""", unsafe_allow_html=True)

# ========== PROGRESS BAR ==========
progress_value = (st.session_state.paso_actual - 1) / 4
col1, col2 = st.columns([3, 1])
with col1:
    st.progress(progress_value)
with col2:
    st.write(f"**Paso {st.session_state.paso_actual}/5**")

st.markdown("")

# ========== BOTÓN FLOTANTE PARA AGENDAR (pasos 1 a 4) ==========
# El objetivo de la herramienta es que el cliente agende una reunión: el botón
# está siempre a mano. En el Paso 5 lo sustituye un recuadro destacado.
if st.session_state.paso_actual < 5:
    st.markdown(f"<a class='cta-flotante' href='{URL_AGENDA}' target='_blank' rel='noopener'>"
                f"<span class='cta-dudas'>¿Tienes dudas?</span> Habla con nuestro equipo</a>",
                unsafe_allow_html=True)

# ========== PASO ACTUAL ==========
PASOS = {1: paso1_datos, 2: paso2_preferencias, 3: paso3_estatus, 4: paso4_cartera, 5: paso5_resumen}
PASOS.get(st.session_state.paso_actual, paso1_datos).mostrar()


# ========== FOOTER ==========
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: {COLOR_GRIS}; font-size: 0.9em; margin-top: 30px;'>
    <p><b>© {datetime.now().year} Reental Wealth Services</b> | Simulador de Cartera</p>
    <p>Para más información: <a href='https://reental.co' target='_blank' style='color: {COLOR_AMBAR_OSCURO};'>www.reental.co</a></p>
    <p style='font-size: 0.85em; margin-top: 15px;'>
        <i>Este simulador es una herramienta educativa. Las proyecciones mostradas son estimaciones basadas en datos históricos 
        y parámetros actuales. La rentabilidad pasada no garantiza resultados futuros.</i>
    </p>
</div>
""", unsafe_allow_html=True)

# ========== AL CAMBIAR DE PASO, VOLVER ARRIBA ==========
# Streamlit conserva la posición de la página al pulsar «Siguiente»/«Atrás», así
# que en el móvil se llegaba al paso nuevo por abajo. Este bloque solo se pinta
# cuando cambia el paso y sube la página hasta arriba.
if st.session_state.get("_paso_mostrado") != st.session_state.paso_actual:
    st.session_state._paso_mostrado = st.session_state.paso_actual
    import streamlit.components.v1 as _componentes
    _componentes.html(f"""
    <script>
    // paso {st.session_state.paso_actual}
    (function () {{
        const doc = window.parent.document;
        const subir = () => {{
            ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]', 'section.main', '.main']
                .forEach(sel => {{ const e = doc.querySelector(sel); if (e) e.scrollTop = 0; }});
            window.parent.scrollTo(0, 0);
        }};
        subir(); setTimeout(subir, 150); setTimeout(subir, 500); setTimeout(subir, 1000);
    }})();
    </script>
    """, height=0)
