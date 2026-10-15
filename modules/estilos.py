"""
ESTILOS - CSS de toda la app (paleta, tipografía, botones, tablas y móvil).
"""
from modules.comun import *  # noqa: F401,F403  (constantes, colores y funciones comunes)


def aplicar_estilos():
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fustat:wght@400;500;600;700;800&display=swap');

        html, body, .stApp, .stApp div, .stApp p, .stApp label, .stApp input, .stApp textarea,
        .stApp button, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp span:not([data-testid="stIconMaterial"]) {{
            font-family: 'Fustat', 'Segoe UI', sans-serif;
        }}
        /* Los iconos de Streamlit usan su propia fuente: si se les cambia, en vez
           del icono aparece su nombre en texto (p. ej. «keyboard_double»). */
        [data-testid="stIconMaterial"], .material-symbols-rounded {{
            font-family: 'Material Symbols Rounded' !important;
        }}

        .stApp {{ background-color: {COLOR_FONDO}; color: {COLOR_NAVY}; }}

        /* Títulos */
        h1 {{ color: {COLOR_NAVY}; font-weight: 800; }}
        h2 {{
            color: {COLOR_NAVY};
            font-size: 1.7em;
            font-weight: 800;
            margin-top: 10px;
            padding-bottom: 6px;
            border-bottom: 3px solid {COLOR_AMBAR};
            display: inline-block;
        }}
        h3 {{ color: {COLOR_NAVY}; font-size: 1.25em; font-weight: 700; margin-top: 10px; }}
        h4 {{ color: {COLOR_GRIS}; font-weight: 600; }}

        /* Botones: ámbar con texto navy (más legible que el blanco sobre ámbar) */
        .stButton button, .stDownloadButton button {{
            background-color: {COLOR_AMBAR};
            color: {COLOR_NAVY};
            border: none;
            border-radius: 8px;
            font-weight: 700;
            transition: all 0.2s ease;
        }}
        .stButton button:hover, .stDownloadButton button:hover {{
            background-color: #f5a11f;
            color: {COLOR_NAVY};
            border: none;
        }}
        .stButton button:focus:not(:active) {{ color: {COLOR_NAVY}; border: none; }}
        .stButton button:disabled {{
            background-color: {COLOR_BORDE};
            color: {COLOR_GRIS_CLARO};
        }}

        /* Campos de formulario sobre blanco */
        div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {{
            background-color: #ffffff;
            border-color: {COLOR_BORDE};
            border-radius: 8px;
        }}

        /* Barra de progreso */
        .stProgress > div > div > div > div {{ background-color: {COLOR_AMBAR}; }}

        /* Tablas */
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {{
            border: 1px solid {COLOR_BORDE};
            border-radius: 12px;
            background-color: #ffffff;
        }}

        hr {{ border-color: {COLOR_BORDE}; }}

        /* Botones secundarios (Atrás, opciones no elegidas, crear otra cartera): contorno en vez
           de relleno, para que la acción principal de cada pantalla destaque */
        [class*="st-key-"][class*="_back"] button, [class*="st-key-"][class*="_sec"] button,
        .st-key-btn_nueva_cartera button {{
            background-color: #ffffff; color: {COLOR_NAVY}; border: 1px solid #c9cdd3;
            font-weight: 600;
        }}
        [class*="st-key-"][class*="_back"] button:hover, [class*="st-key-"][class*="_sec"] button:hover,
        .st-key-btn_nueva_cartera button:hover {{
            background-color: #f1f3f5; color: {COLOR_NAVY}; border: 1px solid #b4b9c1;
        }}
        /* Foco visible con teclado */
        .stButton button:focus-visible, .stDownloadButton button:focus-visible {{
            outline: 2px solid {COLOR_AMBAR_OSCURO}; outline-offset: 2px;
        }}
        /* Superficies del navegador con la paleta de la marca */
        ::selection {{ background: {COLOR_AMBAR_CLARO}; color: {COLOR_NAVY}; }}
        .stApp input, .stApp textarea {{ caret-color: {COLOR_AMBAR_OSCURO}; }}
        .stApp a {{ color: {COLOR_AMBAR_OSCURO}; text-underline-offset: 2px; }}
        /* Cifras alineadas en columnas */
        .kpi-valor, .tarjeta-valor, .tabla-comp td {{ font-variant-numeric: tabular-nums; }}

        /* Pantallas táctiles: zonas de pulsación de al menos 44 px */
        @media (pointer: coarse) {{
            .stButton button, .stDownloadButton button {{ min-height: 44px; }}
            .st-key-tabla_cartera div[data-baseweb="input"] {{ min-height: 44px !important; }}
        }}

        /* ===== Botón para agendar una reunión: círculo flotante arriba a la derecha ===== */
        a.cta-flotante, .stApp a.cta-flotante {{
            position: fixed; top: 76px; right: 28px; z-index: 999991;
            display: flex; align-items: center; gap: 10px; text-decoration: none;
        }}
        a.cta-flotante .cta-texto {{
            background: #ffffff; color: {COLOR_NAVY}; border: 1px solid {COLOR_BORDE};
            border-radius: 999px; padding: 9px 16px; font-size: 14px; font-weight: 600; line-height: 1.2;
            box-shadow: 0 6px 18px rgba(31, 41, 55, 0.14); white-space: nowrap;
            transition: transform 0.2s ease;
        }}
        a.cta-flotante .cta-dudas {{ color: {COLOR_AMBAR_OSCURO}; font-weight: 800; }}
        a.cta-flotante .cta-corta {{ display: none; }}
        a.cta-flotante .cta-circulo {{
            position: relative; width: 58px; height: 58px; border-radius: 50%; flex: 0 0 58px;
            background: {COLOR_AMBAR}; display: flex; align-items: center; justify-content: center;
            box-shadow: 0 10px 24px rgba(252, 163, 17, 0.45);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        a.cta-flotante .cta-circulo svg {{ width: 28px; height: 28px; }}
        /* Onda suave alrededor del círculo para llamar la atención */
        a.cta-flotante .cta-circulo::after {{
            content: ""; position: absolute; inset: 0; border-radius: 50%;
            border: 2px solid {COLOR_AMBAR}; animation: cta-onda 2.6s ease-out infinite;
        }}
        @keyframes cta-onda {{
            0% {{ transform: scale(1); opacity: 0.7; }}
            70% {{ transform: scale(1.45); opacity: 0; }}
            100% {{ transform: scale(1.45); opacity: 0; }}
        }}
        a.cta-flotante:hover .cta-circulo {{ transform: scale(1.06); box-shadow: 0 14px 30px rgba(252, 163, 17, 0.55); }}
        a.cta-flotante:hover .cta-texto {{ transform: translateX(-3px); }}
        a.cta-flotante:focus-visible {{ outline: none; }}
        a.cta-flotante:focus-visible .cta-circulo {{ outline: 3px solid {COLOR_NAVY}; outline-offset: 3px; }}
        @media (prefers-reduced-motion: reduce) {{
            a.cta-flotante .cta-circulo::after {{ animation: none; opacity: 0; }}
        }}

        /* ===== Tablas (ordenador) y tarjetas (móvil) con los mismos datos ===== */
        [class*="st-key-vista_tarjetas_"] {{ display: none; }}
        [class*="st-key-tm_"], .tm-tarjeta {{
            background: #ffffff; border: 1px solid {COLOR_BORDE}; border-radius: 12px;
            padding: 12px 14px; margin-bottom: 1.1rem;
        }}
        [class*="st-key-tm_"] div[data-testid="stVerticalBlock"] {{ gap: 0.25rem; }}
        [class*="st-key-tm_"]:has(input:checked) {{ border: 2px solid {COLOR_AMBAR}; background: #fffaf0; }}
        [class*="st-key-tm_"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0 !important; }}
        [class*="st-key-tm_"] label {{ min-height: 44px; align-items: center; font-weight: 600; }}
        .tm-nombre {{ font-weight: 700; font-size: 16px; color: {COLOR_NAVY}; }}
        .tm-pct {{ font-weight: 800; color: {COLOR_AMBAR_OSCURO}; font-variant-numeric: tabular-nums; }}
        .tm-sub {{ font-size: 13px; color: {COLOR_GRIS}; margin: 2px 0 8px 0; }}
        .tm-datos {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 12px; }}
        .tm-datos.dos {{ grid-template-columns: repeat(2, 1fr); }}
        /* Tarjetas de selección de proyectos (Paso 4): nombre junto a la casilla y datos debajo */
        [class*="st-key-tm_"] [data-testid="stCheckbox"] label p {{
            font-size: 17px; font-weight: 700; color: {COLOR_NAVY};
        }}
        .tm-proyecto {{ grid-template-columns: repeat(6, minmax(0, 1fr)); padding-left: 28px; margin-top: 2px; }}
        .tm-proyecto .tm-texto {{ font-size: 14px; font-weight: 600; }}
        .tm-proyecto a {{ font-weight: 700; text-decoration: none; }}
        .tm-datos div {{ display: flex; flex-direction: column; }}
        .tm-datos span {{ font-size: 11px; font-weight: 700; color: {COLOR_GRIS}; letter-spacing: 0.3px;
                         text-transform: uppercase; }}
        .tm-datos b {{ font-size: 15px; color: {COLOR_NAVY}; font-variant-numeric: tabular-nums; }}

        /* Etiquetas que solo se ven en el móvil (en el ordenador las da la cabecera) */
        .v-movil {{ display: none; }}
        .etq-movil {{ display: none; font-size: 11px; font-weight: 700; color: {COLOR_GRIS};
                     letter-spacing: 0.4px; margin: 2px 0 3px 0; }}

        /* ===== MÓVIL (pantallas de menos de 640 px). En el ordenador no cambia nada ===== */
        @media (max-width: 640px) {{
            [data-testid="stMainBlockContainer"], .block-container {{
                padding-left: 1rem !important; padding-right: 1rem !important; padding-top: 2.5rem !important;
            }}
            .titulo-app {{ font-size: 27px !important; }}
            .marca-app {{ font-size: 18px !important; }}
            .stApp h2, .stApp [data-testid="stMarkdownContainer"] h2 {{ font-size: 1.4rem !important; }}
            .stApp h3, .stApp [data-testid="stMarkdownContainer"] h3 {{ font-size: 1.15rem !important; }}
            .stApp h4, .stApp [data-testid="stMarkdownContainer"] h4 {{ font-size: 1.02rem !important; }}
            /* El icono de enlace junto a los títulos se ve siempre en el móvil: se oculta */
            [data-testid="stHeaderActionElements"] {{ display: none !important; }}
            .etq-movil {{ display: block; }}
            /* Botón para agendar en el móvil: solo el círculo (como en las apps), sin la burbuja
               de texto, que taparía el contenido al desplazarse */
            a.cta-flotante, .stApp a.cta-flotante {{ top: 56px; right: 12px; }}
            a.cta-flotante .cta-circulo {{ width: 54px; height: 54px; flex-basis: 54px; }}
            a.cta-flotante .cta-circulo svg {{ width: 26px; height: 26px; }}
            a.cta-flotante .cta-texto {{ display: none; }}
            /* Sin zoom automático del iPhone al escribir: casillas de al menos 16 px */
            .stApp input, .stApp textarea {{ font-size: 16px !important; }}

            /* Tarjetas de proyectos: datos en dos columnas */
            .tm-proyecto {{ grid-template-columns: repeat(2, minmax(0, 1fr)); padding-left: 0; }}
            /* Tablas → tarjetas */
            [class*="st-key-vista_tabla_"] {{ display: none; }}
            [class*="st-key-vista_tarjetas_"] {{ display: block; }}

            /* Paso 2: sin hueco vacío en las tarjetas cortas */
            .tarjeta-estatus {{ min-height: 0 !important; }}

            /* Filas de navegación: sin huecos vacíos */
            [data-testid="stHorizontalBlock"]:has([class*="_back"]) > [data-testid="stColumn"]:not(:has(button)) {{
                display: none;
            }}
            /* Paso 5: la acción principal primero */
            [data-testid="stHorizontalBlock"]:has(.st-key-btn_paso5_back) {{ flex-direction: column-reverse; }}
            /* Pasos 2 a 4: «Atrás» y «Siguiente» fijos abajo, uno al lado del otro, siempre a mano */
            [data-testid="stHorizontalBlock"]:has([class*="_back"]):not(:has(.st-key-btn_paso5_back)) {{
                position: fixed; left: 0; right: 0; bottom: 0; z-index: 999990;
                flex-direction: row !important; flex-wrap: nowrap !important; gap: 0.6rem !important;
                background: {COLOR_FONDO}; border-top: 1px solid {COLOR_BORDE};
                margin: 0; width: 100% !important;
                padding: 10px 1rem calc(10px + env(safe-area-inset-bottom));
                box-shadow: 0 -6px 16px rgba(31, 41, 55, 0.06);
            }}
            /* Hueco al final de la página para que la barra no tape el pie */
            [data-testid="stMainBlockContainer"]:has([class*="_back"]):not(:has(.st-key-btn_paso5_back)) {{
                padding-bottom: 96px !important;
            }}
            [data-testid="stHorizontalBlock"]:has([class*="_back"]):not(:has(.st-key-btn_paso5_back))
                > [data-testid="stColumn"]:has([class*="_back"]) {{
                flex: 0 0 34% !important; min-width: 0 !important; width: 34% !important;
            }}
            [data-testid="stHorizontalBlock"]:has([class*="_back"]):not(:has(.st-key-btn_paso5_back))
                > [data-testid="stColumn"]:has(button):not(:has([class*="_back"])) {{
                flex: 1 1 0 !important; min-width: 0 !important; width: auto !important;
            }}
            [data-testid="stHorizontalBlock"]:has([class*="_back"]):not(:has(.st-key-btn_paso5_back))
                [data-testid="stCaptionContainer"] {{ display: none; }}
            .v-escritorio {{ display: none; }}
            .v-movil {{ display: inline !important; }}

            /* Tarjetas de resumen del Paso 5: de dos en dos en vez de una debajo de otra */
            [data-testid="stHorizontalBlock"]:has(.tarjeta) {{ flex-wrap: wrap; gap: 0.6rem !important; row-gap: 0.6rem !important; }}
            [data-testid="stHorizontalBlock"]:has(.tarjeta) > [data-testid="stColumn"] {{
                flex: 1 1 calc(50% - 0.6rem) !important; min-width: calc(50% - 0.6rem) !important;
                width: calc(50% - 0.6rem) !important;
            }}
            .tarjeta {{ padding: 10px 12px !important; min-height: 88px !important; margin-bottom: 1rem; }}
            .tarjeta-valor {{ font-size: 19px !important; }}
            .tarjeta-titulo, .tarjeta-sub {{ font-size: 11px !important; }}

            /* Tabla de la comparativa por estatus: más compacta */
            .tabla-comp td {{ padding: 8px 3px !important; font-size: 11px !important; }}
            .tabla-comp td:first-child {{ min-width: 78px; max-width: 96px; padding-left: 7px !important;
                                         white-space: normal !important; position: sticky; left: 0;
                                         background: inherit; z-index: 1; }}

            /* Mapa: se recorta el espacio vacío de arriba y abajo */
            .st-key-mapa [data-testid="stVegaLiteChart"] {{
                height: 56vw !important; overflow: hidden; display: flex; align-items: center;
            }}
        }}
    </style>
    """, unsafe_allow_html=True)
