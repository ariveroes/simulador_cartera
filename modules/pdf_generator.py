"""
PDF_GENERATOR.PY - Versión simple

Genera PDF básico sin dependencias pesadas (Plotly).
Compatible con Streamlit Cloud.
"""

from io import BytesIO
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors


def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_proyectos):
    """
    Genera un PDF con la cartera del cliente.
    
    Args:
        datos_cliente: dict con datos personales
        proyectos_cartera: list de proyectos seleccionados
        distribuciones: dict con porcentajes por proyecto
        df_proyectos: DataFrame con datos de proyectos
    
    Returns:
        BytesIO con el PDF
    """
    
    # Crear buffer
    pdf_buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#ff8c00'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ff8c00'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    
    # Contenido del PDF
    content = []
    
    # ========== PORTADA ==========
    content.append(Spacer(1, 0.5*inch))
    content.append(Paragraph("SIMULADOR DE CARTERA INMOBILIARIA", title_style))
    content.append(Spacer(1, 0.3*inch))
    content.append(Paragraph(f"Reporte de {datos_cliente.get('nombre', 'Cliente')}", heading_style))
    content.append(Spacer(1, 0.2*inch))
    content.append(Paragraph(f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    content.append(Spacer(1, 0.5*inch))
    
    # ========== DATOS CLIENTE ==========
    content.append(Paragraph("Datos de Inversión", heading_style))
    
    datos_table = [
        ['Campo', 'Valor'],
        ['Nombre', datos_cliente.get('nombre', 'N/A')],
        ['Email', datos_cliente.get('email', 'N/A')],
        ['Capital', datos_cliente.get('capital', 'N/A')],
        ['Estatus', datos_cliente.get('estatus', 'N/A')],
        ['Objetivo', datos_cliente.get('objetivo', 'N/A')[:50]],
        ['Distribución', datos_cliente.get('distribucion', 'N/A')],
    ]
    
    datos_table_obj = Table(datos_table, colWidths=[2*inch, 4*inch])
    datos_table_obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    content.append(datos_table_obj)
    content.append(Spacer(1, 0.3*inch))
    
    # ========== CARTERA ==========
    content.append(PageBreak())
    content.append(Paragraph("Tu Cartera de Inversión", heading_style))
    
    cartera_data = [['Proyecto', 'Ubicación', 'Rentabilidad Anualizada', '% Invertido']]
    
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_proyectos[df_proyectos['ID'] == proyecto_id]
        
        if len(proyecto_row) > 0:
            row = proyecto_row.iloc[0]
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            rentabilidad = row.get('Rentabilidad_Anualizada_SuperReentel', 0)
            
            cartera_data.append([
                proyecto['nombre'][:40],
                row.get('Ubicación', 'N/A'),
                f"{rentabilidad:.2f}%",
                f"{porcentaje:.1f}%"
            ])
    
    cartera_table = Table(cartera_data, colWidths=[2.5*inch, 1.2*inch, 1.3*inch, 1*inch])
    cartera_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    content.append(cartera_table)
    content.append(Spacer(1, 0.3*inch))
    
    # ========== PROYECCIONES ==========
    content.append(Paragraph("Proyecciones de Rentabilidad", heading_style))
    
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
    
    proyecciones_data = [['Plazo', 'Capital Inicial', 'Capital Final', 'Ganancia']]
    
    for meses in [6, 12, 24, 36, 60]:
        capital_final = calculadora.calcular_proyeccion(capital_estimado, rentabilidad_promedio, meses)
        ganancia = capital_final - capital_estimado
        
        proyecciones_data.append([
            f"{meses} meses",
            f"€{capital_estimado:,.0f}",
            f"€{capital_final:,.0f}",
            f"€{ganancia:,.0f}"
        ])
    
    proyecciones_table = Table(proyecciones_data, colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    proyecciones_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    content.append(proyecciones_table)
    content.append(Spacer(1, 0.5*inch))
    
    # ========== FOOTER ==========
    content.append(Spacer(1, 0.5*inch))
    footer_text = Paragraph(
        "<b>Aviso Legal:</b> Este documento es informativo y no constituye una recomendación de inversión. "
        "Consulte con un asesor financiero antes de realizar cualquier inversión.",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_LEFT
        )
    )
    content.append(footer_text)
    
    # Construir PDF
    doc.build(content)
    
    # Retornar buffer
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
