"""
PASO 4 - Proyectos disponibles y reparto de la cartera.
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    st.markdown("## Paso 4: Crea tu cartera de inversión")
    st.markdown("Selecciona aquellos proyectos que quieras incluir en tu cartera")
    st.markdown("")
    
    if st.session_state.df_proyectos is not None and len(st.session_state.df_proyectos) > 0:
        df_proyectos_todos = st.session_state.df_proyectos.copy()

        # Obtener parámetros
        mercados_seleccionados = st.session_state.datos_cliente.get('mercados', [])
        objetivo = st.session_state.datos_cliente.get('objetivo', '') or ''
        estatus = st.session_state.datos_cliente.get('estatus', None)
        estatus_p4 = estatus or 'Reentel'
        ingresos_pasivos = 'ingresos' in objetivo.lower()

        # ========== PROYECTOS DISPONIBLES (UNA SOLA LISTA) ==========
        # Todo lo que se puede comprar hoy, sin distinguir de dónde sale:
        #  - los proyectos que se están financiando, al precio de emisión;
        #  - los que tienen tokens a la venta, a su precio más bajo (salvo los que
        #    terminan en menos de MESES_MINIMOS_HASTA_FIN meses).
        ofertas_por_proy = agrupar_ofertas_por_proyecto(cargar_todas_ofertas_secundario(df_proyectos_todos))

        precio_por_id = {}      # precio de compra de un token, en la divisa del proyecto
        origen_por_id = {}      # 'Emisión' o 'Mercado' (solo para uso interno)
        filas_disponibles = []
        for _, row in df_proyectos_todos.iterrows():
            pid = row.get('ID')
            if pid is None or str(pid).strip() == '' or (isinstance(pid, float) and pid != pid):
                continue
            div_proy = divisa_proyecto(row)
            if str(row.get('ESTADO', '')).upper() == 'FINANCIÁNDOSE':
                precio, origen = _num(row.get('Precio Emisión', 0)), 'Emisión'
            else:
                ofertas = (ofertas_por_proy.get(str(pid).lower())
                           or ofertas_por_proy.get(str(row.get('Token Address', '')).lower()) or [])
                precios = [convertir_divisa(_num(o.get('precio_venta'), 0.0), o.get('divisa', 'USD'), div_proy)
                           for o in ofertas if _num(o.get('precio_venta'), 0.0) > 0]
                if not precios or termina_pronto(row.get('fecha_fin_calculo')):
                    continue
                precio, origen = min(precios), 'Mercado'
            if not precio or precio <= 0:
                continue
            precio_por_id[pid] = precio
            origen_por_id[pid] = origen
            filas_disponibles.append(row)

        df_disponibles = pd.DataFrame(filas_disponibles)
        fuera_de_mercado = 0
        if len(df_disponibles) > 0 and mercados_seleccionados:
            en_mercado = df_disponibles['Ubicación'].isin(mercados_seleccionados)
            fuera_de_mercado = int((~en_mercado).sum())
            df_disponibles = df_disponibles[en_mercado]

        st.markdown("### Proyectos disponibles según tus preferencias de inversión")
        if ingresos_pasivos:
            criterio = ("Primero los que pagan rentas mensuales, después los trimestrales y por último los que "
                        "pagan al final; dentro de cada grupo, de mayor a menor rentabilidad anualizada.")
        else:
            criterio = "De mayor a menor rentabilidad anualizada."

        ids_seleccionados = []
        if len(df_disponibles) > 0:
            st.caption(f"Ordenados según tu objetivo de inversión. {criterio}")
            df_display = preparar_proyectos_para_paso4(df_disponibles, estatus)
            df_display = aplicar_rentabilidad_ajustada(df_display, df_disponibles, estatus, precio_por_id)
            simbolo_por_id = {row['ID']: ('$' if divisa_proyecto(row) == 'USD' else '€')
                              for _, row in df_disponibles.iterrows()}
            df_display['Precio'] = df_display['ID'].map(
                lambda pid: f"{es(precio_por_id[pid], 2)} {simbolo_por_id.get(pid, '€')}" if pid in precio_por_id else "-")
            # Ranking según las preferencias
            df_display = df_display.sort_values('Rentabilidad Anualizada', ascending=False,
                                                na_position='last', kind='stable')
            if ingresos_pasivos:
                df_display = priorizar_rentas(df_display)
            # Enlace al dossier comercial (columna CQ del Master)
            if 'dossier' in df_disponibles.columns:
                dossier_por_id = dict(zip(df_disponibles['ID'], df_disponibles['dossier']))
                df_display['Dossier'] = df_display['ID'].map(dossier_por_id).fillna('')
            ids_seleccionados = tabla_seleccionable(df_display, "tabla_proyectos")
            if fuera_de_mercado:
                plural = 's' if fuera_de_mercado != 1 else ''
                st.caption(f"Hay {fuera_de_mercado} proyecto{plural} más disponible{plural} en otros "
                           "mercados. Puedes añadir esos mercados en el Paso 2.")
        elif fuera_de_mercado:
            st.info(f"Ahora mismo no hay proyectos disponibles en los mercados que has elegido. Hay "
                    f"{fuera_de_mercado} en otros mercados: puedes añadirlos en el Paso 2.")
        else:
            st.info("Ahora mismo no hay proyectos disponibles.")

        # ========== GUARDAR SELECCIÓN ==========
        ids_seleccionados = list(dict.fromkeys(ids_seleccionados))  # sin duplicados, en orden

        for pid in list(st.session_state.cartera_selecciones.keys()):
            st.session_state.cartera_selecciones[pid]['seleccionado'] = pid in ids_seleccionados
        for pid in ids_seleccionados:
            if pid not in st.session_state.cartera_selecciones:
                st.session_state.cartera_selecciones[pid] = {'seleccionado': True, 'porcentaje': 0}

        filas_por_id = {row['ID']: row for _, row in df_proyectos_todos.iterrows()}

        # ========== CONSTRUIR CARTERA ==========
        st.markdown("---")
        st.markdown("### Construye tu cartera")

        MODOS_REPARTO = ["Por igual", "Por % de mi cartera"]
        if st.session_state.get('modo_reparto') not in MODOS_REPARTO:
            st.session_state.modo_reparto = "Por igual"

        proyectos_seleccionados = []
        divisa_cliente_p4 = (st.session_state.datos_cliente.get('divisa') or 'EUR').upper()
        simbolo_cliente_p4 = '€' if divisa_cliente_p4 == 'EUR' else '$'
        ids_validos = [pid for pid in ids_seleccionados if pid in filas_por_id and pid in precio_por_id]
        tokens_compra = st.session_state.tokens_compra
        for pid in ids_validos:
            tokens_compra.setdefault(pid, 0.0)

        def _simbolo(div):
            return '$' if str(div).upper() in ('USD', 'USDT', '$') else '€'

        def _etiqueta(o):
            texto = f"{es(o['precio'], 2)} {_simbolo(o['divisa'])}"
            if _simbolo(o['divisa']) != simbolo_cliente_p4:
                texto += (f" (aprox. {es(convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4), 2)} "
                          f"{simbolo_cliente_p4})")
            return texto

        # Precio de compra de cada proyecto elegido (el de la tabla)
        opcion_por_id = {pid: {'tipo': origen_por_id.get(pid, 'Emisión'), 'precio': precio_por_id[pid],
                               'divisa': divisa_proyecto(filas_por_id[pid]), 'n_tokens': None}
                         for pid in ids_validos}

        def _oferta(pid):
            return opcion_por_id[pid]

        def _precio_cliente(o):
            """Precio de un token en la divisa del cliente."""
            return convertir_divisa(o['precio'], o['divisa'], divisa_cliente_p4)

        def _olvidar_widgets(pid):
            """Las casillas se vuelven a rellenar desde tokens_compra en la siguiente vuelta."""
            st.session_state.pop(f"pct_{pid}", None)

        # ----- Estado de partida -----
        # El importe a invertir es el TOTAL: incluye lo que cuesta el estatus. Lo que
        # se reparte entre los proyectos es lo que queda después de descontarlo.
        importe_capital_p4 = importe_cliente(st.session_state.datos_cliente)
        coste_estatus_p4 = coste_estatus_cliente(st.session_state.datos_cliente)
        importe_total_p4 = max(0.0, importe_capital_p4 - coste_estatus_p4)   # para inmuebles
        def _texto_importe(valor):
            """Importe con separador de miles y el símbolo dentro de la casilla: «50.000 €»."""
            return f"{es(valor, 0)} {simbolo_cliente_p4}"
        
        def _leer_importe(texto):
            """Convierte lo escrito («50.000 €», «50000», «50,000 $»…) en número. None si no se entiende."""
            limpio = re.sub(r"[^\d.,]", "", str(texto or ""))
            if not limpio:
                return None
            if _formato_euro():
                limpio = limpio.replace(".", "").replace(",", ".")
            else:
                limpio = limpio.replace(",", "")
            try:
                return float(limpio)
            except ValueError:
                return None
        
        if 'input_importe' not in st.session_state:
            st.session_state.input_importe = _texto_importe(importe_capital_p4)
        modo = st.session_state.modo_reparto
        estatus_p4 = st.session_state.datos_cliente.get('estatus') or 'Reentel'

        def _cambiar_importe():
            anterior = importe_cliente(st.session_state.datos_cliente)
            nuevo = _leer_importe(st.session_state.input_importe)
            if nuevo is None or nuevo <= 0:
                # No se entiende lo escrito: se deja el importe que había
                st.session_state.input_importe = _texto_importe(anterior)
                return
            st.session_state.datos_cliente['capital_ajustado'] = nuevo
            st.session_state.input_importe = _texto_importe(nuevo)
            # Repartiendo por %, se mantienen los % y cambian los tokens (sobre lo que va a inmuebles)
            anterior_inm = max(0.0, anterior - coste_estatus_p4)
            nuevo_inm = max(0.0, nuevo - coste_estatus_p4)
            if st.session_state.modo_reparto == "Por % de mi cartera" and anterior_inm:
                for p in list(st.session_state.tokens_compra):
                    st.session_state.tokens_compra[p] *= nuevo_inm / anterior_inm
                    _olvidar_widgets(p)

        def _cambiar_modo():
            valor = st.session_state.get("selector_modo")
            if valor in MODOS_REPARTO:          # si se deselecciona, se mantiene el anterior
                st.session_state.modo_reparto = valor
            for p in list(st.session_state.tokens_compra):
                _olvidar_widgets(p)

        # Reparto por igual: el mismo importe en cada proyecto. También se usa como
        # punto de partida en «Por %» si todos los proyectos están a 0.
        todos_a_cero = all(_num(tokens_compra.get(p), 0.0) <= 0 for p in ids_validos)
        if (modo == "Por igual" or todos_a_cero) and ids_validos and importe_total_p4 > 0:
            parte = importe_total_p4 / len(ids_validos)
            for p in ids_validos:
                precio = _precio_cliente(_oferta(p))
                tokens_compra[p] = parte / precio if precio else 0.0
                if modo != "Por igual":
                    _olvidar_widgets(p)

        # ----- Cálculos a partir de los tokens -----
        filas_calc = []
        importe_repartido = 0.0
        for pid in ids_validos:
            o = _oferta(pid)
            tokens = max(0.0, _num(tokens_compra.get(pid), 0.0))
            importe = tokens * _precio_cliente(o)
            importe_repartido += importe
            row = filas_por_id[pid]
            precio_proy = convertir_divisa(o['precio'], o['divisa'], divisa_proyecto(row))
            rent = rentabilidad_ajustada(row, estatus_p4, precio_proy)
            filas_calc.append((pid, o, tokens, importe, rent))
        pendiente = importe_total_p4 - importe_repartido
        tolerancia = max(1.0, importe_total_p4 * 0.0005)
        tokens_totales = sum(f[2] for f in filas_calc)
        rent_media = (sum((f[4]['anual'] or 0.0) * f[3] for f in filas_calc) / importe_repartido
                      if importe_repartido > 0 else 0.0)
        rent_total_media = (sum((f[4]['total'] or 0.0) * f[3] for f in filas_calc) / importe_repartido
                            if importe_repartido > 0 else 0.0)


        # ----- Estilos de esta sección -----
        st.markdown(f"""
        <style>
        [class*="st-key-kpi_"] {{
            background: #ffffff; border: 1px solid {COLOR_BORDE} !important; border-radius: 12px;
            padding: 12px 14px 10px 14px; min-height: 118px;
        }}
        [class*="st-key-kpi_"] div[data-testid="stVerticalBlock"] {{ gap: 0.15rem; }}
        .kpi-titulo {{ font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.5px; }}
        .kpi-valor {{ font-size: 26px; font-weight: 800; color: {COLOR_NAVY}; line-height: 1.25; }}
        .kpi-sub {{ font-size: 12px; color: {COLOR_GRIS}; }}
        .st-key-kpi_importe div[data-baseweb="input"] {{ min-height: 38px; }}
        .st-key-kpi_importe input {{ font-size: 22px; font-weight: 800; color: {COLOR_NAVY}; padding: 2px 8px; }}
        .st-key-kpi_pendiente button {{ padding: 2px 10px; min-height: 28px; font-size: 12px; }}
        /* Repartido + estatus y las dos rentabilidades: dos tarjetas una encima de otra.
           Importe y pendiente ocupan toda la altura de la franja. */
        [class*="st-key-kpipar_"] {{ gap: 0.75rem !important; height: 100%; }}
        [class*="st-key-kpipar_"] > * {{ flex: 1 1 0; }}
        [class*="st-key-kpipar_"] [class*="st-key-kpi_"] {{ min-height: 0; height: 100%; }}
        [data-testid="stHorizontalBlock"]:has(.st-key-kpi_importe) {{ align-items: stretch; }}
        [data-testid="stHorizontalBlock"]:has(.st-key-kpi_importe) > [data-testid="stColumn"] > div,
        .st-key-kpi_importe, .st-key-kpi_pendiente {{ height: 100%; }}
        [data-testid="stLayoutWrapper"]:has(> .st-key-kpi_importe),
        [data-testid="stLayoutWrapper"]:has(> .st-key-kpi_pendiente),
        [data-testid="stLayoutWrapper"]:has(> [class*="st-key-kpipar_"]) {{ flex: 1 1 auto; height: 100%; }}
        .st-key-js_enfocar {{ height: 0 !important; overflow: hidden; margin: 0 !important; }}
        /* Aviso cuando el importe no llega para el estatus */
        .st-key-aviso_estatus {{
            background: {COLOR_AMBAR_CLARO}; border: 1px solid #f6c56b; border-radius: 12px;
            padding: 14px 18px; margin: 14px 0 4px 0; gap: 0.6rem;
        }}
        .st-key-aviso_estatus p {{ margin-bottom: 0; }}
        .st-key-aviso_estatus [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}

        .st-key-tabla_cartera {{
            background: #ffffff; border: 1px solid {COLOR_BORDE}; border-radius: 12px; padding: 4px 6px;
        }}
        .st-key-tabla_cartera div[data-testid="stVerticalBlock"] {{ gap: 0; }}
        .st-key-tabla_cartera div[data-testid="stHorizontalBlock"] {{ gap: 0.75rem; }}
        .st-key-tabla_cartera p {{ margin-bottom: 0; }}
        .st-key-tabla_cartera [data-testid="stMarkdownContainer"],
        [class*="st-key-kpi_"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
        .nota-gris {{ display: block; margin-top: 2px; }}
        [class*="st-key-fila_"] {{ padding: 8px 10px; border-radius: 8px; }}
        [class*="st-key-fila_par_"] {{ background: {COLOR_FONDO}; }}
        .st-key-tabla_cartera div[data-baseweb="input"],
        .st-key-tabla_cartera div[data-baseweb="select"] > div {{ min-height: 32px; }}
        .st-key-tabla_cartera input {{ padding: 4px 8px; }}
        .st-key-tabla_cartera button[data-testid="stNumberInputStepUp"],
        .st-key-tabla_cartera button[data-testid="stNumberInputStepDown"] {{ display: none; }}
        .st-key-tabla_cartera .stButton button {{ padding: 2px 10px; min-height: 32px; }}
        .fila-cab {{ font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.4px; padding: 6px 10px 2px 10px; }}
        .proy-nombre {{ font-weight: 700; color: {COLOR_NAVY}; }}
        .proy-sub, .nota-gris {{ font-size: 12px; color: {COLOR_GRIS}; }}
        .barra-pct {{ background: #f1f3f5; border-radius: 4px; height: 8px; width: 100%; }}
        .barra-pct > div {{ background: {COLOR_AMBAR}; border-radius: 4px; height: 8px; }}

        @media (max-width: 640px) {{
            /* Indicadores: importe a todo el ancho; repartido + estatus y las dos
               rentabilidades de dos en dos; pendiente a todo el ancho */
            [data-testid="stHorizontalBlock"]:has(.st-key-kpi_importe) {{ flex-wrap: wrap; gap: 0.5rem; }}
            [data-testid="stHorizontalBlock"]:has(.st-key-kpi_importe) > [data-testid="stColumn"] {{
                flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important;
            }}
            [class*="st-key-kpipar_"] {{ flex-direction: row !important; gap: 0.5rem !important; }}
            [class*="st-key-kpipar_"] > * {{ flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }}
            [class*="st-key-kpi_"] {{ min-height: 0; padding: 10px 10px 8px 10px; }}
            .kpi-valor {{ font-size: 17px; }}
            .kpi-titulo {{ font-size: 10.5px; letter-spacing: 0.2px; }}
            .kpi-sub {{ font-size: 11px; }}
            .st-key-kpi_pendiente button {{ font-size: 11px; padding: 2px 6px; }}

            /* Filas de proyectos: sin cabecera (cada dato lleva su etiqueta) */
            .st-key-cab_cartera {{ display: none; }}
            [class*="st-key-fila_"] {{ padding: 12px 8px; }}
            [class*="st-key-fila_"] [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; gap: 0.35rem 0.6rem; }}
            [class*="st-key-fila_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
                flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important;
            }}
            /* Importe (o %) y reparto, uno al lado del otro */
            [class*="st-key-fila_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3),
            [class*="st-key-fila_"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {{
                flex: 1 1 calc(50% - 0.5rem) !important; min-width: calc(50% - 0.5rem) !important;
                width: calc(50% - 0.5rem) !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)

        def _kpi(clave):
            try:
                return st.container(key=f"kpi_{clave}")
            except TypeError:
                return st.container(border=True)

        # ----- 1) Franja de indicadores -----
        # Ordenador: importe | repartido + estatus | rent. anualizada + total | pendiente.
        # Móvil: importe; repartido y estatus; las dos rentabilidades; pendiente.
        def _kpi_par(clave):
            try:
                return st.container(key=f"kpipar_{clave}")
            except TypeError:
                return st.container()

        datos_p4 = st.session_state.datos_cliente
        divisa_datos_p4 = datos_p4.get('divisa') or 'EUR'

        def _coste_de(est):
            return coste_estatus_cliente({'estatus': est, 'divisa': divisa_datos_p4})

        def _subir_importe():
            st.session_state.resaltar_importe = True
            st.session_state.enfocar_importe = True

        def _cambiar_estatus(nuevo):
            st.session_state.datos_cliente['estatus'] = nuevo
            st.session_state.pop('resaltar_importe', None)
            for p in list(st.session_state.tokens_compra):
                _olvidar_widgets(p)

        k1, k2, k3, k4 = st.columns([1.25, 1, 1, 1])
        with k1, _kpi("importe"):
            st.markdown("<div class='kpi-titulo'>IMPORTE A INVERTIR</div>", unsafe_allow_html=True)
            st.text_input("Importe a invertir", key="input_importe", on_change=_cambiar_importe,
                          label_visibility="collapsed")
            importe_capital_p4 = importe_cliente(st.session_state.datos_cliente)
            importe_total_p4 = max(0.0, importe_capital_p4 - coste_estatus_p4)
            no_llega = coste_estatus_p4 > 0 and importe_total_p4 <= 0
            if not no_llega:
                st.session_state.pop('resaltar_importe', None)
            if no_llega and st.session_state.get('resaltar_importe'):
                # «Subir importe de inversión»: la casilla se marca en rojo hasta que llegue
                st.markdown(
                    f"<style>.st-key-kpi_importe {{ border-color: {COLOR_ROJO} !important; "
                    f"background: #fef2f2 !important; }} .st-key-kpi_importe div[data-baseweb='input'] "
                    f"{{ border: 1.5px solid {COLOR_ROJO} !important; }}</style>"
                    + html_seguro(
                        f"<div class='kpi-sub' style='color:{COLOR_ROJO}; font-weight:700; margin-top:2px;'>"
                        f"Necesitas más de {es(coste_estatus_p4, 0)} {simbolo_cliente_p4} para el estatus "
                        f"{estatus_p4}</div>"), unsafe_allow_html=True)
            elif coste_estatus_p4 > 0:
                st.markdown(html_seguro(
                    f"<div class='kpi-sub' style='color:{COLOR_NAVY}; margin-top:2px;'>"
                    f"<b>{es(importe_total_p4, 0)} {simbolo_cliente_p4}</b> a inmuebles y "
                    f"<b>{es(coste_estatus_p4, 0)} {simbolo_cliente_p4}</b> a tu estatus {estatus_p4} "
                    f"(siguen siendo tuyos y también generan rendimiento)</div>"), unsafe_allow_html=True)
            rango = st.session_state.datos_cliente.get('capital', '')
            st.markdown(html_seguro(f"<div class='kpi-sub'>En el Paso 1 elegiste «{rango}». Te proponemos el "
                                    "punto medio de ese rango; puedes cambiarlo por el importe exacto que "
                                    "quieras invertir.</div>"), unsafe_allow_html=True)

        with k2, _kpi_par("reparto"):
            with _kpi("repartido"):
                st.markdown(html_seguro(
                    f"<div class='kpi-titulo'>REPARTIDO</div>"
                    f"<div class='kpi-valor'>{'—' if no_llega else f'{es(importe_repartido, 0)} {simbolo_cliente_p4}'}</div>"
                    f"<div class='kpi-sub'>{len(ids_validos)} "
                    f"proyecto{'s' if len(ids_validos) != 1 else ''}</div>"), unsafe_allow_html=True)
            with _kpi("estatus"):
                if coste_estatus_p4 > 0:
                    valor_est = f"{es(coste_estatus_p4, 0)} {simbolo_cliente_p4}"
                    sub_est = f"{estatus_p4} · a plazo fijo durante 2 años"
                else:
                    valor_est, sub_est = "—", "Sin estatus (Reentel)"
                st.markdown(html_seguro(
                    f"<div class='kpi-titulo'>EN ESTATUS</div>"
                    f"<div class='kpi-valor'>{valor_est}</div>"
                    f"<div class='kpi-sub'>{sub_est}</div>"), unsafe_allow_html=True)

        with k3, _kpi_par("rentab"):
            hay_reparto = importe_repartido > 0
            with _kpi("rentabilidad"):
                st.markdown(html_seguro(
                    f"<div class='kpi-titulo'>RENT. ANUALIZADA</div>"
                    f"<div class='kpi-valor'>{es(rent_media, 2) + ' %' if hay_reparto else '—'}</div>"
                    f"<div class='kpi-sub'>estimada · {estatus_p4} · al precio de compra</div>"),
                    unsafe_allow_html=True)
            with _kpi("rent_total"):
                st.markdown(html_seguro(
                    f"<div class='kpi-titulo'>RENT. TOTAL</div>"
                    f"<div class='kpi-valor'>{es(rent_total_media, 2) + ' %' if hay_reparto else '—'}</div>"
                    f"<div class='kpi-sub'>estimada · {estatus_p4} · hasta el final de cada proyecto</div>"),
                    unsafe_allow_html=True)

        with k4, _kpi("pendiente"):
            if not ids_validos or no_llega:
                titulo, valor, color = "PENDIENTE", "—", COLOR_GRIS_CLARO
            elif abs(pendiente) <= tolerancia:
                titulo, valor, color = "PENDIENTE", "✓ Todo repartido", COLOR_VERDE
            elif pendiente > 0:
                titulo, valor, color = "PENDIENTE", f"{es(pendiente, 0)} {simbolo_cliente_p4}", COLOR_AMBAR_OSCURO
            else:
                titulo, valor, color = "TE HAS PASADO EN", f"{es(-pendiente, 0)} {simbolo_cliente_p4}", COLOR_ROJO
            st.markdown(html_seguro(f"<div class='kpi-titulo'>{titulo}</div>"
                                    f"<div class='kpi-valor' style='color:{color};'>{valor}</div>"),
                        unsafe_allow_html=True)
            if ids_validos and not no_llega and abs(pendiente) > tolerancia and importe_repartido > 0:
                def _usar_repartido(valor):
                    st.session_state.datos_cliente['capital_ajustado'] = valor
                    st.session_state.input_importe = _texto_importe(valor)
                    for p in list(st.session_state.tokens_compra):
                        _olvidar_widgets(p)
                importe_ajustado = importe_repartido + coste_estatus_p4
                st.button(md(f"Usar {es(importe_ajustado, 0)} {simbolo_cliente_p4} como importe"),
                          key="btn_ajustar_capital_sec", on_click=_usar_repartido, args=(importe_ajustado,),
                          help="Cambia el importe a invertir para que coincida con lo que has repartido"
                               + (" más lo que va a tu estatus" if coste_estatus_p4 > 0 else ""))

        # ----- Aviso: el importe no llega para el estatus elegido -----
        if no_llega:
            opciones = [("Subir importe de inversión", "btn_subir_importe_sec", _subir_importe, ())]
            coste_pro = _coste_de('ReentelPro')
            if estatus_p4 == 'SuperReentel' and importe_capital_p4 - coste_pro > 0:
                opciones.append(("Elegir ReentelPro", "btn_elegir_pro_sec", _cambiar_estatus, ('ReentelPro',)))
            opciones.append(("Continuar sin estatus", "btn_sin_estatus_sec", _cambiar_estatus, ('Reentel',)))
            with st.container(key="aviso_estatus"):
                st.markdown(html_seguro(
                    f"<div style='color:{COLOR_NAVY}; font-size:15px;'>Con <b>{es(importe_capital_p4, 0)} "
                    f"{simbolo_cliente_p4}</b> no llega para el estatus <b>{estatus_p4}</b>, que requiere "
                    f"<b>{es(coste_estatus_p4, 0)} {simbolo_cliente_p4}</b>. En este caso, puedes:</div>"),
                    unsafe_allow_html=True)
                cols_aviso = st.columns(len(opciones))
                for col, (texto, clave, accion, args) in zip(cols_aviso, opciones):
                    col.button(texto, key=clave, on_click=accion, args=args, use_container_width=True)

        # Tras pulsar «Subir importe de inversión», el cursor va a la casilla del importe
        if st.session_state.pop('enfocar_importe', False):
            with st.container(key="js_enfocar"):
                _script = """
                <script>
                (function () {
                    const doc = window.parent.document;
                    const ir = () => {
                        const i = doc.querySelector('.st-key-input_importe input');
                        if (!i) return;
                        i.scrollIntoView({block: 'center'}); i.focus(); i.select();
                    };
                    setTimeout(ir, 100); setTimeout(ir, 400);
                })();
                </script>
                """
                if hasattr(st, "iframe"):
                    st.iframe(_script, height=1)
                else:
                    import streamlit.components.v1 as _componentes
                    _componentes.html(_script, height=0)

        # ----- 2) Barra de reparto -----
        if ids_validos and importe_total_p4 > 0:
            base = max(importe_total_p4, importe_repartido)
            tramos = []
            for i, (pid, o, tokens, importe, rent) in enumerate(filas_calc):
                if importe <= 0:
                    continue
                ancho = importe / base * 100
                nombre = str(filas_por_id[pid]['Nombre del proyecto']).replace("'", "&#39;")
                color = PALETA_GRAFICOS[i % len(PALETA_GRAFICOS)]
                texto_color = "#ffffff" if color in ("#1f2937", "#15803d", "#3e4753") else COLOR_NAVY
                etiqueta = nombre if ancho >= 9 else ""
                tramos.append(
                    f"<div title='{nombre}: {es(importe / importe_total_p4 * 100, 1)} %' "
                    f"style='width:{ancho:.3f}%;background:{color};color:{texto_color};"
                    f"overflow:hidden;white-space:nowrap;text-overflow:ellipsis;padding:0 6px;'>{etiqueta}</div>")
            if pendiente > tolerancia:
                ancho = pendiente / base * 100
                tramos.append(f"<div title='Pendiente' style='width:{ancho:.3f}%;background:{COLOR_BORDE};"
                              f"color:{COLOR_GRIS};overflow:hidden;white-space:nowrap;padding:0 6px;'>"
                              f"{'pendiente' if ancho >= 9 else ''}</div>")
            st.markdown(
                "<div style='display:flex;height:26px;border-radius:8px;overflow:hidden;margin:12px 0 4px 0;"
                f"font-size:12px;font-weight:700;line-height:26px;border:1px solid {COLOR_BORDE};"
                f"background:{COLOR_BORDE};'>" + "".join(tramos) + "</div>",
                unsafe_allow_html=True)
            if pendiente < -tolerancia:
                st.markdown(html_seguro(f"<div class='nota-gris' style='color:{COLOR_ROJO};'>Lo repartido supera "
                                        f"tu importe a invertir en {es(-pendiente, 0)} {simbolo_cliente_p4}.</div>"),
                            unsafe_allow_html=True)

        # ----- 3) Modo de reparto (píldoras) -----
        st.markdown("")
        if st.session_state.get('selector_modo') not in MODOS_REPARTO:
            st.session_state.selector_modo = modo
        if hasattr(st, "segmented_control"):
               st.segmented_control("**¿Cómo quieres repartir tu cartera?**", MODOS_REPARTO, key="selector_modo",
                                 on_change=_cambiar_modo)
        else:
            st.radio("¿Cómo quieres repartir tu cartera?", MODOS_REPARTO, horizontal=True,
                     key="selector_modo", on_change=_cambiar_modo)

        # ----- 4) Tabla: una fila por proyecto -----
        if not ids_validos:
            st.info("Marca en la tabla de arriba los proyectos que quieras incluir")
        else:
            def _contenedor(clave):
                try:
                    return st.container(key=clave)
                except TypeError:
                    return st.container()

            def _columnas():
                anchos = [2.8, 2.2, 1.8, 2.6]
                try:
                    return st.columns(anchos, vertical_alignment="center")
                except TypeError:
                    return st.columns(anchos)

            titulo_entrada = "% DE TU CARTERA" if modo == "Por % de mi cartera" else "IMPORTE"

            def _guardar_pct(pid, precio_cliente, importe_total):
                pct = max(0.0, float(st.session_state.get(f"pct_{pid}") or 0.0))
                st.session_state.tokens_compra[pid] = (importe_total * pct / 100 / precio_cliente
                                                       if precio_cliente else 0.0)

            def _dividendo_corto(texto):
                t = str(texto or "").lower()
                partes = []
                if "mensual" in t:
                    partes.append("mensual")
                if "trimestral" in t:
                    partes.append("trimestral")
                if "final" in t:
                    partes.append("al final")
                return " + ".join(partes) if partes else (str(texto) if texto else "")

            try:
                from modules.formateo_datos import _buscar_columna_tipologia
                col_tipo = _buscar_columna_tipologia(df_proyectos_todos)
            except Exception:
                col_tipo = None

            with _contenedor("tabla_cartera"):
                with _contenedor("cab_cartera"):
                    c = _columnas()
                    for col, titulo in zip(c, ["PROYECTO", "PRECIO DE COMPRA", titulo_entrada, "REPARTO"]):
                        col.markdown(f"<div class='fila-cab'>{titulo}</div>", unsafe_allow_html=True)

                for n_fila, (pid, o, tokens, importe, rent) in enumerate(filas_calc):
                    row = filas_por_id[pid]
                    nombre = row['Nombre del proyecto']
                    precio_cli = _precio_cliente(o)
                    pct = importe / importe_total_p4 * 100 if importe_total_p4 else 0.0

                    with _contenedor(f"fila_{'par' if n_fila % 2 else 'impar'}_{n_fila}"):
                        c_nom, c_precio, c_entrada, c_pct = _columnas()

                        # Proyecto + ubicación · dividendo · rentabilidad al precio de compra
                        detalles = [str(row.get('Ubicación', '') or '')]
                        if col_tipo:
                            detalles.append(_dividendo_corto(row.get(col_tipo)))
                        if rent['anual'] is not None:
                            detalles.append(f"{es(rent['anual'], 1)} % anual")
                        c_nom.markdown(f"<div class='proy-nombre'>{nombre}</div>"
                                       f"<div class='proy-sub'>{' · '.join(d for d in detalles if d)}</div>",
                                       unsafe_allow_html=True)

                        # Precio de compra de un token
                        c_precio.markdown("<div class='etq-movil'>PRECIO DE COMPRA</div>"
                                          + html_seguro(_etiqueta(o)), unsafe_allow_html=True)

                        # Por igual: el importe que le toca; por %: la casilla del %
                        with c_entrada:
                            st.markdown(f"<div class='etq-movil'>{titulo_entrada}</div>", unsafe_allow_html=True)
                            if modo == "Por % de mi cartera":
                                if f"pct_{pid}" not in st.session_state:
                                    st.session_state[f"pct_{pid}"] = round(pct, 1)
                                st.number_input("%", min_value=0.0, max_value=100.0, step=1.0, format="%.1f",
                                                key=f"pct_{pid}", on_change=_guardar_pct,
                                                args=(pid, precio_cli, importe_total_p4),
                                                label_visibility="collapsed")
                                st.markdown(html_seguro(f"<div class='nota-gris'>{es(importe, 0)} "
                                                        f"{simbolo_cliente_p4}</div>"), unsafe_allow_html=True)
                            else:
                                st.markdown(html_seguro(f"<div class='proy-nombre'>{es(importe, 0)} "
                                                        f"{simbolo_cliente_p4}</div>"), unsafe_allow_html=True)

                        # Reparto: barrita + %
                        c_pct.markdown(html_seguro(
                            "<div class='etq-movil'>REPARTO</div>"
                            "<div style='display:flex;align-items:center;gap:8px;'>"
                            f"<div class='barra-pct' style='flex:1;'><div style='width:{min(pct, 100):.2f}%;"
                            f"background:{COLOR_AMBAR};'></div></div>"
                            f"<div style='font-weight:700;color:{COLOR_NAVY};min-width:52px;text-align:right;'>"
                            f"{es(pct, 1)} %</div></div>"), unsafe_allow_html=True)

                    # Datos para el Paso 5
                    st.session_state.precios_compra[pid] = {'precio': o['precio'], 'divisa': o['divisa'],
                                                            'tipo': o['tipo'], 'n_tokens': None}
                    st.session_state.cartera_selecciones.setdefault(pid, {'seleccionado': True})['porcentaje'] = pct
                    proyectos_seleccionados.append({
                        'id': pid, 'nombre': nombre, 'ubicacion': row['Ubicación'],
                        'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0),
                        'address': row.get('Token Address', ''), 'precio_emision': _num(row.get('Precio Emisión', 0)),
                    })

            if modo == "Por igual":
                st.caption("Para decidir tú cuánto invertir en cada proyecto, elige «Por % de mi cartera».")

        suma_porcentajes = 100 if (ids_validos and abs(pendiente) <= tolerancia) else (
            round(importe_repartido / importe_total_p4 * 100, 1) if importe_total_p4 else 0.0)

        st.markdown("")
        st.markdown("---")
        st.markdown("")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso4_back"):
                st.session_state.paso_actual = 3
                st.rerun()

        with col3:
            if len(proyectos_seleccionados) > 0 and suma_porcentajes == 100:
                if st.button("Generar cartera >", use_container_width=True, key="btn_paso4_next"):
                    # Si queda una diferencia mínima por redondeo, el importe pasa a ser
                    # exactamente lo repartido para que los % sumen 100.
                    if abs(pendiente) > 0.01 and importe_repartido > 0:
                        st.session_state.datos_cliente['capital_ajustado'] = importe_repartido + coste_estatus_p4
                        for pid, o, tokens, importe, _rent in filas_calc:
                            st.session_state.cartera_selecciones[pid]['porcentaje'] = importe / importe_repartido * 100
                    st.session_state.datos_cliente['cartera'] = {
                        'proyectos': proyectos_seleccionados,
                        'distribuciones': st.session_state.cartera_selecciones
                    }
                    st.session_state.paso_actual = 5
                    st.rerun()
            else:
                st.button("Generar cartera >", use_container_width=True, disabled=True)
    else:
        st.error("No se cargaron proyectos")
