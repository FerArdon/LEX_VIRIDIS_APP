"""
LEX VIRIDIS - Base View
Clase base para asegurar consistencia y facilitar el manejo de hilos.
"""

import tkinter as tk
import customtkinter as ctk
import threading
from ..design_system_ctk import Colors, Typography

class BaseView(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.db = app.engine.db_manager if app.engine else None
        self.configure(fg_color="transparent")
        
        # Grid layout estándar
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    @staticmethod
    def add_context_menu(ctk_textbox):
        """Agrega menú contextual (clic derecho) a un CTkTextbox.

        Opciones: Seleccionar todo · Copiar · Cortar · Pegar
        Funciona en modo 'disabled' (solo lectura) omitiendo Cortar y Pegar.
        """
        inner = ctk_textbox._textbox  # widget tk.Text interno de CTkTextbox

        menu = tk.Menu(inner, tearoff=0)

        def _select_all():
            inner.tag_add("sel", "1.0", "end")
            inner.mark_set("insert", "1.0")
            inner.see("insert")

        def _copy():
            try:
                text = inner.get("sel.first", "sel.last")
                inner.clipboard_clear()
                inner.clipboard_append(text)
            except tk.TclError:
                pass

        def _cut():
            _copy()
            try:
                inner.delete("sel.first", "sel.last")
            except tk.TclError:
                pass

        def _paste():
            try:
                text = inner.clipboard_get()
                inner.insert("insert", text)
            except tk.TclError:
                pass

        def _show_menu(event):
            menu.delete(0, "end")
            menu.add_command(label="Seleccionar todo", command=_select_all,
                             accelerator="Ctrl+A")
            menu.add_separator()
            menu.add_command(label="Copiar",  command=_copy,  accelerator="Ctrl+C")
            # Cortar y Pegar solo si el widget está en modo editable
            state = str(inner.cget("state"))
            if state != "disabled":
                menu.add_command(label="Cortar",  command=_cut,   accelerator="Ctrl+X")
                menu.add_command(label="Pegar",   command=_paste, accelerator="Ctrl+V")
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        # Bind en el widget interno y en el CTkTextbox (captura ambas superficies)
        inner.bind("<Button-3>", _show_menu)
        ctk_textbox.bind("<Button-3>", _show_menu)

    def run_in_thread(self, target, args=()):
        """Ejecuta una tarea pesada en un hilo secundario."""
        thread = threading.Thread(target=target, args=args, daemon=True)
        thread.start()
        return thread

    def update_ui(self, func, *args):
        """Envía una actualización a la UI desde un hilo secundario."""
        self.after(0, lambda: func(*args))

    def show_toast(self, message, type="info"):
        """Placeholder para notificaciones tipo Toast (Solicitado por Fer)."""
        # Se implementará en MainApp como un widget global
        if hasattr(self.app, "show_toast"):
            self.app.show_toast(message, type)
        else:
            print(f"[{type.upper()}] {message}")

    def show_export_success_dialog(self, file_path):
        """Diálogo personalizado Estilo Windows 11 para confirmar exportación."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Exportación Exitosa")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        dialog.resizable(False, False)
        
        # Centrar
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 100
        dialog.geometry(f"+{x}+{y}")

        lbl_icon = ctk.CTkLabel(dialog, text="✅", font=("Segoe UI Variable", 40))
        lbl_icon.pack(pady=(20, 10))

        lbl_msg = ctk.CTkLabel(
            dialog, 
            text="Documento exportado correctamente", 
            font=Typography.bold()
        )
        lbl_msg.pack(pady=5)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        def open_file():
            import os
            os.startfile(file_path)
            dialog.destroy()

        btn_open = ctk.CTkButton(
            btn_frame, 
            text="Abrir archivo", 
            width=120, 
            command=open_file,
            fg_color=Colors.ACCENT_BLUE
        )
        btn_open.pack(side="left", padx=10)

        btn_close = ctk.CTkButton(
            btn_frame, 
            text="Cerrar", 
            width=100, 
            command=dialog.destroy,
            fg_color="transparent",
            border_width=2,
            border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY
        )
        btn_close.pack(side="left", padx=10)
