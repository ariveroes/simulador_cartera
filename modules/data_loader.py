"""
DATA_LOADER.PY - V2 REVISADA

CAMBIOS:
✅ Ahora usa maestro.py para leer Google Sheet
✅ Más simple porque maestro.py centraliza la lectura
✅ Solo filtra proyectos FINANCIÁNDOSE
"""

import os
import streamlit as st
from modules import maestro


# URL de Google Sheet exportada como CSV
GSHEET_CSV_URL = os.getenv(
    "GSHEET_CSV_URL",
    "https://docs.google.com/spreadsheets/d/1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY/export?format=csv&gid=0"
)


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet usando maestro.py
    
    Solo retorna proyectos en FINANCIÁNDOSE.
    """
    try:
        # maestro.py se encarga de leer el Sheet, normalizar datos, etc.
        todos_proyectos = maestro.proyectos(GSHEET_CSV_URL)
        
        if not todos_proyectos:
            st.warning("No se encontraron proyectos en el Sheet")
            return []
        
        # Filtrar solo FINANCIÁNDOSE
        proyectos_financiando = [
            p for p in todos_proyectos 
            if p.get("estado", "").upper() == "FINANCIÁNDOSE"
        ]
        
        if not proyectos_financiando:
            st.warning("No hay proyectos en estado FINANCIÁNDOSE")
        else:
            st.success(f"✅ Cargados {len(proyectos_financiando)} proyectos en FINANCIÁNDOSE")
        
        return proyectos_financiando
        
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
