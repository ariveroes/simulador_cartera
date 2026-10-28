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
# (bandera, código ISO de 2 letras, prefijo, nombre, iniciales de 3 letras). El primero sale por defecto.
# Todos los países (fuente: el plan internacional de numeración de la UIT, vía la
# librería phonenumbers). España primero; el resto, por orden alfabético en español.
PREFIJOS_TELEFONO = [
    ("🇪🇸", "ES", "+34", "España", "ESP"),
    ("🇦🇫", "AF", "+93", "Afganistán", "AFG"),
    ("🇦🇱", "AL", "+355", "Albania", "ALB"),
    ("🇩🇪", "DE", "+49", "Alemania", "DEU"),
    ("🇦🇩", "AD", "+376", "Andorra", "AND"),
    ("🇦🇴", "AO", "+244", "Angola", "AGO"),
    ("🇦🇮", "AI", "+1", "Anguila", "AIA"),
    ("🇦🇬", "AG", "+1", "Antigua y Barbuda", "ATG"),
    ("🇸🇦", "SA", "+966", "Arabia Saudí", "SAU"),
    ("🇩🇿", "DZ", "+213", "Argelia", "DZA"),
    ("🇦🇷", "AR", "+54", "Argentina", "ARG"),
    ("🇦🇲", "AM", "+374", "Armenia", "ARM"),
    ("🇦🇼", "AW", "+297", "Aruba", "ABW"),
    ("🇦🇺", "AU", "+61", "Australia", "AUS"),
    ("🇦🇹", "AT", "+43", "Austria", "AUT"),
    ("🇦🇿", "AZ", "+994", "Azerbaiyán", "AZE"),
    ("🇧🇸", "BS", "+1", "Bahamas", "BHS"),
    ("🇧🇩", "BD", "+880", "Bangladés", "BGD"),
    ("🇧🇧", "BB", "+1", "Barbados", "BRB"),
    ("🇧🇭", "BH", "+973", "Baréin", "BHR"),
    ("🇧🇪", "BE", "+32", "Bélgica", "BEL"),
    ("🇧🇿", "BZ", "+501", "Belice", "BLZ"),
    ("🇧🇯", "BJ", "+229", "Benín", "BEN"),
    ("🇧🇲", "BM", "+1", "Bermudas", "BMU"),
    ("🇧🇾", "BY", "+375", "Bielorrusia", "BLR"),
    ("🇧🇴", "BO", "+591", "Bolivia", "BOL"),
    ("🇧🇦", "BA", "+387", "Bosnia y Herzegovina", "BIH"),
    ("🇧🇼", "BW", "+267", "Botsuana", "BWA"),
    ("🇧🇷", "BR", "+55", "Brasil", "BRA"),
    ("🇧🇳", "BN", "+673", "Brunéi", "BRN"),
    ("🇧🇬", "BG", "+359", "Bulgaria", "BGR"),
    ("🇧🇫", "BF", "+226", "Burkina Faso", "BFA"),
    ("🇧🇮", "BI", "+257", "Burundi", "BDI"),
    ("🇧🇹", "BT", "+975", "Bután", "BTN"),
    ("🇨🇻", "CV", "+238", "Cabo Verde", "CPV"),
    ("🇰🇭", "KH", "+855", "Camboya", "KHM"),
    ("🇨🇲", "CM", "+237", "Camerún", "CMR"),
    ("🇨🇦", "CA", "+1", "Canadá", "CAN"),
    ("🇧🇶", "BQ", "+599", "Caribe neerlandés", "BES"),
    ("🇶🇦", "QA", "+974", "Catar", "QAT"),
    ("🇹🇩", "TD", "+235", "Chad", "TCD"),
    ("🇨🇿", "CZ", "+420", "Chequia", "CZE"),
    ("🇨🇱", "CL", "+56", "Chile", "CHL"),
    ("🇨🇳", "CN", "+86", "China", "CHN"),
    ("🇨🇾", "CY", "+357", "Chipre", "CYP"),
    ("🇻🇦", "VA", "+39", "Ciudad del Vaticano", "VAT"),
    ("🇨🇴", "CO", "+57", "Colombia", "COL"),
    ("🇰🇲", "KM", "+269", "Comoras", "COM"),
    ("🇨🇬", "CG", "+242", "Congo", "COG"),
    ("🇰🇵", "KP", "+850", "Corea del Norte", "PRK"),
    ("🇰🇷", "KR", "+82", "Corea del Sur", "KOR"),
    ("🇨🇷", "CR", "+506", "Costa Rica", "CRI"),
    ("🇨🇮", "CI", "+225", "Côte d’Ivoire", "CIV"),
    ("🇭🇷", "HR", "+385", "Croacia", "HRV"),
    ("🇨🇺", "CU", "+53", "Cuba", "CUB"),
    ("🇨🇼", "CW", "+599", "Curazao", "CUW"),
    ("🇩🇰", "DK", "+45", "Dinamarca", "DNK"),
    ("🇩🇲", "DM", "+1", "Dominica", "DMA"),
    ("🇪🇨", "EC", "+593", "Ecuador", "ECU"),
    ("🇪🇬", "EG", "+20", "Egipto", "EGY"),
    ("🇸🇻", "SV", "+503", "El Salvador", "SLV"),
    ("🇦🇪", "AE", "+971", "Emiratos Árabes Unidos", "ARE"),
    ("🇪🇷", "ER", "+291", "Eritrea", "ERI"),
    ("🇸🇰", "SK", "+421", "Eslovaquia", "SVK"),
    ("🇸🇮", "SI", "+386", "Eslovenia", "SVN"),
    ("🇺🇸", "US", "+1", "Estados Unidos", "USA"),
    ("🇪🇪", "EE", "+372", "Estonia", "EST"),
    ("🇸🇿", "SZ", "+268", "Esuatini", "SWZ"),
    ("🇪🇹", "ET", "+251", "Etiopía", "ETH"),
    ("🇵🇭", "PH", "+63", "Filipinas", "PHL"),
    ("🇫🇮", "FI", "+358", "Finlandia", "FIN"),
    ("🇫🇯", "FJ", "+679", "Fiyi", "FJI"),
    ("🇫🇷", "FR", "+33", "Francia", "FRA"),
    ("🇬🇦", "GA", "+241", "Gabón", "GAB"),
    ("🇬🇲", "GM", "+220", "Gambia", "GMB"),
    ("🇬🇪", "GE", "+995", "Georgia", "GEO"),
    ("🇬🇭", "GH", "+233", "Ghana", "GHA"),
    ("🇬🇮", "GI", "+350", "Gibraltar", "GIB"),
    ("🇬🇩", "GD", "+1", "Granada", "GRD"),
    ("🇬🇷", "GR", "+30", "Grecia", "GRC"),
    ("🇬🇱", "GL", "+299", "Groenlandia", "GRL"),
    ("🇬🇵", "GP", "+590", "Guadalupe", "GLP"),
    ("🇬🇺", "GU", "+1", "Guam", "GUM"),
    ("🇬🇹", "GT", "+502", "Guatemala", "GTM"),
    ("🇬🇫", "GF", "+594", "Guayana Francesa", "GUF"),
    ("🇬🇬", "GG", "+44", "Guernesey", "GGY"),
    ("🇬🇳", "GN", "+224", "Guinea", "GIN"),
    ("🇬🇶", "GQ", "+240", "Guinea Ecuatorial", "GNQ"),
    ("🇬🇼", "GW", "+245", "Guinea-Bisáu", "GNB"),
    ("🇬🇾", "GY", "+592", "Guyana", "GUY"),
    ("🇭🇹", "HT", "+509", "Haití", "HTI"),
    ("🇭🇳", "HN", "+504", "Honduras", "HND"),
    ("🇭🇺", "HU", "+36", "Hungría", "HUN"),
    ("🇮🇳", "IN", "+91", "India", "IND"),
    ("🇮🇩", "ID", "+62", "Indonesia", "IDN"),
    ("🇮🇶", "IQ", "+964", "Irak", "IRQ"),
    ("🇮🇷", "IR", "+98", "Irán", "IRN"),
    ("🇮🇪", "IE", "+353", "Irlanda", "IRL"),
    ("🇮🇲", "IM", "+44", "Isla de Man", "IMN"),
    ("🇨🇽", "CX", "+61", "Isla de Navidad", "CXR"),
    ("🇳🇫", "NF", "+672", "Isla Norfolk", "NFK"),
    ("🇮🇸", "IS", "+354", "Islandia", "ISL"),
    ("🇦🇽", "AX", "+358", "Islas Aland", "ALA"),
    ("🇰🇾", "KY", "+1", "Islas Caimán", "CYM"),
    ("🇨🇨", "CC", "+61", "Islas Cocos", "CCK"),
    ("🇨🇰", "CK", "+682", "Islas Cook", "COK"),
    ("🇫🇴", "FO", "+298", "Islas Feroe", "FRO"),
    ("🇫🇰", "FK", "+500", "Islas Malvinas", "FLK"),
    ("🇲🇵", "MP", "+1", "Islas Marianas del Norte", "MNP"),
    ("🇲🇭", "MH", "+692", "Islas Marshall", "MHL"),
    ("🇸🇧", "SB", "+677", "Islas Salomón", "SLB"),
    ("🇹🇨", "TC", "+1", "Islas Turcas y Caicos", "TCA"),
    ("🇻🇬", "VG", "+1", "Islas Vírgenes Británicas", "VGB"),
    ("🇻🇮", "VI", "+1", "Islas Vírgenes de EE. UU.", "VIR"),
    ("🇮🇱", "IL", "+972", "Israel", "ISR"),
    ("🇮🇹", "IT", "+39", "Italia", "ITA"),
    ("🇯🇲", "JM", "+1", "Jamaica", "JAM"),
    ("🇯🇵", "JP", "+81", "Japón", "JPN"),
    ("🇯🇪", "JE", "+44", "Jersey", "JEY"),
    ("🇯🇴", "JO", "+962", "Jordania", "JOR"),
    ("🇰🇿", "KZ", "+7", "Kazajistán", "KAZ"),
    ("🇰🇪", "KE", "+254", "Kenia", "KEN"),
    ("🇰🇬", "KG", "+996", "Kirguistán", "KGZ"),
    ("🇰🇮", "KI", "+686", "Kiribati", "KIR"),
    ("🇽🇰", "XK", "+383", "Kosovo", "XKX"),
    ("🇰🇼", "KW", "+965", "Kuwait", "KWT"),
    ("🇱🇦", "LA", "+856", "Laos", "LAO"),
    ("🇱🇸", "LS", "+266", "Lesoto", "LSO"),
    ("🇱🇻", "LV", "+371", "Letonia", "LVA"),
    ("🇱🇧", "LB", "+961", "Líbano", "LBN"),
    ("🇱🇷", "LR", "+231", "Liberia", "LBR"),
    ("🇱🇾", "LY", "+218", "Libia", "LBY"),
    ("🇱🇮", "LI", "+423", "Liechtenstein", "LIE"),
    ("🇱🇹", "LT", "+370", "Lituania", "LTU"),
    ("🇱🇺", "LU", "+352", "Luxemburgo", "LUX"),
    ("🇲🇰", "MK", "+389", "Macedonia del Norte", "MKD"),
    ("🇲🇬", "MG", "+261", "Madagascar", "MDG"),
    ("🇲🇾", "MY", "+60", "Malasia", "MYS"),
    ("🇲🇼", "MW", "+265", "Malaui", "MWI"),
    ("🇲🇻", "MV", "+960", "Maldivas", "MDV"),
    ("🇲🇱", "ML", "+223", "Mali", "MLI"),
    ("🇲🇹", "MT", "+356", "Malta", "MLT"),
    ("🇲🇦", "MA", "+212", "Marruecos", "MAR"),
    ("🇲🇶", "MQ", "+596", "Martinica", "MTQ"),
    ("🇲🇺", "MU", "+230", "Mauricio", "MUS"),
    ("🇲🇷", "MR", "+222", "Mauritania", "MRT"),
    ("🇾🇹", "YT", "+262", "Mayotte", "MYT"),
    ("🇲🇽", "MX", "+52", "México", "MEX"),
    ("🇫🇲", "FM", "+691", "Micronesia", "FSM"),
    ("🇲🇩", "MD", "+373", "Moldavia", "MDA"),
    ("🇲🇨", "MC", "+377", "Mónaco", "MCO"),
    ("🇲🇳", "MN", "+976", "Mongolia", "MNG"),
    ("🇲🇪", "ME", "+382", "Montenegro", "MNE"),
    ("🇲🇸", "MS", "+1", "Montserrat", "MSR"),
    ("🇲🇿", "MZ", "+258", "Mozambique", "MOZ"),
    ("🇲🇲", "MM", "+95", "Myanmar (Birmania)", "MMR"),
    ("🇳🇦", "NA", "+264", "Namibia", "NAM"),
    ("🇳🇷", "NR", "+674", "Nauru", "NRU"),
    ("🇳🇵", "NP", "+977", "Nepal", "NPL"),
    ("🇳🇮", "NI", "+505", "Nicaragua", "NIC"),
    ("🇳🇪", "NE", "+227", "Níger", "NER"),
    ("🇳🇬", "NG", "+234", "Nigeria", "NGA"),
    ("🇳🇺", "NU", "+683", "Niue", "NIU"),
    ("🇳🇴", "NO", "+47", "Noruega", "NOR"),
    ("🇳🇨", "NC", "+687", "Nueva Caledonia", "NCL"),
    ("🇳🇿", "NZ", "+64", "Nueva Zelanda", "NZL"),
    ("🇴🇲", "OM", "+968", "Omán", "OMN"),
    ("🇳🇱", "NL", "+31", "Países Bajos", "NLD"),
    ("🇵🇰", "PK", "+92", "Pakistán", "PAK"),
    ("🇵🇼", "PW", "+680", "Palaos", "PLW"),
    ("🇵🇦", "PA", "+507", "Panamá", "PAN"),
    ("🇵🇬", "PG", "+675", "Papúa Nueva Guinea", "PNG"),
    ("🇵🇾", "PY", "+595", "Paraguay", "PRY"),
    ("🇵🇪", "PE", "+51", "Perú", "PER"),
    ("🇵🇫", "PF", "+689", "Polinesia Francesa", "PYF"),
    ("🇵🇱", "PL", "+48", "Polonia", "POL"),
    ("🇵🇹", "PT", "+351", "Portugal", "PRT"),
    ("🇵🇷", "PR", "+1", "Puerto Rico", "PRI"),
    ("🇭🇰", "HK", "+852", "RAE de Hong Kong (China)", "HKG"),
    ("🇲🇴", "MO", "+853", "RAE de Macao (China)", "MAC"),
    ("🇬🇧", "GB", "+44", "Reino Unido", "GBR"),
    ("🇨🇫", "CF", "+236", "República Centroafricana", "CAF"),
    ("🇨🇩", "CD", "+243", "República Democrática del Congo", "COD"),
    ("🇩🇴", "DO", "+1", "República Dominicana", "DOM"),
    ("🇷🇪", "RE", "+262", "Reunión", "REU"),
    ("🇷🇼", "RW", "+250", "Ruanda", "RWA"),
    ("🇷🇴", "RO", "+40", "Rumanía", "ROU"),
    ("🇷🇺", "RU", "+7", "Rusia", "RUS"),
    ("🇪🇭", "EH", "+212", "Sáhara Occidental", "ESH"),
    ("🇼🇸", "WS", "+685", "Samoa", "WSM"),
    ("🇦🇸", "AS", "+1", "Samoa Americana", "ASM"),
    ("🇧🇱", "BL", "+590", "San Bartolomé", "BLM"),
    ("🇰🇳", "KN", "+1", "San Cristóbal y Nieves", "KNA"),
    ("🇸🇲", "SM", "+378", "San Marino", "SMR"),
    ("🇲🇫", "MF", "+590", "San Martín", "MAF"),
    ("🇵🇲", "PM", "+508", "San Pedro y Miquelón", "SPM"),
    ("🇻🇨", "VC", "+1", "San Vicente y las Granadinas", "VCT"),
    ("🇸🇭", "SH", "+290", "Santa Elena", "SHN"),
    ("🇱🇨", "LC", "+1", "Santa Lucía", "LCA"),
    ("🇸🇹", "ST", "+239", "Santo Tomé y Príncipe", "STP"),
    ("🇸🇳", "SN", "+221", "Senegal", "SEN"),
    ("🇷🇸", "RS", "+381", "Serbia", "SRB"),
    ("🇸🇨", "SC", "+248", "Seychelles", "SYC"),
    ("🇸🇱", "SL", "+232", "Sierra Leona", "SLE"),
    ("🇸🇬", "SG", "+65", "Singapur", "SGP"),
    ("🇸🇽", "SX", "+1", "Sint Maarten", "SXM"),
    ("🇸🇾", "SY", "+963", "Siria", "SYR"),
    ("🇸🇴", "SO", "+252", "Somalia", "SOM"),
    ("🇱🇰", "LK", "+94", "Sri Lanka", "LKA"),
    ("🇿🇦", "ZA", "+27", "Sudáfrica", "ZAF"),
    ("🇸🇩", "SD", "+249", "Sudán", "SDN"),
    ("🇸🇸", "SS", "+211", "Sudán del Sur", "SSD"),
    ("🇸🇪", "SE", "+46", "Suecia", "SWE"),
    ("🇨🇭", "CH", "+41", "Suiza", "CHE"),
    ("🇸🇷", "SR", "+597", "Surinam", "SUR"),
    ("🇸🇯", "SJ", "+47", "Svalbard y Jan Mayen", "SJM"),
    ("🇹🇭", "TH", "+66", "Tailandia", "THA"),
    ("🇹🇼", "TW", "+886", "Taiwán", "TWN"),
    ("🇹🇿", "TZ", "+255", "Tanzania", "TZA"),
    ("🇹🇯", "TJ", "+992", "Tayikistán", "TJK"),
    ("🇮🇴", "IO", "+246", "Territorio Británico del Océano Índico", "IOT"),
    ("🇵🇸", "PS", "+970", "Territorios Palestinos", "PSE"),
    ("🇹🇱", "TL", "+670", "Timor-Leste", "TLS"),
    ("🇹🇬", "TG", "+228", "Togo", "TGO"),
    ("🇹🇰", "TK", "+690", "Tokelau", "TKL"),
    ("🇹🇴", "TO", "+676", "Tonga", "TON"),
    ("🇹🇹", "TT", "+1", "Trinidad y Tobago", "TTO"),
    ("🇹🇳", "TN", "+216", "Túnez", "TUN"),
    ("🇹🇲", "TM", "+993", "Turkmenistán", "TKM"),
    ("🇹🇷", "TR", "+90", "Turquía", "TUR"),
    ("🇹🇻", "TV", "+688", "Tuvalu", "TUV"),
    ("🇺🇦", "UA", "+380", "Ucrania", "UKR"),
    ("🇺🇬", "UG", "+256", "Uganda", "UGA"),
    ("🇺🇾", "UY", "+598", "Uruguay", "URY"),
    ("🇺🇿", "UZ", "+998", "Uzbekistán", "UZB"),
    ("🇻🇺", "VU", "+678", "Vanuatu", "VUT"),
    ("🇻🇪", "VE", "+58", "Venezuela", "VEN"),
    ("🇻🇳", "VN", "+84", "Vietnam", "VNM"),
    ("🇼🇫", "WF", "+681", "Wallis y Futuna", "WLF"),
    ("🇾🇪", "YE", "+967", "Yemen", "YEM"),
    ("🇩🇯", "DJ", "+253", "Yibuti", "DJI"),
    ("🇿🇲", "ZM", "+260", "Zambia", "ZMB"),
    ("🇿🇼", "ZW", "+263", "Zimbabue", "ZWE"),
]


def etiqueta_prefijo(p):
    """Texto del desplegable de prefijo: «🇪🇸 +34 España». El prefijo va delante para
    que se vea aunque el nombre se corte en el móvil. Se puede buscar por el nombre
    del país o por el prefijo (+34)."""
    return f"{p[0]} {p[2]} {p[3]}"


def validar_telefono(numero, pais):
    """Comprueba el teléfono según el formato del país elegido (p. ej. España: 9 cifras;
    México y Argentina: 10). `pais` es una fila de PREFIJOS_TELEFONO.
    Devuelve (es_valido, teléfono con prefijo para guardar, cifras esperadas en ese país).
    Usa la librería phonenumbers (la base de datos de numeración de Google); si no
    estuviera instalada, solo se comprueba que tenga entre 6 y 14 cifras."""
    numero = (numero or "").strip()
    texto_valido = bool(re.match(r"^\+?[\d\s().-]+$", numero))
    cifras = re.sub(r"\D", "", numero)
    guardar = numero if numero.startswith("+") else f"{pais[2]} {numero}"
    try:
        import phonenumbers
    except ImportError:
        return texto_valido and 6 <= len(cifras) <= 14, guardar, ""
    esperadas = ""
    try:
        meta = phonenumbers.PhoneMetadata.metadata_for_region(pais[1])
        largos = sorted(set(meta.mobile.possible_length or meta.general_desc.possible_length or ()))
        if pais[1] == "AR":   # en Argentina se suele escribir sin el 9 de los móviles
            largos = [10]
        if largos:
            esperadas = (f"{largos[0]}" if len(largos) == 1
                         else ", ".join(str(l) for l in largos[:-1]) + f" o {largos[-1]}")
    except Exception:
        pass
    if not texto_valido:
        return False, guardar, esperadas
    try:
        num = phonenumbers.parse(numero, pais[1])
    except phonenumbers.NumberParseException:
        return False, guardar, esperadas
    if not phonenumbers.is_valid_number(num):
        return False, guardar, esperadas
    return True, phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL), esperadas


def ejemplo_telefono(pais):
    """Número de ejemplo del país elegido, sin el prefijo (España: «612 34 56 78»)."""
    try:
        import phonenumbers
        ej = phonenumbers.example_number_for_type(pais[1], phonenumbers.PhoneNumberType.MOBILE)
        texto = phonenumbers.format_number(ej, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        texto = texto.split(" ", 1)[1]
        if pais[1] == "AR" and texto.startswith("9 "):   # en Argentina se suele escribir sin el 9
            texto = texto[2:]
        return texto
    except Exception:
        return "600 123 456"


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

    # Si no se puede abrir el Sheet OTC (p. ej. es privado y no está compartido con la
    # cuenta de servicio del simulador), no se muestra nada de OTC: sin las reservas,
    # el stock de Reental parecería disponible aunque ya esté comprometido.
    try:
        otc_storage._libro().worksheet("Ofertas")
    except Exception as e:
        print(f"❌ No se puede leer el Sheet OTC ({otc_storage.SPREADSHEET_ID}): {e}. "
              "Compártelo (Lector) con el client_email de [gcp_service_account] de los Secrets.")
        return {"catalogo": {}, "precios": {}, "error": "sin_acceso_sheet"}

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
    return {"catalogo": cat, "precios": precios, "error": "",
            "n_ofertas": len(ofertas or []), "n_reservas": len(reservas or []),
            "leido": datetime.now().strftime("%d/%m/%Y %H:%M")}


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

    if res.get("error") == "sin_acceso_sheet":
        st.warning("Ahora mismo no hemos podido revisar todos los proyectos disponibles. "
                   "Inténtalo de nuevo en unos minutos.")
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

# En el Paso 4 no se muestran los proyectos que terminan en menos de estos meses:
# les queda tan poco que su rentabilidad anualizada sale disparada y no es comparable.
MESES_MINIMOS_HASTA_FIN = 4


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


# Objetivos del Paso 2: (título, explicación). Se guarda el título; el Paso 4 ordena
# los proyectos por rentas si el objetivo contiene «ingresos».
OBJETIVOS = [
    ("Quiero maximizar mi rentabilidad",
     "Quiero invertir en proyectos con mayor rentabilidad anualizada, aunque eso implique esperar más "
     "tiempo para ver el beneficio."),
    ("Quiero recibir ingresos pasivos recurrentes",
     "Quiero invertir en proyectos que me generen rentas periódicas."),
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


def tabla_seleccionable(df_display, key, prefijo_rent=""):
    """
    Muestra los proyectos para elegir, uno debajo de otro (en el ordenador y en el
    móvil), y devuelve la lista de IDs marcados en el mismo orden.

    Cada tarjeta: casilla con el nombre del proyecto y, debajo, país, rentabilidad
    anualizada y total, precio, tipo de rendimientos y enlace al dossier.
    `prefijo_rent` va delante de las rentabilidades (p. ej. «Hasta »).
    """
    if df_display is None or len(df_display) == 0:
        return []
    
    marcados_antes = st.session_state.sel_tablas.get(key, set())
    
    def _pct(v):
        try:
            return f"{prefijo_rent}{es(float(v), 2)} %" if v is not None and v == v else "—"
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




# ========== DIAGNÓSTICO OTC (oculto) ==========
# Se abre añadiendo ?diagnostico=1 a la dirección del simulador (o ?diagnostico=<clave>
# si en los Secrets hay [diagnostico] clave = "…"). Enseña qué lee del documento OTC y,
# proyecto a proyecto, si aparece en el simulador y, si no, por qué.
def diagnostico_otc_pedido():
    valor = str(st.query_params.get("diagnostico", "") or "")
    if not valor:
        return False
    try:
        clave = str(st.secrets["diagnostico"]["clave"])
    except Exception:
        clave = "1"
    return valor == clave


def diagnostico_otc():
    from modules import otc_storage
    st.markdown("## Diagnóstico OTC")
    st.caption("Solo para uso interno. Qué lee el simulador del documento OTC y por qué cada proyecto "
               "aparece o no. Para salir, quita «?diagnostico=…» de la dirección.")

    df = cargar_todos_proyectos()
    if st.button("Volver a leer ahora (sin esperar los 15 minutos)"):
        catalogo_otc.clear()
    res = catalogo_otc(_proyectos_para_catalogo(df))

    if res.get("error") == "sin_acceso_sheet":
        st.error("❌ No puede leer el documento OTC. Compártelo como Lector con este correo: "
                 f"**{_correo_cuenta_servicio()}**")
        return
    if res.get("error") == "falta_clave":
        st.error("❌ Falta la clave de Etherscan en los Secrets ([etherscan] api_key).")
        return
    st.success(f"✅ Lee el documento OTC: {res.get('n_ofertas', '?')} ofertas y {res.get('n_reservas', '?')} "
               f"reservas (leído el {res.get("leido", "?")} UTC; se vuelve a leer cada 15 minutos).")

    por_addr = {str(r.get('Token Address', '') or '').strip().lower(): r for _, r in df.iterrows()}
    cat = res.get("catalogo") or {}
    precios = res.get("precios") or {}
    filas = []
    for addr, d in cat.items():
        fila = por_addr.get(addr)
        reental = d.get('reental') or 0.0
        terceros = d.get('terceros') or []
        validas = ([reental] if reental > MIN_TOKENS_OTC else []) + [
            t['disponible'] for t in terceros if t['disponible'] > MIN_TOKENS_OTC and (t.get('precio') or 0) > 0]
        fin = fila.get('fecha_fin_calculo') if fila is not None else None
        if fila is None:
            motivo = "No está en el Master con ese Token Address"
        elif termina_pronto(fin):
            motivo = (f"Termina en menos de {MESES_MINIMOS_HASTA_FIN} meses"
                      + (f" (fin {fin.strftime('%m/%Y')})" if hasattr(fin, 'strftime') else ""))
        elif not validas:
            motivo = f"{MIN_TOKENS_OTC} tokens o menos en cada oferta"
        else:
            motivo = ""
        filas.append({
            "Proyecto": (fila.get('Nombre del proyecto') if fila is not None else d.get('nombre')) or addr[:10],
            "ID": (fila.get('ID') if fila is not None else d.get('id')) or "",
            "Estado (Master)": fila.get('ESTADO', '') if fila is not None else "",
            "Stock Reental (tokens)": round(reental, 2),
            "Precio stock": ("precio OTC" if _precio_stock_reental(precios, addr) is not None else "emisión")
                            if reental > 0.001 else "",
            "Ofertas de terceros": len(terceros),
            "Tokens de terceros": round(sum(t['disponible'] for t in terceros), 2),
            "Fin estimado": fin.strftime('%m/%Y') if hasattr(fin, 'strftime') else "—",
            "¿Aparece?": "Sí" if not motivo else "No",
            "Motivo": motivo,
        })
    if filas:
        tabla = pd.DataFrame(filas).sort_values(["¿Aparece?", "Proyecto"], ascending=[False, True])
        st.markdown(f"#### Proyectos con tokens a la venta ({len(filas)})")
        st.dataframe(tabla, hide_index=True, use_container_width=True)
    else:
        st.info("El catálogo OTC está vacío: ningún proyecto tiene tokens disponibles.")

    # Ofertas activas del documento que la cadena no confirma (no llegan al catálogo)
    try:
        ofertas = otc_storage.read_list("Ofertas")
    except Exception:
        ofertas = []
    en_catalogo = {t.get('oferta_id') for d in cat.values() for t in (d.get('terceros') or [])}
    descartadas = [{
        "Proyecto": o.get('proyecto_nombre', ''), "Tokens en el documento": o.get('n_tokens', ''),
        "Precio": o.get('precio_venta', ''), "Divisa": o.get('divisa', ''),
    } for o in ofertas if o.get('estado') == 'activa' and o.get('id') not in en_catalogo]
    if descartadas:
        st.markdown(f"#### Ofertas activas en el documento que no se muestran ({len(descartadas)})")
        st.caption("La cadena no confirma que haya tokens disponibles: la wallet del vendedor ya no los "
                   "tiene, están reservados o entregados, o no se pudo leer la cadena en ese momento. "
                   "La herramienta OTC de tu compañero usa el mismo criterio para lo «disponible».")
        st.dataframe(pd.DataFrame(descartadas), hide_index=True, use_container_width=True)

    st.caption(f"Además, los proyectos que se están financiando aparecen siempre a precio de emisión, "
               f"aunque no tengan tokens en OTC. En el Paso 3, los de mercados no elegidos en el Paso 2 "
               f"salen más abajo, en «otros mercados».")


def _correo_cuenta_servicio():
    try:
        return str(st.secrets["gcp_service_account"]["client_email"])
    except Exception:
        return "el client_email de [gcp_service_account] en los Secrets"


# Todo lo definido aquí se exporta (también lo que empieza por «_»)
__all__ = [_n for _n in dir() if not _n.startswith("__")]
