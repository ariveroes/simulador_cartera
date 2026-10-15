"""
COMÚN - Constantes, colores y funciones que usan todos los pasos del simulador.

Los archivos de cada paso (paso1_datos.py … paso5_resumen.py) y app.py lo
importan con «from modules.comun import *», así que todo lo que se define aquí
está disponible en ellos con el mismo nombre.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import math
import re
import traceback
import uuid
from modules.data_loader import cargar_proyectos, cargar_todos_proyectos
from modules.calculo_cartera import rankear_proyectos, CalculadoraCartera
from modules.formateo_datos import preparar_proyectos_para_paso4
from modules.pdf_generator import generar_pdf_cartera
from modules import leads

# ========== AGENDA DE REUNIONES ==========
# Enlace para agendar una reunión con el equipo (botón flotante, Paso 2 y Paso 5)
URL_AGENDA = "https://api.leadconnectorhq.com/widget/booking/kAzM5NH9hFxtc88sTQKy"

# ========== PREFIJOS TELEFÓNICOS (Paso 1) ==========
# (bandera, código del país, prefijo). El primero es el que sale por defecto.
# Todos los países (fuente: el plan internacional de numeración de la UIT, vía la
# librería phonenumbers). España primero; el resto, por orden alfabético en español.
PREFIJOS_TELEFONO = [
    ("🇪🇸", "ESP", "+34"),  # España
    ("🇦🇫", "AFG", "+93"),  # Afganistán
    ("🇦🇱", "ALB", "+355"),  # Albania
    ("🇩🇪", "DEU", "+49"),  # Alemania
    ("🇦🇩", "AND", "+376"),  # Andorra
    ("🇦🇴", "AGO", "+244"),  # Angola
    ("🇦🇮", "AIA", "+1"),  # Anguila
    ("🇦🇬", "ATG", "+1"),  # Antigua y Barbuda
    ("🇸🇦", "SAU", "+966"),  # Arabia Saudí
    ("🇩🇿", "DZA", "+213"),  # Argelia
    ("🇦🇷", "ARG", "+54"),  # Argentina
    ("🇦🇲", "ARM", "+374"),  # Armenia
    ("🇦🇼", "ABW", "+297"),  # Aruba
    ("🇦🇺", "AUS", "+61"),  # Australia
    ("🇦🇹", "AUT", "+43"),  # Austria
    ("🇦🇿", "AZE", "+994"),  # Azerbaiyán
    ("🇧🇸", "BHS", "+1"),  # Bahamas
    ("🇧🇩", "BGD", "+880"),  # Bangladés
    ("🇧🇧", "BRB", "+1"),  # Barbados
    ("🇧🇭", "BHR", "+973"),  # Baréin
    ("🇧🇪", "BEL", "+32"),  # Bélgica
    ("🇧🇿", "BLZ", "+501"),  # Belice
    ("🇧🇯", "BEN", "+229"),  # Benín
    ("🇧🇲", "BMU", "+1"),  # Bermudas
    ("🇧🇾", "BLR", "+375"),  # Bielorrusia
    ("🇧🇴", "BOL", "+591"),  # Bolivia
    ("🇧🇦", "BIH", "+387"),  # Bosnia y Herzegovina
    ("🇧🇼", "BWA", "+267"),  # Botsuana
    ("🇧🇷", "BRA", "+55"),  # Brasil
    ("🇧🇳", "BRN", "+673"),  # Brunéi
    ("🇧🇬", "BGR", "+359"),  # Bulgaria
    ("🇧🇫", "BFA", "+226"),  # Burkina Faso
    ("🇧🇮", "BDI", "+257"),  # Burundi
    ("🇧🇹", "BTN", "+975"),  # Bután
    ("🇨🇻", "CPV", "+238"),  # Cabo Verde
    ("🇰🇭", "KHM", "+855"),  # Camboya
    ("🇨🇲", "CMR", "+237"),  # Camerún
    ("🇨🇦", "CAN", "+1"),  # Canadá
    ("🇧🇶", "BES", "+599"),  # Caribe neerlandés
    ("🇶🇦", "QAT", "+974"),  # Catar
    ("🇹🇩", "TCD", "+235"),  # Chad
    ("🇨🇿", "CZE", "+420"),  # Chequia
    ("🇨🇱", "CHL", "+56"),  # Chile
    ("🇨🇳", "CHN", "+86"),  # China
    ("🇨🇾", "CYP", "+357"),  # Chipre
    ("🇻🇦", "VAT", "+39"),  # Ciudad del Vaticano
    ("🇨🇴", "COL", "+57"),  # Colombia
    ("🇰🇲", "COM", "+269"),  # Comoras
    ("🇨🇬", "COG", "+242"),  # Congo
    ("🇰🇵", "PRK", "+850"),  # Corea del Norte
    ("🇰🇷", "KOR", "+82"),  # Corea del Sur
    ("🇨🇷", "CRI", "+506"),  # Costa Rica
    ("🇨🇮", "CIV", "+225"),  # Côte d’Ivoire
    ("🇭🇷", "HRV", "+385"),  # Croacia
    ("🇨🇺", "CUB", "+53"),  # Cuba
    ("🇨🇼", "CUW", "+599"),  # Curazao
    ("🇩🇰", "DNK", "+45"),  # Dinamarca
    ("🇩🇲", "DMA", "+1"),  # Dominica
    ("🇪🇨", "ECU", "+593"),  # Ecuador
    ("🇪🇬", "EGY", "+20"),  # Egipto
    ("🇸🇻", "SLV", "+503"),  # El Salvador
    ("🇦🇪", "ARE", "+971"),  # Emiratos Árabes Unidos
    ("🇪🇷", "ERI", "+291"),  # Eritrea
    ("🇸🇰", "SVK", "+421"),  # Eslovaquia
    ("🇸🇮", "SVN", "+386"),  # Eslovenia
    ("🇺🇸", "USA", "+1"),  # Estados Unidos
    ("🇪🇪", "EST", "+372"),  # Estonia
    ("🇸🇿", "SWZ", "+268"),  # Esuatini
    ("🇪🇹", "ETH", "+251"),  # Etiopía
    ("🇵🇭", "PHL", "+63"),  # Filipinas
    ("🇫🇮", "FIN", "+358"),  # Finlandia
    ("🇫🇯", "FJI", "+679"),  # Fiyi
    ("🇫🇷", "FRA", "+33"),  # Francia
    ("🇬🇦", "GAB", "+241"),  # Gabón
    ("🇬🇲", "GMB", "+220"),  # Gambia
    ("🇬🇪", "GEO", "+995"),  # Georgia
    ("🇬🇭", "GHA", "+233"),  # Ghana
    ("🇬🇮", "GIB", "+350"),  # Gibraltar
    ("🇬🇩", "GRD", "+1"),  # Granada
    ("🇬🇷", "GRC", "+30"),  # Grecia
    ("🇬🇱", "GRL", "+299"),  # Groenlandia
    ("🇬🇵", "GLP", "+590"),  # Guadalupe
    ("🇬🇺", "GUM", "+1"),  # Guam
    ("🇬🇹", "GTM", "+502"),  # Guatemala
    ("🇬🇫", "GUF", "+594"),  # Guayana Francesa
    ("🇬🇬", "GGY", "+44"),  # Guernesey
    ("🇬🇳", "GIN", "+224"),  # Guinea
    ("🇬🇶", "GNQ", "+240"),  # Guinea Ecuatorial
    ("🇬🇼", "GNB", "+245"),  # Guinea-Bisáu
    ("🇬🇾", "GUY", "+592"),  # Guyana
    ("🇭🇹", "HTI", "+509"),  # Haití
    ("🇭🇳", "HND", "+504"),  # Honduras
    ("🇭🇺", "HUN", "+36"),  # Hungría
    ("🇮🇳", "IND", "+91"),  # India
    ("🇮🇩", "IDN", "+62"),  # Indonesia
    ("🇮🇶", "IRQ", "+964"),  # Irak
    ("🇮🇷", "IRN", "+98"),  # Irán
    ("🇮🇪", "IRL", "+353"),  # Irlanda
    ("🇮🇲", "IMN", "+44"),  # Isla de Man
    ("🇨🇽", "CXR", "+61"),  # Isla de Navidad
    ("🇳🇫", "NFK", "+672"),  # Isla Norfolk
    ("🇮🇸", "ISL", "+354"),  # Islandia
    ("🇦🇽", "ALA", "+358"),  # Islas Aland
    ("🇰🇾", "CYM", "+1"),  # Islas Caimán
    ("🇨🇨", "CCK", "+61"),  # Islas Cocos
    ("🇨🇰", "COK", "+682"),  # Islas Cook
    ("🇫🇴", "FRO", "+298"),  # Islas Feroe
    ("🇫🇰", "FLK", "+500"),  # Islas Malvinas
    ("🇲🇵", "MNP", "+1"),  # Islas Marianas del Norte
    ("🇲🇭", "MHL", "+692"),  # Islas Marshall
    ("🇸🇧", "SLB", "+677"),  # Islas Salomón
    ("🇹🇨", "TCA", "+1"),  # Islas Turcas y Caicos
    ("🇻🇬", "VGB", "+1"),  # Islas Vírgenes Británicas
    ("🇻🇮", "VIR", "+1"),  # Islas Vírgenes de EE. UU.
    ("🇮🇱", "ISR", "+972"),  # Israel
    ("🇮🇹", "ITA", "+39"),  # Italia
    ("🇯🇲", "JAM", "+1"),  # Jamaica
    ("🇯🇵", "JPN", "+81"),  # Japón
    ("🇯🇪", "JEY", "+44"),  # Jersey
    ("🇯🇴", "JOR", "+962"),  # Jordania
    ("🇰🇿", "KAZ", "+7"),  # Kazajistán
    ("🇰🇪", "KEN", "+254"),  # Kenia
    ("🇰🇬", "KGZ", "+996"),  # Kirguistán
    ("🇰🇮", "KIR", "+686"),  # Kiribati
    ("🇽🇰", "XKX", "+383"),  # Kosovo
    ("🇰🇼", "KWT", "+965"),  # Kuwait
    ("🇱🇦", "LAO", "+856"),  # Laos
    ("🇱🇸", "LSO", "+266"),  # Lesoto
    ("🇱🇻", "LVA", "+371"),  # Letonia
    ("🇱🇧", "LBN", "+961"),  # Líbano
    ("🇱🇷", "LBR", "+231"),  # Liberia
    ("🇱🇾", "LBY", "+218"),  # Libia
    ("🇱🇮", "LIE", "+423"),  # Liechtenstein
    ("🇱🇹", "LTU", "+370"),  # Lituania
    ("🇱🇺", "LUX", "+352"),  # Luxemburgo
    ("🇲🇰", "MKD", "+389"),  # Macedonia del Norte
    ("🇲🇬", "MDG", "+261"),  # Madagascar
    ("🇲🇾", "MYS", "+60"),  # Malasia
    ("🇲🇼", "MWI", "+265"),  # Malaui
    ("🇲🇻", "MDV", "+960"),  # Maldivas
    ("🇲🇱", "MLI", "+223"),  # Mali
    ("🇲🇹", "MLT", "+356"),  # Malta
    ("🇲🇦", "MAR", "+212"),  # Marruecos
    ("🇲🇶", "MTQ", "+596"),  # Martinica
    ("🇲🇺", "MUS", "+230"),  # Mauricio
    ("🇲🇷", "MRT", "+222"),  # Mauritania
    ("🇾🇹", "MYT", "+262"),  # Mayotte
    ("🇲🇽", "MEX", "+52"),  # México
    ("🇫🇲", "FSM", "+691"),  # Micronesia
    ("🇲🇩", "MDA", "+373"),  # Moldavia
    ("🇲🇨", "MCO", "+377"),  # Mónaco
    ("🇲🇳", "MNG", "+976"),  # Mongolia
    ("🇲🇪", "MNE", "+382"),  # Montenegro
    ("🇲🇸", "MSR", "+1"),  # Montserrat
    ("🇲🇿", "MOZ", "+258"),  # Mozambique
    ("🇲🇲", "MMR", "+95"),  # Myanmar (Birmania)
    ("🇳🇦", "NAM", "+264"),  # Namibia
    ("🇳🇷", "NRU", "+674"),  # Nauru
    ("🇳🇵", "NPL", "+977"),  # Nepal
    ("🇳🇮", "NIC", "+505"),  # Nicaragua
    ("🇳🇪", "NER", "+227"),  # Níger
    ("🇳🇬", "NGA", "+234"),  # Nigeria
    ("🇳🇺", "NIU", "+683"),  # Niue
    ("🇳🇴", "NOR", "+47"),  # Noruega
    ("🇳🇨", "NCL", "+687"),  # Nueva Caledonia
    ("🇳🇿", "NZL", "+64"),  # Nueva Zelanda
    ("🇴🇲", "OMN", "+968"),  # Omán
    ("🇳🇱", "NLD", "+31"),  # Países Bajos
    ("🇵🇰", "PAK", "+92"),  # Pakistán
    ("🇵🇼", "PLW", "+680"),  # Palaos
    ("🇵🇦", "PAN", "+507"),  # Panamá
    ("🇵🇬", "PNG", "+675"),  # Papúa Nueva Guinea
    ("🇵🇾", "PRY", "+595"),  # Paraguay
    ("🇵🇪", "PER", "+51"),  # Perú
    ("🇵🇫", "PYF", "+689"),  # Polinesia Francesa
    ("🇵🇱", "POL", "+48"),  # Polonia
    ("🇵🇹", "PRT", "+351"),  # Portugal
    ("🇵🇷", "PRI", "+1"),  # Puerto Rico
    ("🇭🇰", "HKG", "+852"),  # RAE de Hong Kong (China)
    ("🇲🇴", "MAC", "+853"),  # RAE de Macao (China)
    ("🇬🇧", "GBR", "+44"),  # Reino Unido
    ("🇨🇫", "CAF", "+236"),  # República Centroafricana
    ("🇨🇩", "COD", "+243"),  # República Democrática del Congo
    ("🇩🇴", "DOM", "+1"),  # República Dominicana
    ("🇷🇪", "REU", "+262"),  # Reunión
    ("🇷🇼", "RWA", "+250"),  # Ruanda
    ("🇷🇴", "ROU", "+40"),  # Rumanía
    ("🇷🇺", "RUS", "+7"),  # Rusia
    ("🇪🇭", "ESH", "+212"),  # Sáhara Occidental
    ("🇼🇸", "WSM", "+685"),  # Samoa
    ("🇦🇸", "ASM", "+1"),  # Samoa Americana
    ("🇧🇱", "BLM", "+590"),  # San Bartolomé
    ("🇰🇳", "KNA", "+1"),  # San Cristóbal y Nieves
    ("🇸🇲", "SMR", "+378"),  # San Marino
    ("🇲🇫", "MAF", "+590"),  # San Martín
    ("🇵🇲", "SPM", "+508"),  # San Pedro y Miquelón
    ("🇻🇨", "VCT", "+1"),  # San Vicente y las Granadinas
    ("🇸🇭", "SHN", "+290"),  # Santa Elena
    ("🇱🇨", "LCA", "+1"),  # Santa Lucía
    ("🇸🇹", "STP", "+239"),  # Santo Tomé y Príncipe
    ("🇸🇳", "SEN", "+221"),  # Senegal
    ("🇷🇸", "SRB", "+381"),  # Serbia
    ("🇸🇨", "SYC", "+248"),  # Seychelles
    ("🇸🇱", "SLE", "+232"),  # Sierra Leona
    ("🇸🇬", "SGP", "+65"),  # Singapur
    ("🇸🇽", "SXM", "+1"),  # Sint Maarten
    ("🇸🇾", "SYR", "+963"),  # Siria
    ("🇸🇴", "SOM", "+252"),  # Somalia
    ("🇱🇰", "LKA", "+94"),  # Sri Lanka
    ("🇿🇦", "ZAF", "+27"),  # Sudáfrica
    ("🇸🇩", "SDN", "+249"),  # Sudán
    ("🇸🇸", "SSD", "+211"),  # Sudán del Sur
    ("🇸🇪", "SWE", "+46"),  # Suecia
    ("🇨🇭", "CHE", "+41"),  # Suiza
    ("🇸🇷", "SUR", "+597"),  # Surinam
    ("🇸🇯", "SJM", "+47"),  # Svalbard y Jan Mayen
    ("🇹🇭", "THA", "+66"),  # Tailandia
    ("🇹🇼", "TWN", "+886"),  # Taiwán
    ("🇹🇿", "TZA", "+255"),  # Tanzania
    ("🇹🇯", "TJK", "+992"),  # Tayikistán
    ("🇮🇴", "IOT", "+246"),  # Territorio Británico del Océano Índico
    ("🇵🇸", "PSE", "+970"),  # Territorios Palestinos
    ("🇹🇱", "TLS", "+670"),  # Timor-Leste
    ("🇹🇬", "TGO", "+228"),  # Togo
    ("🇹🇰", "TKL", "+690"),  # Tokelau
    ("🇹🇴", "TON", "+676"),  # Tonga
    ("🇹🇹", "TTO", "+1"),  # Trinidad y Tobago
    ("🇹🇳", "TUN", "+216"),  # Túnez
    ("🇹🇲", "TKM", "+993"),  # Turkmenistán
    ("🇹🇷", "TUR", "+90"),  # Turquía
    ("🇹🇻", "TUV", "+688"),  # Tuvalu
    ("🇺🇦", "UKR", "+380"),  # Ucrania
    ("🇺🇬", "UGA", "+256"),  # Uganda
    ("🇺🇾", "URY", "+598"),  # Uruguay
    ("🇺🇿", "UZB", "+998"),  # Uzbekistán
    ("🇻🇺", "VUT", "+678"),  # Vanuatu
    ("🇻🇪", "VEN", "+58"),  # Venezuela
    ("🇻🇳", "VNM", "+84"),  # Vietnam
    ("🇼🇫", "WLF", "+681"),  # Wallis y Futuna
    ("🇾🇪", "YEM", "+967"),  # Yemen
    ("🇩🇯", "DJI", "+253"),  # Yibuti
    ("🇿🇲", "ZMB", "+260"),  # Zambia
    ("🇿🇼", "ZWE", "+263"),  # Zimbabue
]


def etiqueta_prefijo(p):
    """Texto del desplegable de prefijo: «🇪🇸 ESP (+34)»."""
    return f"{p[0]} {p[1]} ({p[2]})"


# ========== PALETA ==========
# Paleta del informe mensual de Reental Wealth: ámbar, navy y fondo gris claro,
# con la tipografía Fustat.
COLOR_AMBAR = "#fca311"
COLOR_AMBAR_OSCURO = "#d97706"      # ámbar legible sobre blanco (textos, avisos)
COLOR_AMBAR_CLARO = "#feedcf"
COLOR_NAVY = "#1f2937"
COLOR_GRIS = "#6d737c"
COLOR_GRIS_CLARO = "#9ca1aa"
COLOR_BORDE = "#e5e7eb"
COLOR_FONDO = "#f9fafb"
COLOR_VERDE = "#15803d"
COLOR_ROJO = "#dc2626"
PALETA_GRAFICOS = ["#fca311", "#1f2937", "#15803d", "#fcd287", "#9ca1aa", "#f5a11f", "#3e4753"]


# ========== FUNCIONES AUXILIARES OTC ==========
# Los módulos OTC de la herramienta del compañero (otc_inventario, otc_saldos,
# aave_lend, utils, reental_tokens) se importan entre sí sin el prefijo
# "modules.", así que la carpeta modules/ tiene que estar en la ruta de Python.
import os
import sys
_DIR_MODULES = os.path.dirname(os.path.abspath(__file__))   # esta misma carpeta modules/
if _DIR_MODULES not in sys.path:
    sys.path.insert(0, _DIR_MODULES)


def _num(valor, defecto=0.0):
    try:
        return float(str(valor).replace(',', '.'))
    except (TypeError, ValueError):
        return defecto


def _proyectos_para_catalogo(df):
    """Tupla (hashable, para la caché) con lo que el catálogo OTC necesita de cada proyecto."""
    filas = []
    for _, r in df.iterrows():
        addr = str(r.get('Token Address', '') or '').strip().lower()
        if not (addr.startswith('0x') and len(addr) == 42):
            continue
        filas.append((addr, str(r.get('ID', '') or '').strip(),
                      str(r.get('Nombre del proyecto', '') or ''),
                      str(r.get('Divisa', '') or 'EUR'),
                      _num(r.get('Precio Emisión', 0)),
                      str(r.get('Ubicación', '') or ''),
                      str(r.get('ESTADO', '') or '')))
    return tuple(filas)


# Wallet de custodia de Reental: la misma que usan pages/02_OTC.py y
# pages/06_Constructor_Propuestas.py de la herramienta OTC (OTC_WALLET).
OTC_WALLET_CUSTODIA = "0xce0719ec1bda336ba069c6961ad167767829301a"


@st.cache_data(ttl=900, show_spinner="Revisando proyectos disponibles…")
def catalogo_otc(proyectos):
    """Lo disponible hoy en OTC, calculado con los MISMOS módulos que la herramienta
    OTC del compañero (otc_inventario.catalogo): stock propio de Reental en la
    wallet de custodia + ofertas activas de terceros, ambos contrastados con la
    cadena y descontando reservas y entregas. Se cachea 15 minutos."""
    import otc_inventario
    from modules import otc_storage

    try:
        api_key = str(st.secrets["etherscan"]["api_key"]).strip()
    except Exception:
        api_key = ""
    if not api_key:
        return {"catalogo": {}, "precios": {}, "error": "falta_clave"}
    try:
        custodia = str(st.secrets["otc"]["custodia"]).strip().lower()
    except Exception:
        custodia = OTC_WALLET_CUSTODIA

    por_addr, por_id = {}, {}
    for addr, pid, nombre, divisa, precio, ubic, estado in proyectos:
        p = {"id": pid, "nombre": nombre, "token_address": addr, "divisa": divisa,
             "precio_emision": precio, "ubicacion": ubic, "estado": estado,
             "fecha_fin": None, "tipo_renta": "—"}
        por_addr[addr] = p
        if pid:
            por_id[pid.lower()] = p

    reservas = otc_storage.read_list("Reservas")
    ofertas = otc_storage.read_list("Ofertas")

    balances, entradas = {}, {}
    if custodia:
        balances, _envios, entradas, _ = otc_inventario.balances_de_wallet(
            custodia, api_key, por_addr, por_id)

    cat = otc_inventario.catalogo(balances, reservas, ofertas, api_key,
                                  otc_inventario.saldo_en_wallet, entradas, custodia)
    try:
        precios = otc_storage.read_dict("precios_otc")
    except Exception:
        precios = {}
    return {"catalogo": cat, "precios": precios, "error": ""}


def _precio_stock_reental(precios, addr):
    """Precio de venta del stock propio de Reental: el de la pestaña precios_otc
    y, si no hay, el de emisión (mismo criterio que pages/02_OTC.py)."""
    v = (precios.get(addr) or {}).get("precio_otc") if isinstance(precios.get(addr), dict) else None
    valor = _num(v, None)
    return valor if valor and valor > 0 else None


def cargar_ofertas_otc(df_proyectos=None):
    """Ofertas OTC disponibles, en el formato que usa el resto de la app."""
    if df_proyectos is None or len(df_proyectos) == 0:
        return []
    try:
        res = catalogo_otc(_proyectos_para_catalogo(df_proyectos))
    except Exception as e:
        print(f"❌ Error calculando la disponibilidad OTC: {e}")
        traceback.print_exc()
        st.warning("Ahora mismo no hemos podido revisar todos los proyectos disponibles. "
                   "Inténtalo de nuevo en unos minutos.")
        return []

    proyecto_de = {str(r.get('Token Address', '')).strip().lower(): r
                   for _, r in df_proyectos.iterrows()}
    ofertas = []
    for addr, d in (res.get("catalogo") or {}).items():
        fila = proyecto_de.get(addr)
        pid = str(fila.get('ID', '')) if fila is not None else str(d.get('id', ''))
        nombre = str(fila.get('Nombre del proyecto', '')) if fila is not None else d.get('nombre', '')

        # Stock propio de Reental
        if (d.get('reental') or 0) > 0.001:
            precio = _precio_stock_reental(res.get("precios") or {}, addr)
            origen_precio = 'precio OTC' if precio is not None else 'precio de emisión'
            if precio is None:
                precio = _num(fila.get('Precio Emisión', 0)) if fila is not None else 0
            ofertas.append({
                'proyecto_id': pid.lower(), 'token_address': addr, 'proyecto_nombre': nombre,
                'n_tokens': round(d['reental'], 4), 'precio_venta': precio,
                'divisa': str(fila.get('Divisa', 'EUR')) if fila is not None else 'EUR',
                'estado': 'activa', 'canal': 'Stock Reental',
                'origen_precio': origen_precio,
            })

        # Ofertas de terceros (ya filtradas por la cadena)
        for t in d.get('terceros', []):
            ofertas.append({
                'proyecto_id': pid.lower(), 'token_address': addr, 'proyecto_nombre': nombre,
                'n_tokens': round(t['disponible'], 4), 'precio_venta': t['precio'],
                'divisa': t.get('divisa', 'USD'), 'estado': 'activa',
                'canal': 'Oferta de tercero', 'origen_precio': 'precio de la oferta',
            })

    if res.get("error") == "falta_clave":
        print("❌ Falta la clave de Etherscan en los Secrets ([etherscan] api_key)")
        st.warning("Ahora mismo no hemos podido revisar todos los proyectos disponibles. "
                   "Inténtalo de nuevo en unos minutos.")
    return ofertas

def cargar_ofertas_p2p():
    """Carga operaciones P2P cerradas (como ofertas del mercado secundario)"""
    try:
        from modules import p2p_mercado
        df_p2p = p2p_mercado.cargar()
        
        if df_p2p is None or df_p2p.empty:
            return []
        
        # Convertir a lista de dicts compatible con OTC
        # P2P contiene operaciones CERRADAS, las mostramos como "ofertas históricas"
        ofertas_p2p = []
        for idx, row in df_p2p.iterrows():
            oferta = {
                'id': row.get('hash', f"P2P-{idx}"),
                'proyecto_id': row.get('proyecto', '').lower() if pd.notna(row.get('proyecto')) else '',
                'token_address': row.get('token_address', '').lower() if pd.notna(row.get('token_address')) else '',
                'proyecto_nombre': row.get('proyecto', ''),
                'n_tokens': row.get('tokens', 0),
                'precio_venta': row.get('precio_unitario', 0),
                'divisa': 'USD',
                'inversor': row.get('vendedor', 'Desconocido'),
                'estado': 'cerrada',  # P2P son operaciones ya cerradas
                'canal': 'P2P',
                'fecha': row.get('fecha', '')
            }
            ofertas_p2p.append(oferta)
        
        return ofertas_p2p
    except Exception as e:
        print(f"❌ Error cargando P2P: {e}")
        return []

def cargar_todas_ofertas_secundario(df_proyectos=None):
    """Carga TODAS las ofertas del mercado secundario: OTC + P2P"""
    ofertas_otc = cargar_ofertas_otc(df_proyectos)
    ofertas_p2p = cargar_ofertas_p2p()
    
    # Combinar ambos canales
    todas_ofertas = (ofertas_otc or []) + (ofertas_p2p or [])
    
    return todas_ofertas

# En la tabla OTC no se muestran los proyectos que terminan en menos de estos
# meses (en primera emisión sí): les queda
# tan poco que su rentabilidad anualizada sale disparada y no es comparable.
MESES_MINIMOS_HASTA_FIN = 3


def termina_pronto(fecha_fin, meses=MESES_MINIMOS_HASTA_FIN):
    """True si el proyecto termina antes de `meses` meses desde hoy."""
    if fecha_fin is None or (isinstance(fecha_fin, float) and fecha_fin != fecha_fin):
        return False
    if isinstance(fecha_fin, datetime):
        fecha_fin = fecha_fin.date()
    if not hasattr(fecha_fin, "year"):
        return False
    hoy = datetime.now().date()
    mes = hoy.month - 1 + meses
    anio, mes = hoy.year + mes // 12, mes % 12 + 1
    dia = min(hoy.day, [31, 29 if anio % 4 == 0 and (anio % 100 or anio % 400 == 0) else 28,
                        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    limite = hoy.replace(year=anio, month=mes, day=dia)
    return fecha_fin < limite


# Mínimo de tokens disponibles para que una oferta OTC (o el stock de Reental)
# aparezca en el simulador. Las que tengan esta cantidad o menos no se muestran.
MIN_TOKENS_OTC = 10


def agrupar_ofertas_por_proyecto(ofertas):
    """Agrupa por proyecto_id o token_address las ofertas ACTIVAS
    (mismo criterio que otc_inventario.catalogo de la herramienta OTC)."""
    ofertas_por_proyecto = {}

    for oferta in ofertas:
        # Solo ofertas vivas: las eliminadas, vendidas, etc. no son comprables
        if str(oferta.get('estado', '')).strip().lower() != 'activa':
            continue
        # Solo ofertas con un mínimo de tokens disponibles
        if _num(oferta.get('n_tokens'), 0.0) <= MIN_TOKENS_OTC:
            continue

        # Usar proyecto_id o token_address como clave
        proyecto_id = (oferta.get('proyecto_id') or '').lower()
        token_address = (oferta.get('token_address') or '').lower()
        
        clave = proyecto_id or token_address or None
        
        if not clave:
            continue
        
        if clave not in ofertas_por_proyecto:
            ofertas_por_proyecto[clave] = []
        
        ofertas_por_proyecto[clave].append(oferta)
    
    return ofertas_por_proyecto

# ========== ANCHOS Y FORMATOS DE COLUMNAS (TABLAS PASO 4) ==========
# Para cambiar el ancho de una columna, edita solo su línea aquí.
# width admite "small", "medium", "large" o un número de píxeles (ej. 90).
CONFIG_COLUMNAS_PASO4 = {
    'ID': st.column_config.Column(width="small"),
    'Nombre del proyecto': st.column_config.Column(width=170, pinned=True),
    'Tipología de dividendo': st.column_config.Column(width="medium"),
    'ESTADO': st.column_config.Column('Estado', width=145),
    'Fecha Inicio Estimada': st.column_config.Column(width="small"),
    'Fecha Fin Estimada': st.column_config.Column(width="small"),
    'Ubicación': st.column_config.Column(width="small"),
    'Rentabilidad Total': st.column_config.NumberColumn('Rentabilidad total', format='%.2f%%', width=90),
    'Rentabilidad Anualizada': st.column_config.NumberColumn('Rentabilidad anualizada', format='%.2f%%', width=90),
    'Precio': st.column_config.TextColumn('Precio', width=90, help="Precio de compra de un token"),
}

# ========== SUPUESTOS DE MERCADO POR DEFECTO (Paso 5) ==========
# Se usan si no se puede leer el valor real. No son editables por el usuario.
TIPO_CAMBIO_DEFECTO = 1.14      # USD por 1 €
PRECIO_RNT_DEFECTO = 0.32       # USDT por 1 RNT
# RNT necesarios para cada estatus
RNT_POR_ESTATUS = {'SuperReentel': 28000, 'ReentelPro': 14000, 'Reentel': 0}
# Rendimiento anual estimado del estatus, sobre lo que cuesta (sin reinvertir)
RENDIMIENTO_ESTATUS = 3.5

# Código ISO numérico de cada país (para pintarlo en el mapa del Paso 5).
# Si aparece un mercado nuevo en el Master, basta con añadirlo aquí.
CODIGOS_PAIS = {
    'espana': 724, 'mexico': 484, 'usa': 840, 'eeuu': 840, 'estados unidos': 840,
    'republica dominicana': 214, 'argentina': 32, 'emiratos arabes': 784,
    'emiratos arabes unidos': 784, 'dubai': 784, 'portugal': 620, 'francia': 250,
    'italia': 380, 'alemania': 276, 'suecia': 752, 'polonia': 616, 'panama': 591,
    'colombia': 170, 'costa rica': 188, 'reino unido': 826, 'andorra': 20,
}



@st.cache_data(ttl=86400)
def tipo_cambio_actual():
    """USD por 1 € según el BCE (se consulta una vez al día). Si falla, valor por defecto."""
    try:
        from modules import divisas
        tipo = divisas.usd_por_euro()
        return round(tipo, 4) if tipo else TIPO_CAMBIO_DEFECTO
    except Exception:
        return TIPO_CAMBIO_DEFECTO


@st.cache_data(ttl=3600)
def precio_rnt_actual():
    """Precio del RNT en USDT según el pool (se consulta como mucho una vez por hora)."""
    try:
        from modules import pool_rnt
        precio = pool_rnt.precio_actual(st.secrets["etherscan"]["api_key"])
        return round(precio, 4) if precio else PRECIO_RNT_DEFECTO
    except Exception:
        return PRECIO_RNT_DEFECTO


from modules.rentabilidad_compra import rentabilidad_ajustada


def divisa_proyecto(row):
    """'USD' o 'EUR' según la divisa del proyecto en el Master."""
    return 'USD' if str(row.get('Divisa', '') or '').strip().upper() in ('USD', '$', 'USDT') else 'EUR'


def convertir_divisa(importe, desde, hacia):
    """Convierte entre EUR y USD (USDT cuenta como USD) con el tipo del BCE."""
    desde = 'USD' if str(desde).upper() in ('USD', 'USDT', '$') else 'EUR'
    hacia = 'USD' if str(hacia).upper() in ('USD', 'USDT', '$') else 'EUR'
    if desde == hacia:
        return importe
    tc = tipo_cambio_actual()
    return importe * tc if desde == 'EUR' else importe / tc


def aplicar_rentabilidad_ajustada(df_display, df_origen, estatus, precio_por_id=None):
    """Sustituye 'Rentabilidad Total' y 'Rentabilidad Anualizada' de una tabla del
    Paso 4 por las calculadas con el precio de compra y los meses que quedan
    (mismas fórmulas que la plantilla de propuestas). `precio_por_id` va en la
    divisa de cada proyecto; si un proyecto no está, se usa su precio de emisión."""
    if df_display is None or len(df_display) == 0:
        return df_display
    filas = {row['ID']: row for _, row in df_origen.iterrows()}
    totales, anuales = [], []
    for pid in df_display['ID']:
        row = filas.get(pid)
        if row is None:
            totales.append(None); anuales.append(None)
            continue
        r = rentabilidad_ajustada(row, estatus, (precio_por_id or {}).get(pid))
        totales.append(round(r['total'], 2))
        anuales.append(round(r['anual'], 2) if r['anual'] is not None else None)
    df_display = df_display.copy()
    df_display['Rentabilidad Total'] = totales
    df_display['Rentabilidad Anualizada'] = anuales
    return df_display


# Importe con el que se simula cada rango de capital del Paso 1 (punto medio del
# rango; para "Más de 50.000", que no tiene techo, se usan 100.000).
CAPITAL_SIMULADO = {
    "Menos de 5.000": 2500,
    "Entre 5.000 y 10.000": 7500,
    "Entre 10.000 y 50.000": 30000,
    "Más de 50.000": 100000,
}

def _indice(opciones, valor):
    """Posición de `valor` en `opciones` (para recordar lo elegido al volver atrás)."""
    return opciones.index(valor) if valor in opciones else None


def importe_simulado(capital_texto):
    return CAPITAL_SIMULADO.get(capital_texto, 30000)


def importe_cliente(datos):
    """Capital con el que se simula: el ajustado en el Paso 4 si lo hay; si no,
    el punto medio del rango elegido en el Paso 1."""
    return datos.get('capital_ajustado') or importe_simulado(datos.get('capital'))


def coste_estatus_cliente(datos):
    """Lo que cuesta el estatus elegido (los RNT que exige), en la divisa del cliente.
    Se descuenta del importe a invertir: el resto es lo que va a inmuebles."""
    rnt = RNT_POR_ESTATUS.get(datos.get('estatus') or 'Reentel', 0)
    if not rnt:
        return 0.0
    return convertir_divisa(rnt * precio_rnt_actual(), 'USD', (datos.get('divisa') or 'EUR'))


def capital_mostrado(datos, simbolo):
    """Texto del capital para la pantalla y el PDF: el importe con el que se simula."""
    return f"{es(importe_cliente(datos), 0)} {simbolo}"


def md(texto):
    """Escapa el símbolo $ para st.markdown/avisos: Streamlit lo interpreta como
    inicio de fórmula matemática y descoloca el texto (pasaba con la divisa USD)."""
    return str(texto).replace("$", "\\$")


def html_seguro(texto):
    """Lo mismo para fragmentos HTML: el $ se escribe como entidad."""
    return str(texto).replace("$", "&#36;")


def ajustar_capital(importe_repartido):
    """Fija el capital en lo que suman los tokens elegidos, para que el reparto sea
    exactamente el 100 %. Los tokens de cada proyecto no cambian."""
    if importe_repartido and importe_repartido > 0:
        st.session_state.datos_cliente['capital_ajustado'] = importe_repartido


def _formato_euro():
    """True si el cliente invierte en euros (o aún no lo ha elegido)."""
    try:
        return (st.session_state.get('datos_cliente') or {}).get('divisa', 'EUR') != 'USD'
    except Exception:
        return True


def es(valor, decimales=2):
    """Número según la divisa del cliente:
    en euros  → 257.109,50 (punto para miles, coma para decimales)
    en dólares → 257,109.50 (coma para miles, punto para decimales)"""
    try:
        texto = f"{float(valor):,.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)
    if not _formato_euro():
        return texto
    return texto.replace(",", "@").replace(".", ",").replace("@", ".")


OBJETIVOS = [
    "Maximizar rentabilidad - quiero invertir en los proyectos con mayor rentabilidad anualizada",
    "Ingresos pasivos regulares - quiero invertir en proyectos que me den rentas periódicas",
]


def priorizar_rentas(df):
    """Para el objetivo de ingresos pasivos: primero los proyectos con rendimientos
    mensuales, luego trimestrales y al final los que solo pagan al terminar.
    Dentro de cada grupo se respeta el orden que ya tenían."""
    if df is None or len(df) == 0:
        return df
    try:
        from modules.formateo_datos import _buscar_columna_tipologia
        col = _buscar_columna_tipologia(df)
    except Exception:
        col = None
    if not col:
        return df
    def _grupo(t):
        t = str(t or "").lower()
        return 0 if "mensual" in t else 1 if "trimestral" in t else 2
    orden = df[col].map(_grupo)
    return df.assign(_orden=orden).sort_values("_orden", kind="stable").drop(columns="_orden")


def tabla_seleccionable(df_display, key):
    """
    Muestra los proyectos para elegir, uno debajo de otro (en el ordenador y en el
    móvil), y devuelve la lista de IDs marcados en el mismo orden.

    Cada tarjeta: casilla con el nombre del proyecto y, debajo, país, rentabilidad
    anualizada y total, precio, tipo de rendimientos y enlace al dossier.
    """
    if df_display is None or len(df_display) == 0:
        return []
    
    marcados_antes = st.session_state.sel_tablas.get(key, set())
    
    def _pct(v):
        try:
            return f"{es(float(v), 2)} %" if v is not None and v == v else "—"
        except (TypeError, ValueError):
            return "—"
    
    marcados = []
    with st.container(key=f"lista_{key}"):
        for _, fila in df_display.iterrows():
            pid = fila['ID']
            clave_casilla = f"tarjeta_{key}_{pid}"
            if clave_casilla not in st.session_state:
                st.session_state[clave_casilla] = pid in marcados_antes
            dossier = str(fila.get('Dossier', '') or '').strip()
            enlace = (f"<a href='{dossier}' target='_blank' rel='noopener'>Ver dossier ↗</a>"
                      if dossier.lower().startswith('http') else "—")
            tipo = str(fila.get('Tipología de dividendo', '') or '').strip() or "—"
            with st.container(key=f"tm_{key}_{pid}"):
                elegido = st.checkbox(f"{fila.get('Nombre del proyecto', pid)}", key=clave_casilla)
                st.markdown(html_seguro(
                    "<div class='tm-datos tm-proyecto'>"
                    f"<div><b class='tm-pais'>{fila.get('Ubicación', '') or '—'}</b></div>"
                    f"<div><span>Rent. anualizada</span><b>{_pct(fila.get('Rentabilidad Anualizada'))}</b></div>"
                    f"<div><span>Rent. total</span><b>{_pct(fila.get('Rentabilidad Total'))}</b></div>"
                    f"<div><span>Precio</span><b>{fila.get('Precio', '—')}</b></div>"
                    f"<div><span>Tipo de rendimientos</span><b class='tm-texto'>{tipo}</b></div>"
                    f"<div><span>Dossier</span><b>{enlace}</b></div>"
                    "</div>"), unsafe_allow_html=True)
            if elegido:
                marcados.append(pid)
    
    st.session_state.sel_tablas[key] = set(marcados)
    return marcados


# Todo lo definido aquí se exporta (también lo que empieza por «_»)
__all__ = [_n for _n in dir() if not _n.startswith("__")]
