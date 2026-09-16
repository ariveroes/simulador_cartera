def preparar_distribucion_cartera(df_proyectos, distribucion_type):
    """
    Prepara estructura para distribución de cartera.
    
    Args:
        df_proyectos: DataFrame con proyectos
        distribucion_type: 'Distribuir en partes iguales' o 'Elegir cuánto invertir en cada proyecto'
    
    Returns:
        dict con estructura para distribución
    """
    
    if df_proyectos is None or len(df_proyectos) == 0:
        return {}
    
    proyectos = []
    for idx, row in df_proyectos.iterrows():
        proyectos.append({
            'id': row['ID'],
            'nombre': row['Nombre del proyecto'],
            'ubicacion': row['Ubicación'],
            'rentabilidad': row.get('Rentabilidad_Anualizada_SuperReentel', 0),
            'seleccionado': False,
            'porcentaje': 0
        })
    
    return {
        'tipo': distribucion_type,
        'proyectos': proyectos,
        'suma_porcentaje': 0
    }



def preparar_proyectos_para_paso4(df_proyectos, estatus_cliente):
    """
    Prepara el DataFrame de proyectos para visualización en Paso 4.
    
    Args:
        df_proyectos: DataFrame con todos los proyectos
        estatus_cliente: Estatus seleccionado (SuperReentel, ReentelPro, Reentel)
    
    Returns:
        DataFrame formateado con solo columnas necesarias
    """
    
    if df_proyectos is None or len(df_proyectos) == 0:
        return pd.DataFrame()
    
    df_display = df_proyectos.copy()
    
    # Limpiar filas vacías
    df_display = df_display[df_display['ID'].notna()]
    df_display = df_display[df_display['ID'] != '']
    df_display = df_display[df_display['Nombre del proyecto'].notna()]
    df_display = df_display[df_display['Nombre del proyecto'] != '']
    
    if len(df_display) == 0:
        return pd.DataFrame()
    
    # Mapear columnas de rentabilidad según estatus
    if estatus_cliente == 'SuperReentel':
        col_total = 'Rentabilidad_Total_SuperReentel'
        col_anualizada = 'Rentabilidad_Anualizada_SuperReentel'
    elif estatus_cliente == 'ReentelPro':
        col_total = 'Rentabilidad_Total_ReentelPro'
        col_anualizada = 'Rentabilidad_Anualizada_ReentelPro'
    else:  # Reentel
        col_total = 'Rentabilidad_Total_Reentel'
        col_anualizada = 'Rentabilidad_Anualizada_Reentel'
    
    # Crear columnas de visualización con nombres amigables
    # Limpiar "%" y convertir a número
    rentabilidad_total = df_display[col_total].astype(str).str.replace('%', '').str.strip()
    df_display[f'Rentabilidad Total'] = pd.to_numeric(rentabilidad_total, errors='coerce').fillna(0)
    
    rentabilidad_anualizada = df_display[col_anualizada].astype(str).str.replace('%', '').str.strip()
    df_display[f'Rentabilidad Anualizada'] = pd.to_numeric(rentabilidad_anualizada, errors='coerce').fillna(0)
    
    # Seleccionar solo columnas necesarias
    columnas_mostrar = [
        'ID',
        'Nombre del proyecto',
        'ESTADO',
        'Fecha Inicio Estimada',
        'Fecha Fin Estimada',
        'Ubicación',
        'Tipología de dividendo',
        'Rentabilidad Total',
        'Rentabilidad Anualizada'
    ]
    
    # Filtrar columnas que existan
    columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
    
    df_resultado = df_display[columnas_disponibles]
    
    # Filtrar filas con ID válido
    df_resultado = df_resultado[df_resultado['ID'] != '']
    df_resultado = df_resultado[df_resultado['ID'].notna()]
    
    return df_resultado
