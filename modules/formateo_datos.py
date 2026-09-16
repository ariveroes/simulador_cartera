"""
FORMATEO DE DATOS - Prepara DataFrame para visualización en Paso 4
"""

import pandas as pd
from datetime import datetime, timedelta


def preparar_proyectos_para_paso4(df_proyectos, estatus_cliente):
    """
    Prepara el DataFrame de proyectos para visualización en Paso 4.
    """
    
    if df_proyectos is None or len(df_proyectos) == 0:
        return pd.DataFrame()
    
    df_display = df_proyectos.copy()
    
    # DEBUG: Mostrar todas las columnas disponibles
    print("\n=== COLUMNAS DISPONIBLES EN EL DATAFRAME ===")
    print(list(df_display.columns))
    print("==========================================\n")
    
    # Limpiar filas completamente vacías o con valores "None"
    df_display = df_display[df_display['ID'] != 'None']
    df_display = df_display[df_display['ID'].notna()]
    df_display = df_display[df_display['Nombre del proyecto'] != 'None']
    df_display = df_display[df_display['Nombre del proyecto'].notna()]
    
    if len(df_display) == 0:
        return pd.DataFrame()
    
    # Mapping de columnas según estatus para rentabilidad
    if estatus_cliente == 'SuperReentel':
        col_rendim = 'Estimación Rentab. Rendim. Recurr. anualizados SR'
        col_plusvalia = 'Estimación Rentab. Plusvalía SR'
    elif estatus_cliente == 'ReentelPro':
        col_rendim = 'Estimación Rentab. Rendim. Recurr. anualizados RP'
        col_plusvalia = 'Estimación Rentab. Plusvalía RP'
    else:  # Reentel
        col_rendim = 'Estimación Rentab. Rendim. Recurr. anualizados Reentel'
        col_plusvalia = 'Estimación Rentab. Plusvalía Reentel'
    
    print(f"Buscando columnas: {col_rendim} y {col_plusvalia}")
    print(f"¿Existe col_rendim?: {col_rendim in df_display.columns}")
    print(f"¿Existe col_plusvalia?: {col_plusvalia in df_display.columns}")
    
    # Calcular rentabilidad total y anualizada
    try:
        if col_rendim in df_display.columns and col_plusvalia in df_display.columns:
            rentab_total = (
                pd.to_numeric(df_display[col_rendim], errors='coerce').fillna(0) +
                pd.to_numeric(df_display[col_plusvalia], errors='coerce').fillna(0)
            )
            rentab_anualizada = pd.to_numeric(df_display[col_rendim], errors='coerce').fillna(0)
            
            df_display[f'Rentabilidad Total ({estatus_cliente})'] = rentab_total
            df_display[f'Rentabilidad Anualizada ({estatus_cliente})'] = rentab_anualizada
            
            print(f"Rentabilidades calculadas. Muestra: {rentab_anualizada.head()}")
        else:
            print(f"ERROR: Columnas no encontradas")
            df_display[f'Rentabilidad Total ({estatus_cliente})'] = 0
            df_display[f'Rentabilidad Anualizada ({estatus_cliente})'] = 0
    except Exception as e:
        print(f"Error calculando rentabilidad: {e}")
        df_display[f'Rentabilidad Total ({estatus_cliente})'] = 0
        df_display[f'Rentabilidad Anualizada ({estatus_cliente})'] = 0
    
    # Procesar fechas (solo mes y año)
    df_display['Fecha Inicio Estimada'] = 'N/A'
    df_display['Fecha Fin Estimada'] = 'N/A'
    
    try:
        for idx, row in df_display.iterrows():
            try:
                # Obtener meses desde financiación o lanzamiento
                meses_financiacion = row.get('Estimación Nº Meses desde inicio de renta en base a Financiación', '')
                meses_lanzamiento = row.get('Estimación Nº Meses desde Lanzamiento', '')
                
                # Usar financiación si existe, sino usar lanzamiento
                meses_str = str(meses_financiacion).strip() if meses_financiacion else ''
                if not meses_str or meses_str == 'None' or meses_str == '':
                    meses_str = str(meses_lanzamiento).strip() if meses_lanzamiento else '0'
                
                meses_int = int(float(meses_str or 0))
                
                if meses_int > 0:
                    # Fecha de inicio
                    fecha_inicio = datetime.now() + timedelta(days=30*meses_int)
                    df_display.loc[idx, 'Fecha Inicio Estimada'] = fecha_inicio.strftime('%m/%Y')
                    
                    # Fecha de fin (24 meses después)
                    fecha_fin = fecha_inicio + timedelta(days=730)
                    df_display.loc[idx, 'Fecha Fin Estimada'] = fecha_fin.strftime('%m/%Y')
            except Exception as e:
                print(f"Error procesando fecha en fila {idx}: {e}")
                pass
                
    except Exception as e:
        print(f"Error procesando fechas: {e}")
    
    # Seleccionar solo columnas necesarias
    columnas_mostrar = [
        'ID',
        'Nombre del proyecto',
        'ESTADO',
        'Fecha Inicio Estimada',
        'Fecha Fin Estimada',
        'Ubicación',
        'Tipología de Dividendos',
        f'Rentabilidad Total ({estatus_cliente})',
        f'Rentabilidad Anualizada ({estatus_cliente})'
    ]
    
    # Filtrar columnas que existan
    columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
    
    df_resultado = df_display[columnas_disponibles]
    
    # Filtrar filas con ID válido
    df_resultado = df_resultado[df_resultado['ID'] != 'None']
    df_resultado = df_resultado[df_resultado['ID'].notna()]
    
    return df_resultado
