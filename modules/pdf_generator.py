"""
PDF GENERATOR - Genera PDF idéntico al botón "Reental Wealth" del Sheet 1
Usa reportlab para máximo control sobre el diseño
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, grey, lightgrey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import os


class PDFCartera:
    """
    Generador de PDF para cartera inmobiliaria.
    Replica el diseño del Sheet 1 "Reental Wealth".
    """
    
    def __init__(self, nombre_archivo="cartera_inmobiliaria.pdf"):
        """
        Args:
            nombre_archivo: str - Nombre del archivo PDF a generar
        """
        self.nombre_archivo = nombre_archivo
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title="Cartera Inmobiliaria Reental"
        )
        self.styles = getSampleStyleSheet()
        self._estilos_personalizados()
        self.story = []
    
    def _estilos_personalizados(self):
        """Define estilos personalizados para el PDF"""
        # Títulos
        self.styles.add(ParagraphStyle(
            name='TituloSeccion',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#1f77b4'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=black,
            spaceAfter=6
        ))
        
        # Normal
        self.styles.add(ParagraphStyle(
            name='Normal',
            fontSize=9,
            textColor=black,
            spaceAfter=6
        ))
        
        # Métrica
        self.styles.add(ParagraphStyle(
            name='Metrica',
            fontSize=11,
            textColor=HexColor('#1f77b4'),
            fontName='Helvetica-Bold',
            spaceAfter=4
        ))
    
    def agregar_header(self, nombre_inversor, email, estatus, tipo_cambio):
        """
        Sección 1: Datos del inversor
        """
        # Título
        self.story.append(Paragraph("PROPUESTA DE INVERSIÓN INMOBILIARIA", self.styles['TituloSeccion']))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Datos
        datos = [
            ['DATOS INVERSOR', ''],
            ['Titular:', nombre_inversor],
            ['Email:', email],
            ['Estatus:', estatus],
            ['Fecha:', datetime.now().strftime('%d/%m/%Y')],
            ['', ''],
            ['TIPO DE CAMBIO', ''],
            ['EUR / USD:', f'{tipo_cambio:.4f}'],
        ]
        
        tabla = Table(datos, colWidths=[2.5*cm, 10*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 11),
            ('TEXTCOLOR', (0, 0), (1, 0), HexColor('#1f77b4')),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (0, -1), 9),
            ('BOTTOMPADDING', (0, 0), (1, -1), 8),
            ('TOPPADDING', (0, 0), (1, -1), 8),
            ('GRID', (0, 0), (1, 5), 1, lightgrey),
            ('GRID', (0, 6), (1, -1), 1, lightgrey),
        ]))
        
        self.story.append(tabla)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_resumen_cartera(self, num_inmuebles, media_meses, inversion_total_eur,
                                inversion_total_usd, coste_estatus, tipo_cambio,
                                rent_recurrente, rent_plusvalia, rent_total_anualizada):
        """
        Sección 2: Resumen de la cartera
        """
        self.story.append(Paragraph("RESUMEN DE LA CARTERA", self.styles['TituloSeccion']))
        
        datos = [
            ['Descripción', 'EUR', 'USD'],
            ['Número de inmuebles propuestos', str(num_inmuebles), str(num_inmuebles)],
            ['Media de meses restantes', f'{media_meses:.0f}', f'{media_meses:.0f}'],
            ['Valor inversión estimada total', f'€ {inversion_total_eur:,.0f}', f'$ {inversion_total_usd:,.0f}'],
            ['Coste de adquisición estatus', f'€ {coste_estatus:,.0f}', f'$ {coste_estatus*tipo_cambio:,.0f}'],
            ['Valor total de inversión', f'€ {inversion_total_eur + coste_estatus:,.0f}', 
             f'$ {inversion_total_usd + coste_estatus*tipo_cambio:,.0f}'],
            ['', '', ''],
            ['Rentabilidad anual recurrente', f'{rent_recurrente*100:.2f}%', f'{rent_recurrente*100:.2f}%'],
            ['Rentabilidad final', f'{rent_plusvalia*100:.2f}%', f'{rent_plusvalia*100:.2f}%'],
            ['Rentabilidad total anualizada', f'{rent_total_anualizada*100:.2f}%', f'{rent_total_anualizada*100:.2f}%'],
        ]
        
        tabla = Table(datos, colWidths=[5.5*cm, 3.5*cm, 3.5*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (2, 0), 10),
            ('BACKGROUND', (0, 0), (2, 0), HexColor('#f0f2f6')),
            ('TEXTCOLOR', (0, 0), (2, 0), black),
            ('ALIGN', (0, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (2, -1), 9),
            ('BOTTOMPADDING', (0, 0), (2, -1), 6),
            ('TOPPADDING', (0, 0), (2, -1), 6),
            ('GRID', (0, 0), (2, -1), 0.5, lightgrey),
            ('ROWBACKGROUND', (0, 6), (2, 6), white),  # Línea en blanco
        ]))
        
        self.story.append(tabla)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_reinversion(self, resultados_por_horizonte):
        """
        Sección 3: Cartera con reinversión (interés compuesto)
        
        Args:
            resultados_por_horizonte: dict {6: {...}, 12: {...}, ...}
        """
        self.story.append(Paragraph("CARTERA CON REINVERSIÓN: EL PODER DEL INTERÉS COMPUESTO", 
                                   self.styles['TituloSeccion']))
        
        # Tabla de ganancias
        datos_ganancia = [
            ['Horizonte (meses)', '6 meses', '12 meses', '24 meses', '36 meses', '60 meses']
        ]
        
        fila_ganancia = ['Ganancia total']
        for horizonte in [6, 12, 24, 36, 60]:
            if horizonte in resultados_por_horizonte:
                ganancia = resultados_por_horizonte[horizonte]['ganancia']
                fila_ganancia.append(f'€ {ganancia:,.0f}')
            else:
                fila_ganancia.append('N/A')
        
        datos_ganancia.append(fila_ganancia)
        
        tabla_ganancia = Table(datos_ganancia, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        tabla_ganancia.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (5, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (5, 0), 9),
            ('BACKGROUND', (0, 0), (5, 0), HexColor('#f0f2f6')),
            ('ALIGN', (0, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (5, -1), 9),
            ('BOTTOMPADDING', (0, 0), (5, -1), 6),
            ('TOPPADDING', (0, 0), (5, -1), 6),
            ('GRID', (0, 0), (5, -1), 0.5, lightgrey),
        ]))
        
        self.story.append(tabla_ganancia)
        self.story.append(Spacer(1, 0.15*inch))
        
        # Tabla de rentabilidad acumulada
        datos_rent = [
            ['Rentabilidad acumulada', '6 meses', '12 meses', '24 meses', '36 meses', '60 meses']
        ]
        
        fila_rent = ['']
        for horizonte in [6, 12, 24, 36, 60]:
            if horizonte in resultados_por_horizonte:
                rent = resultados_por_horizonte[horizonte]['rentabilidad_acumulada']
                fila_rent.append(f'{rent*100:.2f}%')
            else:
                fila_rent.append('N/A')
        
        datos_rent.append(fila_rent)
        
        tabla_rent = Table(datos_rent, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        tabla_rent.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (5, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (5, 0), 9),
            ('BACKGROUND', (0, 0), (5, 0), HexColor('#f0f2f6')),
            ('ALIGN', (0, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (5, -1), 9),
            ('BOTTOMPADDING', (0, 0), (5, -1), 6),
            ('TOPPADDING', (0, 0), (5, -1), 6),
            ('GRID', (0, 0), (5, -1), 0.5, lightgrey),
        ]))
        
        self.story.append(tabla_rent)
        self.story.append(Spacer(1, 0.15*inch))
        
        # Tabla de rentabilidad anualizada
        datos_anual = [
            ['Rentabilidad anualizada', '6 meses', '12 meses', '24 meses', '36 meses', '60 meses']
        ]
        
        fila_anual = ['']
        for horizonte in [6, 12, 24, 36, 60]:
            if horizonte in resultados_por_horizonte:
                rent_anual = resultados_por_horizonte[horizonte]['rentabilidad_anualizada']
                fila_anual.append(f'{rent_anual*100:.2f}%')
            else:
                fila_anual.append('N/A')
        
        datos_anual.append(fila_anual)
        
        tabla_anual = Table(datos_anual, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        tabla_anual.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (5, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (5, 0), 9),
            ('BACKGROUND', (0, 0), (5, 0), HexColor('#f0f2f6')),
            ('ALIGN', (0, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (5, -1), 9),
            ('BOTTOMPADDING', (0, 0), (5, -1), 6),
            ('TOPPADDING', (0, 0), (5, -1), 6),
            ('GRID', (0, 0), (5, -1), 0.5, lightgrey),
        ]))
        
        self.story.append(tabla_anual)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_detalles_proyectos(self, cartera_lista):
        """
        Sección 4: Detalles de los proyectos
        """
        self.story.append(Paragraph("ANÁLISIS CARTERA PROPUESTA", self.styles['TituloSeccion']))
        self.story.append(Paragraph("Resumen información de los activos invertidos", 
                                   self.styles['Subtitulo']))
        
        # Tabla de proyectos
        datos = [
            ['ID', 'Nombre', 'Nº Tokens', '% Cartera', 'Ubicación', 'Estado', 'Inversión (€)']
        ]
        
        for proyecto in cartera_lista:
            datos.append([
                proyecto.get('id', ''),
                proyecto.get('nombre', ''),
                str(proyecto.get('tokens', '')),
                f"{proyecto.get('porcentaje', 0):.1f}%",
                proyecto.get('ubicacion', ''),
                proyecto.get('estado', ''),
                f"€ {proyecto.get('inversion_eur', 0):,.0f}"
            ])
        
        tabla = Table(datos, colWidths=[1.2*cm, 3.5*cm, 1.3*cm, 1.3*cm, 2*cm, 1.8*cm, 2.2*cm])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (6, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (6, 0), 8),
            ('BACKGROUND', (0, 0), (6, 0), HexColor('#f0f2f6')),
            ('TEXTCOLOR', (0, 0), (6, 0), black),
            ('ALIGN', (0, 0), (6, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (6, -1), 8),
            ('BOTTOMPADDING', (0, 0), (6, -1), 5),
            ('TOPPADDING', (0, 0), (6, -1), 5),
            ('GRID', (0, 0), (6, -1), 0.5, lightgrey),
            ('ROWBACKGROUND', (0, 1), (6, -1), HexColor('#fafafa')),
        ]))
        
        self.story.append(tabla)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_footer(self):
        """
        Footer del documento
        """
        self.story.append(Spacer(1, 0.2*inch))
        pie = Paragraph(
            '<font size=8 color="#666666">'
            'Este documento es una propuesta de inversión basada en datos estimados. '
            'Las rentabilidades reales pueden variar. Consulta con tu asesor Reental antes de invertir.'
            '</font>',
            self.styles['Normal']
        )
        self.story.append(pie)
    
    def generar(self, nombre_inversor, email, estatus, tipo_cambio,
                num_inmuebles, media_meses, inversion_total_eur, inversion_total_usd,
                coste_estatus, rent_recurrente, rent_plusvalia, rent_total_anualizada,
                resultados_por_horizonte, cartera_lista):
        """
        Genera el PDF completo
        """
        self.agregar_header(nombre_inversor, email, estatus, tipo_cambio)
        self.agregar_resumen_cartera(
            num_inmuebles, media_meses, inversion_total_eur, inversion_total_usd,
            coste_estatus, tipo_cambio, rent_recurrente, rent_plusvalia, rent_total_anualizada
        )
        self.agregar_reinversion(resultados_por_horizonte)
        self.agregar_detalles_proyectos(cartera_lista)
        self.agregar_footer()
        
        # Build PDF
        self.doc.build(self.story)
        
        # Obtener bytes
        self.buffer.seek(0)
        return self.buffer.getvalue()
    
    def guardar(self, ruta):
        """Guarda el PDF en disco"""
        with open(ruta, 'wb') as f:
            f.write(self.buffer.getvalue())
