"""
DATA LOADER - Acceso a Google Sheets e importación de proyectos
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import requests
from datetime import datetime, timedelta
import json
from config.constants import (
    SHEET_INTERMEDIO_GSHEET_ID,
    SHEET_INTERMEDIO_WORKSHEET_NAME,
    TIPO_CAMBIO_API,
    TIMEOUT_API
)


@st.cache_resource
def obtener_cliente_gspread():
    """
    Obtiene cliente autenticado de gspread.
    Requiere archivo de credenciales en Streamlit secrets.
    """
    try:
        # Para Streamlit Cloud: usar st.secrets
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            creds_dict = st.secrets['gcp_service_account']
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_info(
                creds_dict, scopes=scopes
            )
            return gspread.authorize(creds)
        else:
            # Para desarrollo local: archivo service_account.json
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                'service_account.json', scopes=scopes
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error autenticando con Google Sheets: {e}")
        return None


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """Carga proyectos desde datos simulados (sin Google Sheets)"""
    try:
        from test_data import crear_df_prueba
        df = crear_df_prueba()
        st.success(f"✅ Cargados {len(df)} proyectos (datos simulados)")
        return df
    except Exception as e:
        st.error(f"Error cargando proyectos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=86400)  # Caché de 24 horas (fin del día)
def obtener_tipo_cambio_eur_usd():
    """
    Obtiene tipo de cambio EUR → USD.
    Se cachea por 24 horas para evitar llamadas constantes.
    
    Returns:
        float: Tipo de cambio EUR/USD
    """
    try:
        response = requests.get(TIPO_CAMBIO_API, timeout=TIMEOUT_API)
        response.raise_for_status()
        
        data = response.json()
        tasa = data['rates']['USD']
        
        return tasa
        
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Error obteniendo tipo de cambio: {e}")
        # Retornar un valor por defecto (último conocido)
        return 1.08  # Valor aproximado


def convertir_moneda(cantidad, de_divisa, a_divisa, tipo_cambio=None):
    """
    Convierte cantidad entre EUR y USD.
    
    Args:
        cantidad: float
        de_divisa: str ("EUR" o "USD")
        a_divisa: str ("EUR" o "USD")
        tipo_cambio: float (EUR/USD). Si None, se obtiene automáticamente.
    
    Returns:
        float: cantidad convertida
    """
    if de_divisa == a_divisa:
        return cantidad
    
    if tipo_cambio is None:
        tipo_cambio = obtener_tipo_cambio_eur_usd()
    
    if de_divisa == "EUR" and a_divisa == "USD":
        return cantidad * tipo_cambio
    elif de_divisa == "USD" and a_divisa == "EUR":
        return cantidad / tipo_cambio
    else:
        return cantidad


def limpiar_datos_proyectos(df):
    """
    Limpia y prepara DataFrame de proyectos.
    Convierte tipos de datos, elimina duplicados, etc.
    
    Args:
        df: DataFrame crudo de Google Sheets
    
    Returns:
        DataFrame limpio
    """
    if df.empty:
        return df
    
    # Renombrar columnas si es necesario
    # (adaptarse al nombre exacto de las columnas del Sheet)
    
    # Convertir columnas numéricas
    columnas_numericas = [
        'Nº de Tokens',
        'Px Emisión Token',
        'Importe proyecto en €',
        'Importe proyecto en $',
        'Estimación Rentab. Total Reentel',
        'Estimación Rentab. Rendim. Recurr. anualizados Reentel',
        'Estimación Rentab. Plusvalía Reentel',
        'Estimación Rentab. Total RP',
        'Estimación Rentab. Rendim. Recurr. anualizados RP',
        'Estimación Rentab. Plusvalía RP',
        'Estimación Rentab. Total SR',
        'Estimación Rentab. Rendim. Recurr. anualizados SR',
        'Estimación Rentab. Plusvalía SR',
        'Estimación Nº Años desde Lanzamiento',
        'Estimación Nº Meses desde Lanzamiento',
        'Nº Meses restantes de renta hasta Estimación fin'
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convertir fechas
    columnas_fechas = [
        'LANZAMIENTO',
        'Estimación fecha Inicio de Renta desde Lanzamiento',
        'Estimación fecha de fin desde Lanzamiento'
    ]
    
    for col in columnas_fechas:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Eliminar filas sin ID
    df = df.dropna(subset=['ID'])
    
    # Eliminar duplicados por ID
    df = df.drop_duplicates(subset=['ID'], keep='first')
    
    return df.reset_index(drop=True)


def filtrar_proyectos_por_estado(df, estados_validos=None):
    """
    Filtra proyectos por estado.
    
    Args:
        df: DataFrame de proyectos
        estados_validos: lista de estados a incluir. 
                        Si None, excluye CERRADO
    
    Returns:
        DataFrame filtrado
    """
    if df.empty:
        return df
    
    if 'ESTADO' not in df.columns:
        return df
    
    if estados_validos is None:
        # Por defecto, excluir CERRADO
        df = df[df['ESTADO'] != 'CERRADO']
    else:
        df = df[df['ESTADO'].isin(estados_validos)]
    
    return df


def obtener_proyectos_primaria(df):
    """
    Filtra proyectos en venta primaria.
    
    Venta primaria = PRELANZAMIENTO + FINANCIÁNDOSE
    
    Args:
        df: DataFrame de proyectos
    
    Returns:
        DataFrame con solo proyectos primaria
    """
    if df.empty or 'ESTADO' not in df.columns:
        return df
    
    primaria = ['PRELANZAMIENTO', 'FINANCIÁNDOSE']
    return df[df['ESTADO'].isin(primaria)]


def obtener_proyectos_p2p(df):
    """
    Filtra proyectos en P2P (todos excepto CERRADO y primaria).
    
    Args:
        df: DataFrame de proyectos
    
    Returns:
        DataFrame con solo proyectos P2P
    """
    if df.empty or 'ESTADO' not in df.columns:
        return df
    
    # P2P = Todo lo que NO es CERRADO y NO es primaria
    primaria = ['PRELANZAMIENTO', 'FINANCIÁNDOSE']
    
    p2p = df[(df['ESTADO'] != 'CERRADO') & (~df['ESTADO'].isin(primaria))]
    
    return p2p


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test local
    print("Probando data loader...")
    
    df = cargar_proyectos()
    print(f"Cargados {len(df)} proyectos")
    print(df.head())
    
    tasa = obtener_tipo_cambio_eur_usd()
    print(f"Tipo de cambio EUR/USD: {tasa}")
