"""
DATA_LOADER.PY - V3 REVISADA CON GSPREAD

CAMBIOS:
✅ Ahora usa maestro.py que lee via gspread (auténticado)
✅ Seguro: usa Streamlit secrets
✅ Solo filtra proyectos FINANCIÁNDOSE
"""

import streamlit as st
from modules import maestro


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet usando maestro.py (gspread)
    
    Requiere: st.secrets["gcp_service_account"]
    Solo retorna proyectos en FINANCIÁNDOSE.
    """
    try:
        # maestro.py se encarga de leer el Sheet via gspread, normalizar datos, etc.
        todos_proyectos = maestro.proyectos()
        
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
