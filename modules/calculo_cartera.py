"""
CÁLCULOS FINANCIEROS - Rentabilidades, reinversión, interés compuesto
Replicación de fórmulas del Sheet 1, pestaña Cálculos
"""

import numpy as np
import pandas as pd
from config.constants import REINVERSION_RATES, STAKING_RATE, HORIZONTES_CALCULO


class CalculadoraCartera:
    """
    Calcula rentabilidades de cartera con y sin reinversión.
    """
    
    def __init__(self, estatus, tasa_reinversion=None):
        """
        Args:
            estatus: str ("Reentel", "ReentelPro", "SuperReentel")
            tasa_reinversion: float (anual). Si None, se usa de REINVERSION_RATES.
        """
        self.estatus = estatus
        self.tasa_reinversion = tasa_reinversion or REINVERSION_RATES.get(estatus, 0.11)
        self.tasa_reinversion_mensual = self.tasa_reinversion / 12
        
    def calcular_rentabilidades_cartera(self, proyectos_seleccionados, capital_inicial):
        """
        Calcula rentabilidades SIN reinversión para la cartera.
        
        Args:
            proyectos_seleccionados: list of dict con proyectos y su inversión
                {
                    'id': 'SVQ-1',
                    'nombre': 'Sevilla 1',
                    'inversion_eur': 5000,
                    'inversion_usd': 5400,
                    'rent_recurrente': 0.10,      # % anual
                    'rent_plusvalia': 0.08,        # % total al final
                    'meses_renta_totales': 24,
                    'meses_restantes': 20
                }
            capital_inicial: float (EUR o USD)
        
        Returns:
            dict con rentabilidades
        """
        if not proyectos_seleccionados:
            return {
                'rent_anual_recurrente': 0,
                'rent_plusvalia': 0,
                'rent_total': 0,
                'rent_total_anualizada': 0
            }
        
        # Calcular rentabilidades ponderadas
        total_rent_recurrente = 0
        total_rent_plusvalia = 0
        
        for proyecto in proyectos_seleccionados:
            ponderacion = proyecto['inversion_eur'] / capital_inicial
            
            rent_recurrente = proyecto.get('rent_recurrente', 0) or 0
            rent_plusvalia = proyecto.get('rent_plusvalia', 0) or 0
            
            total_rent_recurrente += rent_recurrente * ponderacion
            total_rent_plusvalia += rent_plusvalia * ponderacion
        
        rent_total = total_rent_recurrente + total_rent_plusvalia
        
        return {
            'rent_anual_recurrente': total_rent_recurrente,
            'rent_plusvalia': total_rent_plusvalia,
            'rent_total': rent_total,
            'rent_total_anualizada': rent_total  # En este caso es anualizada
        }
    
    def valor_final_portfolio_reinversion(self, proyectos_seleccionados, 
                                         capital_inicial, horizonte_meses):
        """
        Calcula valor final del portfolio CON reinversión de dividendos.
        
        FÓRMULA (del Sheet 1, fila 75-91):
        Valor_Final = Capital_Inicial 
                    + ∑ Rendimientos_Recurrentes_Reinvertidos
                    + Plusvalía_Acumulada
                    + Reinversión_de_Plusvalía
        
        Args:
            proyectos_seleccionados: list de proyectos
            capital_inicial: float
            horizonte_meses: int (6, 12, 24, 36, 60)
        
        Returns:
            dict con detalles del valor final
        """
        if not proyectos_seleccionados:
            return {
                'capital_inicial': capital_inicial,
                'valor_final': capital_inicial,
                'ganancia': 0,
                'rentabilidad_acumulada': 0,
                'rentabilidad_anualizada': 0,
                'componentes': {}
            }
        
        # COMPONENTE 1: Capital inicial
        valor_final = capital_inicial
        
        # COMPONENTE 2: Rendimientos recurrentes reinvertidos
        # Fórmula: Inversión * (rentabilidad/12) * ((1+tasa)^meses - 1) / tasa
        rendimientos_reinvertidos = 0
        
        for proyecto in proyectos_seleccionados:
            inversion = proyecto['inversion_eur']
            rent_recurrente = proyecto.get('rent_recurrente', 0) or 0
            meses_renta = proyecto.get('meses_renta_totales', horizonte_meses)
            
            # Meses que realmente hay renta
            meses_efectivos = min(horizonte_meses, meses_renta)
            
            # Rentabilidad mensual
            rent_mensual = rent_recurrente / 12
            
            # Fórmula de interés compuesto
            if self.tasa_reinversion_mensual > 0:
                componente = inversion * rent_mensual * (
                    ((1 + self.tasa_reinversion_mensual) ** meses_efectivos - 1) 
                    / self.tasa_reinversion_mensual
                )
            else:
                # Si tasa es 0, es interés simple
                componente = inversion * rent_mensual * meses_efectivos
            
            rendimientos_reinvertidos += componente
        
        # COMPONENTE 3: Plusvalía y reinversión de plusvalía
        plusvalia_total = 0
        
        for proyecto in proyectos_seleccionados:
            inversion = proyecto['inversion_eur']
            rent_plusvalia = proyecto.get('rent_plusvalia', 0) or 0
            meses_renta = proyecto.get('meses_renta_totales', horizonte_meses)
            
            plusvalia_proyecto = inversion * rent_plusvalia
            
            # Si el proyecto termina antes del horizonte, reinvertir la plusvalía
            if horizonte_meses >= meses_renta:
                meses_reinv = horizonte_meses - meses_renta
                if meses_reinv > 0:
                    # Reinvertir a la tasa de reinversión
                    plusvalia_reinvertida = plusvalia_proyecto * (
                        (1 + self.tasa_reinversion_mensual) ** meses_reinv
                    )
                    plusvalia_total += plusvalia_reinvertida
                else:
                    plusvalia_total += plusvalia_proyecto
            else:
                # No hay plusvalía aún (proyecto no ha terminado)
                plusvalia_total += 0
        
        # Valor final
        valor_final = capital_inicial + rendimientos_reinvertidos + plusvalia_total
        
        # Cálculos de rentabilidad
        ganancia = valor_final - capital_inicial
        rentabilidad_acumulada = ganancia / capital_inicial if capital_inicial > 0 else 0
        
        # Rentabilidad anualizada: (valor_final/capital)^(12/meses) - 1
        if horizonte_meses > 0 and capital_inicial > 0:
            rentabilidad_anualizada = (valor_final / capital_inicial) ** (12 / horizonte_meses) - 1
        else:
            rentabilidad_anualizada = 0
        
        return {
            'capital_inicial': capital_inicial,
            'valor_final': valor_final,
            'ganancia': ganancia,
            'rentabilidad_acumulada': rentabilidad_acumulada,
            'rentabilidad_anualizada': rentabilidad_anualizada,
            'componentes': {
                'rendimientos_reinvertidos': rendimientos_reinvertidos,
                'plusvalia': plusvalia_total
            }
        }
    
    def calcular_cartera_completa(self, proyectos_seleccionados, capital_inicial):
        """
        Calcula cartera para TODOS los horizontes de cálculo.
        
        Returns:
            dict con resultados para cada horizonte
        """
        resultados = {}
        
        for horizonte in HORIZONTES_CALCULO:
            resultados[horizonte] = self.valor_final_portfolio_reinversion(
                proyectos_seleccionados, capital_inicial, horizonte
            )
        
        return resultados


def calcular_score_similitud(proyecto, criterios_cliente, estatus_cliente):
    """
    Calcula score de similitud entre proyecto y preferencias del cliente.
    
    SIMILITUD: max 3 puntos
    - Duración coincide: 1 punto
    - Rendimiento coincide: 1 punto
    - Ubicación coincide: 1 punto
    
    Args:
        proyecto: dict/row del proyecto
        criterios_cliente: dict con preferencias
        estatus_cliente: str
    
    Returns:
        float (0-3)
    """
    similitud = 0
    
    # Duración
    if 'Estimación Nº Meses desde Lanzamiento' in proyecto:
        meses = proyecto['Estimación Nº Meses desde Lanzamiento']
        if criterios_cliente.get('duracion') == 'Corto plazo' and meses <= 18:
            similitud += 1
        elif criterios_cliente.get('duracion') == 'Largo plazo' and meses > 18:
            similitud += 1
    
    # Rendimiento
    if 'Tipología de Dividendo' in proyecto:
        tipologia = proyecto['Tipología de Dividendo']
        preferencias_rend = criterios_cliente.get('rendimientos', ['Periódicos', 'Finales'])
        
        if 'Periódicos' in preferencias_rend and tipologia != 'rendimientos a final del proyecto':
            similitud += 1
        elif 'Finales' in preferencias_rend and tipologia == 'rendimientos a final del proyecto':
            similitud += 1
    
    # Ubicación
    if 'Ubicación' in proyecto:
        ubicacion = proyecto['Ubicación']
        if ubicacion in criterios_cliente.get('ubicacion', []):
            similitud += 1
    
    return similitud / 3  # Normalizar 0-1


def calcular_score_rentabilidad(proyecto, estatus_cliente, max_rentabilidad):
    """
    Calcula score de rentabilidad anualizada.
    
    Args:
        proyecto: dict/row del proyecto
        estatus_cliente: str ("Reentel", "ReentelPro", "SuperReentel")
        max_rentabilidad: float (para normalizar 0-1)
    
    Returns:
        float (0-1)
    """
    # Columna de rentabilidad anualizada según estatus
    columnas_rent = {
        'Reentel': 'Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel',
        'ReentelPro': 'Estimación Rentab. Total (Alq. + Plusv.) anualizado RP',
        'SuperReentel': 'Estimación Rentab. Total (Alq. + Plusv.) anualizado SR'
    }
    
    col = columnas_rent.get(estatus_cliente)
    
    if col and col in proyecto:
        rent = float(proyecto[col]) if isinstance(proyecto[col], (int, float)) else 0
        if max_rentabilidad > 0:
            return min(rent / max_rentabilidad, 1.0)  # Cap a 1.0
    
    return 0


def calcular_score_duracion(proyecto, max_meses):
    """
    Calcula score de duración (inverso: menos meses = más score).
    
    Args:
        proyecto: dict/row del proyecto
        max_meses: float (máximos meses en dataset)
    
    Returns:
        float (0-1)
    """
    if 'Nº Meses restantes de renta hasta Estimacion fin' in proyecto:
        meses = proyecto['Nº Meses restantes de renta hasta Estimacion fin']
        if isinstance(meses, (int, float)) and max_meses > 0:
            # Inverso: menos meses = mayor score
            return max(1 - (meses / max_meses), 0)
    
    return 0.5  # Valor por defecto


def rankear_proyectos(df_proyectos, criterios_cliente, estatus_cliente):
    """
    Rankea proyectos por similitud + rentabilidad + duración.
    
    Ponderación: 33% cada uno (todos valen igual)
    
    Args:
        df_proyectos: DataFrame con proyectos
        criterios_cliente: dict con preferencias
        estatus_cliente: str
    
    Returns:
        DataFrame con scores y ranking
    """
    if df_proyectos.empty:
        return df_proyectos
    
    df = df_proyectos.copy()
    
    # Calcular scores individuales
    max_rent = df['Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel'].max()
    max_meses = df['Estimación Nº Meses desde inicio de renta en base a Financiación'].max()
    
    # Normalizar
    if pd.isna(max_rent) or max_rent == 0:
        max_rent = 0.25  # Valor por defecto
    if pd.isna(max_meses) or max_meses == 0:
        max_meses = 60  # Valor por defecto
    
    # Aplicar scoring
    df['score_similitud'] = df.apply(
        lambda row: calcular_score_similitud(row, criterios_cliente, estatus_cliente),
        axis=1
    )
    
    df['score_rentabilidad'] = df.apply(
        lambda row: calcular_score_rentabilidad(row, estatus_cliente, max_rent),
        axis=1
    )
    
    df['score_duracion'] = df.apply(
        lambda row: calcular_score_duracion(row, max_meses),
        axis=1
    )
    
    # Score ponderado (33% cada uno)
    df['score_total'] = (
        df['score_similitud'] * 0.333 + 
        df['score_rentabilidad'] * 0.333 + 
        df['score_duracion'] * 0.334
    )
    
    # Ordenar por score
    df = df.sort_values('score_total', ascending=False).reset_index(drop=True)
    
    return df
