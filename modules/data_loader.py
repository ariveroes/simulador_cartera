"""
DATA LOADER - Carga proyectos desde Google Sheets intermedio
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime


# Configuración
SHEET_INTERMEDIO_GSHEET_ID = "1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY"
SHEET_INTERMEDIO_WORKSHEET_NAME = "Master Inmuebles Pro"


def excel_col_to_index(col_ref):
    """Convierte referencia de Excel (A, BR, DC, etc) a índice 1-based para gspread"""
    col_ref = col_ref.upper()
    result = 0
    for char in col_ref:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result


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


def parsear_fecha(fecha_str):
    """
    Convierte fecha DD/MM/YYYY a MM/YYYY
    Si está vacía o inválida, retorna vacío
    """
    if not fecha_str or isinstance(fecha_str, float):
        return ""
    
    fecha_str = str(fecha_str).strip()
    if not fecha_str:
        return ""
    
    try:
        # Parsear DD/MM/YYYY
        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
        # Retornar MM/YYYY
        return fecha_obj.strftime("%m/%Y")
    except:
        return ""


def obtener_valor_columna(worksheet, col_ref, row_num):
    """
    Obtiene valor de una celda específica usando referencia de columna Excel
    col_ref: 'A', 'BR', 'DC', etc
    row_num: número de fila (1-based)
    """
    try:
        col_index = excel_col_to_index(col_ref)
        valor = worksheet.cell(row_num, col_index).value
        return valor if valor else ""
    except:
        return ""


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet Intermedio usando referencias de Excel.
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
        
        # Obtener todas las filas
        todas_las_filas = worksheet.get_all_values()
        
        if len(todas_las_filas) < 3:
            st.error("Sheet vacío o con estructura incorrecta")
            return pd.DataFrame()
        
        # Datos desde fila 3 en adelante (row_num empieza en 3 porque gspread usa 1-based)
        datos_mapeados = []
        
        for row_num in range(3, len(todas_las_filas) + 3):
            fila_dict = {}
            
            # Obtener valores usando referencias de Excel exactas
            id_val = obtener_valor_columna(worksheet, 'A', row_num)
            nombre_val = obtener_valor_columna(worksheet, 'B', row_num)
            estado_val = obtener_valor_columna(worksheet, 'C', row_num)
            ubicacion_val = obtener_valor_columna(worksheet, 'O', row_num)
            
            # Si no hay ID o nombre, saltar la fila
            if not id_val or not nombre_val:
                continue
            
            fila_dict['ID'] = id_val
            fila_dict['Nombre del proyecto'] = nombre_val
            fila_dict['ESTADO'] = estado_val
            fila_dict['Ubicación'] = ubicacion_val
            
            # Fechas de inicio (H, o si está vacío usar E)
            fecha_inicio_h = obtener_valor_columna(worksheet, 'H', row_num)
            if fecha_inicio_h:
                fila_dict['Fecha Inicio Estimada'] = parsear_fecha(fecha_inicio_h)
            else:
                fecha_inicio_e = obtener_valor_columna(worksheet, 'E', row_num)
                fila_dict['Fecha Inicio Estimada'] = parsear_fecha(fecha_inicio_e)
            
            # Fechas de fin (I, o si está vacío usar F)
            fecha_fin_i = obtener_valor_columna(worksheet, 'I', row_num)
            if fecha_fin_i:
                fila_dict['Fecha Fin Estimada'] = parsear_fecha(fecha_fin_i)
            else:
                fecha_fin_f = obtener_valor_columna(worksheet, 'F', row_num)
                fila_dict['Fecha Fin Estimada'] = parsear_fecha(fecha_fin_f)
            
            # Rentabilidades SuperReentel
            rent_sr = obtener_valor_columna(worksheet, 'BR', row_num)
            fila_dict['Rentabilidad_Total_SuperReentel'] = rent_sr if rent_sr else (
                obtener_valor_columna(worksheet, 'AE', row_num)
            )
            
            rent_sr_anual = obtener_valor_columna(worksheet, 'BU', row_num)
            fila_dict['Rentabilidad_Anualizada_SuperReentel'] = rent_sr_anual if rent_sr_anual else (
                obtener_valor_columna(worksheet, 'AH', row_num)
            )
            
            # Rentabilidades ReentelPro
            rent_rp = obtener_valor_columna(worksheet, 'BM', row_num)
            fila_dict['Rentabilidad_Total_ReentelPro'] = rent_rp if rent_rp else (
                obtener_valor_columna(worksheet, 'AA', row_num)
            )
            
            rent_rp_anual = obtener_valor_columna(worksheet, 'BP', row_num)
            fila_dict['Rentabilidad_Anualizada_ReentelPro'] = rent_rp_anual if rent_rp_anual else (
                obtener_valor_columna(worksheet, 'AD', row_num)
            )
            
            # Rentabilidades Reentel
            rent_r = obtener_valor_columna(worksheet, 'BH', row_num)
            fila_dict['Rentabilidad_Total_Reentel'] = rent_r if rent_r else (
                obtener_valor_columna(worksheet, 'W', row_num)
            )
            
            rent_r_anual = obtener_valor_columna(worksheet, 'BK', row_num)
            fila_dict['Rentabilidad_Anualizada_Reentel'] = rent_r_anual if rent_r_anual else (
                obtener_valor_columna(worksheet, 'Z', row_num)
            )
            
            datos_mapeados.append(fila_dict)
        
        if not datos_mapeados:
            st.warning("No se encontraron datos en el sheet")
            return pd.DataFrame()
        
        df = pd.DataFrame(datos_mapeados)
        
        # Convertir columnas numéricas
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
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
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
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
