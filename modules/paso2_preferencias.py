"""
PASO 2 - Objetivo de inversión y mercados.
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    st.markdown("## Paso 2: Define tu estrategia de inversión")
    st.markdown("")
    
    # Objetivo: dos tarjetas una encima de otra, como las del estatus
    st.markdown("**¿Cuál es tu objetivo de inversión?** *")
    guardado = st.session_state.datos_cliente.get('objetivo')
    if guardado and 'ingresos' in guardado.lower():
        guardado = OBJETIVOS[1][0]
    elif guardado and 'rentabilidad' in guardado.lower():
        guardado = OBJETIVOS[0][0]
    objetivo = guardado
    c_obj, _ = st.columns([2, 1])
    with c_obj:
        for n, (titulo, texto) in enumerate(OBJETIVOS):
            elegido = objetivo == titulo
            marca = (f"<span style='font-size:12px; font-weight:700; color:{COLOR_AMBAR_OSCURO}; "
                     f"white-space:nowrap;'>✓ Elegido</span>" if elegido else "")
            st.markdown(
                f"<div class='tarjeta-objetivo' style='border:{'2px' if elegido else '1px'} solid "
                f"{COLOR_AMBAR if elegido else COLOR_BORDE}; border-radius:14px; padding:16px 20px; "
                f"background-color:{COLOR_AMBAR_CLARO if elegido else '#ffffff'};'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center; gap:12px; "
                f"margin-bottom:6px;'><span style='color:{COLOR_NAVY}; font-weight:800; font-size:17px;'>"
                f"{titulo}</span>{marca}</div>"
                f"<div style='color:{COLOR_NAVY}; font-size:15px; line-height:1.55;'>{texto}</div></div>",
                unsafe_allow_html=True)
            # El elegido lleva el botón relleno; el otro, de contorno
            if st.button("✓ Elegido" if elegido else "Elegir este objetivo",
                         key=f"btn_objetivo_{n}{'' if elegido else '_sec'}", use_container_width=True):
                st.session_state.datos_cliente['objetivo'] = titulo
                st.rerun()
            if n == 0:
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    
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
