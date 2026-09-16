"""
PDF GENERATOR - Genera PDF con resumen de cartera
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime


def generar_pdf_cartera(datos_cliente, proyectos_cartera, distribuciones, df_todos):
    """
    Genera PDF con resumen de cartera.
    """
    
    # Crear buffer para PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    style_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#ff8c00'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ff8c00'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # TITULO
    elements.append(Paragraph("SIMULADOR DE CARTERA INMOBILIARIA", style_titulo))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # RESUMEN CLIENTE
    elements.append(Paragraph("DATOS DEL CLIENTE", style_heading))
    datos_tabla = [
        ['Nombre', datos_cliente.get('nombre', 'N/A')],
        ['Email', datos_cliente.get('email', 'N/A')],
        ['Capital a invertir', f"{datos_cliente.get('capital', 'N/A')}"],
        ['Estatus', datos_cliente.get('estatus', 'N/A')],
        ['Objetivo', datos_cliente.get('objetivo', 'N/A')],
        ['Distribución', datos_cliente.get('distribucion', 'N/A')],
    ]
    
    tabla_datos = Table(datos_tabla, colWidths=[2*inch, 4*inch])
    tabla_datos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3e0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(tabla_datos)
    elements.append(Spacer(1, 0.3*inch))
    
    # TABLA CARTERA
    elements.append(Paragraph("TU CARTERA DE INVERSIÓN", style_heading))
    
    cartera_data = [['Proyecto', 'Ubicación', 'Rentabilidad Total', 'Rentabilidad Anualizada', '% Invertido']]
    
    for proyecto in proyectos_cartera:
        proyecto_id = proyecto['id']
        proyecto_row = df_todos[df_todos['ID'] == proyecto_id]
        
        if len(proyecto_row) > 0:
            row = proyecto_row.iloc[0]
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0)
            
            cartera_data.append([
                proyecto['nombre'],
                row.get('Ubicación', 'N/A'),
                f"{row.get('Rentabilidad_Total_SuperReentel', 0):.2f}%",
                f"{row.get('Rentabilidad_Anualizada_SuperReentel', 0):.2f}%",
                f"{porcentaje:.1f}%"
            ])
    
    tabla_cartera = Table(cartera_data, colWidths=[2*inch, 1.2*inch, 1.3*inch, 1.3*inch, 1.2*inch])
    tabla_cartera.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    elements.append(tabla_cartera)
    elements.append(Spacer(1, 0.3*inch))
    
    # PROYECCIONES
    elements.append(Paragraph("PROYECCIONES DE RENTABILIDAD", style_heading))
    
    # Mapeo de capital a valores numéricos
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
        proyecto_row = df_todos[df_todos['ID'] == proyecto_id]
        if len(proyecto_row) > 0:
            porcentaje = distribuciones.get(proyecto_id, {}).get('porcentaje', 0) / 100
            try:
                rentabilidad = float(str(proyecto_row.iloc[0].get('Rentabilidad_Anualizada_SuperReentel', 0)).replace('%', '')) / 100
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
    
    tabla_proyecciones = Table(proyecciones_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    tabla_proyecciones.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff8c00')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
    ]))
    elements.append(tabla_proyecciones)
    
    doc.build(elements)
    buffer.seek(0)
    
    return buffer
