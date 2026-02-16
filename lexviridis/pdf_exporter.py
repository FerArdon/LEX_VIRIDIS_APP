
"""
LEX VIRIDIS - Exportador de PDFs Profesionales
Genera documentos legales con formato institucional.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, legal, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

# Colores institucionales
VERDE_PRIMARIO = colors.HexColor("#1B5E20")
VERDE_CLARO = colors.HexColor("#4CAF50")
DORADO = colors.HexColor("#D4AF37")
GRIS_TEXTO = colors.HexColor("#424242")
GRIS_CLARO = colors.HexColor("#BDBDBD")


class PDFExporter:
    """Exportador de PDFs con formato legal profesional."""

    # Tamaños de página disponibles
    PAGE_SIZES = {
        'carta': letter,
        'legal': legal,
        'a4': A4,
    }

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path.cwd() / "exports"
        self.output_dir.mkdir(exist_ok=True)
        self._setup_styles()

    def _setup_styles(self):
        """Configura estilos de párrafo personalizados."""
        self.styles = getSampleStyleSheet()

        # Título principal
        self.styles.add(ParagraphStyle(
            name='LexTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=VERDE_PRIMARIO,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))

        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='LexSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=GRIS_TEXTO,
            alignment=TA_CENTER,
            spaceAfter=20,
        ))

        # Nombre de norma
        self.styles.add(ParagraphStyle(
            name='NormaTitulo',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=VERDE_PRIMARIO,
            alignment=TA_LEFT,
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
        ))

        # Número de artículo
        self.styles.add(ParagraphStyle(
            name='ArticuloNumero',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=DORADO,
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=6,
            fontName='Helvetica-Bold',
        ))

        # Contenido de artículo
        self.styles.add(ParagraphStyle(
            name='ArticuloContenido',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=GRIS_TEXTO,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=14,
            firstLineIndent=20,
        ))

        # Pie de página
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=GRIS_CLARO,
            alignment=TA_CENTER,
        ))

        # Fecha
        self.styles.add(ParagraphStyle(
            name='Fecha',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=GRIS_CLARO,
            alignment=TA_CENTER,
            spaceAfter=30,
        ))

    def _create_header(self, story: list, titulo: str = "Compendio Legal Ambiental"):
        """Crea el encabezado del documento."""
        # Logo (texto estilizado)
        story.append(Paragraph("🌿 LEX VIRIDIS", self.styles['LexTitle']))
        story.append(Paragraph(titulo.upper(), self.styles['LexSubtitle']))

        # Línea decorativa
        story.append(HRFlowable(
            width="80%",
            thickness=2,
            color=VERDE_PRIMARIO,
            spaceBefore=5,
            spaceAfter=5,
            hAlign='CENTER',
        ))

        # Fecha de generación
        fecha = datetime.now().strftime("%d de %B de %Y, %H:%M")
        story.append(Paragraph(f"Documento generado el {fecha}", self.styles['Fecha']))

    def _add_footer(self, canvas, doc):
        """Añade pie de página a cada hoja."""
        canvas.saveState()

        # Línea
        canvas.setStrokeColor(GRIS_CLARO)
        canvas.setLineWidth(0.5)
        canvas.line(inch, 0.65*inch, doc.pagesize[0] - inch, 0.65*inch)

        # Texto del pie
        canvas.setFillColor(GRIS_CLARO)
        canvas.setFont('Helvetica', 9)

        # Página
        page_text = f"Página {doc.page}"
        canvas.drawString(inch, 0.45*inch, page_text)

        # LEX VIRIDIS
        canvas.drawRightString(doc.pagesize[0] - inch, 0.45*inch, "LEX VIRIDIS Pro")

        canvas.restoreState()

    def export_articulos(
        self,
        articulos: list[dict],
        filename: str = None,
        titulo: str = "Resultados de Búsqueda",
        page_size: str = 'carta',
        include_index: bool = False,
    ) -> Path:
        """
        Exporta una lista de artículos a PDF.

        Args:
            articulos: Lista de diccionarios con 'numero', 'contenido', 'norma_titulo'
            filename: Nombre del archivo (sin extensión)
            titulo: Título del documento
            page_size: 'carta', 'legal', o 'a4'
            include_index: Incluir índice al inicio

        Returns:
            Path al archivo PDF generado
        """
        if not articulos:
            raise ValueError("No hay artículos para exportar")

        # Generar nombre de archivo
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lex_viridis_export_{timestamp}"

        output_path = self.output_dir / f"{filename}.pdf"

        # Configurar documento
        pagesize = self.PAGE_SIZES.get(page_size, letter)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=pagesize,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=inch,
        )

        story = []

        # Header
        self._create_header(story, titulo)

        # Resumen
        normas_unicas = set()
        for art in articulos:
            norma = art.get('norma_titulo') or art.get('file', 'Desconocido')
            normas_unicas.add(norma)

        resumen = f"<b>Total:</b> {len(articulos)} artículo(s) de {len(normas_unicas)} norma(s)"
        story.append(Paragraph(resumen, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Índice opcional
        if include_index:
            story.append(Paragraph("<b>ÍNDICE</b>", self.styles['NormaTitulo']))
            for i, art in enumerate(articulos, 1):
                numero = art.get('numero') or art.get('numero_articulo', '?')
                norma = art.get('norma_titulo') or Path(art.get('file', '')).stem
                story.append(Paragraph(
                    f"{i}. Artículo {numero} - {norma[:50]}...",
                    self.styles['Normal']
                ))
            story.append(PageBreak())

        # Contenido - Agrupar por norma
        norma_actual = None
        for art in articulos:
            norma = art.get('norma_titulo') or art.get('file', 'Documento')
            if isinstance(norma, Path):
                norma = norma.stem

            # Nueva sección de norma
            if norma != norma_actual:
                norma_actual = norma
                story.append(Paragraph(norma, self.styles['NormaTitulo']))
                story.append(HRFlowable(
                    width="100%",
                    thickness=1,
                    color=VERDE_CLARO,
                    spaceAfter=10,
                ))

            # Artículo
            numero = art.get('numero') or art.get('numero_articulo', '')
            contenido = art.get('contenido', art.get('context', ''))

            story.append(Paragraph(f"Artículo {numero}", self.styles['ArticuloNumero']))

            # Limpiar contenido para ReportLab
            contenido_limpio = self._clean_text(contenido)
            story.append(Paragraph(contenido_limpio, self.styles['ArticuloContenido']))

        # Construir PDF
        doc.build(
            story,
            onFirstPage=self._add_footer,
            onLaterPages=self._add_footer,
        )

        logging.info(f"✅ PDF exportado: {output_path}")
        return output_path

    def export_search_results(
        self,
        results: list[dict],
        query: str,
        filename: str = None,
    ) -> Path:
        """
        Exporta resultados de búsqueda a PDF.
        """
        titulo = f"Búsqueda: {query}"

        # Convertir formato de resultados de búsqueda a artículos
        articulos = []
        for res in results:
            articulos.append({
                'numero': res.get('context', '').split(':')[0].replace('Art. ', '').strip(),
                'contenido': res.get('context', ''),
                'norma_titulo': Path(res.get('file', '')).stem,
            })

        return self.export_articulos(
            articulos,
            filename=filename,
            titulo=titulo,
        )

    def export_norma_completa(
        self,
        norma_id: int,
        db_path: Path,
        filename: str = None,
    ) -> Path:
        """
        Exporta una norma completa con todos sus artículos.
        """
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Obtener norma
        cursor.execute("SELECT titulo, tipo FROM normas WHERE id = ?", (norma_id,))
        norma = cursor.fetchone()

        if not norma:
            conn.close()
            raise ValueError(f"Norma ID {norma_id} no encontrada")

        # Obtener artículos
        cursor.execute("""
            SELECT numero_articulo, contenido
            FROM articulos
            WHERE norma_id = ?
            ORDER BY id
        """, (norma_id,))

        articulos = [{
            'numero': row['numero_articulo'],
            'contenido': row['contenido'],
            'norma_titulo': norma['titulo'],
        } for row in cursor.fetchall()]

        conn.close()

        return self.export_articulos(
            articulos,
            filename=filename,
            titulo=norma['titulo'],
            include_index=len(articulos) > 10,
        )

    def _clean_text(self, text: str) -> str:
        """Limpia texto para uso en ReportLab."""
        if not text:
            return ""

        # Escapar caracteres especiales de XML
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')

        # Remover caracteres problemáticos
        text = text.replace('\x00', '')

        return text


# Función de conveniencia
def exportar_a_pdf(
    articulos: list[dict],
    filename: str = None,
    titulo: str = "Exportación LEX VIRIDIS",
    abrir_al_terminar: bool = True,
) -> Path:
    """
    Función de conveniencia para exportar artículos a PDF.
    """
    exporter = PDFExporter()
    output_path = exporter.export_articulos(articulos, filename, titulo)

    if abrir_al_terminar:
        import platform
        import subprocess

        if platform.system() == 'Windows':
            os.startfile(str(output_path))
        elif platform.system() == 'Darwin':
            subprocess.run(['open', str(output_path)])
        else:
            subprocess.run(['xdg-open', str(output_path)])

    return output_path
