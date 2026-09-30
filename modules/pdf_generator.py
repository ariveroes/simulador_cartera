"""
PDF_GENERATOR.PY

Incluye precios_compra en:
- Tabla de cartera (muestra Precio Compra y tipo: Emisión vs OTC)
- Cálculos de importe con precio real
- Análisis en PDF con precio actual
"""

from io import BytesIO
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfgen import canvas


COLOR_NARANJA = colors.HexColor('#ff8c00')
COLOR_GRIS = colors.HexColor('#666666')
COLOR_BLANCO = colors.whitesmoke
COLOR_FONDO = colors.HexColor('#f9f9f9')


def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_proyectos, precios_compra=None):
    """
    Genera un PDF profesional con la cartera del cliente.
    
    Args:
        datos_cliente: dict con datos personales
        proyectos_cartera: list de proyectos seleccionados
        distribuciones: dict con porcentajes
        df_proyectos: DataFrame con datos
        precios_compra: dict con precios reales seleccionados {proyecto_id: {precio, divisa, tipo}}
    
    Returns:
        bytes del PDF
    """
    
    if precios_compra is None:
        precios_compra = {}
    
    pdf_buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.8*inch,
        bottomMargin=0.8*inch,
    )
    
    styles = getSampleStyleSheet()
    
    # Estilos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=COLOR_NARANJA,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=COLOR_GRIS,
        spaceAfter=24,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=COLOR_NARANJA,
        spaceAfter=10,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderColor=COLOR_NARANJA,
        borderWidth=2,
        borderPadding=5
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    content = []
    
    # ========== PÁGINA 1: PORTADA ==========
    content.append(Spacer(1, 0.8*inch))
    content.append(Paragraph("SIMULADOR DE CARTERA", title_style))
    content.append(Paragraph("INMOBILIARIA REENTAL", title_style))
    content.append(Spacer(1, 0.3*inch))
    content.append(Paragraph("Reporte Personalizado de Inversión", subtitle_style))
    
    content.append(Spacer(1, 0.5*inch))
    
    portada_info = [
        [f"<b>Inversor:</b> {datos_cliente.get('nombre', 'Cliente')}", 
         f"<b>Email:</b> {datos_cliente.get('email', 'N/A')}"],
        [f"<b>Estatus:</b> {datos_cliente.get('estatus', 'Reentel')}", 
         f"<b>Capital Estimado:</b> {datos_cliente.get('capital', 'N/A')}"],
        [f"<b>Objetivo:</b> {'Ingresos Pasivos' if 'ingresos' in datos_cliente.get('objetivo', '').lower() else 'Maximizar Rentabilidad'}", 
         f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y')}"],
    ]
    
    portada_table = Table(portada_info, colWidths=[3.2*inch, 3.2*inch])
    portada_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    content.append(portada_table)
    content.append(Spacer(1, 1*inch))
    content.append(Paragraph(
        "<i>Este documento es informativo y no constituye asesoramiento financiero. "
        "Consulte con un profesional antes de invertir. "
        "Los precios mostrados corresponden a precios de emisión y/u ofertas OTC reales al momento de generación.</i>",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=9, textColor=COLOR_GRIS, alignment=TA_CENTER)
    ))
    
    content.append(PageBreak())
    
    # ========== PÁGINA 2: RESUMEN Y CARTERA ==========
    content.append(Paragraph("1. RESUMEN EJECUTIVO", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    kpi_data = [
        ['KPI', 'Valor'],
        ['Número de Proyectos', str(len(proyectos_cartera))],
        ['Distribución', datos_cliente.get('distribucion', 'Partes iguales')],
        ['Mercados', ', '.join(datos_cliente.get('mercados', ['Global']))],
        ['Estatus Seleccionado', datos_cliente.get('estatus', 'Reentel')],
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2.5*inch, 3.9*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NARANJA),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLANCO),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
    ]))
    
    content.append(kpi_table)
    content.append(Spacer(1, 0.3*inch))
    
    # ========== TABLA CARTERA CON PRECIO_COMPRA ==========
    content.append(Paragraph("2. CARTERA DE INVERSIÓN (CON PRECIOS REALES)", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    cartera_data = [['Proyecto', 'Ubicación', 'Precio Compra', 'Rent. Anual', '% Invertido']]
    
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_proyectos[df_proyectos['ID'] == proyecto_id]
        
        if len(proyecto_row) > 0:
            row = proyecto_row.iloc[0]
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            rentabilidad = row.get('Rentabilidad_Anualizada_SuperReentel', 0)
            
            # NUEVO: Mostrar precio_compra real
            precio_info = precios_compra.get(proyecto_id, {})
            precio_compra = precio_info.get('precio', row.get('Precio Emisión', 0))
            tipo_precio = precio_info.get('tipo', 'Emisión')
            
            precio_str = f"€{precio_compra:.2f} ({tipo_precio})"
            
            cartera_data.append([
                proyecto['nombre'][:35],
                row.get('Ubicación', 'N/A'),
                precio_str,
                f"{rentabilidad:.2f}%",
                f"{porcentaje:.1f}%"
            ])
    
    cartera_table = Table(cartera_data, colWidths=[1.6*inch, 1.0*inch, 1.3*inch, 1.1*inch, 0.9*inch])
    cartera_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NARANJA),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLANCO),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
    ]))
    
    content.append(cartera_table)
    content.append(Spacer(1, 0.3*inch))
    
    # Nota sobre precios
    content.append(Paragraph(
        "<b>Nota de Precios:</b> Emisión = Precio oficial del token | OTC = Precio de compra en mercado secundario (oferta real)",
        ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, textColor=COLOR_GRIS)
    ))
    content.append(Spacer(1, 0.2*inch))
    
    # ========== ANÁLISIS POR UBICACIÓN ==========
    content.append(Paragraph("3. ANÁLISIS POR UBICACIÓN", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    ubicaciones = {}
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_proyectos[df_proyectos['ID'] == proyecto_id]
        if len(proyecto_row) > 0:
            ubicacion = proyecto_row.iloc[0].get('Ubicación', 'N/A')
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            
            if ubicacion not in ubicaciones:
                ubicaciones[ubicacion] = {'porcentaje': 0, 'count': 0}
            ubicaciones[ubicacion]['porcentaje'] += porcentaje
            ubicaciones[ubicacion]['count'] += 1
    
    ubicacion_data = [['Ubicación', 'Proyectos', '% Cartera']]
    for ub, info in sorted(ubicaciones.items()):
        ubicacion_data.append([ub, str(info['count']), f"{info['porcentaje']:.1f}%"])
    
    ubicacion_table = Table(ubicacion_data, colWidths=[2.5*inch, 1.5*inch, 2.4*inch])
    ubicacion_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NARANJA),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLANCO),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
    ]))
    
    content.append(ubicacion_table)
    
    content.append(PageBreak())
    
    # ========== PÁGINA 3: PROYECCIONES ==========
    content.append(Paragraph("4. PROYECCIONES DE PATRIMONIO", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    capital_map = {
        "Menos de 5.000": 2500,
        "Entre 5.000 y 10.000": 7500,
        "Entre 10.000 y 50.000": 30000,
        "Más de 50.000": 100000
    }
    
    capital_text = datos_cliente.get('capital', 'Entre 10.000 y 50.000')
    capital_estimado = capital_map.get(capital_text, 75000)
    
    from modules.calculo_cartera import CalculadoraCartera
    
    estatus = datos_cliente.get('estatus', 'Reentel')
    calculadora = CalculadoraCartera(estatus)
    
    rentabilidad_promedio = 0
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_proyectos[df_proyectos['ID'] == proyecto_id]
        if len(proyecto_row) > 0:
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0) / 100
            try:
                rentabilidad_pct = float(str(proyecto_row.iloc[0].get('Rentabilidad_Anualizada_SuperReentel', 0)).replace('%', ''))
                rentabilidad = rentabilidad_pct / 100
            except:
                rentabilidad = 0
            rentabilidad_promedio += rentabilidad * porcentaje
    
    proyecciones_data = [['Plazo', 'Capital Inicial', 'Capital Final', 'Ganancia', 'ROI']]
    
    for meses in [6, 12, 24, 36, 60]:
        capital_final = calculadora.calcular_proyeccion(capital_estimado, rentabilidad_promedio, meses)
        ganancia = capital_final - capital_estimado
        roi = (ganancia / capital_estimado * 100) if capital_estimado > 0 else 0
        
        proyecciones_data.append([
            f"{meses} meses",
            f"€{capital_estimado:,.0f}",
            f"€{capital_final:,.0f}",
            f"€{ganancia:,.0f}",
            f"{roi:.2f}%"
        ])
    
    proyecciones_table = Table(proyecciones_data, colWidths=[0.9*inch, 1.3*inch, 1.3*inch, 1.2*inch, 1.0*inch])
    proyecciones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NARANJA),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLANCO),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
    ]))
    
    content.append(proyecciones_table)
    content.append(Spacer(1, 0.3*inch))
    
    content.append(Paragraph(
        f"<b>Capital Estimado:</b> €{capital_estimado:,.0f} | "
        f"<b>Rentabilidad Promedio Anual:</b> {rentabilidad_promedio*100:.2f}%",
        ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=COLOR_GRIS)
    ))
    content.append(Spacer(1, 0.3*inch))
    
    # Resumen técnico
    content.append(Paragraph("5. RESUMEN TÉCNICO", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    tech_data = [
        ['Parámetro', 'Valor'],
        ['Número de Proyectos', str(len(proyectos_cartera))],
        ['Rentabilidad Media Ponderada', f"{rentabilidad_promedio*100:.2f}%"],
        ['Diversificación por Ubicación', f"{len(ubicaciones)} mercados"],
        ['Precios: Emisión vs OTC', "Ambos tipos incluidos"],
        ['Plazo de Análisis', '6 a 60 meses'],
    ]
    
    tech_table = Table(tech_data, colWidths=[2.5*inch, 3.9*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NARANJA),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_BLANCO),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
    ]))
    
    content.append(tech_table)
    
    content.append(PageBreak())
    
    # ========== PÁGINA 4: AVISO LEGAL ==========
    content.append(Paragraph("AVISO LEGAL Y TÉRMINOS", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    legal_text = f"""
    <b>Responsabilidad y Limitaciones:</b><br/>
    Este documento es información educativa y no constituye asesoramiento financiero, fiscal o legal. 
    Las proyecciones mostradas son estimaciones basadas en datos históricos y parámetros actuales, 
    y pueden no reflejar resultados futuros. La rentabilidad pasada no garantiza resultados futuros.<br/><br/>
    
    <b>Precios Utilizados:</b><br/>
    • Emisión: Precio oficial del token en su lanzamiento o programa de inversión.<br/>
    • OTC: Precio de compra en mercado secundario / ofertas reales disponibles.<br/>
    • Los precios pueden cambiar sin previo aviso.<br/><br/>
    
    <b>Riesgos de Inversión:</b><br/>
    • Las inversiones inmobiliarias conllevan riesgos de liquidez, mercado y crédito.<br/>
    • Los rendimientos pueden ser menores a los proyectados.<br/>
    • El mercado OTC es menos líquido que el mercado principal.<br/>
    • Consulte con un asesor financiero independiente antes de invertir.<br/><br/>
    
    <b>Datos y Privacidad:</b><br/>
    Este documento contiene información confidencial y personal. Úselo únicamente para fines de análisis personal.
    No comparta con terceros sin consentimiento.<br/><br/>
    
    <b>Fecha de Generación:</b> {datetime.now().strftime('%d de %B de %Y a las %H:%M')}<br/>
    <b>Herramienta:</b> Simulador de Cartera Inmobiliaria Reental (FASE 3 - Precios OTC)
    """
    
    content.append(Paragraph(legal_text, ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_GRIS,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )))
    
    content.append(Spacer(1, 0.3*inch))
    
    footer = Paragraph(
        "<b>© 2024 Reental Wealth Services. Todos los derechos reservados.</b><br/>"
        "Para más información: <a href='https://reental.com'>www.reental.com</a>",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=COLOR_NARANJA,
            alignment=TA_CENTER,
            spaceAfter=10
        )
    )
    content.append(footer)
    
    # Construir PDF
    doc.build(content)
    
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
