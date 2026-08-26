"""
PDF GENERATOR PROFESIONAL - Diseño como el ejemplo de Federico
Con gráficos, colores, análisis detallado
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white, grey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import numpy as np

# Colores
COLOR_DARK = HexColor('#1a1f3a')
COLOR_ORANGE = HexColor('#f7931e')
COLOR_BLUE = HexColor('#2c5aa0')
COLOR_LIGHT_BLUE = HexColor('#4a90e2')
COLOR_TEXT_LIGHT = HexColor('#e0e0e0')


class PDFCarteraProf:
    """PDF profesional con diseño oscuro y gráficos"""
    
    def __init__(self):
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        self.styles = getSampleStyleSheet()
        self._estilos_personalizados()
        self.story = []
        self.width, self.height = A4
    
    def _estilos_personalizados(self):
        """Estilos profesionales"""
        self.styles.add(ParagraphStyle(
            name='TituloPortada',
            fontSize=48,
            textColor=white,
            fontName='Helvetica-Bold',
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            fontSize=16,
            textColor=COLOR_ORANGE,
            fontName='Helvetica-Bold',
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading3Custom',
            fontSize=12,
            textColor=COLOR_ORANGE,
            fontName='Helvetica-Bold',
            spaceAfter=8
        ))
        
       self.styles.add(ParagraphStyle(
    name='NormalCustom',
            fontSize=9,
            textColor=COLOR_TEXT_LIGHT
        ))
    
    def agregar_portada(self, nombre_inversor, estatus):
        """Portada profesional"""
        # Fondo oscuro simulado con tabla
        portada_data = [
            [''],
            [''],
            ['SIMULACIÓN DE\nCARTERA\nINMOBILIARIA'],
            [''],
            [''],
            [f'Estatus: {estatus}'],
            [''],
            ['Reental Wealth'],
            [datetime.now().strftime('%d de %B de %Y')]
        ]
        
        portada = Table(portada_data, colWidths=[self.width - 1*inch])
        portada.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_DARK),
            ('TEXTCOLOR', (0, 2), (-1, 2), COLOR_ORANGE),
            ('TEXTCOLOR', (0, 5), (-1, 5), COLOR_ORANGE),
            ('TEXTCOLOR', (0, 7), (-1, -1), COLOR_ORANGE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 44),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 5), (-1, 5), 12),
            ('FONTSIZE', (0, 7), (-1, -1), 11),
            ('ROWHEIGHT', (0, 0), (-1, -1), 50),
        ]))
        
        self.story.append(portada)
        self.story.append(PageBreak())
    
    def crear_grafico_ganancia(self, resultados, filename):
        """Gráfico de ganancia acumulada"""
        horizontes = [6, 12, 24, 36, 60]
        ganancias_reentel = []
        ganancias_sr = []
        
        for h in horizontes:
            if h in resultados:
                ganancias_reentel.append(resultados[h]['ganancia'])
                ganancias_sr.append(resultados[h]['ganancia'] * 1.1)  # Simulado
        
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_DARK)
        ax.set_facecolor(COLOR_DARK)
        
        x = np.arange(len(horizontes))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, ganancias_reentel, width, label='Reentel', color=COLOR_BLUE)
        bars2 = ax.bar(x + width/2, ganancias_sr, width, label='SuperReentel', color=COLOR_ORANGE)
        
        ax.set_xlabel('Horizontes (meses)', color=COLOR_TEXT_LIGHT)
        ax.set_ylabel('Ganancia (€)', color=COLOR_TEXT_LIGHT)
        ax.set_xticks(x)
        ax.set_xticklabels(horizontes)
        ax.legend(facecolor=COLOR_DARK, edgecolor=COLOR_TEXT_LIGHT, labelcolor=COLOR_TEXT_LIGHT)
        
        ax.tick_params(colors=COLOR_TEXT_LIGHT)
        ax.spines['bottom'].set_color(COLOR_TEXT_LIGHT)
        ax.spines['left'].set_color(COLOR_TEXT_LIGHT)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(filename, facecolor=COLOR_DARK, bbox_inches='tight', dpi=100)
        plt.close()
    
    def crear_grafico_rentabilidad(self, resultados, filename):
        """Gráfico de rentabilidad anualizada"""
        horizontes = [6, 12, 24, 36, 60]
        rentabilidades = []
        
        for h in horizontes:
            if h in resultados:
                rentabilidades.append(resultados[h]['rentabilidad_anualizada'] * 100)
        
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_DARK)
        ax.set_facecolor(COLOR_DARK)
        
        ax.plot(horizontes, rentabilidades, marker='o', linewidth=3, markersize=8, 
               color=COLOR_ORANGE, label='Rentabilidad Anualizada')
        ax.fill_between(horizontes, rentabilidades, alpha=0.3, color=COLOR_ORANGE)
        
        ax.set_xlabel('Horizontes (meses)', color=COLOR_TEXT_LIGHT)
        ax.set_ylabel('Rentabilidad (%)', color=COLOR_TEXT_LIGHT)
        ax.legend(facecolor=COLOR_DARK, edgecolor=COLOR_TEXT_LIGHT, labelcolor=COLOR_TEXT_LIGHT)
        
        ax.tick_params(colors=COLOR_TEXT_LIGHT)
        ax.spines['bottom'].set_color(COLOR_TEXT_LIGHT)
        ax.spines['left'].set_color(COLOR_TEXT_LIGHT)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Agregar valores en los puntos
        for i, (h, r) in enumerate(zip(horizontes, rentabilidades)):
            ax.text(h, r + 1, f'{r:.1f}%', ha='center', color=COLOR_ORANGE, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(filename, facecolor=COLOR_DARK, bbox_inches='tight', dpi=100)
        plt.close()
    
    def agregar_resumen(self, num_inmuebles, inversion_total, rentabilidad_anual):
        """Sección resumen con métricas"""
        self.story.append(Paragraph("RESUMEN DE LA CUENTA", self.styles['Subtitulo']))
        self.story.append(Spacer(1, 0.2*inch))
        
        resumen_data = [
            ['Número de inmuebles', str(num_inmuebles)],
            ['Inversión total (€)', f'{inversion_total:,.2f}'],
            ['Rentabilidad anualizada', f'{rentabilidad_anual*100:.2f}%'],
        ]
        
        resumen_table = Table(resumen_data, colWidths=[4*cm, 4*cm])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), COLOR_DARK),
            ('TEXTCOLOR', (0, 0), (0, -1), COLOR_ORANGE),
            ('TEXTCOLOR', (1, 0), (1, -1), white),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, COLOR_LIGHT_BLUE),
            ('ROWHEIGHT', (0, 0), (-1, -1), 30),
        ]))
        
        self.story.append(resumen_table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_graficos(self, resultados):
        """Agregar gráficos de ganancia y rentabilidad"""
        self.story.append(Paragraph("PROYECCIÓN CON REINVERSIÓN", self.styles['Subtitulo']))
        self.story.append(Spacer(1, 0.1*inch))
        
        # Crear gráficos
        self.crear_grafico_ganancia(resultados, '/tmp/ganancia.png')
        self.crear_grafico_rentabilidad(resultados, '/tmp/rentabilidad.png')
        
        # Agregar gráficos al PDF
        try:
            img_ganancia = RLImage('/tmp/ganancia.png', width=6*inch, height=3.5*inch)
            self.story.append(img_ganancia)
            self.story.append(Spacer(1, 0.2*inch))
            
            img_rentabilidad = RLImage('/tmp/rentabilidad.png', width=6*inch, height=3.5*inch)
            self.story.append(img_rentabilidad)
            self.story.append(Spacer(1, 0.2*inch))
        except:
            self.story.append(Paragraph("Error al generar gráficos", self.styles['NormalCustom']))
    
    def agregar_tabla_proyectos(self, cartera_lista):
        """Tabla con detalles de proyectos"""
        self.story.append(PageBreak())
        self.story.append(Paragraph("ANÁLISIS CARTERA PROPUESTA", self.styles['Subtitulo']))
        self.story.append(Spacer(1, 0.2*inch))
        
        datos = [
            ['ID', 'Nombre', 'Inversión (€)', '% Cartera', 'Rentabilidad']
        ]
        
        for proyecto in cartera_lista:
            datos.append([
                proyecto.get('id', ''),
                proyecto.get('nombre', '')[:20],
                f"€ {proyecto.get('inversion_eur', 0):,.0f}",
                f"{proyecto.get('porcentaje', 0):.1f}%",
                f"{proyecto.get('rentabilidad', 0)*100:.1f}%"
            ])
        
        tabla = Table(datos, colWidths=[1.5*cm, 3*cm, 2*cm, 2*cm, 2*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_ORANGE),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_DARK),
            ('BACKGROUND', (0, 1), (-1, -1), COLOR_DARK),
            ('TEXTCOLOR', (0, 1), (-1, -1), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, COLOR_LIGHT_BLUE),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))
        
        self.story.append(tabla)
        self.story.append(Spacer(1, 0.3*inch))
    
    def agregar_footer(self):
        """Footer con disclaimer"""
        self.story.append(Spacer(1, 0.2*inch))
        footer_text = (
            '<font size=8 color="#999999">'
            'Este documento es una propuesta de inversión basada en datos estimados. '
            'Las rentabilidades reales pueden variar. '
            'Consulta con tu asesor Reental antes de invertir.'
            '</font>'
        )
        self.story.append(Paragraph(footer_text, self.styles['NormalCustom']))
    
    def generar(self, nombre_inversor, email, estatus, tipo_cambio,
                num_inmuebles, inversion_total_eur, rentabilidad_anual,
                resultados_por_horizonte, cartera_lista):
        """Genera el PDF profesional completo"""
        
        self.agregar_portada(nombre_inversor, estatus)
        self.agregar_resumen(num_inmuebles, inversion_total_eur, rentabilidad_anual)
        self.agregar_graficos(resultados_por_horizonte)
        self.agregar_tabla_proyectos(cartera_lista)
        self.agregar_footer()
        
        # Build PDF
        self.doc.build(self.story)
        
        # Obtener bytes
        self.buffer.seek(0)
        return self.buffer.getvalue()
