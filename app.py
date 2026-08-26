"""
HERRAMIENTA CONSTRUCCIÓN DE CARTERA INMOBILIARIA - Streamlit App
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
    layout="wide"
)

st.title("🏠 Simulador de Cartera Inmobiliaria Reental")

# ============================================================================
# INICIALIZAR SESSION STATE
# ============================================================================

if 'df_proyectos' not in st.session_state:
    st.session_state.df_proyectos = None
if 'proyectos_seleccionados' not in st.session_state:
    st.session_state.proyectos_seleccionados = []
if 'tipo_cambio' not in st.session_state:
    st.session_state.tipo_cambio = 1.167

# ============================================================================
# SIDEBAR - DATOS INVERSOR
# ============================================================================

with st.sidebar:
    st.header("📋 Tus Datos")
    
    nombre_inversor = st.text_input("Nombre completo", placeholder="Juan Pérez")
    email_inversor = st.text_input("Email", placeholder="juan@example.com")
    divisa_seleccionada = st.selectbox("Divisa", ["EUR", "USD"])
    capital_disponible = st.number_input("Capital a invertir (€)", min_value=1000, value=50000)
    estatus_cliente = st.selectbox("Estatus Reental", ["Reentel", "ReentelPro", "SuperReentel"])
    
    st.markdown("---")
    
    st.header("⚙️ Tipo de cambio")
    tipo_cambio_manual = st.number_input("EUR a USD (manual)", value=1.167, step=0.001)
    st.session_state.tipo_cambio = tipo_cambio_manual
    
    st.markdown("---")
    st.markdown("<small>*Herramienta de Reental Wealth*</small>", unsafe_allow_html=True)

# ============================================================================
# TABS PRINCIPALES
# ============================================================================

tab1, tab2, tab3 = st.tabs(["Preferencias", "Ranking", "Proyección"])

# ============================================================================
# TAB 1: PREFERENCIAS
# ============================================================================

with tab1:
    st.header("Tus Preferencias de Inversión")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Duración")
        duracion = st.radio("Elige plazo", ["Corto plazo (<18 meses)", "Largo plazo (≥18 meses)"])
        duracion_key = "Corto plazo" if "Corto" in duracion else "Largo plazo"
    
    with col2:
        st.subheader("Tipología")
        tipologia = st.multiselect("Tipo de dividendo", 
            ["Periódicos", "Finales", "Ambos"],
            default=["Periódicos"])
    
    with col3:
        st.subheader("Ubicaciones")
        ubicaciones = st.multiselect("Dónde invertir",
            ["España", "USA", "Global", "México", "Argentina"],
            default=["España", "USA"])
    
    st.markdown("---")
    
    if st.button("🔍 Buscar Proyectos", use_container_width=True, key="buscar"):
        st.session_state.df_proyectos = cargar_proyectos()
        
        if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
            # Rankear
            df_ranked = rankear_proyectos(
                st.session_state.df_proyectos,
                {'duracion': duracion_key, 'ubicaciones': ubicaciones},
                estatus_cliente
            )
            st.session_state.df_proyectos = df_ranked
            st.success(f"✅ Encontrados {len(df_ranked)} proyectos")
        else:
            st.error("❌ No se encontraron proyectos")

# ============================================================================
# TAB 2: RANKING
# ============================================================================

with tab2:
    st.header("Proyectos Rankeados")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        
        # Mostrar tabla de ranking
        df_display = st.session_state.df_proyectos[[
            'ID', 'Nombre del proyecto', 'Ubicación', 'ESTADO', 
            'score_ranking'
        ]].copy() if 'score_ranking' in st.session_state.df_proyectos.columns else st.session_state.df_proyectos
        
        st.dataframe(df_display, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Selecciona proyectos")
        
        # Multiselect de proyectos
        proyectos_disponibles = st.session_state.df_proyectos['ID'].tolist()
        st.session_state.proyectos_seleccionados = st.multiselect(
            "Elige proyectos",
            proyectos_disponibles,
            key="proyectos_select"
        )
        
        if st.session_state.proyectos_seleccionados:
            st.success(f"✅ {len(st.session_state.proyectos_seleccionados)} proyecto(s) seleccionado(s)")
    else:
        st.info("👆 Primero, busca proyectos en la pestaña 'Preferencias'")

# ============================================================================
# TAB 3: PROYECCIÓN
# ============================================================================

with tab3:
    st.header("Proyección de Rentabilidad")
    
    if st.session_state.proyectos_seleccionados and st.session_state.df_proyectos is not None:
        
        # Filtrar proyectos seleccionados
        df_seleccionados = st.session_state.df_proyectos[
            st.session_state.df_proyectos['ID'].isin(st.session_state.proyectos_seleccionados)
        ]
        
        # PASO 1: Distribución
        st.subheader("Paso 1: Distribución de Capital")
        
        tipo_dist = st.radio("¿Cómo distribuir?", 
            ["Igual", "Proporcional", "Manual"],
            key="dist_type")
        
        distribucion = distribuir_capital(df_seleccionados, capital_disponible, tipo_dist)
        
        if distribucion:
            df_dist = pd.DataFrame(distribucion)
            st.dataframe(df_dist[['ID', 'Nombre', 'Inversion', 'Porcentaje']], use_container_width=True)
            
            st.markdown("---")
            
            # PASO 2: Cálculos
            st.subheader("Paso 2: Proyección Rentabilidades")
            
            cartera_norm = normalizar_cartera(distribucion)
            calculadora = CalculadoraCartera(estatus_cliente)
            resultados = calculadora.calcular_cartera_completa(cartera_norm, capital_disponible)
            
            # Mostrar resultados
            cols = st.columns(5)
            for idx, horizonte in enumerate([6, 12, 24, 36, 60]):
                with cols[idx]:
                    res = resultados[horizonte]
                    st.metric(
                        f"{horizonte} meses",
                        f"€ {res['ganancia']:,.0f}",
                        f"{res['rentabilidad_anualizada']*100:.2f}%/año"
                    )
            
            st.markdown("---")
            
            # Tabla detallada
            st.subheader("Detalles por Horizonte")
            
            datos_tabla = []
            for horizonte in [6, 12, 24, 36, 60]:
                res = resultados[horizonte]
                datos_tabla.append({
                    'Horizonte': f'{horizonte} meses',
                    'Valor Final': f'€ {res["valor_final"]:,.0f}',
                    'Ganancia': f'€ {res["ganancia"]:,.0f}',
                    'Rent. Acum.': f'{res["rentabilidad_acumulada"]*100:.2f}%',
                    'Rent. Anual': f'{res["rentabilidad_anualizada"]*100:.2f}%'
                })
            
            df_resultados = pd.DataFrame(datos_tabla)
            st.dataframe(df_resultados, use_container_width=True)
            
            st.success("✅ Proyección completada")
        else:
            st.error("Error distribuindo capital")
    
    else:
        st.info("👆 Selecciona proyectos en la pestaña 'Ranking'")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("<small>🏠 Simulador de Cartera Inmobiliaria Reental © 2026</small>", unsafe_allow_html=True)
