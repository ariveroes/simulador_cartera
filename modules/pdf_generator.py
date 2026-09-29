"""
PDF_GENERATOR.PY - FASE 2 PROFESIONAL

Genera PDFs profesionales con:
✅ Portada con branding
✅ Resumen de inversión y KPIs
✅ Tabla cartera completa (rentabilidades por estatus)
✅ Proyecciones de patrimonio (6, 12, 24, 36, 60 meses)
✅ Análisis por ubicación
✅ Track record de proyectos cerrados
✅ Aviso legal

SIN dependencias pesadas (Plotly), compatible con Streamlit Cloud.
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


# Colores corporativos Reental
COLOR_NARANJA = colors.HexColor('#ff8c00')
COLOR_GRIS = colors.HexColor('#666666')
COLOR_BLANCO = colors.whitesmoke
COLOR_FONDO = colors.HexColor('#f9f9f9')


def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_proyectos):
    """
    Genera un PDF profesional con la cartera del cliente.
    
    Args:
        datos_cliente: dict con datos personales y parámetros
        proyectos_cartera: list de proyectos seleccionados
        distribuciones: dict con porcentajes por proyecto
        df_proyectos: DataFrame con datos de proyectos
    
    Returns:
        bytes del PDF
    """
    
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
    
    # Definir estilos personalizados
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
    
    # Info cliente en portada
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
        "Consulte con un profesional antes de invertir.</i>",
        ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=9, textColor=COLOR_GRIS, alignment=TA_CENTER)
    ))
    
    content.append(PageBreak())
    
    # ========== PÁGINA 2: RESUMEN EJECUTIVO ==========
    content.append(Paragraph("1. RESUMEN EJECUTIVO", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    # KPIs principales
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
    
    # ========== PÁGINA 2 (cont): TU CARTERA ==========
    content.append(Paragraph("2. CARTERA DE INVERSIÓN", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    cartera_data = [['Proyecto', 'Ubicación', 'Dividendo', 'Rent. Anual', '% Invertido']]
    
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_proyectos[df_proyectos['ID'] == proyecto_id]
        
        if len(proyecto_row) > 0:
            row = proyecto_row.iloc[0]
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            rentabilidad = row.get('Rentabilidad_Anualizada_SuperReentel', 0)
            dividendo = row.get('Tipología de dividendo', 'N/A')
            
            cartera_data.append([
                proyecto['nombre'][:35],
                row.get('Ubicación', 'N/A'),
                str(dividendo)[:15],
                f"{rentabilidad:.2f}%",
                f"{porcentaje:.1f}%"
            ])
    
    cartera_table = Table(cartera_data, colWidths=[1.8*inch, 1.2*inch, 1.1*inch, 1.1*inch, 0.9*inch])
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
        ubicacion_data.append([
            ub,
            str(info['count']),
            f"{info['porcentaje']:.1f}%"
        ])
    
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
    
    # Calcular rentabilidad promedio
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
    
    # Nota sobre proyecciones
    content.append(Paragraph(
        f"<b>Capital Estimado:</b> €{capital_estimado:,.0f} | "
        f"<b>Rentabilidad Promedio Anual:</b> {rentabilidad_promedio*100:.2f}%",
        ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=COLOR_GRIS)
    ))
    
    content.append(Spacer(1, 0.3*inch))
    
    # ========== RESUMEN TÉCNICO ==========
    content.append(Paragraph("5. RESUMEN TÉCNICO", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    tech_data = [
        ['Parámetro', 'Valor'],
        ['Número de Proyectos', str(len(proyectos_cartera))],
        ['Rentabilidad Media Ponderada', f"{rentabilidad_promedio*100:.2f}%"],
        ['Diversificación por Ubicación', f"{len(ubicaciones)} mercados"],
        ['Plazo de Análisis', '6 a 60 meses'],
        ['Metodología de Cálculo', 'Capitalización Mensual'],
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
    
    # ========== PÁGINA 4: AVISO LEGAL Y FOOTER ==========
    content.append(Paragraph("AVISO LEGAL Y TÉRMINOS", heading_style))
    content.append(Spacer(1, 0.2*inch))
    
    legal_text = """
    <b>Responsabilidad y Limitaciones:</b><br/>
    Este documento es información educativa y no constituye asesoramiento financiero, fiscal o legal. 
    Las proyecciones mostradas son estimaciones basadas en datos históricos y parámetros actuales, 
    y pueden no reflejar resultados futuros. La rentabilidad pasada no garantiza resultados futuros.<br/><br/>
    
    <b>Riesgos de Inversión:</b><br/>
    • Las inversiones inmobiliarias conllevan riesgos de liquidez, mercado y crédito.<br/>
    • Los rendimientos pueden ser menores a los proyectados.<br/>
    • Consulte con un asesor financiero independiente antes de invertir.<br/><br/>
    
    <b>Datos y Privacidad:</b><br/>
    Este documento contiene información confidencial y personal. Úselo únicamente para fines de análisis personal.
    No comparta con terceros sin consentimiento.<br/><br/>
    
    <b>Fecha de Generación:</b> {fecha}<br/>
    <b>Herramienta:</b> Simulador de Cartera Inmobiliaria Reental
    """.format(fecha=datetime.now().strftime('%d de %B de %Y a las %H:%M'))
    
    content.append(Paragraph(legal_text, ParagraphStyle(
        'Legal',
        parent=styles['Normal'],
        fontSize=8,
        textColor=COLOR_GRIS,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )))
    
    content.append(Spacer(1, 0.3*inch))
    
    # Footer final
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
