"""
PASO 2 - Objetivo de inversión y mercados.
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    st.markdown("## Paso 2: Define tu estrategia de inversión")
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
        placeholder="Elige uno o varios mercados",
        key="multiselect_mercados",
        label_visibility="collapsed"
    )
    
    st.markdown("")
    st.markdown("---")
    st.markdown("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("< Atrás", use_container_width=True, key="btn_paso2_back"):
            st.session_state.paso_actual = 1
            st.rerun()
    
    with col3:
        # Validar que estén el objetivo y al menos un mercado
        if objetivo is not None and mercados_seleccionados:
            if st.button("Siguiente >", use_container_width=True, key="btn_paso2_next"):
                st.session_state.datos_cliente['objetivo'] = objetivo
                st.session_state.datos_cliente['mercados'] = mercados_seleccionados
                st.session_state.paso_actual = 3
                st.rerun()
        else:
            st.button("Siguiente >", use_container_width=True, disabled=True, key="btn_paso2_next_disabled")
            faltan = [n for n, ok in (("el objetivo de inversión", objetivo is not None),
                                      ("al menos un mercado", bool(mercados_seleccionados))) if not ok]
            if faltan:
                st.caption("Para continuar, elige " + " y ".join(faltan) + ".")
