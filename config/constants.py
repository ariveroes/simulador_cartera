# CONFIGURACIÓN Y CONSTANTES - HERRAMIENTA CARTERA INMOBILIARIA

# ============================================================================
# TASAS DE REINVERSIÓN (Sheet 1, Datos, filas 25-27)
# ============================================================================
REINVERSION_RATES = {
    "Reentel": 0.11,           # 11% anual
    "ReentelPro": 0.13,        # 13% anual
    "SuperReentel": 0.16       # 16% anual
}

# ============================================================================
# TASAS DE STAKING RNT (Sheet 1, Datos, fila 21)
# ============================================================================
STAKING_RATE = 0.10  # 10% anual (por determinar con usuario si es necesario)

# ============================================================================
# MINIMOS DE INVERSIÓN POR TIPO DE INVERSIÓN
# ============================================================================
MINIMO_INVERSION = {
    "Transferencia bancaria": 500,  # EUR/USD
    "Cripto": 100                   # EUR/USD
}

# ============================================================================
# HORIZONTES DE CÁLCULO (meses)
# Iguales a Sheet 1, fila 72
# ============================================================================
HORIZONTES_CALCULO = [6, 12, 24, 36, 60]

# ============================================================================
# DIVISAS SOPORTADAS
# ============================================================================
DIVISAS = ["EUR", "USD"]

# ============================================================================
# TIPOS DE INVERSIÓN SOPORTADOS
# ============================================================================
TIPOS_INVERSION = ["Transferencia bancaria", "Cripto"]

# ============================================================================
# ESTATUS DISPONIBLES
# ============================================================================
ESTATUS = ["Reentel", "ReentelPro", "SuperReentel"]

# ============================================================================
# DISTRIBUCIÓN DE CAPITAL
# ============================================================================
DISTRIBUCION_CAPITAL_TIPOS = [
    "Igual (mismo monto por proyecto)",
    "Proporcional (según tamaño del proyecto)",
    "Manual (tú eliges % por proyecto)"
]

# ============================================================================
# ESTADOS DE PROYECTOS
# ============================================================================
ESTADOS_PROYECTO = {
    "CERRADO": "Cerrado",
    "EN_EXPLOTACION": "En explotación",
    "EN_REFORMA": "En reforma",
    "FINANCIANDOSE": "Financiándose",
    "PRELANZAMIENTO": "Prelanzamiento"
}

# Estados que son VENTA PRIMARIA
ESTADOS_PRIMARIA = ["PRELANZAMIENTO", "FINANCIANDOSE"]

# ============================================================================
# TIPOLOGÍA DE DIVIDENDOS (Sheet 2, columna Q)
# ============================================================================
TIPOLOGIA_DIVIDENDOS = [
    "rendimientos mensuales + final",
    "rendimientos trimestrales + final",
    "rendimientos mensuales",
    "rendimientos trimestrales",
    "rendimientos a final del proyecto"
]

# Mapeo para UI
TIPOLOGIA_DIVIDENDOS_LABEL = {
    "Periódicos": [
        "rendimientos mensuales + final",
        "rendimientos trimestrales + final",
        "rendimientos mensuales",
        "rendimientos trimestrales"
    ],
    "Finales": [
        "rendimientos a final del proyecto"
    ]
}

# ============================================================================
# UBICACIONES DISPONIBLES (Sheet 2, columna O)
# ============================================================================
UBICACIONES = [
    "España",
    "USA",
    "México",
    "Argentina",
    "República Dominicana",
    "Emiratos Árabes Unidos",
    "Global"
]

# ============================================================================
# GOOGLE SHEETS CONFIG
# ============================================================================
SHEET_INTERMEDIO_URL = "https://docs.google.com/spreadsheets/d/1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY/edit?gid=0#gid=0"
SHEET_INTERMEDIO_GSHEET_ID = "1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY"
SHEET_INTERMEDIO_WORKSHEET_NAME = "Master Inmuebles Pro"

# ============================================================================
# COLUMNAS NECESARIAS DEL SHEET (mapping)
# ============================================================================
COLUMNAS_SHEET = {
    # Datos básicos
    "ID": "A",                    # SVQ-1, GND-1, etc.
    "nombre": "B",                # Sevilla 1, Gandia 1, etc.
    "estado": "C",                # CERRADO, EN EXPLOTACIÓN, etc.
    "fecha_lanzamiento": "D",     # Fecha
    "fecha_inicio_renta": "H",    # Fecha
    "fecha_fin": "I",             # Fecha
    
    # Ubicación y tipo
    "ubicacion": "O",             # España, USA, etc.
    "tipologia_dividendos": "Q",  # rendimientos mensuales + final, etc.
    
    # Financiero
    "precio_token": "K",          # Precio en EUR
    "nro_tokens": "J",            # Número de tokens
    "importe_proyecto_eur": "M",  # Importe en EUR
    "importe_proyecto_usd": "N",  # Importe en USD
    
    # Duraciones (columnas calculadas en Sheet)
    # Estos son ejemplos - puede variar según la fila de referencia
    "meses_desde_lanzamiento": "AI",  # Estimación Nº Meses desde Lanzamiento
    "meses_restantes_renta": "AK",    # Nº Meses restantes de renta
    
    # Rentabilidades ESTIMADAS por estatus (columnas calculadas)
    # Estimación Rentab. Rendimiento Recurr. anualizado
    "rent_recurrente_reentel": "W",   # Ejemplo
    "rent_recurrente_rp": "X",        # Ejemplo
    "rent_recurrente_sr": "Y",        # Ejemplo
    
    # Rentabilidad PLUSVALÍA por estatus
    "rent_plusvalia_reentel": "Z",    # Ejemplo
    "rent_plusvalia_rp": "AA",        # Ejemplo
    "rent_plusvalia_sr": "AB",        # Ejemplo
    
    # Rentabilidad TOTAL anualizada por estatus
    # (Esto es lo que usamos para ranking)
    "rent_anualizada_reentel": "AJ",  # Estimación Rentab. Total anualizado Reentel
    "rent_anualizada_rp": "AK",       # Estimación Rentab. Total anualizado RP
    "rent_anualizada_sr": "AL"        # Estimación Rentab. Total anualizado SR
}

# ============================================================================
# EMAIL CONFIGURACIÓN (para notificaciones si capital > 50k)
# ============================================================================
EMAIL_DESTINO = "tu_email@reental.com"  # CAMBIAR CON EMAIL REAL
CAPITAL_UMBRAL_EMAIL = 50000  # EUR/USD

# ============================================================================
# INFORMACIÓN DE API (TIPO DE CAMBIO)
# ============================================================================
# Usamos Open Exchange Rates o similar
# Por ahora usaremos una API gratuita simple
TIPO_CAMBIO_API = "https://api.exchangerate-api.com/v4/latest/EUR"  # EUR a otras divisas
TIMEOUT_API = 10  # segundos
