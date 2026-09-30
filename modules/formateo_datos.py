"""
FORMATEO DE DATOS - Prepara DataFrame para visualización en Paso 4
"""

import unicodedata
import pandas as pd


def _normalizar(texto):
    """Quita tildes y pasa a minúsculas para comparar nombres de columnas."""
    return unicodedata.normalize('NFKD', str(texto)).encode('ascii', 'ignore').decode().lower()


def _buscar_columna_tipologia(df):
    """Busca la columna de tipología de dividendo aunque el nombre varíe."""
    columnas = [(col, _normalizar(col)) for col in df.columns]
    # 1º: columna que contenga 'tipolog' y 'dividend'
    for col, nombre in columnas:
        if 'tipolog' in nombre and 'dividend' in nombre:
            return col
    # 2º: cualquier columna con 'dividend'
    for col, nombre in columnas:
        if 'dividend' in nombre:
            return col
    return None


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
    try:
        if col_total in df_display.columns:
            rentabilidad_total = df_display[col_total].astype(str).str.replace('%', '').str.strip()
            df_display['Rentabilidad Total'] = pd.to_numeric(rentabilidad_total, errors='coerce').fillna(0)
        else:
            df_display['Rentabilidad Total'] = 0
            
        if col_anualizada in df_display.columns:
            rentabilidad_anualizada = df_display[col_anualizada].astype(str).str.replace('%', '').str.strip()
            df_display['Rentabilidad Anualizada'] = pd.to_numeric(rentabilidad_anualizada, errors='coerce').fillna(0)
        else:
            df_display['Rentabilidad Anualizada'] = 0
    except Exception:
        df_display['Rentabilidad Total'] = 0
        df_display['Rentabilidad Anualizada'] = 0
    
    # Tipología de dividendo (se muestra siempre; '-' si no hay dato)
    col_tipologia = _buscar_columna_tipologia(df_display)
    if col_tipologia:
        df_display['Tipología de dividendo'] = (
            df_display[col_tipologia].fillna('').astype(str).str.strip().replace('', '-')
        )
    else:
        df_display['Tipología de dividendo'] = '-'
    
    # Seleccionar solo columnas necesarias
    columnas_mostrar = [
        'ID',
        'Nombre del proyecto',
        'Estado',
        'Fecha Inicio Estimada',
        'Fecha Fin Estimada',
        'Ubicación',
        'Tipología de dividendo',
        'Rentabilidad Anualizada',
        'Rentabilidad Total'
        
    ]
    
    # Filtrar columnas que existan
    columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
    
    df_resultado = df_display[columnas_disponibles]
    
    # Filtrar filas con ID válido
    df_resultado = df_resultado[df_resultado['ID'] != '']
    df_resultado = df_resultado[df_resultado['ID'].notna()]
    
    return df_resultado
