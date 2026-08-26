"""
HERRAMIENTA CONSTRUCCIÓN DE CARTERA INMOBILIARIA - App Guiada (3 Pasos)
Versión mejorada con manejo robusto de columnas
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
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🏠 Simulador de Cartera Inmobiliaria Reental")

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def obtener_columna(df, posibles_nombres):
    """
    Busca una columna en el DataFrame probando múltiples nombres posibles.
    Útil cuando no sabemos exactamente el nombre de la columna.
    """
    if df is None or df.empty:
        return None
    
    for nombre in posibles_nombres:
        if nombre in df.columns:
            return nombre
    
    # Si no encuentra, retorna None
    return None

def preparar_tabla_proyectos(df_proyectos):
    """
    Prepara la tabla de proyectos para mostrar en Paso 2
    """
    if df_proyectos is None or df_proyectos.empty:
        return None
    
    df_display = df_proyectos.copy()
    
    # Seleccionar columnas disponibles
    cols_a_mostrar = []
    
    # ID
    col_id = obtener_columna(df_display, ['ID'])
    if col_id:
        cols_a_mostrar.append(col_id)
    
    # Nombre
    col_nombre = obtener_columna(df_display, ['Nombre del proyecto', 'Nombre', 'nombre'])
    if col_nombre:
        cols_a_mostrar.append(col_nombre)
    
    # Ubicación
    col_ubicacion = obtener_columna(df_display, ['Ubicación', 'ubicacion'])
    if col_ubicacion:
        cols_a_mostrar.append(col_ubicacion)
    
    # Tipología de Dividendos
    col_tipo_div = obtener_columna(df_display, ['Tipología de Dividendos', 'Tipología de dividendos', 'tipo_dividendo'])
    if col_tipo_div:
        cols_a_mostrar.append(col_tipo_div)
    
    # Plazo
    col_plazo = obtener_columna(df_display, [
        'Estimación Nº Meses desde inicio de renta en base a Financiación',
        'Nº Meses desde inicio de renta',
        'meses_plazo'
    ])
    if col_plazo:
        cols_a_mostrar.append(col_plazo)
    
    if len(cols_a_mostrar) > 0:
        df_display = df_display[cols_a_mostrar].copy()
        
        # Renombrar columnas para la visualización
        nombre_mapeo = {
            cols_a_mostrar[0]: 'ID',
            cols_a_mostrar[1]: 'Nombre' if len(cols_a_mostrar) > 1 else '',
            cols_a_mostrar[2]: 'Ubicación' if len(cols_a_mostrar) > 2 else '',
            cols_a_mostrar[3]: 'Rendimientos' if len(cols_a_mostrar) > 3 else '',
            cols_a_mostrar[4]: 'Plazo (meses)' if len(cols_a_mostrar) > 4 else '',
        }
        
        df_display.columns = [nombre_mapeo.get(col, col) for col in df_display.columns]
        return df_display
    
    return None

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
        'es_inversor': True,
        'capital': 50000,
        'estatus': 'SuperReentel',
        'duracion': 'Corto plazo (≤18 meses)',
        'mercados': ['España', 'EE.UU.'],
        'tipo_rendimientos': 'Rendimientos periódicos',
        'objetivo': 'Recibir rentas periódicas (crecimiento gradual)',
    }

if 'df_proyectos' not in st.session_state:
    st.session_state.df_proyectos = None

if 'proyectos_seleccionados' not in st.session_state:
    st.session_state.proyectos_seleccionados = []

if 'tipo_distribucion' not in st.session_state:
    st.session_state.tipo_distribucion = 'Igual'

# ============================================================================
# PASO 1: ONBOARDING
# ============================================================================

if st.session_state.paso_actual == 1:
    st.markdown("### Paso 1/3: Cuéntanos sobre ti")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.datos_cliente['nombre'] = st.text_input(
            "Nombre completo",
            value=st.session_state.datos_cliente['nombre'],
            placeholder="Juan Pérez"
        )
        
        st.session_state.datos_cliente['email'] = st.text_input(
            "Email",
            value=st.session_state.datos_cliente['email'],
            placeholder="juan@example.com"
        )
        
        st.session_state.datos_cliente['divisa'] = st.selectbox(
            "Divisa preferida",
            ["EUR", "USD"],
            index=0 if st.session_state.datos_cliente['divisa'] == 'EUR' else 1
        )
    
    with col2:
        st.session_state.datos_cliente['es_inversor'] = st.radio(
            "¿Ya eres inversor de Reental?",
            [True, False],
            format_func=lambda x: "Sí" if x else "No",
            index=0 if st.session_state.datos_cliente['es_inversor'] else 1
        )
        
        divisa_label = st.session_state.datos_cliente['divisa']
        st.session_state.datos_cliente['capital'] = st.number_input(
            f"Capital disponible (orientativo en {divisa_label})",
            min_value=1000,
            value=int(st.session_state.datos_cliente['capital']),
            step=1000
        )
    
    st.markdown("---")
    st.markdown("### ¿Qué estatus quieres considerar?")
    
    col1, col2, col3 = st.columns(3)
    
    estatus_info = {
        'SuperReentel': {
            'descripcion': 'Consigue hasta un 50% más de rentabilidad en tus inversiones inmobiliarias y acceso prioritario.',
            'tasa': '16% reinversión anual'
        },
        'ReentelPro': {
            'descripcion': 'Consigue hasta un 25% más de rentabilidad en tus inversiones inmobiliarias y acceso a los proyectos tras los SuperReentel.',
            'tasa': '13% reinversión anual'
        },
        'Reentel': {
            'descripcion': 'Solo quiero invertir en inmobiliario.',
            'tasa': '11% reinversión anual'
        }
    }
    
    with col1:
        is_selected = st.session_state.datos_cliente['estatus'] == 'SuperReentel'
        if st.button(
            f"{'✅ ' if is_selected else ''}SuperReentel\n{estatus_info['SuperReentel']['tasa']}",
            use_container_width=True,
            key="btn_super"
        ):
            st.session_state.datos_cliente['estatus'] = 'SuperReentel'
            st.rerun()
        st.caption(estatus_info['SuperReentel']['descripcion'])
    
    with col2:
        is_selected = st.session_state.datos_cliente['estatus'] == 'ReentelPro'
        if st.button(
            f"{'✅ ' if is_selected else ''}ReentelPro\n{estatus_info['ReentelPro']['tasa']}",
            use_container_width=True,
            key="btn_pro"
        ):
            st.session_state.datos_cliente['estatus'] = 'ReentelPro'
            st.rerun()
        st.caption(estatus_info['ReentelPro']['descripcion'])
    
    with col3:
        is_selected = st.session_state.datos_cliente['estatus'] == 'Reentel'
        if st.button(
            f"{'✅ ' if is_selected else ''}Reentel\n{estatus_info['Reentel']['tasa']}",
            use_container_width=True,
            key="btn_reentel"
        ):
            st.session_state.datos_cliente['estatus'] = 'Reentel'
            st.rerun()
        st.caption(estatus_info['Reentel']['descripcion'])
    
    st.markdown("---")
    st.markdown("### ¿Qué tipo de proyectos te interesan?")
    
    col1, col2 = st.columns(2)
    
    duracion_options = ["Corto plazo (≤18 meses)", "Largo plazo (>18 meses)"]
    mercado_options = ["Todos", "Global", "EE.UU.", "México", "República Dominicana", "Argentina", "España", "Emiratos Árabes"]
    rendimientos_options = ["Final", "Rendimientos periódicos"]
    objetivo_options = [
        "Maximizar rentabilidad (esperar más tiempo)",
        "Recibir rentas periódicas (crecimiento gradual)"
    ]
    
    with col1:
        duracion_idx = 0 if "Corto" in st.session_state.datos_cliente['duracion'] else 1
        st.session_state.datos_cliente['duracion'] = st.radio(
            "Duración",
            duracion_options,
            index=duracion_idx
        )
        
        mercados_validos = [m for m in st.session_state.datos_cliente['mercados'] if m in mercado_options]
        if not mercados_validos:
            mercados_validos = ['España', 'EE.UU.']
        
        st.session_state.datos_cliente['mercados'] = st.multiselect(
            "Mercado",
            mercado_options,
            default=mercados_validos
        )
    
    with col2:
        rendimientos_idx = 0 if "Final" in st.session_state.datos_cliente['tipo_rendimientos'] else 1
        st.session_state.datos_cliente['tipo_rendimientos'] = st.radio(
            "Tipo de rendimientos",
            rendimientos_options,
            index=rendimientos_idx
        )
        
        objetivo_idx = 0 if "Maximizar" in st.session_state.datos_cliente['objetivo'] else 1
        st.session_state.datos_cliente['objetivo'] = st.radio(
            "Objetivo",
            objetivo_options,
            index=objetivo_idx
        )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("Continuar →", use_container_width=True, key="btn_paso1"):
            with st.spinner("Buscando proyectos..."):
                try:
                    st.session_state.df_proyectos = cargar_proyectos()
                    
                    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
                        mercados_map = {
                            'España': 'España',
                            'EE.UU.': 'USA',
                            'Global': 'Global',
                            'México': 'México',
                            'República Dominicana': 'República Dominicana',
                            'Argentina': 'Argentina',
                            'Emiratos Árabes': 'Emiratos Árabes'
                        }
                        
                        mercados_filtrados = [mercados_map.get(m, m) for m in st.session_state.datos_cliente['mercados'] if m != 'Todos']
                        
                        df_ranked = rankear_proyectos(
                            st.session_state.df_proyectos,
                            {
                                'duracion': 'Corto plazo' if 'Corto' in st.session_state.datos_cliente['duracion'] else 'Largo plazo',
                                'ubicaciones': mercados_filtrados if 'Todos' not in st.session_state.datos_cliente['mercados'] else st.session_state.df_proyectos['Ubicación'].unique().tolist() if 'Ubicación' in st.session_state.df_proyectos.columns else []
                            },
                            st.session_state.datos_cliente['estatus']
                        )
                        st.session_state.df_proyectos = df_ranked
                        st.session_state.paso_actual = 2
                        st.rerun()
                    else:
                        st.error("No se encontraron proyectos con tus criterios")
                except Exception as e:
                    st.error(f"Error cargando proyectos: {e}")

# ============================================================================
# PASO 2: SELECCIÓN DE PROYECTOS
# ============================================================================

elif st.session_state.paso_actual == 2:
    st.markdown("### Paso 2/3: Elige tus proyectos")
    st.markdown("---")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        st.markdown("#### Proyectos disponibles (ordenados por relevancia)")
        
        try:
            df_display = preparar_tabla_proyectos(st.session_state.df_proyectos)
            
            if df_display is not None:
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.warning("No se pudieron mostrar los proyectos")
                st.info("Columnas disponibles en el DataFrame:")
                for col in st.session_state.df_proyectos.columns:
                    st.write(f"  - {col}")
        except Exception as e:
            st.error(f"Error mostrando proyectos: {e}")
        
        st.markdown("---")
        st.markdown("#### Selecciona los proyectos que te interesan")
        
        col_id = obtener_columna(st.session_state.df_proyectos, ['ID'])
        
        if col_id:
            proyectos_disponibles = st.session_state.df_proyectos[col_id].tolist()
            
            st.session_state.proyectos_seleccionados = st.multiselect(
                "Proyectos",
                proyectos_disponibles,
                default=st.session_state.proyectos_seleccionados,
                key="select_proyectos"
            )
            
            if st.session_state.proyectos_seleccionados:
                st.success(f"✅ {len(st.session_state.proyectos_seleccionados)} proyecto(s) seleccionado(s)")
                
                st.markdown("---")
                st.markdown("#### ¿Cómo quieres distribuir el capital?")
                
                dist_options = ["Homogénea (igual para cada proyecto)", "Proporcional (según tamaño)", "Manual (tú eliges %)"]
                dist_idx = 0 if "Homogénea" in st.session_state.tipo_distribucion else (
                    1 if "Proporcional" in st.session_state.tipo_distribucion else 2
                )
                
                st.session_state.tipo_distribucion = st.radio(
                    "Tipo de distribución",
                    dist_options,
                    index=dist_idx,
                    key="dist_radio"
                )
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("← Atrás", use_container_width=True):
                        st.session_state.paso_actual = 1
                        st.rerun()
                
                with col3:
                    if st.button("Continuar →", use_container_width=True):
                        st.session_state.paso_actual = 3
                        st.rerun()
            else:
                st.warning("Selecciona al menos un proyecto para continuar")
        else:
            st.error("No se encontró columna de ID en los proyectos")
    else:
        st.error("No hay proyectos disponibles")

# ============================================================================
# PASO 3: RESULTADOS
# ============================================================================

elif st.session_state.paso_actual == 3:
    st.markdown("### Paso 3/3: Tus Resultados")
    st.markdown("---")
    
    if st.session_state.proyectos_seleccionados and st.session_state.df_proyectos is not None:
        
        col_id = obtener_columna(st.session_state.df_proyectos, ['ID'])
        
        if col_id:
            df_seleccionados = st.session_state.df_proyectos[
                st.session_state.df_proyectos[col_id].isin(st.session_state.proyectos_seleccionados)
            ]
            
            tipo_dist_map = {
                "Homogénea (igual para cada proyecto)": "Igual",
                "Proporcional (según tamaño)": "Proporcional",
                "Manual (tú eliges %)": "Manual"
            }
            tipo_dist_short = tipo_dist_map.get(st.session_state.tipo_distribucion, "Igual")
            
            try:
                distribucion = distribuir_capital(df_seleccionados, st.session_state.datos_cliente['capital'], tipo_dist_short)
                
                if distribucion:
                    st.markdown("#### Tu Cartera")
                    
                    df_cartera = pd.DataFrame(distribucion)
                    divisa = st.session_state.datos_cliente['divisa']
                    
                    # Formatear para mostrar
                    df_mostrar = df_cartera[['ID', 'Nombre', 'Inversion', 'Porcentaje']].copy()
                    df_mostrar.columns = ['ID', 'Nombre', f'Inversión ({divisa})', '% Cartera']
                    df_mostrar[f'Inversión ({divisa})'] = df_mostrar[f'Inversión ({divisa})'].apply(lambda x: f"{divisa} {x:,.0f}")
                    df_mostrar['% Cartera'] = df_mostrar['% Cartera'].apply(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    st.markdown("#### Proyección de Ganancias")
                    
                    cartera_norm = normalizar_cartera(distribucion)
                    calculadora = CalculadoraCartera(st.session_state.datos_cliente['estatus'])
                    resultados = calculadora.calcular_cartera_completa(cartera_norm, st.session_state.datos_cliente['capital'])
                    
                    cols = st.columns(5)
                    for idx, horizonte in enumerate([6, 12, 24, 36, 60]):
                        with cols[idx]:
                            res = resultados[horizonte]
                            st.metric(
                                f"{horizonte}M",
                                f"{divisa} {res['ganancia']:,.0f}",
                                f"{res['rentabilidad_anualizada']*100:.2f}%/año"
                            )
                    
                    st.markdown("---")
                    st.markdown("#### Detalles de la Proyección")
                    
                    datos_tabla = []
                    for horizonte in [6, 12, 24, 36, 60]:
                        res = resultados[horizonte]
                        datos_tabla.append({
                            'Horizonte': f'{horizonte} meses',
                            'Valor Final': f'{divisa} {res["valor_final"]:,.0f}',
                            'Ganancia': f'{divisa} {res["ganancia"]:,.0f}',
                            'Rent. Acumulada': f'{res["rentabilidad_acumulada"]*100:.2f}%',
                            'Rent. Anualizada': f'{res["rentabilidad_anualizada"]*100:.2f}%'
                        })
                    
                    df_resultados = pd.DataFrame(datos_tabla)
                    st.dataframe(df_resultados, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button("← Atrás", use_container_width=True):
                            st.session_state.paso_actual = 2
                            st.rerun()
                else:
                    st.error("Error distribuyendo capital")
            except Exception as e:
                st.error(f"Error en los cálculos: {e}")
        else:
            st.error("No se encontró la columna ID")
    else:
        st.info("Vuelve al Paso 2 para seleccionar proyectos")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("<small>🏠 Simulador de Cartera Inmobiliaria Reental © 2026</small>", unsafe_allow_html=True)
