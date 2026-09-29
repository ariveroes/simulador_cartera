"""
PROPUESTA.PY - Lógica centralizada de cartera
MÓDULO CENTRAL para cálculos de inversión inmobiliaria

Maneja:
- Proyectos individuales con precio real (emisión vs OTC)
- Cálculos de importe invertido
- Rentabilidades por estatus
- Carteras completas
- Proyecciones con reinversión
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Proyecto:
    """
    Representa UN proyecto en una cartera.
    Incluye tokens, precio real pagado, y cálculos de rentabilidad.
    """
    
    def __init__(self, 
                 datos_sheet: Dict,
                 tokens: float,
                 precio_compra: Optional[float] = None,
                 estatus: str = 'Reentel'):
        """
        Args:
            datos_sheet: Dict con datos del proyecto (de data_loader)
            tokens: Cantidad de tokens a invertir
            precio_compra: Precio pagado. Si None, usa precio_emision
            estatus: 'Reentel', 'ReentelPro', 'SuperReentel'
        """
        self.datos = datos_sheet
        self.tokens = float(tokens)
        self.estatus = estatus
        
        # Precio real pagado (OTC vs emisión)
        self.precio_emision = float(datos_sheet.get('precio_emision', 0) or 0)
        self.precio_compra = float(precio_compra) if precio_compra else self.precio_emision
        
        # Diferencia para debugging
        self.es_otc = self.precio_compra != self.precio_emision
        self.ahorro = self.precio_emision - self.precio_compra if self.es_otc else 0
    
    def importe_nativo(self) -> float:
        """Calcula importe en divisa nativa del proyecto (EUR/USD)"""
        return self.tokens * self.precio_compra
    
    def importe_eur(self, eurusd: float = 1.0) -> float:
        """Convierte importe a EUR"""
        divisa = self.datos.get('divisa', 'EUR')
        importe_nativo = self.importe_nativo()
        
        if divisa == 'EUR':
            return importe_nativo
        elif divisa == 'USD':
            return importe_nativo / eurusd
        else:
            return importe_nativo
    
    def importe_usd(self, eurusd: float = 1.0) -> float:
        """Convierte importe a USD"""
        divisa = self.datos.get('divisa', 'EUR')
        importe_nativo = self.importe_nativo()
        
        if divisa == 'USD':
            return importe_nativo
        elif divisa == 'EUR':
            return importe_nativo * eurusd
        else:
            return importe_nativo
    
    def rentabilidad_anualizada(self) -> float:
        """Rentabilidad anualizada según estatus (en %)"""
        col_map = {
            'Reentel': 'Rentabilidad_Anualizada_Reentel',
            'ReentelPro': 'Rentabilidad_Anualizada_ReentelPro',
            'SuperReentel': 'Rentabilidad_Anualizada_SuperReentel'
        }
        
        col = col_map.get(self.estatus, col_map['Reentel'])
        valor = self.datos.get(col, 0)
        
        # Limpiar si viene como string con %
        if isinstance(valor, str):
            valor = valor.replace('%', '').strip()
        
        try:
            return float(valor) / 100  # Convertir a decimal (ej: 12 → 0.12)
        except:
            return 0.0
    
    def rentabilidad_total(self) -> float:
        """Rentabilidad total según estatus (en %)"""
        col_map = {
            'Reentel': 'Rentabilidad_Total_Reentel',
            'ReentelPro': 'Rentabilidad_Total_ReentelPro',
            'SuperReentel': 'Rentabilidad_Total_SuperReentel'
        }
        
        col = col_map.get(self.estatus, col_map['Reentel'])
        valor = self.datos.get(col, 0)
        
        if isinstance(valor, str):
            valor = valor.replace('%', '').strip()
        
        try:
            return float(valor) / 100
        except:
            return 0.0
    
    def ganancia_esperada(self, eurusd: float = 1.0, plazo_meses: int = 12) -> float:
        """
        Ganancia esperada en EUR
        
        Args:
            eurusd: Tipo de cambio
            plazo_meses: Plazo para proyección (default 12 meses)
        """
        importe = self.importe_eur(eurusd)
        rentabilidad_anual = self.rentabilidad_anualizada()
        
        # Proyectar según plazo
        tasa_mensual = rentabilidad_anual / 12
        ganancia = importe * (((1 + tasa_mensual) ** plazo_meses) - 1)
        
        return ganancia
    
    def capital_final(self, eurusd: float = 1.0, plazo_meses: int = 12) -> float:
        """Capital final después de rentabilidad"""
        return self.importe_eur(eurusd) + self.ganancia_esperada(eurusd, plazo_meses)
    
    def to_dict(self) -> Dict:
        """Retorna proyección como dict (para PDF, sesión, etc.)"""
        return {
            'id': self.datos.get('ID'),
            'nombre': self.datos.get('Nombre del proyecto'),
            'ubicacion': self.datos.get('Ubicación'),
            'tokens': round(self.tokens, 3),
            'precio_compra': round(self.precio_compra, 2),
            'precio_emision': round(self.precio_emision, 2),
            'es_otc': self.es_otc,
            'ahorro': round(self.ahorro * self.tokens, 2) if self.es_otc else 0,
            'importe_nativo': round(self.importe_nativo(), 2),
            'rentabilidad_anualizada': round(self.rentabilidad_anualizada() * 100, 2),
            'rentabilidad_total': round(self.rentabilidad_total() * 100, 2),
            'estatus': self.estatus,
        }


class Cartera:
    """
    Agrupa múltiples proyectos.
    Centraliza cálculos de cartera completa y proyecciones.
    """
    
    def __init__(self, estatus: str = 'Reentel', eurusd: float = 1.0):
        """
        Args:
            estatus: Estatus del inversor
            eurusd: Tipo de cambio EUR/USD
        """
        self.estatus = estatus
        self.eurusd = eurusd
        self.proyectos: List[Proyecto] = []
        self.fecha_creacion = datetime.now()
    
    def agregar(self, proyecto: Proyecto) -> None:
        """Agrega un proyecto a la cartera"""
        if not isinstance(proyecto, Proyecto):
            raise ValueError("Debe ser instancia de Proyecto")
        self.proyectos.append(proyecto)
    
    def numero_proyectos(self) -> int:
        """Número de proyectos en cartera"""
        return len(self.proyectos)
    
    def importe_total_eur(self) -> float:
        """Importe total invertido en EUR"""
        return sum(p.importe_eur(self.eurusd) for p in self.proyectos)
    
    def importe_total_usd(self) -> float:
        """Importe total invertido en USD"""
        return sum(p.importe_usd(self.eurusd) for p in self.proyectos)
    
    def rentabilidad_promedio_ponderada(self) -> float:
        """
        Rentabilidad anualizada promedio ponderada por importe
        (no por número de proyectos)
        """
        if not self.proyectos:
            return 0.0
        
        total_importe = self.importe_total_eur()
        if total_importe == 0:
            return 0.0
        
        suma_ponderada = sum(
            p.importe_eur(self.eurusd) * p.rentabilidad_anualizada()
            for p in self.proyectos
        )
        
        return suma_ponderada / total_importe
    
    def proyeccion(self, plazo_meses: int = 12) -> Dict:
        """
        Proyecciona la cartera en un plazo determinado
        
        Returns:
            Dict con: capital_inicial, capital_final, ganancia, rentabilidad_pct
        """
        capital_inicial = self.importe_total_eur()
        
        if capital_inicial == 0:
            return {
                'plazo_meses': plazo_meses,
                'capital_inicial': 0,
                'capital_final': 0,
                'ganancia': 0,
                'rentabilidad_pct': 0,
            }
        
        rentabilidad_anual = self.rentabilidad_promedio_ponderada()
        tasa_mensual = rentabilidad_anual / 12
        capital_final = capital_inicial * ((1 + tasa_mensual) ** plazo_meses)
        ganancia = capital_final - capital_inicial
        
        return {
            'plazo_meses': plazo_meses,
            'capital_inicial': round(capital_inicial, 2),
            'capital_final': round(capital_final, 2),
            'ganancia': round(ganancia, 2),
            'rentabilidad_pct': round((capital_final / capital_inicial - 1) * 100, 2) if capital_inicial > 0 else 0,
        }
    
    def proyecciones_multiples(self, plazos: List[int] = None) -> List[Dict]:
        """Proyecciones para múltiples plazos"""
        if plazos is None:
            plazos = [6, 12, 24, 36, 60]
        
        return [self.proyeccion(plazo) for plazo in plazos]
    
    def to_dataframe(self) -> pd.DataFrame:
        """Retorna cartera como DataFrame"""
        datos = [p.to_dict() for p in self.proyectos]
        return pd.DataFrame(datos)
    
    def resumen(self) -> Dict:
        """Resumen completo de la cartera"""
        return {
            'numero_proyectos': self.numero_proyectos(),
            'estatus': self.estatus,
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'importe_total_eur': round(self.importe_total_eur(), 2),
            'importe_total_usd': round(self.importe_total_usd(), 2),
            'rentabilidad_promedio_anualizada': round(self.rentabilidad_promedio_ponderada() * 100, 2),
            'proyectos': self.to_dataframe().to_dict('records'),
            'proyecciones': self.proyecciones_multiples(),
        }


# ============================================================================
# FUNCIONES DE ALTO NIVEL
# ============================================================================

def construir_cartera(seleccion: List[Tuple], 
                      df_proyectos: pd.DataFrame,
                      estatus: str = 'Reentel',
                      eurusd: float = 1.0) -> Cartera:
    """
    Construye una cartera a partir de la selección del usuario
    
    Args:
        seleccion: Lista de tuplas (proyecto_row, tokens, precio_compra)
                   donde proyecto_row es un pd.Series del DataFrame
        df_proyectos: DataFrame con datos de todos los proyectos
        estatus: Estatus del inversor
        eurusd: Tipo de cambio
    
    Returns:
        Cartera con todos los proyectos agregados
    """
    cartera = Cartera(estatus, eurusd)
    
    for item in seleccion:
        # Manejar ambos formatos: tupla o dict
        if isinstance(item, dict):
            proyecto_row = item['proyecto']
            tokens = item['tokens']
            precio_compra = item.get('precio_compra')
        else:
            # Tupla (proyecto, tokens, precio_compra)
            if len(item) == 3:
                proyecto_row, tokens, precio_compra = item
            else:
                # Tupla (proyecto, tokens) - compatible hacia atrás
                proyecto_row, tokens = item
                precio_compra = None
        
        # Convertir pd.Series a dict si es necesario
        if isinstance(proyecto_row, pd.Series):
            datos_dict = proyecto_row.to_dict()
        else:
            datos_dict = proyecto_row
        
        # Crear proyecto y agregar a cartera
        proyecto = Proyecto(
            datos_sheet=datos_dict,
            tokens=tokens,
            precio_compra=precio_compra,
            estatus=estatus
        )
        cartera.agregar(proyecto)
    
    return cartera


def resumir_cartera_para_pdf(cartera: Cartera) -> Dict:
    """
    Prepara resumen de cartera para PDF
    
    Returns:
        Dict listo para pasar a pdf_generator.py
    """
    return {
        'numero_proyectos': cartera.numero_proyectos(),
        'estatus': cartera.estatus,
        'importe_total_eur': cartera.importe_total_eur(),
        'importe_total_usd': cartera.importe_total_usd(),
        'rentabilidad_promedio': cartera.rentabilidad_promedio_ponderada() * 100,
        'proyectos': cartera.to_dataframe().to_dict('records'),
        'proyecciones': cartera.proyecciones_multiples(),
    }
