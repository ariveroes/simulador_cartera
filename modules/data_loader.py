"""
DATA LOADER - Carga proyectos desde Google Sheets intermedio
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


# Configuración
SHEET_INTERMEDIO_GSHEET_ID = "1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY"
SHEET_INTERMEDIO_WORKSHEET_NAME = "Master Inmuebles Pro"


def obtener_cliente_gspread():
    """Autentica con Google Sheets usando secrets"""
    try:
        creds_dict = st.secrets.get("gcp_service_account")
        
        if not creds_dict:
            st.error("No se encontraron credenciales en Secrets")
            return None
        
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets',
                   'https://www.googleapis.com/auth/drive']
        )
        
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"Error autenticando con Google: {e}")
        return None


def limpiar_datos_proyectos(df):
    """
    Limpia y normaliza tipos de datos.
    Convierte columnas numéricas de string a float.
    """
    
    # Columnas numéricas esperadas
    columnas_numericas = [
        'Estimación Nº Meses desde Lanzamiento',
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel',
        'Estimación Rentab. Plusvalía Reentel',
        'Estimación Rentab. Rendim. Recurr. anualizados RP',
        'Estimación Rentab. Plusvalía RP',
        'Estimación Rentab. Rendim. Recurr. anualizados SR',
        'Estimación Rentab. Plusvalía SR',
        'Importe proyecto en €',
        'Estimación Nº Meses desde inicio de renta en base a Financiación'
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet Intermedio.
    Solo retorna proyectos en FINANCIÁNDOSE.
    """
    try:
        client = obtener_cliente_gspread()
        
        if client is None:
            st.error("No se pudo conectar a Google Sheets")
            return pd.DataFrame()
        
        # Abrir el sheet
        sheet = client.open_by_key(SHEET_INTERMEDIO_GSHEET_ID)
        worksheet = sheet.worksheet(SHEET_INTERMEDIO_WORKSHEET_NAME)
        
        # Obtener todos los valores (headers en fila 2, datos desde fila 3)
        todas_las_filas = worksheet.get_all_values()
        
        if len(todas_las_filas) < 2:
            st.error("Sheet vacío o con estructura incorrecta")
            return pd.DataFrame()
        
        # Headers están en fila 2 (índice 1)
        headers = todas_las_filas[1]
        
        # Datos desde fila 3 (índice 2)
        datos_filas = todas_las_filas[2:]
        
        # Crear DataFrame
        df = pd.DataFrame(datos_filas, columns=headers)
        
        # Limpiar columnas completamente vacías
        df = df.dropna(axis=1, how='all')
        
        # Limpiar tipos de datos
        df = limpiar_datos_proyectos(df)
        
        # Filtrar SOLO FINANCIÁNDOSE
        df_financiando = df[df['ESTADO'] == 'FINANCIÁNDOSE'].copy()
        
        st.success(f"✅ Cargados {len(df_financiando)} proyectos en FINANCIÁNDOSE")
        return df_financiando
        
    except Exception as e:
        st.error(f"Error cargando proyectos: {e}")
        return pd.DataFrame()
