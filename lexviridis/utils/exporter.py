"""
LEX VIRIDIS - Exporter Utility
Gestión de exportación de datos a formatos nativos de Windows 11.
"""

import os
from datetime import datetime
from tkinter import filedialog, messagebox
import logging

class Exporter:
    @staticmethod
    def export_to_txt(data, search_query="General"):
        """
        Exporta resultados de búsqueda o reportes de IA a un archivo .txt.
        Implementa codificación utf-8-sig para compatibilidad total con Windows.
        """
        if not data:
            logging.warning("Intento de exportación sin datos.")
            return False

        # 1. Configurar diálogo de guardado
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Reporte_LexViridis_{now}.txt"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile=default_filename,
            title="Guardar Reporte de Búsqueda"
        )

        if not file_path:
            logging.info("Exportación cancelada por el usuario.")
            return False

        # 2. Validar permisos de escritura
        try:
            with open(file_path, 'a', encoding='utf-8-sig') as f:
                pass 
        except PermissionError:
            messagebox.showerror("Error de Permisos", f"No se tiene permiso para escribir en:\n{file_path}")
            return False

        # 3. Generar contenido formateado
        try:
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                # Encabezado Institucional
                f.write("="*70 + "\n")
                f.write(f"LEXVIRIDIS - REPORTE DE BÚSQUEDA - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Término buscado: {search_query}\n")
                f.write("="*70 + "\n\n")

                if isinstance(data, list):
                    # Formato tabular para resultados de búsqueda
                    f.write(f"{'NORMA':<50} | {'PÁG':<5} | {'RELEVANCIA':<10}\n")
                    f.write("-" * 70 + "\n")
                    for item in data:
                        # Limpiar nombres largos
                        norma = os.path.basename(item.get('file', 'N/A'))[:47]
                        pagi = str(item.get('page', '0'))
                        rel = f"{item.get('relevance', 0):.2f}"
                        f.write(f"{norma:<50} | {pagi:<5} | {rel:<10}\n")
                        
                    f.write("\n" + "="*70 + "\n")
                    f.write("DETALLE DE FRAGMENTOS:\n")
                    f.write("="*70 + "\n")
                    for i, item in enumerate(data, 1):
                        f.write(f"\n[{i}] {item.get('norma_titulo', 'Sin Título')}\n")
                        f.write(f"Ubicación: {item.get('file', 'N/A')}\n")
                        f.write(f"Contexto: {item.get('context', '...')}\n")
                        f.write("-" * 40 + "\n")
                else:
                    # Formato de texto libre (para Asistente IA)
                    f.write(str(data))

                f.write(f"\n\nFin del reporte generado por LEX VIRIDIS.")

            messagebox.showinfo("Exportación Exitosa", f"Archivo guardado exitosamente en:\n{file_path}")
            return True

        except Exception as e:
            logging.error(f"Error fatal en exportación: {e}")
            messagebox.showerror("Error de Exportación", f"Ocurrió un error inesperado:\n{e}")
            return False
