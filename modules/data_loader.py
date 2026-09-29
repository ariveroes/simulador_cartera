"""
DATA_LOADER.PY - V4 FINAL

CAMBIOS:
✅ Lee via maestro.py (gspread auténticado)
✅ Convierte lista de dicts a DataFrame
✅ Mapea nombres de columnas a lo que espera app.py
✅ Solo filtra proyectos FINANCIÁNDOSE
"""

import pandas as pd
import streamlit as st
from modules import maestro


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet usando maestro.py (gspread)
    
    Retorna: DataFrame con columnas mapeadas para app.py
    Solo retorna proyectos en FINANCIÁNDOSE.
    """
    try:
        # Obtener lista de dicts de maestro.py
        todos_proyectos = maestro.proyectos()
        
        if not todos_proyectos:
            st.warning("No se encontraron proyectos en el Sheet")
            return pd.DataFrame()
        
        # Filtrar solo FINANCIÁNDOSE
        proyectos_financiando = [
            p for p in todos_proyectos 
            if p.get("estado", "").upper() == "FINANCIÁNDOSE"
        ]
        
        if not proyectos_financiando:
            st.warning("No hay proyectos en estado FINANCIÁNDOSE")
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(proyectos_financiando)
        
        # Mapear nombres de columnas a lo que espera app.py
        # maestro.py retorna minúsculas, app.py espera con formato específico
        mapeo_columnas = {
            'id': 'ID',
            'nombre': 'Nombre del proyecto',
            'estado': 'ESTADO',
            'ubicacion': 'Ubicación',
            'tipologia_dividendo': 'Tipología de Dividendo',
            'precio_emision': 'Precio Emisión',
            'divisa': 'Divisa',
            'meses_pendientes': 'Meses Pendientes',
            'address': 'Token Address',
            'emision': 'Emisión',
            'est_anual_rnt': 'Rentabilidad_Anualizada_Reentel',
            'est_anual_rp': 'Rentabilidad_Anualizada_ReentelPro',
            'est_anual_sr': 'Rentabilidad_Anualizada_SuperReentel',
            'est_total_rnt': 'Rentabilidad_Total_Reentel',
            'est_total_rp': 'Rentabilidad_Total_ReentelPro',
            'est_total_sr': 'Rentabilidad_Total_SuperReentel',
        }
        
        # Renombrar solo las columnas que existen
        columnas_a_renombrar = {k: v for k, v in mapeo_columnas.items() if k in df.columns}
        df = df.rename(columns=columnas_a_renombrar)
        
        st.success(f"✅ Cargados {len(df)} proyectos en FINANCIÁNDOSE")
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
