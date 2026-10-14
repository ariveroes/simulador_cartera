"""
LEADS - Guarda en un Google Sheet los datos que deja cada usuario del simulador.

Usa la misma cuenta de servicio que maestro.py (st.secrets["gcp_service_account"]).
El Sheet se indica en los Secrets:

    [leads]
    sheet_id = "1mBaPpzVWCijgRqZxKNgRiyrra81o86OEi_LloEI8c5M"
    pestana  = "Leads"          # opcional, por defecto "Leads"

El Sheet tiene que estar compartido (como Editor) con el email de la cuenta de
servicio. Si la pestaña no existe, se crea con sus cabeceras.

Guardar un lead NUNCA debe romper el simulador: si algo falla, se registra en
los logs y la app sigue.
"""
from __future__ import annotations

import re
import traceback
from datetime import datetime, timezone

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

CABECERAS = [
    "Fecha (UTC)", "ID lead", "Evento", "Nombre", "Email", "Teléfono", "¿Ya inversor?",
    "Divisa", "Capital (rango)", "Estatus", "Objetivo",
    "Distribución", "Mercados", "Cartera", "Importe simulado",
]


def _sheet_id() -> str:
    """El ID del Sheet. Acepta también la URL entera por si se pegó así."""
    valor = str(st.secrets["leads"]["sheet_id"]).strip()
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", valor)
    return m.group(1) if m else valor


@st.cache_resource(show_spinner=False)
def _hoja():
    cfg = st.secrets["leads"]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
    libro = gspread.authorize(creds).open_by_key(_sheet_id())
    nombre = cfg.get("pestana", "Leads")
    try:
        ws = libro.worksheet(nombre)
    except gspread.WorksheetNotFound:
        ws = libro.add_worksheet(title=nombre, rows=1000, cols=len(CABECERAS))
    if not ws.row_values(1):
        ws.append_row(CABECERAS, value_input_option="RAW")
    return ws


def configurado() -> bool:
    try:
        return bool(st.secrets["leads"]["sheet_id"])
    except Exception:
        return False


def diagnostico() -> str:
    """Comprueba la conexión con el Sheet de leads y explica qué falla."""
    if not configurado():
        return ("❌ No hay configuración de leads en los Secrets. Añade:\n\n"
                "[leads]\nsheet_id = \"ID_DEL_SHEET\"")
    try:
        email_cuenta = dict(st.secrets["gcp_service_account"]).get("client_email", "?")
    except Exception:
        return "❌ Falta la sección [gcp_service_account] en los Secrets."
    try:
        _hoja.clear()
        ws = _hoja()
        return (f"✅ Conexión correcta con la pestaña «{ws.title}» del Sheet {_sheet_id()}. "
                f"Los leads se están guardando ahí.")
    except gspread.exceptions.SpreadsheetNotFound:
        return (f"❌ La cuenta de servicio no encuentra el Sheet {_sheet_id()}. Revisa que el ID es "
                f"correcto y que el Sheet está compartido como Editor con {email_cuenta}.")
    except gspread.exceptions.APIError as e:
        texto = str(e)
        if "PERMISSION_DENIED" in texto or "403" in texto:
            return (f"❌ Sin permiso para escribir en el Sheet. Compártelo como **Editor** con "
                    f"{email_cuenta}. Si el Sheet está en una unidad de tu empresa, puede que no "
                    f"se permita compartir con cuentas externas.")
        if "not supported for this document" in texto.lower():
            return ("❌ El archivo es un Excel subido a Drive, no un Google Sheet. Ábrelo y usa "
                    "Archivo → Guardar como Hojas de cálculo de Google, y usa el ID del nuevo archivo.")
        return f"❌ Error de Google: {texto[:300]}"
    except Exception as e:
        return f"❌ Error inesperado: {type(e).__name__}: {str(e)[:300]}"


def guardar(lead_id: str, evento: str, datos: dict, cartera: str = "", importe: str = "") -> bool:
    """Añade una fila al Sheet de leads. Devuelve True si se guardó."""
    if not configurado():
        print("⚠️ Lead no guardado: falta [leads] sheet_id en los Secrets")
        return False
    fila = [
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        lead_id,
        evento,
        datos.get("nombre", ""),
        datos.get("email", ""),
        datos.get("telefono", ""),
        datos.get("ya_inversor", ""),
        datos.get("divisa", ""),
        datos.get("capital", ""),
        datos.get("estatus", ""),
        datos.get("objetivo", ""),
        datos.get("distribucion", ""),
        ", ".join(datos.get("mercados", []) or []),
        cartera,
        importe,
    ]
    try:
        _hoja().append_row(fila, value_input_option="RAW")
        return True
    except Exception:
        print("❌ No se pudo guardar el lead:")
        traceback.print_exc()
        return False
