# STATUS DEL PROYECTO - Constructor de Cartera Inmobiliaria

**Fecha:** 26 Agosto 2024
**Estado General:** ✅ SCAFFOLD COMPLETO | ⏳ DESARROLLO EN PROGRESO

---

## ✅ COMPLETADO

### Estructura y Setup
- [x] Proyecto scaffolding (carpetas, archivos base)
- [x] `requirements.txt` con todas las dependencias
- [x] `.gitignore` configurado
- [x] `.streamlit/config.toml` con temas
- [x] `README.md` con instrucciones completas

### Configuración (config/constants.py)
- [x] Tasas de reinversión por estatus (11%, 13%, 16%)
- [x] Mínimos de inversión (500€ transferencia, 100€ cripto)
- [x] Horizontes de cálculo (6, 12, 24, 36, 60 meses)
- [x] Estados de proyecto, ubicaciones, tipología dividendos
- [x] Email config para notificaciones (pendiente implementar)
- [x] Google Sheets config (Sheet Intermedio URL y IDs)

### Data Loader (modules/data_loader.py)
- [x] Acceso a Google Sheets via gspread
- [x] Caché de 1 hora para proyectos
- [x] Caché de 24 horas para tipo de cambio EUR/USD (API automática)
- [x] Conversión moneda EUR ↔ USD
- [x] Limpieza de datos
- [x] Filtrado por estado (excluir cerrados)
- [x] Separación primaria vs P2P

### Cálculos Financieros (modules/calculo_cartera.py)
- [x] Clase `CalculadoraCartera` con reinversión
- [x] Fórmula crítica: interés compuesto (Sheet 1, fila 75-91)
- [x] Cálculo para 5 horizontes (6, 12, 24, 36, 60m)
- [x] Rentabilidades SIN reinversión (recurrente + plusvalía)
- [x] Rentabilidades CON reinversión (interés compuesto)
- [x] Ranking automático (similitud + rentabilidad + duración)
- [x] Scoring de proyectos (33% cada criterio)

### UI Principal (app.py)
- [x] Setup Streamlit page config
- [x] Session state management
- [x] **Sidebar - Configuración inicial:**
  - [x] Datos inversor (nombre, email)
  - [x] Divisa (EUR/USD)
  - [x] Capital disponible
  - [x] Tipo inversión (Transferencia/Cripto)
  - [x] Estatus (Reentel/RP/SR)
  - [x] Coste estatus (input manual)
  - [x] Tipo de cambio (display)

- [x] **Tab 1 - Preferencias:**
  - [x] Duración (Corto/Largo plazo)
  - [x] Rendimientos (Periódicos/Finales/Ambos)
  - [x] Ubicaciones (multiselect)
  - [x] Botón "Buscar Proyectos"

- [x] **Tab 2 - Ranking:**
  - [x] Tabla de proyectos rankeados
  - [x] Multiselect de proyectos
  - [x] Preview de selección
  - [x] Cálculo de inversión total aproximada
  - [x] Conversión a USD si se selecciona

- [x] **Tab 3 - PDF:**
  - [x] Placeholder para próximamente
  - [x] TODO marker para próxima fase

---

## ⏳ PENDIENTE (PRÓXIMAS FASES)

### Fase 2: Cálculos y PDF (SIGUIENTE)
- [ ] Implementar Tab 3 completamente
- [ ] Crear función `distribuir_capital()` con 3 opciones:
  - [ ] Igual (mismo monto por proyecto)
  - [ ] Proporcional (según tamaño del proyecto)
  - [ ] Manual (cliente elige % por proyecto)
- [ ] Integrar `CalculadoraCartera` en UI
- [ ] Display de resultados financieros
- [ ] Gráficos de proyección de rentabilidad
- [ ] Exportar a PDF (librería: reportlab o weasyprint)
  - [ ] Sección 1: Datos del inversor
  - [ ] Sección 2: Resumen de cartera
  - [ ] Sección 3: Rentabilidades sin/con reinversión
  - [ ] Sección 4: Análisis de cartera
  - [ ] Sección 5: Detalles de proyectos

### Fase 3: Validaciones y Polish
- [ ] Validar capital mínimo por proyecto
- [ ] Validar no exceder capital disponible
- [ ] Validar estatus vs tipo inversión
- [ ] Error handling mejorado
- [ ] Mensajes de éxito/error personalizados
- [ ] Loading spinners

### Fase 4: Email Notificaciones
- [ ] Implementar envío de email si capital > 50k
- [ ] Template de email profesional
- [ ] Datos a incluir en email
- [ ] Setup de SMTP (SendGrid, AWS SES, etc.)

### Fase 5: Integración P2P
- [ ] Decidir entre:
  - [ ] Opción A: Link externo
  - [ ] Opción B: Integración directa
  - [ ] Opción C: Columna en Sheet
- [ ] Implementar seleccionada

### Fase 6: Deployment
- [ ] Crear repo en GitHub
- [ ] Setup GitHub Actions (CI/CD)
- [ ] Deploy en Streamlit Cloud
- [ ] Testing en producción
- [ ] Documentación para clientes

### Futuro (Roadmap)
- [ ] Dashboard de análisis de cartera
- [ ] Exportar a Excel
- [ ] Simulación de escenarios
- [ ] Integración con billetera Reental
- [ ] Soporte multiidioma
- [ ] App móvil

---

## 🔧 CONFIGURACIÓN PENDIENTE (Usuario)

**Para que todo funcione, necesitas:**

### 1. Google Sheets API Credentials
- Crear service account en Google Cloud
- Descargar JSON y guardar como `service_account.json`
- Compartir Google Sheet con service account email

### 2. Verificar columnas del Sheet Intermedio
- Confirmar nombres exactos de columnas
- Ajustar mapping en `config/constants.py` si es necesario
- Especialmente rentabilidades anualizado (AJ, AK, AL)

### 3. Completar constantes
Si falta algo, está marcado en `config/constants.py`:
```python
EMAIL_DESTINO = "tu_email@reental.com"  # CAMBIAR
```

---

## 🧪 CÓMO TESTEAR LOCALMENTE

### 1. Setup
```bash
cd /home/claude
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Poner credenciales
- Descargar `service_account.json` de Google Cloud
- Guardar en carpeta raíz del proyecto

### 3. Correr app
```bash
streamlit run app.py
```

### 4. En navegador
- Ir a http://localhost:8501
- Rellenar configuración inicial
- Buscar proyectos
- Seleccionar proyectos

**Nota:** Tab 3 (PDF) está vacío - eso es siguiente fase

---

## 📊 ARQUITECTURA ACTUAL

```
app.py (Streamlit UI)
    ├─ modules/data_loader.py
    │   ├─ cargar_proyectos()      ← Google Sheets
    │   ├─ obtener_tipo_cambio()   ← API
    │   └─ convertir_moneda()
    │
    └─ modules/calculo_cartera.py
        ├─ CalculadoraCartera      ← Interés compuesto
        └─ rankear_proyectos()     ← Scoring

config/constants.py (Configuración)
    ├─ REINVERSION_RATES
    ├─ MINIMO_INVERSION
    ├─ SHEET_INTERMEDIO_GSHEET_ID
    └─ EMAIL_DESTINO
```

---

## 📝 NOTAS IMPORTANTES

1. **Sheet Intermedio:** Debe ser réplica de Master Inmuebles Pro con IMPORTRANGE
   - URL actual: https://docs.google.com/spreadsheets/d/1sL6fynVPKtfaNs22t019ItKbzMFaOHbO5kqVzMxXHIY/

2. **Columnas críticas:** Verificar que existan exactamente con esos nombres:
   - Estimación Rentab. Total (Alq. + Plusv.) anualizado Reentel/RP/SR
   - Estimación Nº Meses desde Lanzamiento
   - Nº Meses restantes de renta hasta Estimacion fin

3. **Tipo de cambio:** Se cachea 24h automáticamente via:
   - API: exchangerate-api.com
   - Cache: @st.cache_data(ttl=86400)

4. **Fórmula interés compuesto:** Replicada exactamente de Sheet 1
   - Parámetros: Capital, Rentabilidad mensual, Tasa reinversión mensual, Meses
   - Output: Valor final con interés compuesto

---

## 🚀 PRÓXIMOS PASOS RECOMENDADOS

1. **AHORA:** Testear que data_loader funciona
   - Verificar Google Sheets API credentials
   - Verificar que se cargan los proyectos
   - Verificar columnas del Sheet

2. **LUEGO:** Implementar Tab 3 (Cálculos + PDF)
   - Integrar CalculadoraCartera en UI
   - Display de resultados
   - PDF generator

3. **DESPUÉS:** Email notificaciones + Streamlit Cloud deploy

---

**Última actualización:** 26 Agosto 2024 - Compilado por Claude
