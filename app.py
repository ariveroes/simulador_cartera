"""
HERRAMIENTA CONSTRUCCIÓN DE CARTERA INMOBILIARIA
Streamlit App - Interfaz principal
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from io import BytesIO

# Importar módulos propios
from modules.data_loader import (
    cargar_proyectos, limpiar_datos_proyectos, filtrar_proyectos_por_estado,
    obtener_tipo_cambio_eur_usd, convertir_moneda
)
from modules.calculo_cartera import (
    CalculadoraCartera, rankear_proyectos
)
from config.constants import (
    REINVERSION_RATES, ESTATUS, TIPOS_INVERSION, UBICACIONES,
    MINIMO_INVERSION, HORIZONTES_CALCULO, DIVISAS
)

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Cartera Inmobiliaria Reental",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILOS
# ============================================================================

st.markdown("""
<style>
    .header-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INICIALIZACIÓN DE SESSION STATE
# ============================================================================

def inicializar_session_state():
    """Inicializa variables de sesión"""
    if 'df_proyectos' not in st.session_state:
        st.session_state.df_proyectos = None
    if 'df_proyectos_filtrados' not in st.session_state:
        st.session_state.df_proyectos_filtrados = None
    if 'proyectos_seleccionados' not in st.session_state:
        st.session_state.proyectos_seleccionados = []
    if 'tipo_cambio' not in st.session_state:
        st.session_state.tipo_cambio = obtener_tipo_cambio_eur_usd()

inicializar_session_state()

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-section">
    <h1>🏠 Constructor de Cartera Inmobiliaria</h1>
    <p>Crea tu cartera personalizada según tus preferencias y calcula la rentabilidad esperada</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - CONFIGURACIÓN INICIAL
# ============================================================================

st.sidebar.markdown("### ⚙️ CONFIGURACIÓN")

# Datos del inversor
nombre_inversor = st.sidebar.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
email_inversor = st.sidebar.text_input("Email", placeholder="tu@email.com")

st.sidebar.markdown("---")

# Divisa
divisa_seleccionada = st.sidebar.radio("💱 Divisa de inversión", DIVISAS, horizontal=True)

# Capital disponible
capital_disponible = st.sidebar.number_input(
    "💰 Capital disponible",
    min_value=0,
    value=50000,
    step=1000,
    help="En EUR o USD según tu selección"
)

st.sidebar.markdown("---")

# Tipo de inversión
tipo_inversion = st.sidebar.selectbox(
    "🔄 Tipo de inversión",
    TIPOS_INVERSION,
    help=f"Mínimo por proyecto: EUR 500 o Cripto 100"
)

st.sidebar.markdown("---")

# Estatus
estatus_cliente = st.sidebar.selectbox(
    "👤 Estatus Reental",
    ESTATUS,
    help="Afecta a rentabilidad y coste"
)

# Coste del estatus (cliente lo introduce manualmente)
st.sidebar.markdown(f"**Coste {estatus_cliente}:**")
coste_estatus = st.sidebar.number_input(
    f"Coste en {divisa_seleccionada}",
    min_value=0,
    value=28000 if estatus_cliente == "SuperReentel" else 14000 if estatus_cliente == "ReentelPro" else 0,
    step=100
)

# Verificación simple
minimo_requerido = MINIMO_INVERSION[tipo_inversion]

if capital_disponible > 0 and capital_disponible < minimo_requerido:
    st.sidebar.warning(
        f"⚠️ Capital mínimo: {minimo_requerido} {divisa_seleccionada} para {tipo_inversion}"
    )

st.sidebar.markdown("---")

# Información de tipo de cambio
tipo_cambio_actual = st.session_state.tipo_cambio
st.sidebar.metric("Tipo de cambio EUR/USD", f"{tipo_cambio_actual:.4f}")

# ============================================================================
# MAIN CONTENT - TAB 1: PREFERENCIAS
# ============================================================================

tab1, tab2, tab3 = st.tabs(["🎯 Preferencias", "📊 Ranking", "📄 PDF"])

with tab1:
    st.markdown("### Tus Preferencias de Inversión")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        duracion = st.selectbox(
            "Duración",
            ["Corto plazo (<18 meses)", "Largo plazo (≥18 meses)"]
        )
        duracion_valor = "Corto plazo" if "Corto" in duracion else "Largo plazo"
    
    with col2:
        rendimientos = st.multiselect(
            "Tipología de rendimientos",
            ["Periódicos", "Finales", "Ambos"],
            default=["Periódicos"]
        )
        if "Ambos" in rendimientos:
            rendimientos = ["Periódicos", "Finales"]
    
    with col3:
        ubicaciones = st.multiselect(
            "Ubicaciones",
            UBICACIONES,
            default=["España", "USA"]
        )
    
    # Botón para buscar proyectos
    if st.button("🔍 Buscar Proyectos", key="buscar_proyectos", use_container_width=True):
        with st.spinner("Cargando proyectos..."):
            # Cargar datos
            df = cargar_proyectos()
            df = limpiar_datos_proyectos(df)
            df = filtrar_proyectos_por_estado(df)
            
            st.session_state.df_proyectos = df
            
            # Guardar criterios en sesión
            st.session_state.criterios_cliente = {
                'duracion': duracion_valor,
                'rendimientos': rendimientos,
                'ubicacion': ubicaciones
            }
            
            st.success(f"✅ {len(df)} proyectos disponibles")

# ============================================================================
# MAIN CONTENT - TAB 2: RANKING Y SELECCIÓN
# ============================================================================

with tab2:
    st.markdown("### Proyectos Recomendados")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        
        # Rankear proyectos
        df_ranking = rankear_proyectos(
            st.session_state.df_proyectos,
            st.session_state.criterios_cliente,
            estatus_cliente
        )
        
        # Guardar para usar luego
        st.session_state.df_proyectos_filtrados = df_ranking
        
        # Display tabla
        cols_display = ['ID', 'Nombre', 'Ubicación', 'Estimación Nº Meses desde Lanzamiento',
                       'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel',
                       'score_similitud', 'score_rentabilidad', 'score_duracion', 'score_total']
        
        cols_disponibles = [c for c in cols_display if c in df_ranking.columns]
        
        st.dataframe(
            df_ranking[cols_disponibles],
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        
        # Selección de proyectos
        st.markdown("### Selecciona proyectos para tu cartera")
        
        proyectos_ids = df_ranking['ID'].tolist()
        
        seleccionados = st.multiselect(
            "Proyectos a incluir:",
            proyectos_ids,
            key="seleccion_proyectos"
        )
        
        # Guardar selección
        st.session_state.proyectos_seleccionados = seleccionados
        
        if seleccionados:
            st.markdown(f"✅ {len(seleccionados)} proyectos seleccionados")
            
            # Preview de selección
            df_seleccionados = df_ranking[df_ranking['ID'].isin(seleccionados)][
                ['ID', 'Nombre', 'Ubicación', 'Importe proyecto en €']
            ]
            
            st.dataframe(df_seleccionados, use_container_width=True, hide_index=True)
            
            # Inversión total aproximada
            inversion_total = df_seleccionados['Importe proyecto en €'].sum()
            st.info(f"💰 Inversión inmobiliaria total (aproximado): {inversion_total:,.0f} {divisa_seleccionada}")
            
            if divisa_seleccionada == "USD":
                inversion_usd = convertir_moneda(inversion_total, "EUR", "USD", tipo_cambio_actual)
                st.info(f"💵 En USD: {inversion_usd:,.0f} USD")
    
    else:
        st.info("👆 Selecciona preferencias y haz clic en 'Buscar Proyectos'")

# ============================================================================
# MAIN CONTENT - TAB 3: CÁLCULOS Y PDF
# ============================================================================

with tab3:
    st.markdown("### 📊 Proyección de Rentabilidad con Reinversión")
    
    if st.session_state.proyectos_seleccionados and st.session_state.df_proyectos_filtrados is not None:
        
        # Importar módulos necesarios
        from modules.distribucion_capital import distribuir_capital, normalizar_cartera
        from modules.calculo_cartera import CalculadoraCartera
        from modules.pdf_generator import PDFCarteraProf
        
        # PASO 1: Seleccionar tipo de distribución
        st.markdown("#### Paso 1: Distribución del capital")
        
        col_dist1, col_dist2 = st.columns(2)
        
        with col_dist1:
            tipo_distribucion = st.radio(
                "¿Cómo distribuir el capital?",
                [
                    "Igual (mismo monto por proyecto)",
                    "Proporcional (según tamaño del proyecto)",
                    "Manual (tú eliges % por proyecto)"
                ],
                key="tipo_distribucion"
            )
        
        # Mapear a nombre corto
        tipo_dist_map = {
            "Igual (mismo monto por proyecto)": "Igual",
            "Proporcional (según tamaño del proyecto)": "Proporcional",
            "Manual (tú eliges % por proyecto)": "Manual"
        }
        tipo_dist_short = tipo_dist_map[tipo_distribucion]
        
        # PASO 2: Distribuir capital
        st.markdown("---")
        st.markdown("#### Paso 2: Revisar distribución")
        
        # Obtener proyectos seleccionados con datos
        df_seleccionados = st.session_state.df_proyectos_filtrados[
            st.session_state.df_proyectos_filtrados['ID'].isin(st.session_state.proyectos_seleccionados)
        ]
        
        # Capital a invertir (descontar estatus si "Solo inmuebles")
        capital_a_invertir = capital_disponible
        
        if tipo_dist_short == "Manual":
            st.info("📝 Asigna un porcentaje a cada proyecto (deben sumar 100%)")
            
            porcentajes = {}
            cols_manual = st.columns(len(st.session_state.proyectos_seleccionados))
            
            for idx, (col, proyecto_id) in enumerate(zip(cols_manual, st.session_state.proyectos_seleccionados)):
                with col:
                    porcentajes[proyecto_id] = st.number_input(
                        f"{proyecto_id}",
                        min_value=0.0,
                        max_value=100.0,
                        value=100.0 / len(st.session_state.proyectos_seleccionados),
                        step=1.0,
                        key=f"pct_{proyecto_id}"
                    ) / 100.0
            
            # Validar suma
            suma_porcentajes = sum(porcentajes.values())
            if abs(suma_porcentajes - 1.0) > 0.01:
                st.warning(f"⚠️ Los porcentajes suman {suma_porcentajes*100:.1f}%. Deben sumar 100%")
                porcentajes = None
            else:
                st.success(f"✅ Porcentajes válidos: {suma_porcentajes*100:.1f}%")
            
            distribucion = distribuir_capital(df_seleccionados, capital_a_invertir, "Manual", porcentajes) if porcentajes else []
        
        else:
            distribucion = distribuir_capital(df_seleccionados, capital_a_invertir, tipo_dist_short)
        
        if distribucion:
            # Display distribución
            df_dist = pd.DataFrame(distribucion)
            st.dataframe(
                df_dist[['ID', 'Nombre', 'Inversion', 'Porcentaje']].rename(
                    columns={'Inversion': f'Inversión ({divisa_seleccionada})', 'Porcentaje': '% Cartera'}
                ),
                use_container_width=True,
                hide_index=True
            )
            
            # PASO 3: Calcular rentabilidades
            st.markdown("---")
            st.markdown("#### Paso 3: Cálculos de rentabilidad")
            
            # Normalizar cartera
            cartera_normalizada = normalizar_cartera(distribucion)
            
            # Crear calculadora
            calculadora = CalculadoraCartera(estatus_cliente)
            
            # Calcular para todos los horizontes
            resultados = calculadora.calcular_cartera_completa(
                cartera_normalizada,
                capital_a_invertir
            )
            
            # Display resultados
            st.markdown("**Proyección con reinversión (interés compuesto):**")
            
            # Tabla resumen
            datos_resumen = []
            for horizonte in [6, 12, 24, 36, 60]:
                res = resultados[horizonte]
                datos_resumen.append({
                    'Horizonte': f'{horizonte} meses',
                    'Valor Final': f'€ {res["valor_final"]:,.0f}',
                    'Ganancia': f'€ {res["ganancia"]:,.0f}',
                    'Rentab. Acumulada': f'{res["rentabilidad_acumulada"]*100:.2f}%',
                    'Rentab. Anualizada': f'{res["rentabilidad_anualizada"]*100:.2f}%'
                })
            
            df_resumen = pd.DataFrame(datos_resumen)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
            # PASO 4: Generar PDF
            st.markdown("---")
            st.markdown("#### Paso 4: Descargar PDF")
            
            if st.button("📥 Generar PDF de cartera", use_container_width=True, key="generar_pdf"):
                with st.spinner("Generando PDF..."):
                    try:
                        # Calcular estadísticas de cartera
                        inversion_total_eur = sum(d['Inversion'] for d in distribucion)
                        inversion_total_usd = convertir_moneda(
                            inversion_total_eur, "EUR", "USD", st.session_state.tipo_cambio
                        )
                        media_meses = df_seleccionados.get('Estimación Nº Meses desde Lanzamiento', [24]).mean()
                        
                        # Rentabilidades promedio
                        rent_rec_prom = sum(d.get('Rentab_Recurrente', 0) * d['Inversion'] 
                                          for d in distribucion) / inversion_total_eur if inversion_total_eur > 0 else 0
                        rent_plusv_prom = sum(d.get('Rentab_Plusvalia', 0) * d['Inversion'] 
                                             for d in distribucion) / inversion_total_eur if inversion_total_eur > 0 else 0
                        rent_total_anual = rent_rec_prom + rent_plusv_prom
                        
                        # Calcular media de meses
                        media_meses = df_seleccionados.get('Estimación Nº Meses desde Lanzamiento', [24]).mean() if len(df_seleccionados) > 0 else 24
                        
                        # Generar PDF profesional
                        pdf_gen = PDFCarteraProf()
                        pdf_bytes = pdf_gen.generar(
                            nombre_inversor=nombre_inversor or "Inversor",
                            email=email_inversor or "email@example.com",
                            estatus=estatus_cliente,
                            tipo_cambio=st.session_state.tipo_cambio,
                            num_inmuebles=len(distribucion),
                            inversion_total_eur=inversion_total_eur,
                            rentabilidad_anual=rent_total_anual,
                            resultados_por_horizonte=resultados,
                            cartera_lista=distribucion
                        )
                        
                        # Download button
                        st.download_button(
                            label="✅ Descargar PDF",
                            data=pdf_bytes,
                            file_name=f"cartera_reental_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            key="download_pdf",
                            use_container_width=True
                        )
                        
                        st.success("✅ PDF generado exitosamente")
                        
                    except Exception as e:
                        st.error(f"❌ Error generando PDF: {str(e)}")
                        st.info("Intenta recargar la página e intentar de nuevo")
        
        else:
            st.warning("⚠️ No se pudo distribuir el capital. Verifica los datos.")
    
    else:
        st.warning("⚠️ Selecciona proyectos primero en la pestaña 'Ranking'")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <small>Herramienta de Construcción de Cartera Inmobiliaria Reental © 2024</small>
</div>
""", unsafe_allow_html=True)
