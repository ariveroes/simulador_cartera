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


def excel_col_to_index(col_ref):
    """Convierte referencia de Excel (A, B, AA, BR, etc) a índice 0-based"""
    col_ref = col_ref.upper()
    result = 0
    for char in col_ref:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1  # Convertir a 0-based


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
        'Rentabilidad_Total_SuperReentel',
        'Rentabilidad_Total_ReentelPro',
        'Rentabilidad_Total_Reentel',
        'Rentabilidad_Anualizada_SuperReentel',
        'Rentabilidad_Anualizada_ReentelPro',
        'Rentabilidad_Anualizada_Reentel'
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            except Exception:
                pass
    
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
        
        # Datos desde fila 3 (índice 2)
        datos_filas = todas_las_filas[2:]
        
        # Normalizar todas las filas al número de columnas máximo
        max_cols = max(len(fila) for fila in datos_filas) if datos_filas else 0
        datos_normalizados = []
        for fila in datos_filas:
            fila_ajustada = (fila + [''] * max_cols)[:max_cols]
            datos_normalizados.append(fila_ajustada)
        
        # Mapear columnas por referencia de Excel
        col_indices = {
            'ID': excel_col_to_index('A'),
            'Nombre del proyecto': excel_col_to_index('B'),
            'ESTADO': excel_col_to_index('C'),
            'Fecha_Inicio': excel_col_to_index('H'),
            'Fecha_Inicio_Alt': excel_col_to_index('E'),
            'Fecha_Fin': excel_col_to_index('I'),
            'Fecha_Fin_Alt': excel_col_to_index('F'),
            'Ubicación': excel_col_to_index('O'),
            'Rentabilidad_Total_SuperReentel': excel_col_to_index('BR'),
            'Rentabilidad_Total_SuperReentel_Alt': excel_col_to_index('AE'),
            'Rentabilidad_Total_ReentelPro': excel_col_to_index('BM'),
            'Rentabilidad_Total_ReentelPro_Alt': excel_col_to_index('AA'),
            'Rentabilidad_Total_Reentel': excel_col_to_index('BH'),
            'Rentabilidad_Total_Reentel_Alt': excel_col_to_index('W'),
            'Rentabilidad_Anualizada_SuperReentel': excel_col_to_index('BU'),
            'Rentabilidad_Anualizada_SuperReentel_Alt': excel_col_to_index('AH'),
            'Rentabilidad_Anualizada_ReentelPro': excel_col_to_index('BP'),
            'Rentabilidad_Anualizada_ReentelPro_Alt': excel_col_to_index('AD'),
            'Rentabilidad_Anualizada_Reentel': excel_col_to_index('BK'),
            'Rentabilidad_Anualizada_Reentel_Alt': excel_col_to_index('Z'),
        }
        
        # Crear DataFrame extrayendo por índices
        datos_mapeados = []
        for fila in datos_normalizados:
            fila_dict = {}
            
            # Copiar columnas directamente
            fila_dict['ID'] = fila[col_indices['ID']] if col_indices['ID'] < len(fila) else ''
            fila_dict['Nombre del proyecto'] = fila[col_indices['Nombre del proyecto']] if col_indices['Nombre del proyecto'] < len(fila) else ''
            fila_dict['ESTADO'] = fila[col_indices['ESTADO']] if col_indices['ESTADO'] < len(fila) else ''
            fila_dict['Ubicación'] = fila[col_indices['Ubicación']] if col_indices['Ubicación'] < len(fila) else ''
            
            # Fechas (usar alternativa si principal está vacía)
            fecha_inicio_principal = fila[col_indices['Fecha_Inicio']] if col_indices['Fecha_Inicio'] < len(fila) else ''
            fila_dict['Fecha Inicio Estimada'] = fecha_inicio_principal if fecha_inicio_principal.strip() else (
                fila[col_indices['Fecha_Inicio_Alt']] if col_indices['Fecha_Inicio_Alt'] < len(fila) else ''
            )
            
            fecha_fin_principal = fila[col_indices['Fecha_Fin']] if col_indices['Fecha_Fin'] < len(fila) else ''
            fila_dict['Fecha Fin Estimada'] = fecha_fin_principal if fecha_fin_principal.strip() else (
                fila[col_indices['Fecha_Fin_Alt']] if col_indices['Fecha_Fin_Alt'] < len(fila) else ''
            )
            
            # Rentabilidades SuperReentel
            rent_sr = fila[col_indices['Rentabilidad_Total_SuperReentel']] if col_indices['Rentabilidad_Total_SuperReentel'] < len(fila) else ''
            fila_dict['Rentabilidad_Total_SuperReentel'] = rent_sr if rent_sr.strip() else (
                fila[col_indices['Rentabilidad_Total_SuperReentel_Alt']] if col_indices['Rentabilidad_Total_SuperReentel_Alt'] < len(fila) else '0'
            )
            
            rent_sr_anual = fila[col_indices['Rentabilidad_Anualizada_SuperReentel']] if col_indices['Rentabilidad_Anualizada_SuperReentel'] < len(fila) else ''
            fila_dict['Rentabilidad_Anualizada_SuperReentel'] = rent_sr_anual if rent_sr_anual.strip() else (
                fila[col_indices['Rentabilidad_Anualizada_SuperReentel_Alt']] if col_indices['Rentabilidad_Anualizada_SuperReentel_Alt'] < len(fila) else '0'
            )
            
            # Rentabilidades ReentelPro
            rent_rp = fila[col_indices['Rentabilidad_Total_ReentelPro']] if col_indices['Rentabilidad_Total_ReentelPro'] < len(fila) else ''
            fila_dict['Rentabilidad_Total_ReentelPro'] = rent_rp if rent_rp.strip() else (
                fila[col_indices['Rentabilidad_Total_ReentelPro_Alt']] if col_indices['Rentabilidad_Total_ReentelPro_Alt'] < len(fila) else '0'
            )
            
            rent_rp_anual = fila[col_indices['Rentabilidad_Anualizada_ReentelPro']] if col_indices['Rentabilidad_Anualizada_ReentelPro'] < len(fila) else ''
            fila_dict['Rentabilidad_Anualizada_ReentelPro'] = rent_rp_anual if rent_rp_anual.strip() else (
                fila[col_indices['Rentabilidad_Anualizada_ReentelPro_Alt']] if col_indices['Rentabilidad_Anualizada_ReentelPro_Alt'] < len(fila) else '0'
            )
            
            # Rentabilidades Reentel
            rent_r = fila[col_indices['Rentabilidad_Total_Reentel']] if col_indices['Rentabilidad_Total_Reentel'] < len(fila) else ''
            fila_dict['Rentabilidad_Total_Reentel'] = rent_r if rent_r.strip() else (
                fila[col_indices['Rentabilidad_Total_Reentel_Alt']] if col_indices['Rentabilidad_Total_Reentel_Alt'] < len(fila) else '0'
            )
            
            rent_r_anual = fila[col_indices['Rentabilidad_Anualizada_Reentel']] if col_indices['Rentabilidad_Anualizada_Reentel'] < len(fila) else ''
            fila_dict['Rentabilidad_Anualizada_Reentel'] = rent_r_anual if rent_r_anual.strip() else (
                fila[col_indices['Rentabilidad_Anualizada_Reentel_Alt']] if col_indices['Rentabilidad_Anualizada_Reentel_Alt'] < len(fila) else '0'
            )
            
            datos_mapeados.append(fila_dict)
        
        df = pd.DataFrame(datos_mapeados)
        
        # Limpiar tipos de datos
        df = limpiar_datos_proyectos(df)
        
        # Filtrar SOLO FINANCIÁNDOSE
        if 'ESTADO' in df.columns:
            df_financiando = df[df['ESTADO'] == 'FINANCIÁNDOSE'].copy()
        else:
            st.warning("Columna ESTADO no encontrada en el sheet")
            df_financiando = df.copy()
        
        if len(df_financiando) == 0:
            st.warning("No hay proyectos en estado FINANCIÁNDOSE")
        else:
            st.success(f"✅ Cargados {len(df_financiando)} proyectos en FINANCIÁNDOSE")
        
        return df_financiando
        
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")
        return pd.DataFrame()
