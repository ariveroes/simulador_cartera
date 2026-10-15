"""
PASO 1 - Datos del cliente (nombre, email, teléfono, divisa, capital).
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    st.markdown("## Paso 1: Cuéntanos sobre ti")
    st.markdown("Información básica para personalizar tu simulación")
    st.markdown("")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input(
            "¿Cómo te llamas? *",
            value=st.session_state.datos_cliente.get('nombre', ''),
            key="input_nombre"
        )
        email = st.text_input(
            "¿Cuál es tu email? *",
            value=st.session_state.datos_cliente.get('email', ''),
            key="input_email"
        )
        # Teléfono: país (bandera y prefijo, España por defecto) + número
        opciones_prefijo = [etiqueta_prefijo(p) for p in PREFIJOS_TELEFONO]
        prefijo_guardado = st.session_state.datos_cliente.get('telefono_pais')
        with st.container(key="telefono"):
            # Etiqueta común encima de las dos casillas (prefijo y número), con el mismo
            # aspecto que las etiquetas de Streamlit
            st.markdown("<div class='etiqueta-campo'>¿Cuál es tu número de teléfono? *</div>",
                        unsafe_allow_html=True)
            c_pref, c_num = st.columns([1.3, 2])
            with c_pref:
                pais_tel = st.selectbox(
                    "País del teléfono",
                    opciones_prefijo,
                    index=_indice(opciones_prefijo, prefijo_guardado) or 0,
                    key="select_prefijo",
                    label_visibility="collapsed"
                )
            with c_num:
                numero_tel = st.text_input(
                    "Número de teléfono",
                    value=st.session_state.datos_cliente.get('telefono_numero', ''),
                    placeholder="600 123 456",
                    key="input_telefono",
                    label_visibility="collapsed"
                )
        divisa = st.selectbox(
            "¿En qué divisa prefieres invertir? *",
            ["EUR", "USD"],
            index=_indice(["EUR", "USD"], st.session_state.datos_cliente.get('divisa')) or 0,
            key="select_divisa"
        )
    
    with col2:
        ya_inversor = st.selectbox(
            "¿Eres ya inversor en Reental? *",
            ["No", "Sí"],
            index=_indice(["No", "Sí"], st.session_state.datos_cliente.get('ya_inversor')) or 0,
            key="select_inversor"
        )
        capital = st.selectbox(
            "¿Cuánto capital tienes disponible para invertir? *",
            list(CAPITAL_SIMULADO.keys()),
            index=_indice(list(CAPITAL_SIMULADO.keys()), st.session_state.datos_cliente.get('capital')),
            placeholder="Selecciona tu rango de capital",
            key="select_capital"
        )
    
    st.markdown("")
    st.markdown("---")
    st.markdown("")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col3:
        if st.button("Siguiente >", use_container_width=True, key="btn_paso1_next"):
            email_valido = bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (email or "").strip()))
            digitos_tel = re.sub(r"\D", "", numero_tel or "")
            telefono_valido = (bool(re.match(r"^[\d\s().-]+$", (numero_tel or "").strip()))
                               and 6 <= len(digitos_tel) <= 14)
            prefijo = PREFIJOS_TELEFONO[opciones_prefijo.index(pais_tel)][2] if pais_tel else ""
            if not (nombre and email and numero_tel and divisa is not None and capital is not None
                    and ya_inversor is not None):
                st.error("Por favor completa todos los campos marcados con *")
            elif not email_valido:
                st.error("Revisa el email: no parece una dirección válida.")
            elif not telefono_valido:
                st.error("Revisa el teléfono: escribe solo el número, sin el prefijo (lo eliges a la izquierda).")
            else:
                anteriores = st.session_state.datos_cliente
                nuevos = {
                    'nombre': nombre.strip(),
                    'email': email.strip(),
                    'telefono': f"{prefijo} {numero_tel.strip()}",   # con prefijo (así se guarda en los leads)
                    'telefono_pais': pais_tel,
                    'telefono_numero': numero_tel.strip(),
                    'divisa': divisa,
                    'ya_inversor': ya_inversor,
                    'capital': capital,
                }
                # Se conservan las respuestas de los pasos siguientes; el capital
                # ajustado solo vale mientras no se cambie el rango ni la divisa.
                if anteriores.get('capital') != capital or anteriores.get('divisa') != divisa:
                    anteriores.pop('capital_ajustado', None)
                st.session_state.datos_cliente = {**anteriores, **nuevos}
                # Guardar el lead (si falla, la app sigue igual)
                if 'lead_id' not in st.session_state:
                    st.session_state.lead_id = uuid.uuid4().hex[:10]
                leads.guardar(st.session_state.lead_id, "Datos de contacto", st.session_state.datos_cliente)
                st.session_state.paso_actual = 2
                st.rerun()
