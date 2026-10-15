"""
PASO 2 - Estatus RNT (Reentel, ReentelPro, SuperReentel).
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    st.markdown("## Paso 2: ¿Qué estatus RNT quieres considerar?")
    st.markdown("")
    
    estatus_seleccionado = st.session_state.datos_cliente.get('estatus', None)
    
    OPCIONES_ESTATUS = [
        ('SuperReentel', 'btn_super', "Quiero conseguir hasta un <b>50 % más de rentabilidad</b> en mis "
                                      "inversiones inmobiliarias y <b>acceso prioritario</b> a los proyectos."),
        ('ReentelPro', 'btn_pro', "Quiero conseguir hasta un <b>25 % más de rentabilidad</b> en mis inversiones "
                                  "inmobiliarias y acceder a los proyectos tras los SuperReentel."),
        ('Reentel', 'btn_reen', "Por ahora no quiero estatus."),
    ]
    for col, (nombre_est, clave, texto) in zip(st.columns(3), OPCIONES_ESTATUS):
        elegido = estatus_seleccionado == nombre_est
        with col:
            # HTML en una sola pieza, sin líneas en blanco ni sangría: si no, Markdown
            # lo interpreta como bloque de código y se ve el HTML en vez de la tarjeta
            marca = (f"<span style='font-size:12px; font-weight:700; color:{COLOR_AMBAR_OSCURO};'>✓ Elegido</span>"
                     if elegido else "")
            st.markdown(
                f"<div style='border:{'2px' if elegido else '1px'} solid {COLOR_AMBAR if elegido else COLOR_BORDE}; "
                f"border-radius:14px; padding:18px 20px; min-height:170px; "
                f"background-color:{COLOR_AMBAR_CLARO if elegido else '#ffffff'};'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;'>"
                f"<span style='color:{COLOR_NAVY}; font-weight:800; font-size:17px;'>{nombre_est}</span>{marca}</div>"
                f"<div style='color:{COLOR_NAVY}; font-size:15px; line-height:1.55;'>{texto}</div></div>",
                unsafe_allow_html=True)
            # El elegido lleva el botón relleno; los demás, de contorno
            if st.button("✓ Elegido" if elegido else f"Elegir {nombre_est}",
                         key=f"{clave}{'' if elegido else '_sec'}", use_container_width=True):
                st.session_state.datos_cliente['estatus'] = nombre_est
                st.rerun()
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    # ========== BOTÓN "¿QUIERES MÁS INFO?" ==========
    st.markdown(f"""
    <a href="https://api.leadconnectorhq.com/widget/booking/kAzM5NH9hFxtc88sTQKy" target="_blank" style="text-decoration: none; color: inherit;">
        <div style="background-color: {COLOR_AMBAR_CLARO}; border: 2px solid {COLOR_AMBAR}; color: {COLOR_NAVY}; border-radius: 12px; padding: 15px; font-size: 15px; cursor: pointer; text-align: center;">
            💡 ¿Quieres más información sobre <b> qué es el estatus RNT</b> y cómo puede ayudarte a <b>maximizar tu rentabilidad inmobiliaria</b>? Agenda con nuestro equipo de Onboarding <b style="color: {COLOR_AMBAR_OSCURO};">aquí</b>.
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
