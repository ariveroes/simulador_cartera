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
        telefono = st.text_input(
            "¿Cuál es tu número de teléfono? *",
            value=st.session_state.datos_cliente.get('telefono', ''),
            placeholder="Ej.: +34 600 123 456",
            key="input_telefono"
        )
        divisa = st.selectbox(
            "¿En qué divisa prefieres invertir? *",
            ["EUR", "USD"],
            index=_indice(["EUR", "USD"], st.session_state.datos_cliente.get('divisa')),
            placeholder="Selecciona una divisa",
            key="select_divisa"
        )
    
    with col2:
        ya_inversor = st.selectbox(
            "¿Eres ya inversor en Reental? *",
            ["No", "Sí"],
            index=_indice(["No", "Sí"], st.session_state.datos_cliente.get('ya_inversor')),
            placeholder="Selecciona una opción",
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
            digitos_tel = re.sub(r"\D", "", telefono or "")
            telefono_valido = (bool(re.match(r"^[\d\s().+-]+$", (telefono or "").strip()))
                               and 6 <= len(digitos_tel) <= 15)
            if not (nombre and email and telefono and divisa is not None and capital is not None
                    and ya_inversor is not None):
                st.error("Por favor completa todos los campos marcados con *")
            elif not email_valido:
                st.error("Revisa el email: no parece una dirección válida.")
            elif not telefono_valido:
                st.error("Revisa el teléfono: escribe solo números (puedes empezar por + y el prefijo del país).")
            else:
                anteriores = st.session_state.datos_cliente
                nuevos = {
                    'nombre': nombre.strip(),
                    'email': email.strip(),
                    'telefono': telefono.strip(),
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
