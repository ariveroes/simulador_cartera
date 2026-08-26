"""
DISTRIBUCIÓN DE CAPITAL - Entre proyectos seleccionados
"""

import pandas as pd


def distribuir_capital(df_seleccionados, capital_disponible, tipo_distribucion, porcentajes_manual=None):
    """
    Distribuye capital entre proyectos según tipo.
    
    Args:
        df_seleccionados: DataFrame con proyectos seleccionados
        capital_disponible: float
        tipo_distribucion: str ('Igual', 'Proporcional', 'Manual')
        porcentajes_manual: dict {id: porcentaje}
    
    Returns:
        list de dicts con distribución
    """
    
    if len(df_seleccionados) == 0:
        return []
    
    distribucion = []
    
    if tipo_distribucion == 'Igual':
        # Repartir capital en partes iguales
        capital_por_proyecto = capital_disponible / len(df_seleccionados)
        
        for idx, proyecto in df_seleccionados.iterrows():
            distribucion.append({
                'ID': proyecto.get('ID', ''),
                'Nombre': proyecto.get('Nombre del proyecto', ''),
                'Inversion': capital_por_proyecto,
                'Porcentaje': 100 / len(df_seleccionados),
                'Rentab_Recurrente': float(proyecto.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0)),
                'Rentab_Plusvalia': float(proyecto.get('Estimación Rentab. Plusvalía Reentel', 0)),
                'Estimación Nº Meses desde inicio de renta en base a Financiación': float(proyecto.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24))
            })
    
    elif tipo_distribucion == 'Proporcional':
        # Repartir según importe del proyecto
        total_importe = df_seleccionados.get('Importe proyecto en €', 0).sum()
        
        for idx, proyecto in df_seleccionados.iterrows():
            importe = float(proyecto.get('Importe proyecto en €', 1))
            if total_importe > 0:
                pct = (importe / total_importe) * 100
                inversion = (pct / 100) * capital_disponible
            else:
                pct = 100 / len(df_seleccionados)
                inversion = capital_disponible / len(df_seleccionados)
            
            distribucion.append({
                'ID': proyecto.get('ID', ''),
                'Nombre': proyecto.get('Nombre del proyecto', ''),
                'Inversion': inversion,
                'Porcentaje': pct,
                'Rentab_Recurrente': float(proyecto.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0)),
                'Rentab_Plusvalia': float(proyecto.get('Estimación Rentab. Plusvalía Reentel', 0)),
                'Estimación Nº Meses desde inicio de renta en base a Financiación': float(proyecto.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24))
            })
    
    elif tipo_distribucion == 'Manual' and porcentajes_manual:
        # Repartir según porcentajes manuales
        for idx, proyecto in df_seleccionados.iterrows():
            proyecto_id = proyecto.get('ID', '')
            pct = porcentajes_manual.get(proyecto_id, 0)
            inversion = (pct / 100) * capital_disponible if pct > 0 else 0
            
            distribucion.append({
                'ID': proyecto_id,
                'Nombre': proyecto.get('Nombre del proyecto', ''),
                'Inversion': inversion,
                'Porcentaje': pct * 100,
                'Rentab_Recurrente': float(proyecto.get('Estimación Rentab. Rendim. Recurr. anualizados Reentel', 0)),
                'Rentab_Plusvalia': float(proyecto.get('Estimación Rentab. Plusvalía Reentel', 0)),
                'Estimación Nº Meses desde inicio de renta en base a Financiación': float(proyecto.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24))
            })
    
    return distribucion


def normalizar_cartera(distribucion_list):
    """Convierte lista de distribución a DataFrame normalizado"""
    return pd.DataFrame(distribucion_list)
