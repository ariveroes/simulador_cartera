"""
DISTRIBUCIÓN DE CAPITAL - 3 opciones para repartir inversión entre proyectos
"""

import pandas as pd
import numpy as np


def distribucion_igual(df_proyectos_seleccionados, capital_disponible):
    """
    Distribuye capital de forma IGUAL entre todos los proyectos.
    
    Cada proyecto recibe: capital_disponible / número_proyectos
    
    Args:
        df_proyectos_seleccionados: DataFrame con proyectos seleccionados
        capital_disponible: float (EUR o USD)
    
    Returns:
        list of dict con inversión por proyecto
    """
    if df_proyectos_seleccionados.empty or capital_disponible <= 0:
        return []
    
    n_proyectos = len(df_proyectos_seleccionados)
    inversion_por_proyecto = capital_disponible / n_proyectos
    
    resultado = []
    for idx, row in df_proyectos_seleccionados.iterrows():
        resultado.append({
            'ID': row['ID'],
            'Nombre': row.get('Nombre', ''),
            'Inversion': inversion_por_proyecto,
            'Porcentaje': 100 / n_proyectos,
            'Rentab_Recurrente': row.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0),
            'Rentab_Plusvalia': row.get('Estimación Rentab. Plusvalía Reentel', 0),
            'Meses_Renta': row.get('Estimación Nº Meses desde Lanzamiento', 24)
        })
    
    return resultado


def distribucion_proporcional(df_proyectos_seleccionados, capital_disponible):
    """
    Distribuye capital de forma PROPORCIONAL al tamaño del proyecto.
    
    Inversión_Proyecto = capital_disponible × (Importe_Proyecto / Suma_Importes)
    
    Args:
        df_proyectos_seleccionados: DataFrame con proyectos seleccionados
        capital_disponible: float (EUR o USD)
    
    Returns:
        list of dict con inversión por proyecto
    """
    if df_proyectos_seleccionados.empty or capital_disponible <= 0:
        return []
    
    # Usar columna de importe en EUR
    df = df_proyectos_seleccionados.copy()
    
    # Convertir a numérico
    if 'Importe proyecto en €' in df.columns:
        df['Importe'] = pd.to_numeric(df['Importe proyecto en €'], errors='coerce')
    else:
        df['Importe'] = 1  # Si no existe, asignar igual (fallback a igual)
    
    # Si hay NaN, reemplazar con media
    df['Importe'].fillna(df['Importe'].mean(), inplace=True)
    
    suma_importes = df['Importe'].sum()
    
    if suma_importes == 0:
        # Si no hay importes válidos, usar distribución igual
        return distribucion_igual(df_proyectos_seleccionados, capital_disponible)
    
    resultado = []
    for idx, row in df.iterrows():
        # Calcular ponderación
        ponderacion = row['Importe'] / suma_importes
        inversion = capital_disponible * ponderacion
        
        resultado.append({
            'ID': row['ID'],
            'Nombre': row.get('Nombre', ''),
            'Inversion': inversion,
            'Porcentaje': ponderacion * 100,
            'Rentab_Recurrente': row.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0),
            'Rentab_Plusvalia': row.get('Estimación Rentab. Plusvalía Reentel', 0),
            'Meses_Renta': row.get('Estimación Nº Meses desde Lanzamiento', 24)
        })
    
    return resultado


def distribucion_manual(df_proyectos_seleccionados, capital_disponible, porcentajes_dict):
    """
    Distribuye capital de forma MANUAL según porcentajes especificados por cliente.
    
    Args:
        df_proyectos_seleccionados: DataFrame con proyectos seleccionados
        capital_disponible: float (EUR o USD)
        porcentajes_dict: dict {ID: porcentaje, ...}
            Ej: {'SVQ-1': 0.30, 'GND-2': 0.70}
    
    Returns:
        list of dict con inversión por proyecto
    
    Raises:
        ValueError: Si porcentajes no suman 100%
    """
    if df_proyectos_seleccionados.empty or capital_disponible <= 0:
        return []
    
    # Validar que porcentajes sumen 100%
    suma_porcentajes = sum(porcentajes_dict.values())
    if abs(suma_porcentajes - 1.0) > 0.01:  # Permitir pequeñas variaciones de redondeo
        raise ValueError(
            f"Los porcentajes deben sumar 100%. Actual: {suma_porcentajes * 100:.1f}%"
        )
    
    resultado = []
    for idx, row in df_proyectos_seleccionados.iterrows():
        proyecto_id = row['ID']
        
        if proyecto_id not in porcentajes_dict:
            raise ValueError(f"Proyecto {proyecto_id} no tiene porcentaje asignado")
        
        porcentaje = porcentajes_dict[proyecto_id]
        inversion = capital_disponible * porcentaje
        
        resultado.append({
            'ID': proyecto_id,
            'Nombre': row.get('Nombre', ''),
            'Inversion': inversion,
            'Porcentaje': porcentaje * 100,
            'Rentab_Recurrente': row.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0),
            'Rentab_Plusvalia': row.get('Estimación Rentab. Plusvalía Reentel', 0),
            'Meses_Renta': row.get('Estimación Nº Meses desde Lanzamiento', 24)
        })
    
    return resultado


def distribuir_capital(df_proyectos_seleccionados, capital_disponible, 
                       tipo_distribucion='Igual', porcentajes_dict=None):
    """
    Distribuye capital según tipo seleccionado.
    
    Args:
        df_proyectos_seleccionados: DataFrame
        capital_disponible: float
        tipo_distribucion: str ('Igual', 'Proporcional', 'Manual')
        porcentajes_dict: dict {ID: porcentaje} (solo para Manual)
    
    Returns:
        list of dict con distribución
    """
    if tipo_distribucion == 'Igual':
        return distribucion_igual(df_proyectos_seleccionados, capital_disponible)
    
    elif tipo_distribucion == 'Proporcional':
        return distribucion_proporcional(df_proyectos_seleccionados, capital_disponible)
    
    elif tipo_distribucion == 'Manual':
        if porcentajes_dict is None:
            raise ValueError("Se requiere porcentajes_dict para distribución Manual")
        return distribucion_manual(df_proyectos_seleccionados, capital_disponible, porcentajes_dict)
    
    else:
        raise ValueError(f"Tipo de distribución no válido: {tipo_distribucion}")


def normalizar_cartera(cartera_list):
    """
    Convierte lista de dicts a formato estándar para cálculos.
    
    Args:
        cartera_list: list of dict
    
    Returns:
        list of dict con campos estandarizados
    """
    resultado = []
    for proyecto in cartera_list:
        resultado.append({
            'id': proyecto['ID'],
            'nombre': proyecto['Nombre'],
            'inversion_eur': proyecto['Inversion'],
            'inversion_usd': proyecto['Inversion'],  # Se convertirá si es necesario
            'rent_recurrente': float(proyecto.get('Rentab_Recurrente', 0)) or 0,
            'rent_plusvalia': float(proyecto.get('Rentab_Plusvalia', 0)) or 0,
            'meses_renta_totales': int(proyecto.get('Meses_Renta', 24)) or 24,
            'meses_restantes': int(proyecto.get('Meses_Renta', 24)) or 24
        })
    return resultado
