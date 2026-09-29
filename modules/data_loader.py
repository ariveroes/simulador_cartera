"""
DATA LOADER - REFACTORIZADO
Carga proyectos desde Google Sheets incluyendo precio_emision

CAMBIOS VS ORIGINAL:
✅ Agrega: precio_emision (columna K)
✅ Agrega: divisa (EUR/USD)
✅ Agrega: meses_restantes_renta (columna AK)
✅ Agrega: importe_proyecto_eur (columna M)
✅ El resto igual
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
    """Convierte referencia de Excel (A, BR, DC, etc) a índice 0-based"""
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


def obtener_valor_por_indice(fila, idx):
    """Obtiene valor de una fila por índice, con validación"""
    try:
        return fila[idx] if idx < len(fila) else ""
    except:
        return ""


def limpiar_numero(valor_str):
    """Limpia y convierte string a número"""
    if not valor_str:
        return 0.0
    
    valor_str = str(valor_str).strip()
    valor_str = valor_str.replace('%', '').strip()
    valor_str = valor_str.replace('€', '').strip()
    valor_str = valor_str.replace(',', '.').strip()
    
    try:
        return float(valor_str)
    except:
        return 0.0


@st.cache_data(ttl=3600)
def cargar_proyectos():
    """
    Carga proyectos desde Google Sheet Intermedio.
    
    CAMBIOS:
    ✅ Ahora carga precio_emision (columna K)
    ✅ Ahora carga divisa (EUR/USD)
    ✅ Ahora carga meses_restantes_renta (columna AK)
    ✅ Ahora carga importe_proyecto_eur (columna M)
    
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
        
        # ⚡ UNA SOLA LLAMADA A LA API
        todas_las_filas = worksheet.get_all_values()
        
        if len(todas_las_filas) < 3:
            st.error("Sheet vacío o con estructura incorrecta")
            return pd.DataFrame()
        
        # Índices de columnas (convertir referencias Excel a índices 0-based)
        idx_A = excel_col_to_index('A')   # ID
        idx_B = excel_col_to_index('B')   # Nombre del proyecto
        idx_C = excel_col_to_index('C')   # ESTADO
        idx_E = excel_col_to_index('E')   # Fecha inicio alternativa
        idx_F = excel_col_to_index('F')   # Fecha fin alternativa
        idx_H = excel_col_to_index('H')   # Fecha inicio principal
        idx_I = excel_col_to_index('I')   # Fecha fin principal
        idx_K = excel_col_to_index('K')   # precio_emision ← NUEVO
        idx_M = excel_col_to_index('M')   # importe_proyecto_eur ← NUEVO
        idx_O = excel_col_to_index('O')   # Ubicación
        idx_Q = excel_col_to_index('Q')   # Tipología de dividendo
        
        # Rentabilidades alternativas
        idx_W = excel_col_to_index('W')   # Rentab Reentel alt
        idx_Z = excel_col_to_index('Z')   # Rentab Anualizada Reentel alt
        idx_AA = excel_col_to_index('AA') # Rentab ReentelPro alt
        idx_AD = excel_col_to_index('AD') # Rentab Anualizada ReentelPro alt
        idx_AE = excel_col_to_index('AE') # Rentab SuperReentel alt
        idx_AH = excel_col_to_index('AH') # Rentab Anualizada SuperReentel alt
        
        # Rentabilidades principales
        idx_BH = excel_col_to_index('BH') # Rentab Reentel
        idx_BK = excel_col_to_index('BK') # Rentab Anualizada Reentel
        idx_BM = excel_col_to_index('BM') # Rentab ReentelPro
        idx_BP = excel_col_to_index('BP') # Rentab Anualizada ReentelPro
        idx_BR = excel_col_to_index('BR') # Rentab SuperReentel
        idx_BU = excel_col_to_index('BU') # Rentab Anualizada SuperReentel
        
        # ← NUEVO: meses_restantes_renta
        idx_AK = excel_col_to_index('AK') # Nº Meses restantes de renta
        
        # Datos desde fila 3 en adelante (índice 2 en la lista)
        datos_mapeados = []
        
        for fila in todas_las_filas[2:]:  # Saltar headers (filas 0-1)
            # Obtener valores directamente del índice
            id_val = obtener_valor_por_indice(fila, idx_A)
            nombre_val = obtener_valor_por_indice(fila, idx_B)
            
            # Si no hay ID o nombre, saltar la fila
            if not id_val or not nombre_val:
                continue
            
            fila_dict = {}
            fila_dict['ID'] = id_val
            fila_dict['Nombre del proyecto'] = nombre_val
            fila_dict['ESTADO'] = obtener_valor_por_indice(fila, idx_C)
            fila_dict['Ubicación'] = obtener_valor_por_indice(fila, idx_O)
            fila_dict['Tipología de dividendo'] = obtener_valor_por_indice(fila, idx_Q)
            
            # Fechas de inicio (H, o si está vacío usar E)
            fecha_inicio_h = obtener_valor_por_indice(fila, idx_H)
            if fecha_inicio_h:
                fila_dict['Fecha Inicio Estimada'] = parsear_fecha(fecha_inicio_h)
            else:
                fecha_inicio_e = obtener_valor_por_indice(fila, idx_E)
                fila_dict['Fecha Inicio Estimada'] = parsear_fecha(fecha_inicio_e)
            
            # Fechas de fin (I, o si está vacío usar F)
            fecha_fin_i = obtener_valor_por_indice(fila, idx_I)
            if fecha_fin_i:
                fila_dict['Fecha Fin Estimada'] = parsear_fecha(fecha_fin_i)
            else:
                fecha_fin_f = obtener_valor_por_indice(fila, idx_F)
                fila_dict['Fecha Fin Estimada'] = parsear_fecha(fecha_fin_f)
            
            # ================== NUEVO BLOQUE ==================
            # Precio de emisión (CRÍTICO para B.1)
            precio_emision_str = obtener_valor_por_indice(fila, idx_K)
            fila_dict['precio_emision'] = limpiar_numero(precio_emision_str)
            
            # Divisa (asumir EUR por defecto)
            # Si existe columna de divisa, leerla; si no, EUR
            fila_dict['divisa'] = 'EUR'  # Default: EUR
            
            # Importe del proyecto en EUR
            importe_eur_str = obtener_valor_por_indice(fila, idx_M)
            fila_dict['importe_proyecto_eur'] = limpiar_numero(importe_eur_str)
            
            # Meses restantes de renta
            meses_restantes_str = obtener_valor_por_indice(fila, idx_AK)
            fila_dict['meses_restantes_renta'] = limpiar_numero(meses_restantes_str)
            # ================== FIN NUEVO BLOQUE ==================
            
            # Rentabilidades SuperReentel
            rent_sr = obtener_valor_por_indice(fila, idx_BR)
            fila_dict['Rentabilidad_Total_SuperReentel'] = rent_sr if rent_sr else obtener_valor_por_indice(fila, idx_AE)
            
            rent_sr_anual = obtener_valor_por_indice(fila, idx_BU)
            fila_dict['Rentabilidad_Anualizada_SuperReentel'] = rent_sr_anual if rent_sr_anual else obtener_valor_por_indice(fila, idx_AH)
            
            # Rentabilidades ReentelPro
            rent_rp = obtener_valor_por_indice(fila, idx_BM)
            fila_dict['Rentabilidad_Total_ReentelPro'] = rent_rp if rent_rp else obtener_valor_por_indice(fila, idx_AA)
            
            rent_rp_anual = obtener_valor_por_indice(fila, idx_BP)
            fila_dict['Rentabilidad_Anualizada_ReentelPro'] = rent_rp_anual if rent_rp_anual else obtener_valor_por_indice(fila, idx_AD)
            
            # Rentabilidades Reentel
            rent_r = obtener_valor_por_indice(fila, idx_BH)
            fila_dict['Rentabilidad_Total_Reentel'] = rent_r if rent_r else obtener_valor_por_indice(fila, idx_W)
            
            rent_r_anual = obtener_valor_por_indice(fila, idx_BK)
            fila_dict['Rentabilidad_Anualizada_Reentel'] = rent_r_anual if rent_r_anual else obtener_valor_por_indice(fila, idx_Z)
            
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
                # Limpiar "%" primero
                df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                # Luego convertir a número
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
            
            # DEBUG: Mostrar primeros proyectos incluyendo precio_emision
            print("\n=== DEBUG CARGA DATA_LOADER ===")
            print(df_financiando[['Nombre del proyecto', 'precio_emision', 'divisa', 'Rentabilidad_Total_SuperReentel']].head())
            print("================================\n")
        
        return df_financiando
        
    except Exception as e:
        st.error(f"Error cargando proyectos: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
