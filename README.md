# 🏠 Constructor de Cartera Inmobiliaria Reental

Herramienta interactiva en Streamlit que permite a clientes construir carteras inmobiliarias personalizadas con cálculos automáticos de rentabilidad con reinversión.

## 🎯 Funcionalidades

✅ **Configuración personalizada:**
- Divisa (EUR/USD)
- Capital disponible
- Tipo de inversión (Transferencia bancaria / Cripto)
- Estatus Reental (Reentel / ReentelPro / SuperReentel)

✅ **Filtrado inteligente:**
- Duración (Corto plazo <18m / Largo plazo ≥18m)
- Tipología de rendimientos (Periódicos / Finales / Ambos)
- Ubicación geográfica (múltiple selección)

✅ **Ranking automático:**
- Similitud con preferencias del cliente (33%)
- Rentabilidad anualizada (33%)
- Duración del proyecto (34%)

✅ **Cálculos financieros:**
- Rentabilidades SIN reinversión
- Rentabilidades CON reinversión (interés compuesto)
- 5 horizontes de cálculo (6, 12, 24, 36, 60 meses)

✅ **Generación de PDF:**
- Idéntico al botón "Reental Wealth" del Sheet 1
- Incluye desglose de cartera, rentabilidades, análisis

## 📋 Requisitos

- Python 3.8+
- Google Sheets API (credenciales)
- Acceso a Sheet Intermedio en Google Sheets

## 🚀 Instalación Local

### 1. Clonar o descargar el proyecto

```bash
git clone <repo-url>
cd cartera-builder
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Google Sheets API

#### Opción A: Desarrollo local con `service_account.json`

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto
3. Habilitar Google Sheets API
4. Crear "Service Account"
5. Descargar clave privada (JSON)
6. Guardar como `service_account.json` en raíz del proyecto
7. Compartir Google Sheet con el email del service account

#### Opción B: Streamlit Cloud con `st.secrets`

1. En Streamlit Cloud, ir a Settings → Secrets
2. Copiar contenido de `service_account.json` en formato:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
...
```

### 5. Ejecutar app

```bash
streamlit run app.py
```

La app abrirá en http://localhost:8501

## 📁 Estructura del Proyecto

```
cartera-builder/
│
├── app.py                          # Entrada principal (Streamlit)
├── requirements.txt                # Dependencias
├── README.md                       # Este archivo
│
├── config/
│   ├── __init__.py
│   └── constants.py                # Configuración (tasas, costes, etc.)
│
├── modules/
│   ├── __init__.py
│   ├── data_loader.py              # Carga datos desde Google Sheets
│   ├── calculo_cartera.py          # Cálculos financieros (crítico)
│   └── pdf_generator.py            # [PRÓXIMAMENTE] Generación PDF
│
├── .streamlit/
│   └── config.toml                 # Config de Streamlit (opcional)
│
└── assets/
    └── logo.png                    # [FUTURO] Logo Reental
```

## 🔧 Configuración (constants.py)

### Tasas de Reinversión

```python
REINVERSION_RATES = {
    "Reentel": 0.11,           # 11% anual
    "ReentelPro": 0.13,        # 13% anual
    "SuperReentel": 0.16       # 16% anual
}
```

### Mínimos de Inversión

```python
MINIMO_INVERSION = {
    "Transferencia bancaria": 500,  # EUR/USD
    "Cripto": 100                   # EUR/USD
}
```

### Google Sheets

```python
SHEET_INTERMEDIO_GSHEET_ID = "1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY"
SHEET_INTERMEDIO_WORKSHEET_NAME = "Master Inmuebles Pro"
```

## 📊 Flujo de Datos

```
Google Sheet (Master Inmuebles Pro)
         ↓
    Data Loader (gspread)
         ↓
    DataFrame (pandas)
         ↓
    Filtrado (criterios cliente)
         ↓
    Ranking (scoring)
         ↓
    Selección manual (cliente)
         ↓
    Cálculos financieros
         ↓
    PDF generado
```

## 🧮 Cálculos Financieros

### Rentabilidades SIN Reinversión

```python
Rent_Total = Rent_Recurrente + Rent_Plusvalía
```

### Rentabilidades CON Reinversión (Interés Compuesto)

**Fórmula de la cartera (Sheet 1, fila 75):**

```
Valor_Final = Capital_Inicial 
            + ∑ (Inversión × Rentabilidad_Mensual × ((1 + Tasa_Reinv)^Meses - 1) / Tasa_Reinv)
            + ∑ (Plusvalía × (1 + Tasa_Reinv)^Meses_Post_Cierre)
```

### 5 Horizontes de Cálculo

- **6 meses** - Corto plazo
- **12 meses** - 1 año
- **24 meses** - 2 años
- **36 meses** - 3 años
- **60 meses** - 5 años

## 🔄 Tipo de Cambio EUR/USD

Se obtiene automáticamente via API y se cachea por **24 horas** para evitar llamadas constantes.

```python
API: https://api.exchangerate-api.com/v4/latest/EUR
Cache: @st.cache_data(ttl=86400)
```

## ✉️ Email Notificaciones [PRÓXIMAMENTE]

Si capital disponible > 50k EUR/USD, se envía email a `EMAIL_DESTINO` con detalles de la inversión.

## 🐛 Troubleshooting

### Error: "Authentication failed"

- Verificar credenciales de Google Sheets API
- Compartir Google Sheet con service account email
- Verificar permisos en Google Cloud Console

### Error: "Sheet not found"

- Verificar `SHEET_INTERMEDIO_GSHEET_ID` en `constants.py`
- Verificar nombre de worksheet: `SHEET_INTERMEDIO_WORKSHEET_NAME`

### Datos no se actualizan

- El caché de datos es de 1 hora: `@st.cache_data(ttl=3600)`
- Forzar refresh: Ctrl+Shift+R en Streamlit o `st.cache_data.clear()`

## 🚀 Deployment en Streamlit Cloud

### 1. Push a GitHub

```bash
git add .
git commit -m "Versión inicial"
git push origin main
```

### 2. Conectar en Streamlit Cloud

1. Ir a https://streamlit.io/cloud
2. New app → Select repo → Select branch → Select `app.py`
3. Deploy

### 3. Configurar Secrets

En Streamlit Cloud (Settings → Secrets):

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
...
```

## 📈 Roadmap

- [x] UI básica con Streamlit
- [x] Data loader desde Google Sheets
- [x] Filtrado de proyectos
- [x] Ranking automático
- [ ] Generación de PDF profesional
- [ ] Cálculos financieros completos (Tab 3)
- [ ] Email notificaciones (capital > 50k)
- [ ] Integración P2P
- [ ] Dashboard de análisis
- [ ] Exportar a Excel
- [ ] Soporte multiidioma

## 📝 Notas de Desarrollo

### Columnas del Sheet Master Inmuebles Pro

Verificar que el Sheet Intermedio tenga estas columnas (aproximadas):

| Columna | Descripción |
|---------|-------------|
| A | ID (SVQ-1, GND-2, etc.) |
| B | Nombre |
| C | Estado |
| D | Fecha de lanzamiento |
| J | Nº de Tokens |
| K | Precio Token |
| M | Importe proyecto (€) |
| N | Importe proyecto ($) |
| O | Ubicación |
| Q | Tipología Dividendos |
| AI | Estimación Nº Meses desde Lanzamiento |
| AK | Nº Meses restantes de renta |
| AJ | Rentab. anualizada Reentel |
| AK | Rentab. anualizada RP |
| AL | Rentab. anualizada SR |

Ajustar mapping en `constants.py` si es necesario.

### Fórmulas Críticas

Todas las fórmulas de cálculo están en `modules/calculo_cartera.py`:

- `CalculadoraCartera.valor_final_portfolio_reinversion()` - Fórmula interés compuesto
- `rankear_proyectos()` - Scoring de similitud
- `calcular_score_*()` - Cálculos de score individual

## 🤝 Contribuir

1. Fork el repo
2. Crear rama feature (`git checkout -b feature/feature-name`)
3. Commit cambios (`git commit -m 'Add feature'`)
4. Push rama (`git push origin feature/feature-name`)
5. Abrir Pull Request

## 📄 Licencia

Reental © 2024

## 📞 Soporte

Contacta a: [tu_email@reental.com]

---

**Última actualización:** 26 Agosto 2024
