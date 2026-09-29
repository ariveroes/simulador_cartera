"""
CALCULO_CARTERA.PY - SIMPLIFICADO
Mantiene SOLO: rankear_proyectos() y CalculadoraCartera

CAMBIOS VS ORIGINAL:
✅ Se eliminan: normalizar_cartera() (no se usa)
✅ Se elimina: lógica de proyecciones (ahora en propuesta.py)
✅ Se mantiene: rankeo de proyectos (usado en Paso 3)
✅ Se mantiene: CalculadoraCartera (compatible hacia atrás)
"""

import pandas as pd


def rankear_proyectos(df_proyectos, criterios_cliente, estatus_cliente):
    """
    Rankea proyectos según objetivo:
    - Ingresos pasivos: por tipología de dividendo (mensuales > trimestrales > final)
    - Maximizar rentabilidad: por rentabilidad anualizada más alta
    
    Args:
        df_proyectos: DataFrame con proyectos
        criterios_cliente: Dict con 'duracion' (Corto plazo / Largo plazo)
        estatus_cliente: 'Reentel', 'ReentelPro', 'SuperReentel'
    
    Returns:
        DataFrame ordenado por score de ranking
    """
    
    df = df_proyectos.copy()
    
    objetivo = criterios_cliente.get('duracion', 'Corto plazo')
    
    # Mapear estatus a columnas de rentabilidad
    col_rent_map = {
        'Reentel': 'Rentabilidad_Anualizada_Reentel',
        'ReentelPro': 'Rentabilidad_Anualizada_ReentelPro',
        'SuperReentel': 'Rentabilidad_Anualizada_SuperReentel'
    }
    
    col_rent = col_rent_map.get(estatus_cliente, col_rent_map['Reentel'])
    df['rentabilidad'] = pd.to_numeric(df.get(col_rent, 0), errors='coerce').fillna(0)
    
    # === LÓGICA DE RANKING ===
    
    if 'Corto plazo' in str(objetivo):  # Ingresos pasivos periódicos
        # Rankear por tipología de dividendo
        def score_tipologia(tipologia):
            tipologia_str = str(tipologia).lower()
            if 'mensuales' in tipologia_str:
                return 3
            elif 'trimestrales' in tipologia_str:
                return 2
            elif 'final' in tipologia_str:
                return 1
            else:
                return 0
        
        df['score_tipologia'] = df.get('Tipología de dividendo', '').apply(score_tipologia)
        
        # Score de rentabilidad normalizado
        max_rent = df['rentabilidad'].max()
        if max_rent > 0:
            df['score_rentabilidad'] = df['rentabilidad'] / max_rent * 0.3
        else:
            df['score_rentabilidad'] = 0.15
        
        # Score final: 70% tipología, 30% rentabilidad
        df['score_ranking'] = (df['score_tipologia'] / 3 * 0.7) + df['score_rentabilidad']
    
    else:  # Maximizar rentabilidad
        # Rankear SOLO por rentabilidad anualizada
        max_rent = df['rentabilidad'].max()
        if max_rent > 0:
            df['score_ranking'] = df['rentabilidad'] / max_rent
        else:
            df['score_ranking'] = 0.5
    
    # Ordenar por score descendente
    df = df.sort_values('score_ranking', ascending=False).reset_index(drop=True)
    
    return df


class CalculadoraCartera:
    """
    Clase para cálculos de cartera según estatus y parámetros.
    
    NOTA: Esta clase ahora es principalmente para compatibilidad hacia atrás.
    La lógica principal está en propuesta.py:Cartera
    """
    
    TASAS_REINVERSION = {
        'Reentel': 0.11,
        'ReentelPro': 0.13,
        'SuperReentel': 0.16
    }
    
    HORIZONTES = [6, 12, 24, 36, 60]
    
    def __init__(self, estatus):
        self.estatus = estatus
        self.tasa_reinversion = self.TASAS_REINVERSION.get(estatus, 0.11)
    
    def calcular_proyeccion(self, capital_inicial, rentabilidad_anual, meses):
        """
        Calcula proyección de capital con reinversión.
        
        Args:
            capital_inicial: float en EUR
            rentabilidad_anual: float (ej: 0.12 para 12%)
            meses: int (plazo en meses)
        
        Returns:
            float capital final
        """
        if not capital_inicial or rentabilidad_anual is None:
            return capital_inicial
        
        tasa_mensual = rentabilidad_anual / 12
        capital_final = capital_inicial * ((1 + tasa_mensual) ** meses)
        
        return capital_final
    
    def calcular_ganancia(self, capital_inicial, rentabilidad_anual, meses):
        """
        Calcula ganancia absoluta
        
        Returns:
            float ganancia en EUR
        """
        capital_final = self.calcular_proyeccion(capital_inicial, rentabilidad_anual, meses)
        return capital_final - capital_inicial
