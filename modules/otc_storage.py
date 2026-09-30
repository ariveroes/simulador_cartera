"""
OTC_STORAGE.PY - Acceso a ofertas OTC desde Google Sheets

Lee la hoja "Ofertas" con precios OTC reales.

ESTRUCTURA GOOGLE SHEET:
- SPREADSHEET_ID: 13Q0n7egbAIJSU9UvwwDucd3MUQ48Q44eoMwsPT-PmGs
- Tab: "Ofertas"
- Campos: proyecto_id | precio_venta | divisa | n_tokens | fecha | estado

EJEMPLO:
proyecto_id | precio_venta | divisa | n_tokens | fecha      | estado
------------|-------------|--------|----------|------------|--------
0x123...    | 12.50       | EUR    | 1000     | 30/09/2026 | Activa
0x456...    | 15.00       | USD    | 500      | 29/09/2026 | Activa
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


SPREADSHEET_ID = "13Q0n7egbAIJSU9UvwwDucd3MUQ48Q44eoMwsPT-PmGs"
TABS = {
    "Ofertas": "Ofertas",
    "Reservas": "Reservas",
    "precios_otc": "precios_otc"
}


def _obtener_cliente_gspread():
    """Autentica con Google Sheets usando Streamlit secrets."""
    try:
        creds_dict = st.secrets.get("gcp_service_account")
        if not creds_dict:
            st.error("No se encontraron credenciales en Streamlit secrets")
            return None
        
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Error autenticando con Google Sheets: {e}")
        return None


@st.cache_data(ttl=3600)
def read_list(tab_name: str) -> list:
    """
    Lee una lista de dicts desde un tab de Google Sheets.
    
    Args:
        tab_name: Nombre del tab ('Ofertas', 'Reservas', 'precios_otc')
    
    Returns:
        Lista de dicts con los datos del tab
    """
    client = _obtener_cliente_gspread()
    if not client:
        return []
    
    try:
        sheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet(tab_name)
        
        # Obtener todos los valores
        datos = worksheet.get_all_values()
        
        if not datos or len(datos) < 2:
            return []
        
        # Primera fila = headers
        headers = datos[0]
        
        # Convertir a lista de dicts
        resultado = []
        for row in datos[1:]:
            if len(row) == 0 or all(v == '' for v in row):
                continue  # Saltar filas vacías
            
            fila_dict = {}
            for i, header in enumerate(headers):
                valor = row[i] if i < len(row) else ''
                fila_dict[header.strip()] = valor.strip()
            
            resultado.append(fila_dict)
        
        return resultado
    
    except Exception as e:
        st.error(f"Error leyendo {tab_name}: {e}")
        return []


@st.cache_data(ttl=3600)
def read_dict(tab_name: str, key_column: str = None) -> dict:
    """
    Lee un tab como diccionario keyed por una columna.
    
    Args:
        tab_name: Nombre del tab
        key_column: Columna a usar como clave (si None, usa primera columna)
    
    Returns:
        Dict con key_column como clave
    """
    lista = read_list(tab_name)
    
    if not lista:
        return {}
    
    if key_column is None:
        key_column = list(lista[0].keys())[0]
    
    resultado = {}
    for item in lista:
        key = item.get(key_column, '')
        if key:
            resultado[key] = item
    
    return resultado


def ofertas_por_proyecto(proyecto_id: str) -> list:
    """
    Obtiene todas las ofertas OTC para un proyecto.
    
    Args:
        proyecto_id: Address del token (0x...)
    
    Returns:
        Lista de dicts con ofertas activas del proyecto
    """
    ofertas = read_list("Ofertas")
    
    resultado = []
    for oferta in ofertas:
        if oferta.get('proyecto_id', '').lower() == proyecto_id.lower():
            # Filtrar solo ofertas activas
            if oferta.get('estado', '').lower() == 'activa':
                resultado.append(oferta)
    
    return resultado


def mejor_oferta_otc(proyecto_id: str) -> dict:
    """
    Obtiene la mejor oferta OTC para un proyecto (precio más bajo en EUR).
    
    Args:
        proyecto_id: Address del token (0x...)
    
    Returns:
        Dict con la mejor oferta, o {} si no hay
    """
    ofertas = ofertas_por_proyecto(proyecto_id)
    
    if not ofertas:
        return {}
    
    # Normalizar precios a EUR para comparación
    mejores = []
    for oferta in ofertas:
        try:
            precio = float(oferta.get('precio_venta', 0))
            divisa = oferta.get('divisa', 'EUR')
            
            # Convertir a EUR si es USD (aproximación: 1 USD = 0.92 EUR)
            if divisa.upper() == 'USD':
                precio_eur = precio * 0.92
            else:
                precio_eur = precio
            
            mejores.append({
                **oferta,
                'precio_eur_normalizado': precio_eur
            })
        except:
            continue
    
    if not mejores:
        return {}
    
    # Retornar la de menor precio
    return min(mejores, key=lambda x: x['precio_eur_normalizado'])


def write(tab_name: str, data: list):
    """
    Escribe/actualiza datos en un tab (requiere permisos).
    
    Args:
        tab_name: Nombre del tab
        data: Lista de dicts a escribir
    """
    client = _obtener_cliente_gspread()
    if not client:
        return False
    
    try:
        sheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = sheet.worksheet(tab_name)
        
        # Limpiar el tab
        worksheet.clear()
        
        if not data:
            return True
        
        # Headers
        headers = list(data[0].keys())
        rows = [headers]
        
        # Rows
        for item in data:
            row = [str(item.get(h, '')) for h in headers]
            rows.append(row)
        
        # Escribir
        worksheet.append_rows(rows)
        
        return True
    
    except Exception as e:
        st.error(f"Error escribiendo en {tab_name}: {e}")
        return False


def clear_cache():
    """Limpia el caché de Streamlit (después de actualizar datos)."""
    st.cache_data.clear()
