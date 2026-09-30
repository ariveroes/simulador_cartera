"""
P2P LOADER - Lee los CSV de rnt_p2p directamente del repo de GitHub del compañero.
Siempre coge el finalized_YYYY-MM-DD.csv más reciente + enriquecido.csv.
Configuración en st.secrets["github_p2p"].
"""

import io
import re
import requests
import pandas as pd
import streamlit as st

API = "https://api.github.com"


def _cfg():
    c = st.secrets["github_p2p"]
    return {
        "owner": c["owner"],
        "repo": c["repo"],
        "branch": c.get("branch", "main"),
        "base_path": c.get("base_path", "rnt_p2p").strip("/"),
        "token": c.get("token", ""),
    }


def _headers(token, raw=False):
    h = {"Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _descargar_csv(cfg, ruta):
    url = f"{API}/repos/{cfg['owner']}/{cfg['repo']}/contents/{ruta}"
    r = requests.get(url, headers=_headers(cfg["token"], raw=True),
                     params={"ref": cfg["branch"]}, timeout=20)
    r.raise_for_status()
    # sep=None detecta automáticamente ',' o ';'
    return pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")), sep=None, engine="python")


def _ultimo_finalized(cfg):
    """Devuelve el nombre del finalized_*.csv con la fecha más reciente."""
    url = f"{API}/repos/{cfg['owner']}/{cfg['repo']}/contents/{cfg['base_path']}/exports"
    r = requests.get(url, headers=_headers(cfg["token"]), params={"ref": cfg["branch"]}, timeout=20)
    r.raise_for_status()
    nombres = [f["name"] for f in r.json()
               if re.match(r"finalized_\d{4}-\d{2}-\d{2}\.csv$", f["name"])]
    return max(nombres) if nombres else None  # formato ISO -> orden alfabético = cronológico


@st.cache_data(ttl=600, show_spinner="Cargando datos P2P...")
def cargar_p2p():
    """
    Devuelve dict con:
      'finalized'   -> DataFrame del último export (o vacío)
      'enriquecido' -> DataFrame de enriquecido.csv (o vacío)
      'archivo'     -> nombre del finalized usado
      'error'       -> texto del error si algo falla (o None)
    """
    out = {"finalized": pd.DataFrame(), "enriquecido": pd.DataFrame(), "archivo": None, "error": None}
    try:
        cfg = _cfg()
        nombre = _ultimo_finalized(cfg)
        if nombre:
            out["archivo"] = nombre
            out["finalized"] = _descargar_csv(cfg, f"{cfg['base_path']}/exports/{nombre}")
        out["enriquecido"] = _descargar_csv(cfg, f"{cfg['base_path']}/enriquecido.csv")
    except requests.HTTPError as e:
        code = e.response.status_code
        out["error"] = {401: "Token inválido o caducado",
                        403: "Sin permiso o límite de API alcanzado",
                        404: "Repo, rama o ruta no encontrados (revisa secrets)"}.get(code, str(e))
    except Exception as e:
        out["error"] = str(e)
    return out
