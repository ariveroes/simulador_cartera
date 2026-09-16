"""
FORMATEO DE DATOS - Prepara DataFrame para visualización en Paso 4
"""

import pandas as pd
from datetime import datetime, timedelta


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
    
    # Calcular rentabilidad total y anualizada
    try:
        df_display[f'Rentabilidad Total ({estatus_cliente})'] = (
            pd.to_numeric(df_display[col_rendim], errors='coerce').fillna(0) +
            pd.to_numeric(df_display[col_plusvalia], errors='coerce').fillna(0)
        )
        df_display[f'Rentabilidad Anualizada ({estatus_cliente})'] = pd.to_numeric(
            df_display[col_rendim], errors='coerce'
        ).fillna(0)
    except Exception as e:
        print(f"Error calculando rentabilidad: {e}")
    
    # Procesar fechas (solo mes y año)
    try:
        # Función para calcular fecha de inicio
        def calcular_fecha_inicio(row):
            meses_financiacion = row.get('Estimación Nº Meses desde inicio de renta en base a Financiación', '')
            meses_lanzamiento = row.get('Estimación Nº Meses desde Lanzamiento', '')
            
            # Usar financiación si existe, sino usar lanzamiento
            meses = meses_financiacion if (meses_financiacion and str(meses_financiacion).strip()) else meses_lanzamiento
            
            try:
                meses_int = int(float(meses or 0))
                fecha = datetime.now() + timedelta(days=30*meses_int)
                return fecha.strftime('%m/%Y')
            except:
                return 'N/A'
        
        df_display['Fecha Inicio Estimada'] = df_display.apply(calcular_fecha_inicio, axis=1)
        
        # Fecha de fin (aproximadamente 24 meses después del inicio)
        df_display['Fecha Fin Estimada'] = 'N/A'
        try:
            for idx, inicio in enumerate(df_display['Fecha Inicio Estimada']):
                if inicio != 'N/A':
                    fecha_inicio = datetime.strptime(inicio, '%m/%Y')
                    fecha_fin = fecha_inicio + timedelta(days=730)
                    df_display.loc[idx, 'Fecha Fin Estimada'] = fecha_fin.strftime('%m/%Y')
        except:
            pass
                
    except Exception as e:
        print(f"Error procesando fechas: {e}")
        df_display['Fecha Inicio Estimada'] = 'N/A'
        df_display['Fecha Fin Estimada'] = 'N/A'
    
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
    
    return df_display[columnas_disponibles]
