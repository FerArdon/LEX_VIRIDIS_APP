"""
LEX VIRIDIS - Advanced Export Manager (V7.0)
Soporte para PDF, Excel y TXT con historial de exportaciones.
"""

import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from ..config import config

class ExportLogManager:
    """Gestiona el historial de exportaciones en persistencia JSON."""
    
    LOG_FILE = config.DATA_DIR / "export_history.json"

    @classmethod
    def add_log(cls, filename, format_type):
        try:
            history = cls.get_history()
            new_entry = {
                "filename": os.path.basename(filename),
                "path": str(filename),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "format": format_type
            }
            history.insert(0, new_entry)
            history = history[:10] # Mantener solo las últimas 10
            
            config.DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=4)
        except Exception as e:
            logging.error(f"Error guardando log de exportación: {e}")

    @classmethod
    def get_history(cls):
        if not cls.LOG_FILE.exists():
            return []
        try:
            with open(cls.LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error al cargar historial de exportaciones: {e}")
            return []

class ExportManager:
    """Clase principal para generación de reportes en múltiples formatos."""

    @staticmethod
    def _ensure_export_dir():
        export_dir = config.EXPORT_DIR
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir

    @classmethod
    def export(cls, data, format_type="TXT", query="Consulta", origin="Buscador", callback=None):
        """Punto de entrada principal compatible con hilos."""
        format_type = format_type.upper()
        
        # 1. Diálogo de guardado nativo
        ext_map = {"PDF": ".pdf", "EXCEL": ".xlsx", "TXT": ".txt"}
        type_map = {
            "PDF": [("Documento PDF", "*.pdf")],
            "EXCEL": [("Libro de Excel", "*.xlsx")],
            "TXT": [("Archivo de texto", "*.txt")]
        }
        
        export_dir = cls._ensure_export_dir()
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"Reporte_{origin}_{now}{ext_map.get(format_type, '.txt')}"
        
        file_path = filedialog.asksaveasfilename(
            initialdir=str(export_dir),
            initialfile=default_name,
            defaultextension=ext_map.get(format_type),
            filetypes=type_map.get(format_type),
            title=f"Exportar como {format_type}"
        )
        
        if not file_path:
            return

        # 2. Ejecutar en hilo para no bloquear UI
        def worker():
            try:
                if format_type == "PDF":
                    success = cls._to_pdf(data, query, file_path, origin)
                elif format_type == "EXCEL":
                    success = cls._to_excel(data, query, file_path, origin)
                else:
                    success = cls._to_txt(data, query, file_path, origin)
                
                if success:
                    ExportLogManager.add_log(file_path, format_type)
                    if callback:
                        callback(True, file_path)
                else:
                    if callback:
                        callback(False, "Error en generación.")
            except Exception as e:
                logging.error(f"Error en exportación {format_type}: {e}")
                if callback:
                    callback(False, str(e))

        threading.Thread(target=worker, daemon=True).start()

    @classmethod
    def _to_pdf(cls, data, query, path, origin):
        """Generación de PDF profesional con fpdf2."""
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        
        # Logo y Encabezado Institucional
        logo_path = config.BASE_DIR / "assets" / "LEXVIRIDIS_WHITE_BG.png"
        if logo_path.exists():
            pdf.image(str(logo_path), 10, 8, 30)
        
        pdf.set_font("helvetica", 'B', 16)
        pdf.set_text_color(0, 102, 102) # Teal Institucional
        pdf.cell(0, 10, 'LEX VIRIDIS - REPORTE TÉCNICO', 0, 1, 'C')
        pdf.set_font("helvetica", '', 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Gestión y Control de Información Ambiental", 0, 1, 'C')
        pdf.ln(15)
        
        # Cuadro de Metadatos
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("helvetica", 'B', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 8, " Fecha:", 1, 0, 'L', fill=True)
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 8, f" {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 1, 1, 'L')
        
        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(40, 8, " Origen:", 1, 0, 'L', fill=True)
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 8, f" {origin}", 1, 1, 'L')

        pdf.set_font("helvetica", 'B', 10)
        pdf.cell(40, 8, " Consulta:", 1, 0, 'L', fill=True)
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 8, f" {query}", 1, 1, 'L')
        pdf.ln(10)
        
        # Cuerpo del Reporte
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, "Detalle de Información:", 0, 1)
        pdf.set_font("helvetica", '', 10)
        
        if isinstance(data, list):
            for item in data:
                pdf.set_font("helvetica", 'B', 10)
                pdf.multi_cell(0, 7, f"Norma: {item.get('norma_titulo', 'Sin Título')}")
                pdf.set_font("helvetica", 'I', 9)
                pdf.set_text_color(0, 102, 204)
                pdf.cell(0, 5, f"Página {item.get('page', '0')} | Relevancia: {item.get('relevance', 0):.2f}", 0, 1)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("helvetica", '', 10)
                pdf.multi_cell(0, 6, f"{item.get('context', '...')}", align='J')
                pdf.ln(5)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)
        else:
            pdf.multi_cell(0, 7, str(data), align='J')

        pdf.set_y(-20)
        pdf.set_font("helvetica", 'I', 8)
        pdf.cell(0, 10, f'Página {pdf.page_no()}', 0, 0, 'C')

        pdf.output(path)
        return True

    @classmethod
    def _to_excel(cls, data, query, path, origin):
        """Generación de Excel con auto-ajuste de columnas."""
        import pandas as pd
        if isinstance(data, list):
            rows = []
            for item in data:
                rows.append({
                    "Fecha": datetime.now().strftime('%d/%m/%Y'),
                    "Origen": origin,
                    "Término": query,
                    "Norma": item.get('norma_titulo', 'S/T'),
                    "Página": item.get('page', 0),
                    "Relevancia": float(f"{item.get('relevance', 0):.2f}"),
                    "Fragmento": item.get('context', '...')[:32000] # Límite Excel
                })
            df = pd.DataFrame(rows)
        else:
            df = pd.DataFrame([{"Fecha": datetime.now(), "Origen": origin, "Consulta": query, "Respuesta IA": str(data)}])
            
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Reporte')
            worksheet = writer.sheets['Reporte']
            # Auto-ajuste de columnas
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                max_len = min(max_len, 50) # Capar a 50 chars
                worksheet.column_dimensions[chr(65 + idx)].width = max_len
                
        return True

    @classmethod
    def _to_txt(cls, data, query, path, origin):
        """Generación de TXT con utf-8-sig."""
        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write("="*70 + "\n")
            f.write(f"LEXVIRIDIS - REPORTE - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Consulta: {query}\n")
            f.write("="*70 + "\n\n")
            
            if isinstance(data, list):
                for i, item in enumerate(data, 1):
                    f.write(f"[{i}] {item.get('norma_titulo', 'S/T')}\n")
                    f.write(f"Ubicación: {item.get('file', 'N/A')} | Pág: {item.get('page', '0')}\n")
                    f.write(f"Contexto: {item.get('context', '...')}\n")
                    f.write("-" * 40 + "\n")
            else:
                f.write(str(data))
        return True
