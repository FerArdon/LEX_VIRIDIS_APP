import logging
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Reutilizamos constantes de estilo si existen, si no definimos nuevas
# Intenta importar de pdf_exporter si es posible para consistencia
try:
    from .pdf_exporter import VERDE_PRIMARIO, GRIS_TEXTO, PDFExporter
    STYLES_AVAILABLE = True
except ImportError:
    try:
        from pdf_exporter import VERDE_PRIMARIO, GRIS_TEXTO, PDFExporter
        STYLES_AVAILABLE = True
    except ImportError:
        STYLES_AVAILABLE = False
        VERDE_PRIMARIO = colors.HexColor("#1B5E20")
        GRIS_TEXTO = colors.HexColor("#424242")

class ManualGenerator:
    """Generador de Manual PDF desde Markdown."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("docs")
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos similares a los institucionales."""
        self.styles.add(ParagraphStyle(
            name='ManualTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=VERDE_PRIMARIO,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='ManualHeading1',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=VERDE_PRIMARIO,
            spaceBefore=15,
            spaceAfter=10
        ))
        self.styles.add(ParagraphStyle(
            name='ManualHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#2E7D32"), # Verde un poco más claro
            spaceBefore=10,
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            name='ManualBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=GRIS_TEXTO,
            leading=14,
            spaceAfter=8
        ))

    def generate_from_markdown(self, md_path: Path) -> Path:
        """Convierte un archivo Markdown a PDF."""
        if not md_path.exists():
            raise FileNotFoundError(f"No se encontró {md_path}")

        content = md_path.read_text(encoding='utf-8')
        output_path = self.output_dir / "Manual_Usuario_LexViridis.pdf"
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )

        story = []
        
        # Procesar líneas
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('# '):
                story.append(Paragraph(line[2:], self.styles['ManualTitle']))
                story.append(Spacer(1, 10))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], self.styles['ManualHeading1']))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], self.styles['ManualHeading2']))
            elif line.startswith('![') and '](' in line:
                # Imagen
                # Formato: ![Alt spec](path)
                match = re.search(r'\!\[(.*?)\]\((.*?)\)', line)
                if match:
                    img_path_str = match.group(2)
                    # Intentar resolver ruta relativa a la app o assets
                    # Por ahora placeholder si no existe
                    img_real_path = Path(img_path_str)
                    if not img_real_path.exists():
                        # Buscar en assets si no está en root
                        img_real_path = Path("assets") / img_path_str
                    
                    if img_real_path.exists():
                        try:
                            # Ajustar tamaño max
                            # Usar ruta absoluta para evitar problemas con ReportLab
                            abs_img_path = str(img_real_path.resolve())
                            img = Image(abs_img_path, width=6*inch, height=3*inch, kind='proportional')
                            story.append(img)
                            story.append(Spacer(1, 10))
                        except Exception as e:
                            logging.error(f"Error cargando imagen {img_real_path}: {e}")
                            story.append(Paragraph(f"[Error imagen: {img_path_str}]", self.styles['ManualBody']))
                    else:
                        # Placeholder texto para imagen faltante
                        story.append(Paragraph(f"<i>[Imagen pendiente: {img_path_str}]</i>", self.styles['ManualBody']))
            else:
                # Texto normal
                # Soporte básico de negrita **texto** -> <b>texto</b>
                line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                story.append(Paragraph(line, self.styles['ManualBody']))

        doc.build(story)
        return output_path

if __name__ == "__main__":
    # Prueba standalone
    gen = ManualGenerator()
    try:
        path = gen.generate_from_markdown(Path("docs/MANUAL_USUARIO.md"))
        print(f"Generado: {path}")
    except Exception as e:
        print(f"Error: {e}")
