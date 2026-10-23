"""
PASO 4 (archivo paso5_resumen.py) - Resumen de la cartera, tu cartera optimizada y PDF.
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def mostrar():
    import altair as alt
    from modules.rentabilidad_compra import TASA_REINVERSION
    
    st.markdown("## Paso 4: Tu cartera está lista")
    st.markdown("")
    
    datos = st.session_state.datos_cliente
    cartera = datos.get('cartera', {})
    proyectos_cartera = cartera.get('proyectos', [])
    distribuciones = cartera.get('distribuciones', {})
    precios_compra = st.session_state.precios_compra
    df_proy = st.session_state.df_proyectos
    
    if len(proyectos_cartera) > 0:
        # La simulación es siempre sin estatus (Reentel); el estatus solo se usa para
        # calcular la «cartera optimizada» del final
        estatus = 'Reentel'
        divisa_cliente = (datos.get('divisa') or 'EUR').upper()
        simbolo = '€' if divisa_cliente == 'EUR' else '$'
        otra_divisa = 'USD' if divisa_cliente == 'EUR' else 'EUR'
        otro_simbolo = '$' if divisa_cliente == 'EUR' else '€'
        
        def fmt(importe, s=simbolo):
            return f"{es(importe, 2)} {s}"
        
        def a_numero(valor):
            try:
                return float(str(valor).replace('%', '').replace(',', '.').strip())
            except:
                return 0.0
        
        # Tarjeta de resumen (se usa en supuestos y en la cartera)
        def tarjeta(titulo, valor, sub):
            valor, sub = html_seguro(valor), html_seguro(sub)
            return f"""
            <div class="tarjeta" style="border: 1px solid {COLOR_BORDE}; border-radius: 12px; padding: 14px 16px; background: #ffffff; min-height: 105px;">
                <div class="tarjeta-titulo" style="font-size: 12px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.5px;">{titulo}</div>
                <div class="tarjeta-valor" style="font-size: 26px; font-weight: 800; color: {COLOR_NAVY}; margin: 4px 0;">{valor}</div>
                <div class="tarjeta-sub" style="font-size: 12px; color: {COLOR_GRIS};">{sub}</div>
            </div>
            """
        
        # Supuestos de mercado (no se muestran; se usan en los cálculos y en el PDF)
        tipo_cambio = tipo_cambio_actual()
        precio_rnt = precio_rnt_actual()
        
        def convertir(importe, desde, hacia):
            desde = 'USD' if str(desde).upper() in ('USD', 'USDT') else 'EUR'
            hacia = 'USD' if str(hacia).upper() in ('USD', 'USDT') else 'EUR'
            if desde == hacia:
                return importe
            return importe * tipo_cambio if desde == 'EUR' else importe / tipo_cambio
        
        # ========== TU CARTERA DE INVERSIÓN ==========
        st.markdown("### Tu cartera de inversión")
        
        # El importe a invertir es el total: se descuenta el estatus y el resto va a inmuebles
        capital_total = importe_cliente(datos)  # en la divisa del cliente
        rnt_estatus = RNT_POR_ESTATUS.get(estatus, 0)
        coste_estatus = convertir(rnt_estatus * precio_rnt, 'USD', divisa_cliente)
        importe_inmuebles = max(0.0, capital_total - coste_estatus)
        
        # Columnas de rentabilidad según estatus
        col_anual = f'Rentabilidad_Anualizada_{estatus}'
        col_total = f'Rentabilidad_Total_{estatus}'
        
        # Columna de tipología de dividendo
        try:
            from modules.formateo_datos import _buscar_columna_tipologia
            col_tipologia = _buscar_columna_tipologia(df_proy)
        except Exception:
            col_tipologia = next((c for c in df_proy.columns if 'tipolog' in c.lower()), None)
        
        filas_tabla = []
        filas_graficos = []
        proyectos_pdf = []
        
        # Precio de compra de cada proyecto, convertido a la divisa del propio
        # proyecto: es lo que necesita el cálculo de rentabilidad ajustada.
        def precio_compra_en_divisa_proyecto(pid, row):
            info = precios_compra.get(pid, {})
            precio = a_numero(info.get('precio', row.get('Precio Emisión', 0)))
            return convertir(precio, info.get('divisa', divisa_proyecto(row)), divisa_proyecto(row))
        
        def rent_proyecto(pid, est):
            fila = df_proy[df_proy['ID'] == pid]
            if len(fila) == 0:
                return None
            row = fila.iloc[0]
            return rentabilidad_ajustada(row, est, precio_compra_en_divisa_proyecto(pid, row))
        
        def media_cartera(est, campo):
            """Media de la cartera ponderada por el % invertido en cada proyecto."""
            total = 0.0
            for proyecto in proyectos_cartera:
                r = rent_proyecto(proyecto['id'], est)
                if r is None:
                    continue
                peso = distribuciones.get(proyecto['id'], {}).get('porcentaje', 0)
                total += (r[campo] or 0.0) * peso / 100
            return total
        rentabilidad_media = 0.0
        rentabilidad_total_media = 0.0
        
        for proyecto in proyectos_cartera:
            proyecto_id = proyecto['id']
            fila = df_proy[df_proy['ID'] == proyecto_id]
            if len(fila) == 0:
                continue
            row = fila.iloc[0]
            
            peso = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            
            info_precio = precios_compra.get(proyecto_id, {})
            precio = a_numero(info_precio.get('precio', row.get('Precio Emisión', 0)))
            divisa_precio = info_precio.get('divisa', 'EUR')
            tipo_precio = info_precio.get('tipo', 'Emisión')
            precio_conv = convertir(precio, divisa_precio, divisa_cliente)
            
            r_est = rent_proyecto(proyecto_id, estatus)
            r_rnt = rent_proyecto(proyecto_id, 'Reentel')
            rent_anual = r_est['anual'] or 0.0
            rent_total = r_est['total']
            rentabilidad_media += rent_anual * peso / 100
            rentabilidad_total_media += (rent_total or 0.0) * peso / 100
            
            tipologia = str(row.get(col_tipologia, '') or '').strip() if col_tipologia else ''
            
            filas_tabla.append({
                'Proyecto': proyecto['nombre'],
                'Ubicación': row.get('Ubicación', ''),
                'Precio de compra': fmt(precio_conv),
                'Tipo de dividendo': tipologia or '-',
                'Importe invertido': fmt(importe_inmuebles * peso / 100),
                'Rentabilidad anualizada': rent_anual,
                'Rentabilidad total': rent_total,
                '% cartera': peso,
            })
            
            proyectos_pdf.append({
                'id': str(proyecto_id),
                'nombre': proyecto['nombre'],
                'ubicacion': str(row.get('Ubicación', '') or ''),
                'estado': str(row.get('ESTADO', '') or ''),
                'tipodiv': tipologia or '-',
                'precio': fmt(precio_conv),
                'tipo_precio': tipo_precio,
                'pct': peso,
                'importe': importe_inmuebles * peso / 100,
                'rent_anu_rnt': r_rnt['anual'] or 0.0,
                'rent_tot_rnt': r_rnt['total'],
                'rent_anu_est': rent_anual,
                'rent_tot_est': rent_total,
                'fecha_inicio': str(row.get('Fecha Inicio Estimada', '') or ''),
                'fecha_fin': str(row.get('Fecha Fin Estimada', '') or ''),
            })
            
            filas_graficos.append({
                'ubicacion': str(row.get('Ubicación', '') or 'Sin dato'),
                'tipologia': tipologia or 'Sin dato',
                'divisa': str(row.get('Divisa', '') or 'Sin dato'),
                'peso': peso,
            })
        
        # ----- Tarjetas resumen -----
        # Móvil: de dos en dos (importe | inmuebles; rent. total | rent. anualizada).
        # Ordenador: las cuatro en una fila.
        tarjetas = [
            ("IMPORTE INVERTIDO", fmt(capital_total),
             fmt(convertir(capital_total, divisa_cliente, otra_divisa), otro_simbolo)),
            ("INMUEBLES", f"{len(filas_tabla)}", "proyectos en cartera"),
            ("RENT. TOTAL", f"{es(rentabilidad_total_media, 2)} %", "media ponderada"),
            ("RENT. ANUALIZADA", f"{es(rentabilidad_media, 2)} %", "media ponderada"),
        ]
        with st.container(key="kpis_resumen"):
            cols = st.columns(len(tarjetas))
            for col, (titulo, valor, sub) in zip(cols, tarjetas):
                col.markdown(tarjeta(titulo, valor, sub), unsafe_allow_html=True)
        
        st.caption(("Tu importe se reparte entre inmuebles y estatus. Lo que va al estatus sigue siendo tuyo: "
                    "tiene una permanencia de 2 años y **genera su propio rendimiento**. Pero lo más interesante es que **aumenta la rentabilidad de tus inmuebles**. "
                    if coste_estatus > 0 else "")
                   + "Las rentabilidades se calculan con el precio de compra de cada proyecto y los meses de "
                   "renta que le quedan, y se ponderan por el % de la cartera invertido en cada uno.")
        st.markdown("")
        
        # ----- Tabla de proyectos -----
        if filas_tabla:
            # Ordenador: tabla. Móvil: una tarjeta por proyecto (estilos.py elige cuál se ve)
            with st.container(key="vista_tabla_resumen"):
                st.dataframe(
                    pd.DataFrame(filas_tabla),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Proyecto': st.column_config.Column(pinned=True),
                        'Rentabilidad anualizada': st.column_config.NumberColumn(format='%.2f%%'),
                        'Rentabilidad total': st.column_config.NumberColumn(format='%.2f%%'),
                        '% cartera': st.column_config.NumberColumn(format='%.1f%%'),
                    }
                )
            with st.container(key="vista_tarjetas_resumen"):
                for f in filas_tabla:
                    st.markdown(html_seguro(
                        f"<div class='tm-tarjeta'>"
                        f"<div style='display:flex; justify-content:space-between; gap:8px; align-items:baseline;'>"
                        f"<span class='tm-nombre'>{f['Proyecto']}</span>"
                        f"<span class='tm-pct'>{es(f['% cartera'], 1)} %</span></div>"
                        f"<div class='tm-sub'>{f['Ubicación']} · {f['Tipo de dividendo']}</div>"
                        f"<div class='tm-datos dos'>"
                        f"<div><span>Invertido</span><b>{f['Importe invertido']}</b></div>"
                        f"<div><span>Precio de compra</span><b>{f['Precio de compra']}</b></div>"
                        f"<div><span>Rent. anual</span><b>{es(f['Rentabilidad anualizada'], 2)} %</b></div>"
                        f"<div><span>Rent. total</span><b>{es(f['Rentabilidad total'] or 0, 2)} %</b></div>"
                        f"</div></div>"), unsafe_allow_html=True)
        
        # ----- Gráficos -----
        if filas_graficos:
            df_graf = pd.DataFrame(filas_graficos)
            colores = PALETA_GRAFICOS
            
            def donut(campo, titulo):
                datos_g = df_graf.groupby(campo, as_index=False)['peso'].sum()
                datos_g = datos_g[datos_g['peso'] > 0]
                total = datos_g['peso'].sum()
                datos_g['pct'] = datos_g['peso'] / total if total else 0
                datos_g = datos_g.rename(columns={campo: 'categoria'})
                
                categorias = sorted(datos_g['categoria'].astype(str).unique())
                color_de = {c: colores[i % len(colores)] for i, c in enumerate(categorias)}
                oscuros = ("#1f2937", "#15803d", "#3e4753")
                datos_g['color_texto'] = datos_g['categoria'].astype(str).map(
                    lambda c: "#ffffff" if color_de[c] in oscuros else COLOR_NAVY)
                
                base = alt.Chart(datos_g).encode(
                    theta=alt.Theta('peso:Q', stack=True),
                    color=alt.Color('categoria:N', scale=alt.Scale(domain=categorias,
                                                                   range=[color_de[c] for c in categorias]),
                                    legend=alt.Legend(orient='bottom', title=None, direction='vertical',
                                                      labelLimit=0, labelFontSize=12)),
                    tooltip=[alt.Tooltip('categoria:N', title=titulo),
                             alt.Tooltip('pct:Q', format='.0%', title='Peso')]
                )
                # Tamaño según el espacio real del gráfico (ancho y alto) y los % dentro
                # del anillo: así no se salen por arriba ni se pisan entre ellos
                radio = "max(min(width, height, 210) / 2 - 6, 40)"
                arco = base.mark_arc(innerRadius=alt.ExprRef(f"({radio}) * 0.55"),
                                     outerRadius=alt.ExprRef(radio))
                texto = base.transform_filter('datum.pct >= 0.05').mark_text(
                    radius=alt.ExprRef(f"({radio}) * 0.775"), size=11, fontWeight='bold').encode(
                    text=alt.Text('pct:Q', format='.0%'),
                    color=alt.Color('color_texto:N', scale=None, legend=None))
                return (arco + texto).properties(height=250)
            
            st.markdown("")
            g1, g2, g3 = st.columns(3)
            for g, campo, titulo in ((g1, 'ubicacion', 'Distribución geográfica'),
                                     (g2, 'tipologia', 'Tipología de dividendo'),
                                     (g3, 'divisa', 'Divisa del inmueble')):
                g.markdown(f"<div style='font-size:15px; font-weight:700; color:{COLOR_NAVY}; "
                           f"margin-top:8px;'>{titulo}</div>", unsafe_allow_html=True)
                g.altair_chart(donut(campo, titulo), use_container_width=True)
            
            # ----- Mapa de distribución geográfica -----
            import unicodedata
            def _norm(t):
                return unicodedata.normalize('NFKD', str(t)).encode('ascii', 'ignore').decode().lower().strip()
            
            reparto_pais = df_graf.groupby('ubicacion', as_index=False)['peso'].sum()
            reparto_pais = reparto_pais[reparto_pais['peso'] > 0]
            total_peso = reparto_pais['peso'].sum()
            reparto_pais['pct'] = reparto_pais['peso'] / total_peso * 100 if total_peso else 0
            reparto_pais['id'] = reparto_pais['ubicacion'].map(lambda u: CODIGOS_PAIS.get(_norm(u)))
            en_mapa = reparto_pais.dropna(subset=['id']).astype({'id': int})
            
            if len(en_mapa) > 0:
                paises = alt.topo_feature(
                    'https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json', 'countries')
                
                fondo = alt.Chart(paises).mark_geoshape(
                    fill=COLOR_BORDE, stroke='#ffffff', strokeWidth=0.5
                ).transform_filter('datum.id != 10')   # sin la Antártida
                
                invertidos = alt.Chart(paises).mark_geoshape(
                    stroke='#ffffff', strokeWidth=0.5
                ).transform_lookup(
                    lookup='id',
                    from_=alt.LookupData(en_mapa, 'id', ['ubicacion', 'pct'])
                ).transform_filter(
                    'isValid(datum.pct)'
                ).encode(
                    color=alt.Color('pct:Q', scale=alt.Scale(range=['#fcd287', '#f5a11f']), legend=None),
                    tooltip=[alt.Tooltip('ubicacion:N', title='País'),
                             alt.Tooltip('pct:Q', format='.1f', title='% de la inversión')]
                )
                
                mapa = (fondo + invertidos).project('equalEarth').properties(height=420)
                st.markdown(f"<div style='font-size:15px; font-weight:700; color:{COLOR_NAVY}; "
                            f"margin-top:12px;'>Distribución geográfica de la inversión</div>",
                            unsafe_allow_html=True)
                try:
                    contenedor_mapa = st.container(key="mapa")
                except TypeError:
                    contenedor_mapa = st.container()
                with contenedor_mapa:
                    st.altair_chart(mapa, use_container_width=True)
            
            leyenda = " · ".join(
                f"<span style='color:{COLOR_AMBAR};'>■</span> {r.ubicacion} — {es(r.pct, 1)}%"
                for r in reparto_pais.sort_values('pct').itertuples()
            )
            st.markdown(f"<div style='font-size:13px; color:{COLOR_GRIS};'>{leyenda}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== TU CARTERA vs TU CARTERA OPTIMIZADA ==========
        # El cliente simula sin estatus (Reentel: todo el importe a inmuebles). La «cartera
        # optimizada» es la misma cartera con el mismo importe total y el mejor estatus
        # (parte del importe va al estatus, que rinde RENDIMIENTO_ESTATUS % anual y sube la
        # rentabilidad de los inmuebles). No se nombra el estatus: lo explica el equipo en la llamada.
        st.markdown("### ¿Cuánto puede ganar tu cartera?")
        
        MESES_COMPARATIVA = 36
        PLAZOS_COMPARATIVA = [6, 12, 24, 36, 60]
        
        def ganancia_inmobiliaria(importe, meses, est='Reentel'):
            """Ganancia de repartir `importe` como la cartera (mismos % por proyecto), proyecto a
            proyecto: las rentas se reinvierten al cobrarse; lo que se paga al final (plusvalía,
            proyectos bullet) no se reinvierte hasta que el proyecto termina; y al terminar, el
            capital y el beneficio se reinvierten (ver rentabilidad_compra)."""
            from modules.rentabilidad_compra import ganancia_proyecto
            total = 0.0
            for proyecto in proyectos_cartera:
                fila = df_proy[df_proy['ID'] == proyecto['id']]
                if len(fila) == 0:
                    continue
                row = fila.iloc[0]
                peso = distribuciones.get(proyecto['id'], {}).get('porcentaje', 0)
                total += ganancia_proyecto(importe * peso / 100, row, est,
                                           precio_compra_en_divisa_proyecto(proyecto['id'], row), meses)
            return total
        
        def ganancia_estatus(coste, meses):
            return coste * RENDIMIENTO_ESTATUS / 100 * meses / 12
        
        reparto_estatus = {}
        for est in ['Reentel', 'ReentelPro', 'SuperReentel']:
            coste_e = convertir(RNT_POR_ESTATUS.get(est, 0) * precio_rnt, 'USD', divisa_cliente)
            reparto_estatus[est] = {'coste': coste_e, 'inmuebles': max(0.0, capital_total - coste_e)}
        
        def ganancia_final(est, meses):
            r = reparto_estatus[est]
            return (ganancia_inmobiliaria(r['inmuebles'], meses, est)
                    + ganancia_estatus(r['coste'], meses))
        
        # Mejor estatus para esta cartera e importe (solo si mejora claramente a 36 meses)
        g36 = {est: ganancia_final(est, MESES_COMPARATIVA) for est in reparto_estatus}
        posibles = [e for e in ('ReentelPro', 'SuperReentel') if reparto_estatus[e]['inmuebles'] > 0]
        mejor = max(posibles, key=lambda e: g36[e]) if posibles else None
        extra = (g36[mejor] - g36['Reentel']) if mejor else 0.0
        hay_mejora = bool(mejor) and extra > max(50.0, g36['Reentel'] * 0.03)
        
        rent_anual_media_pdf = {'Reentel': media_cartera('Reentel', 'anual')}
        rent_total_media_pdf = {'Reentel': media_cartera('Reentel', 'total')}
        if hay_mejora:
            rent_anual_media_pdf[mejor] = media_cartera(mejor, 'anual')
            rent_total_media_pdf[mejor] = media_cartera(mejor, 'total')
        
        escenarios_pdf = []
        for meses in [6, 12, 24, 36]:
            g_rnt = ganancia_final('Reentel', meses)
            g_est = ganancia_final(mejor, meses) if hay_mejora else g_rnt
            escenarios_pdf.append({
                'meses': meses, 'g_rnt': g_rnt, 'g_est': g_est, 'g_est_staking': g_est,
                'rent_rnt': (g_rnt / capital_total * 100) if capital_total else 0,
                'rent_est': (g_est / capital_total * 100) if capital_total else 0,
            })
        comparativa_pdf = [{'estatus': est, 'ganancia': g36[est], 'coste': reparto_estatus[est]['coste']}
                           for est in reparto_estatus]
        
        # ----- Gráfica: tu cartera (y tu cartera optimizada, si mejora) -----
        series = [("Tu cartera", 'Reentel', COLOR_NAVY)]
        if hay_mejora:
            series.append(("Tu cartera optimizada", mejor, COLOR_AMBAR))
        orden_series = [s_[0] for s_ in series]
        orden_plazos = [f"{m} meses" for m in PLAZOS_COMPARATIVA]
        filas_barras = []
        for m in PLAZOS_COMPARATIVA:
            for nombre_s, est_s, _ in series:
                g = ganancia_final(est_s, m)
                filas_barras.append({'Plazo': f"{m} meses", 'Escenario': nombre_s, 'Ganancia': g,
                                     'texto': es(g, 0), 'texto_tooltip': fmt(g)})
        datos_barras = pd.DataFrame(filas_barras)
        
        # Etiquetas del eje con el formato de número de la divisa del cliente
        formato_eje = ("replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')"
                       if divisa_cliente == 'EUR' else "format(datum.value, ',.0f')")
        eje_x = alt.X('Plazo:N', sort=orden_plazos, title=None,
                      axis=alt.Axis(labelAngle=0, labelFontSize=12, labelColor=COLOR_GRIS))
        desplazamiento = alt.XOffset('Escenario:N', sort=orden_series)
        eje_y = alt.Y('Ganancia:Q', title=None,
                      axis=alt.Axis(labelExpr=formato_eje, labelColor=COLOR_GRIS,
                                    gridColor=COLOR_BORDE, domain=False, ticks=False))
        barras = alt.Chart(datos_barras).mark_bar(
            cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=eje_x, xOffset=desplazamiento, y=eje_y,
            color=alt.Color('Escenario:N', sort=orden_series,
                            scale=alt.Scale(domain=orden_series, range=[s_[2] for s_ in series]),
                            legend=alt.Legend(orient='bottom', title=None, labelFontSize=12,
                                              symbolType='square', labelLimit=0, direction='vertical')),
            tooltip=[alt.Tooltip('Escenario:N', title='Escenario'),
                     alt.Tooltip('Plazo:N', title='Plazo'),
                     alt.Tooltip('texto_tooltip:N', title='Ganancia')],
        )
        # En pantallas estrechas no se pintan los importes encima de las barras (se
        # pisarían); siguen apareciendo al tocar cada barra
        etiquetas = alt.Chart(datos_barras).mark_text(
            dy=-8, fontSize=10, fontWeight='bold', color=COLOR_NAVY,
            opacity=alt.ExprRef("width < 820 ? 0 : 1")).encode(
            x=eje_x, xOffset=desplazamiento, y=eje_y, text='texto:N')
        
        st.markdown(f"<div style='font-size:16px; font-weight:700; color:{COLOR_NAVY}; margin:6px 0 4px 0;'>"
                    f"Ganancia estimada de tu cartera</div>", unsafe_allow_html=True)
        st.altair_chart((barras + etiquetas).properties(height=360).configure_view(stroke=None),
                        use_container_width=True)
        
        # Mensaje a 36 meses
        mensaje = (f"A {MESES_COMPARATIVA} meses, la ganancia final estimada de tu cartera es de "
                   f"<b>{fmt(g36['Reentel'])}</b>")
        mensaje += (f", y de <b style='color:{COLOR_AMBAR_OSCURO};'>{fmt(g36[mejor])}</b> con tu cartera "
                    f"optimizada." if hay_mejora else ".")
        st.markdown(html_seguro(
            f"<div style='background:{COLOR_AMBAR_CLARO}; border:1px solid {COLOR_AMBAR}; border-radius:10px; "
            f"padding:14px 18px; margin-top:16px; color:{COLOR_NAVY}; font-size:15px;'>{mensaje}</div>"),
            unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12.5px; color:{COLOR_GRIS}; margin:8px 2px 0 2px;'>"
                    f"El cálculo considera la reinversión de los beneficios obtenidos, beneficiándose del interés "
                    f"compuesto: las rentas se reinvierten cuando se cobran; lo que se paga al final del proyecto no "
                    f"se reinvierte hasta que termina, y entonces el capital y el beneficio se reinvierten."
                    + (" La cartera optimizada tiene los mismos proyectos y el mismo importe total, con unas "
                       "condiciones que nuestro equipo te explicará." if hay_mejora else "")
                    + " Las cifras son estimaciones y no garantizan resultados futuros.</div>",
                    unsafe_allow_html=True)
        
        # ----- Llamada a agendar (el objetivo de la herramienta) -----
        moneda = "euro" if divisa_cliente == 'EUR' else "dólar"
        if hay_mejora:
            titulo_cta = (f"Podrías conseguir hasta <span style='color:{COLOR_AMBAR_OSCURO};'>{fmt(extra)} más</span> "
                          f"sin invertir ni un solo {moneda} más")
            texto_cta = "¿Quieres saber cómo? Agenda una llamada con nuestro equipo."
        else:
            titulo_cta = "¿Quieres que revisemos juntos tu cartera para sacarle el máximo partido?"
            texto_cta = "Agenda una llamada con nuestro equipo."
        st.markdown(html_seguro(
            f"<div style='background:{COLOR_AMBAR_CLARO}; border:2px solid {COLOR_AMBAR}; border-radius:14px; "
            f"padding:22px 24px; margin:28px 0 8px 0; display:flex; flex-wrap:wrap; gap:14px 24px; "
            f"align-items:center; justify-content:space-between;'>"
            f"<div style='flex:1 1 320px; color:{COLOR_NAVY};'>"
            f"<div style='font-size:19px; font-weight:800; margin-bottom:4px;'>{titulo_cta}</div>"
            f"<div style='font-size:15px;'>{texto_cta}</div></div>"
            f"<a href='{URL_AGENDA}' target='_blank' rel='noopener' style='background:{COLOR_NAVY}; "
            f"color:#ffffff; text-decoration:none; font-weight:700; padding:13px 22px; border-radius:10px; "
            f"white-space:nowrap;'>Agendar llamada</a></div>"), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== DESCARGAR PDF ==========
        st.markdown("### Descarga tu cartera")
        
        repartos_pdf = {}
        if filas_graficos:
            for campo, titulo in (('ubicacion', 'Distribución geográfica'),
                                  ('tipologia', 'Tipología de dividendo'),
                                  ('divisa', 'Divisa del inmueble')):
                serie = df_graf.groupby(campo)['peso'].sum()
                total = serie.sum()
                repartos_pdf[titulo] = (serie / total * 100).to_dict() if total else {}
        
        resumen_pdf = {
            'divisa': divisa_cliente,
            'estatus': estatus,
            'tipo_cambio': tipo_cambio,
            'precio_rnt': precio_rnt,
            'rnt_estatus': rnt_estatus,
            'n_inmuebles': len(filas_tabla),
            'importe_inmuebles': importe_inmuebles,
            'coste_estatus': coste_estatus,
            'capital_total': capital_total,
            'rentabilidad_media': rentabilidad_media,
            'titular': datos.get('nombre'),
            'proyectos': proyectos_pdf,
            'escenarios': escenarios_pdf,
            'rent_anual_media': rent_anual_media_pdf,
            'rent_total_media': rent_total_media_pdf,
            'repartos': repartos_pdf,
            'comparativa': comparativa_pdf,
            'meses': MESES_COMPARATIVA,
            'optimizada': hay_mejora,
            'estatus_optimo': mejor if hay_mejora else None,
            'extra_optimizada': extra if hay_mejora else 0.0,
        }
        
        # Guardar el lead con la cartera simulada (una sola vez por cartera)
        cartera_txt = "; ".join(
            f"{f['Proyecto']} ({es(f['% cartera'], 1)}% · {f['Precio de compra']})" for f in filas_tabla)
        firma_cartera = f"{st.session_state.get('lead_id', '')}|{estatus}|{cartera_txt}"
        if st.session_state.get('lead_cartera_guardada') != firma_cartera:
            if 'lead_id' not in st.session_state:
                st.session_state.lead_id = uuid.uuid4().hex[:10]
            # En la columna «Estatus» del Sheet, lo que podría ganar de más con el mejor
            # estatus (para que el equipo comercial sepa de qué hablar en la llamada)
            datos_lead = dict(datos)
            datos_lead['estatus'] = (f"Sin estatus · potencial: +{fmt(extra)} a {MESES_COMPARATIVA} meses con {mejor}"
                                     if hay_mejora else "Sin estatus · sin mejora con estatus")
            leads.guardar(st.session_state.lead_id, "Cartera generada", datos_lead,
                          cartera=cartera_txt, importe=fmt(capital_total))
            st.session_state.lead_cartera_guardada = firma_cartera
        
        datos_pdf = dict(st.session_state.datos_cliente)
        if datos_pdf.get('capital_ajustado'):
            datos_pdf['capital'] = capital_mostrado(datos_pdf, simbolo)
        pdf_buffer = generar_pdf_cartera(
            datos_pdf,
            proyectos_cartera,
            distribuciones,
            st.session_state.df_proyectos,
            precios_compra,
            resumen=resumen_pdf
        )
        
        st.download_button(
            label="Descargar cartera en PDF",
            data=pdf_buffer,
            file_name=f"Cartera_{datos['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        st.markdown("")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("< Atrás", use_container_width=True, key="btn_paso5_back"):
                st.session_state.paso_actual = 3
                st.rerun()
        
        with col3:
            if st.button("Crear nueva cartera", use_container_width=True, key="btn_nueva_cartera"):
                st.session_state.paso_actual = 1
                st.session_state.datos_cliente = {}
                st.session_state.cartera_selecciones = {}
                st.session_state.precios_compra = {}
                st.session_state.sel_tablas = {}
                st.session_state.tokens_compra = {}
                st.session_state.oferta_elegida = {}
                st.session_state.tokens_manual = False
                st.session_state.modo_reparto = "Por igual"
                st.session_state.pop('input_importe', None)
                st.session_state.pop('oferta_super_rechazada', None)
                st.session_state.pop('preseleccion_hecha', None)
                st.rerun()
    else:
        st.error("No hay cartera para mostrar")
