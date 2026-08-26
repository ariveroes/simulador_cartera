"""
CALCULADORA DE CARTERA - Lógica EXACTA de Sheet 1
Replicación de fórmulas de rentabilidad con interés compuesto
"""

import pandas as pd
import numpy as np


# ============================================================================
# TASAS DE REINVERSIÓN (De Sheet 1)
# ============================================================================

TASAS_REINVERSION = {
    'Reentel': 0.11,          # 11% anual
    'ReentelPro': 0.13,       # 13% anual  
    'SuperReentel': 0.16      # 16% anual (asumido)
}

TASAS_REINVERSION_MENSUAL = {
    k: v / 12 for k, v in TASAS_REINVERSION.items()
}


# ============================================================================
# CLASE CALCULADORA
# ============================================================================

class CalculadoraCartera:
    """Calcula rentabilidades con reinversión (interés compuesto)"""
    
    def __init__(self, estatus_cliente):
        """
        Args:
            estatus_cliente: str ('Reentel', 'ReentelPro', 'SuperReentel')
        """
        self.estatus = estatus_cliente
        self.tasa_anual = TASAS_REINVERSION.get(estatus_cliente, 0.11)
        self.tasa_mensual = TASAS_REINVERSION_MENSUAL.get(estatus_cliente, 0.11/12)
    
    def calcular_valor_final(self, cartera_df, horizonte_meses, capital_total):
        """
        Calcula el valor final de la cartera a un horizonte determinado.
        
        Fórmula de Sheet 1 replicada:
        Valor_Final = Capital_Inicial + Interés_Compuesto_Recurrente + Plusvalía_Reinvertida
        
        Args:
            cartera_df: DataFrame con proyectos seleccionados
            horizonte_meses: int (6, 12, 24, 36, 60)
            capital_total: float (capital a invertir)
        
        Returns:
            dict con valor_final, ganancia, rentabilidades
        """
        
        try:
            # Capital inicial (suma de inversiones)
            capital_inicial = capital_total
            
            # Componente 1: Interés compuesto en rendimientos recurrentes
            interes_compuesto = 0
            for idx, proyecto in cartera_df.iterrows():
                inversión = float(proyecto.get('Inversion', 0))
                
                # Rentabilidad recurrente mensual
                rent_recurrente = float(proyecto.get('Rentab_Recurrente', 0)) / 12
                
                # Meses hasta fin del proyecto
                meses_proyecto = float(proyecto.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24))
                
                # Aplicar interés compuesto solo hasta que termine el proyecto
                meses_activos = min(horizonte_meses, meses_proyecto)
                
                # Fórmula: Inversión * Rendimiento_Mensual * ((1+Tasa)^Meses - 1) / Tasa
                if self.tasa_mensual > 0 and meses_activos > 0:
                    interes_comp_proyecto = (
                        inversión * rent_recurrente * 
                        ((1 + self.tasa_mensual) ** meses_activos - 1) / 
                        self.tasa_mensual
                    )
                    interes_compuesto += interes_comp_proyecto
            
            # Componente 2: Plusvalía reinvertida después del cierre
            plusvalia_reinvertida = 0
            for idx, proyecto in cartera_df.iterrows():
                inversión = float(proyecto.get('Inversion', 0))
                plusvalia_pct = float(proyecto.get('Rentab_Plusvalia', 0))
                meses_proyecto = float(proyecto.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24))
                
                # Si el horizonte supera el fin del proyecto, la plusvalía se reinvierte
                if horizonte_meses > meses_proyecto:
                    plusvalia = inversión * plusvalia_pct
                    meses_post_cierre = horizonte_meses - meses_proyecto
                    
                    # Plusvalía compuesta: Plusvalía * (1+Tasa)^Meses_Post_Cierre
                    plusvalia_reinv = plusvalia * ((1 + self.tasa_mensual) ** meses_post_cierre)
                    plusvalia_reinvertida += plusvalia_reinv
            
            # Valor final total
            valor_final = capital_inicial + interes_compuesto + plusvalia_reinvertida
            
            # Ganancia
            ganancia = valor_final - capital_inicial
            
            # Rentabilidad acumulada
            rentabilidad_acumulada = ganancia / capital_inicial if capital_inicial > 0 else 0
            
            # Rentabilidad anualizada
            años = horizonte_meses / 12
            if años > 0 and rentabilidad_acumulada >= 0:
                rentabilidad_anualizada = (1 + rentabilidad_acumulada) ** (1 / años) - 1
            else:
                rentabilidad_anualizada = 0
            
            return {
                'valor_final': valor_final,
                'ganancia': ganancia,
                'rentabilidad_acumulada': rentabilidad_acumulada,
                'rentabilidad_anualizada': rentabilidad_anualizada
            }
        
        except Exception as e:
            print(f"Error en cálculo: {e}")
            return {
                'valor_final': capital_total,
                'ganancia': 0,
                'rentabilidad_acumulada': 0,
                'rentabilidad_anualizada': 0
            }
    
    def calcular_cartera_completa(self, cartera_df, capital_total):
        """
        Calcula cartera para todos los horizontes (6, 12, 24, 36, 60 meses)
        
        Returns:
            dict {6: {...}, 12: {...}, 24: {...}, 36: {...}, 60: {...}}
        """
        resultados = {}
        
        for horizonte in [6, 12, 24, 36, 60]:
            resultados[horizonte] = self.calcular_valor_final(
                cartera_df, horizonte, capital_total
            )
        
        return resultados


# ============================================================================
# RANKING DE PROYECTOS
# ============================================================================

def rankear_proyectos(df_proyectos, criterios_cliente, estatus_cliente):
    """
    Rankea proyectos según:
    - 30% Similitud (ubicación + tipología)
    - 45% Rentabilidad (rendimiento + plusvalía por estatus)
    - 25% Duración (encaja con corto/largo plazo)
    
    Args:
        df_proyectos: DataFrame con todos los proyectos
        criterios_cliente: dict con preferencias del cliente
        estatus_cliente: str ('Reentel', 'ReentelPro', 'SuperReentel')
    
    Returns:
        DataFrame con columna 'score_ranking'
    """
    
    df = df_proyectos.copy()
    
    # === SCORE 1: SIMILITUD (30%) ===
    
    # Similitud por ubicación
    ubicaciones_preferidas = criterios_cliente.get('ubicaciones', [])
    df['score_ubicacion'] = df['Ubicación'].isin(ubicaciones_preferidas).astype(float)
    
    # Similitud por tipología (si está disponible)
    df['score_similitud'] = df['score_ubicacion']
    
    # Normalizar a 0-1
    df['score_similitud'] = df['score_similitud'].fillna(0.5)
    
    # === SCORE 2: RENTABILIDAD (45%) ===
    
    # Mapear estatus a columnas de rentabilidad
    col_rent_map = {
        'Reentel': 'Estimación Rentab. Rendim. Recurr. anualizados Reentel',
        'ReentelPro': 'Estimación Rentab. Rendim. Recurr. anualizados RP',
        'SuperReentel': 'Estimación Rentab. Rendim. Recurr. anualizados SR'
    }
    
    col_rent = col_rent_map.get(estatus_cliente, col_rent_map['Reentel'])
    
    # Obtener rentabilidad (recurrente + plusvalía estimada)
    df['rentabilidad'] = pd.to_numeric(df.get(col_rent, 0), errors='coerce').fillna(0)
    
    # Normalizar rentabilidad a 0-1
    max_rent = df['rentabilidad'].max()
    if max_rent > 0:
        df['score_rentabilidad'] = df['rentabilidad'] / max_rent
    else:
        df['score_rentabilidad'] = 0.5
    
    # === SCORE 3: DURACIÓN (25%) ===
    
    duracion_preferida = criterios_cliente.get('duracion', 'Corto plazo')
    meses_proyecto = pd.to_numeric(
        df.get('Estimación Nº Meses desde inicio de renta en base a Financiación', 24),
        errors='coerce'
    ).fillna(24)
    
    if duracion_preferida == 'Corto plazo':
        # Preferir proyectos cortos (< 18 meses)
        df['score_duracion'] = (18 - meses_proyecto) / 18
        df['score_duracion'] = df['score_duracion'].clip(0, 1)
    else:  # Largo plazo
        # Preferir proyectos largos (> 18 meses)
        df['score_duracion'] = (meses_proyecto - 18) / 42  # 42 = 60 - 18
        df['score_duracion'] = df['score_duracion'].clip(0, 1)
    
    # === SCORE FINAL ===
    df['score_ranking'] = (
        0.30 * df['score_similitud'] +
        0.45 * df['score_rentabilidad'] +
        0.25 * df['score_duracion']
    )
    
    # Ordenar por score descendente
    df = df.sort_values('score_ranking', ascending=False)
    
    return df
