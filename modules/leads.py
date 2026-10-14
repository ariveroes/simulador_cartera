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

import traceback
from datetime import datetime, timezone

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

CABECERAS = [
    "Fecha (UTC)", "ID lead", "Evento", "Nombre", "Email", "¿Ya inversor?",
    "Divisa", "Capital (rango)", "Estatus", "Objetivo",
    "Distribución", "Mercados", "Cartera", "Importe simulado",
]


@st.cache_resource(show_spinner=False)
def _hoja():
    cfg = st.secrets["leads"]
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
    libro = gspread.authorize(creds).open_by_key(cfg["sheet_id"])
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


def guardar(lead_id: str, evento: str, datos: dict, cartera: str = "", importe: str = "") -> bool:
    """Añade una fila al Sheet de leads. Devuelve True si se guardó."""
    if not configurado():
        return False
    fila = [
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        lead_id,
        evento,
        datos.get("nombre", ""),
        datos.get("email", ""),
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
