"""
PASO 1 - Datos del cliente (nombre, email, teléfono, divisa, capital).
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)
import inspect


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
            c_pref, c_num = st.columns([0.6, 2])
            with c_pref:
                # Búsqueda por texto exacto: «+44» muestra solo los países con +44 y
                # «reino» muestra Reino Unido (en versiones antiguas de Streamlit no existe
                # esta opción y se usa la búsqueda por defecto)
                busqueda = ({"filter_mode": "contains"}
                            if "filter_mode" in inspect.signature(st.selectbox).parameters else {})
                pais_tel = st.selectbox(
                    "País del teléfono",
                    opciones_prefijo,
                    index=_indice(opciones_prefijo, prefijo_guardado) or 0,
                    key="select_prefijo",
                    placeholder="Buscar",
                    label_visibility="collapsed",
                    **busqueda
                )
            pais_fila = PREFIJOS_TELEFONO[opciones_prefijo.index(pais_tel)] if pais_tel else PREFIJOS_TELEFONO[0]
            # Con el país ya elegido, la casilla solo muestra las iniciales y el prefijo:
            # «ESP (+34)»; en el móvil, la bandera y el prefijo: «🇪🇸 (+34)» (en Windows las
            # banderas no se ven bien). El nombre del país aparece en el desplegable al buscar.
            st.markdown(f"""<style>
                .st-key-select_prefijo [data-testid="stSelectbox"] {{ position: relative; }}
                .st-key-select_prefijo:not(:focus-within) input {{ color: transparent !important; }}
                .st-key-select_prefijo:not(:focus-within) [data-testid="stSelectbox"]::after {{
                    content: "{pais_fila[4]} ({pais_fila[2]})"; position: absolute; left: 9px; top: 50%;
                    transform: translateY(-50%); pointer-events: none; font-size: 14px;
                }}
                @media (max-width: 640px) {{
                    .st-key-select_prefijo:not(:focus-within) [data-testid="stSelectbox"]::after {{
                        font-size: 16px; content: "{pais_fila[0]} ({pais_fila[2]})";
                    }}
                }}
                </style>""", unsafe_allow_html=True)
            with c_num:
                numero_tel = st.text_input(
                    "Número de teléfono",
                    value=st.session_state.datos_cliente.get('telefono_numero', ''),
                    placeholder=ejemplo_telefono(pais_fila),   # ejemplo con el formato del país
                    key="input_telefono",
                    label_visibility="collapsed"
                )
            # Al tocar el desplegable del país se vacía la casilla: lo que escribas
            # sustituye al país anterior en vez de meterse en medio. Si no escribes nada
            # y sales, se mantiene el país que había.
            with st.container(key="js_prefijo"):
                _script = """
                <script>
                (function () {
                    const doc = window.parent.document;
                    if (doc.__prefijoVacia) return;
                    doc.__prefijoVacia = true;
                    const win = window.parent;
                    const fijar = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value').set;
                    const vaciar = (input) => {
                        if (!input || !input.value) return;
                        fijar.call(input, '');
                        input.dispatchEvent(new win.Event('input', { bubbles: true }));
                    };
                    // Solo cuando la persona toca la casilla (no cuando Streamlit le
                    // devuelve el foco tras elegir un país)
                    let tocado = false;
                    doc.addEventListener('pointerdown', (e) => {
                        const caja = e.target.closest && e.target.closest('.st-key-select_prefijo');
                        if (!caja) return;
                        const input = caja.querySelector('input');
                        if (doc.activeElement === input) setTimeout(() => vaciar(input), 0);
                        else tocado = true;
                    }, true);
                    // Al elegir un país de la lista se quita el foco de la casilla, para
                    // que vuelva a verse solo el prefijo
                    doc.addEventListener('click', (e) => {
                        if (!e.target.closest || !e.target.closest('[role="option"]')) return;
                        const input = doc.querySelector('.st-key-select_prefijo input');
                        if (input && doc.activeElement === input) {
                            setTimeout(() => input.blur(), 80); setTimeout(() => input.blur(), 400);
                        }
                    }, true);
                    doc.addEventListener('focusin', (e) => {
                        const input = e.target;
                        if (!tocado || !input.matches || !input.matches('.st-key-select_prefijo input')) return;
                        tocado = false;
                        vaciar(input);
                    }, true);
                })();
                </script>
                """
                if hasattr(st, "iframe"):
                    st.iframe(_script, height=1)
                else:
                    import streamlit.components.v1 as _componentes
                    _componentes.html(_script, height=0)
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
            # Teléfono: se comprueba con el formato del país elegido (España 9 cifras, México 10…)
            telefono_valido, telefono_completo, cifras_pais = validar_telefono(numero_tel, pais_fila)
            if not (nombre and email and numero_tel and divisa is not None and capital is not None
                    and ya_inversor is not None):
                st.error("Por favor completa todos los campos marcados con *")
            elif not email_valido:
                st.error("Revisa el email: no parece una dirección válida.")
            elif not telefono_valido:
                st.error(f"Revisa el teléfono: no parece un número válido de {pais_fila[3]}"
                         + (f" (allí los números tienen {cifras_pais} cifras)" if cifras_pais else "")
                         + ". Escríbelo sin el prefijo, que se elige a la izquierda.")
            else:
                anteriores = st.session_state.datos_cliente
                nuevos = {
                    'nombre': nombre.strip(),
                    'email': email.strip(),
                    'telefono': telefono_completo,   # con prefijo, p. ej. «+34 600 12 34 56» (así se guarda en los leads)
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
