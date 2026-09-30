"""
POOL RNT - Precio actual del RNT en USDT, leído del propio pool.

El precio sale del par RNT/USDT de SushiSwap (red Polygon), que es donde se
forma de verdad:  precio del RNT = reserva_USDT / reserva_RNT

Se consulta a través de la API de Etherscan (necesita una API key gratuita).
En el simulador sirve para rellenar el precio del RNT del Paso 5.
"""
from __future__ import annotations

import requests

BASE = "https://api.etherscan.io/v2/api"
CHAIN = 137                                                  # Polygon
PAR = "0x4097073e82edac2d758ecfd594139a891340d59d"           # SushiSwap RNT/USDT
DEC_RNT, DEC_USDT = 18, 6


def precio_actual(api_key: str) -> float | None:
    """Precio del RNT en USDT ahora mismo (una sola consulta).
    Devuelve None si la consulta falla."""
    try:
        r = requests.get(BASE, params={
            "chainid": CHAIN, "apikey": api_key,
            "module": "proxy", "action": "eth_call",
            "to": PAR, "data": "0x0902f1ac", "tag": "latest",   # getReserves()
        }, timeout=20)
        h = str(r.json().get("result") or "")[2:]
        if len(h) < 128:
            return None
        rnt = int(h[0:64], 16) / 10 ** DEC_RNT
        usdt = int(h[64:128], 16) / 10 ** DEC_USDT
        return usdt / rnt if rnt else None
    except Exception:
        return None
