"""
RENTABILIDAD_COMPRA - Rentabilidad de un proyecto según el PRECIO y el MOMENTO de compra.

Replica las fórmulas de la plantilla de propuestas (pestaña "Cálculos",
columnas U a AL):

  renta      = renta recurrente anual REAL si el proyecto ya paga; si no, la estimada
  plusvalía  = plusvalía REAL si el proyecto está cerrado; si no, la estimada
  renta ajustada     = renta × (precio emisión / precio compra)
  plusvalía ajustada = (precio emisión × (1 + plusvalía) − precio compra) / precio compra
  total              = renta ajustada / 12 × meses de renta pendientes + plusvalía ajustada
  anualizada         = total × 12 / meses de renta pendientes

El momento de compra entra por los "meses de renta pendientes" (desde hoy hasta
el fin): quien compra un proyecto ya en marcha solo cobra las rentas que quedan.

Todas las cifras van en unidades de porcentaje (12.0 = 12 %), igual que maestro.py.
El precio de compra debe venir en la MISMA divisa que el precio de emisión.
"""
from __future__ import annotations

SUFIJO = {"Reentel": "rnt", "ReentelPro": "rp", "SuperReentel": "sr"}


def _num(valor):
    try:
        if valor is None or str(valor).strip() == "":
            return None
        v = float(str(valor).replace("%", "").replace(",", ".").strip())
        return None if v != v else v          # NaN -> None
    except (TypeError, ValueError):
        return None


def _campo(row, nombre, sufijo):
    """El valor de ese estatus o, si no hay, el de Reentel (proyectos sin estatus)."""
    v = _num(row.get(f"{nombre}_{sufijo}"))
    return v if v is not None else _num(row.get(f"{nombre}_rnt"))


def rentabilidad_ajustada(row, estatus: str, precio_compra=None) -> dict:
    """{"renta", "plusvalia", "total", "anual", "meses"} para ese estatus y precio.

    `row` es una fila del DataFrame de proyectos (o un dict) con las claves de
    maestro.py: est_recurr_*, est_plusvalia_*, real_recurr_*, real_plusvalia_*,
    y además 'Precio Emisión', 'Meses Pendientes' y 'ESTADO'.
    """
    suf = SUFIJO.get(estatus or "Reentel", "rnt")
    estado = str(row.get("ESTADO", "") or "").upper()

    renta = _campo(row, "real_recurr", suf)
    if not renta:                                   # sin renta real (o 0): la estimada
        renta = _campo(row, "est_recurr", suf)
    renta = renta or 0.0

    plusvalia = _campo(row, "real_plusvalia", suf) if "CERRAD" in estado else None
    if plusvalia is None:
        plusvalia = _campo(row, "est_plusvalia", suf)
    plusvalia = plusvalia or 0.0

    emision = _num(row.get("Precio Emisión")) or 100.0
    compra = _num(precio_compra) or emision
    meses = _num(row.get("Meses Pendientes")) or 0.0

    renta_aj = renta * emision / compra
    plusv_aj = (emision * (1 + plusvalia / 100) - compra) / compra * 100
    total = renta_aj / 12 * meses + plusv_aj
    anual = total * 12 / meses if meses > 0 else None
    return {"renta": renta_aj, "plusvalia": plusv_aj, "total": total,
            "anual": anual, "meses": meses}
