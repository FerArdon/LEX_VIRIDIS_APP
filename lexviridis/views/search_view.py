"""
LEX VIRIDIS - Search View (CustomTkinter)
Búsqueda FTS con resultados, detalle de artículo, favoritos y exportación.
"""

import os
import customtkinter as ctk
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography


class SearchView(BaseView):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.last_results = []
        self.setup_ui()

    def setup_ui(self):
        # 0. Banner de Sección
        if "banner_search" in self.app.icons:
            ctk.CTkLabel(self, image=self.app.icons["banner_search"], text="").pack(fill="x", pady=(0, 10))

        # 1. Header con título + exportación
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(10, 15))

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="Buscador Legal",
            font=Typography.get_font(22, "bold"),
            text_color=Colors.PRIMARY,
            anchor="w"
        )
        self.lbl_title.pack(side="left")

        # Grupo de Exportación (derecha)
        self.export_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.export_frame.pack(side="right")

        self.format_menu = ctk.CTkOptionMenu(
            self.export_frame,
            values=["PDF", "EXCEL", "TXT"],
            width=90, height=32,
            font=Typography.caption(),
            fg_color=Colors.PRIMARY
        )
        self.format_menu.pack(side="left", padx=5)

        self.btn_export = ctk.CTkButton(
            self.export_frame,
            text=" Exportar",
            image=self.app.icons.get("settings"),
            width=110, height=32,
            fg_color="transparent", border_width=2,
            border_color=Colors.PRIMARY, text_color=Colors.PRIMARY,
            command=self.export_results,
            state="disabled"
        )
        self.btn_export.pack(side="left", padx=5)

        # 2. Barra de Búsqueda
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", pady=10)

        self.entry_search = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Ingresa términos (ej. tala, forestal, biodiversidad)...",
            height=45, corner_radius=10,
            font=Typography.body(),
            border_width=2, border_color=Colors.BORDER
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<Return>", lambda e: self.perform_search())

        self.btn_search = ctk.CTkButton(
            self.search_frame,
            text="  Buscar",
            image=self.app.icons.get("search"),
            compound="left",
            command=self.perform_search,
            fg_color=Colors.ACCENT_BLUE,
            hover_color=Colors.PRIMARY,
            height=45, width=120, corner_radius=10,
            font=Typography.bold()
        )
        self.btn_search.pack(side="right")

        # 3. Área de Resultados
        self.results_area = ctk.CTkScrollableFrame(
            self,
            label_text="Resultados",
            fg_color=(Colors.SURFACE_LIGHT, "#2b2b2b"),
            corner_radius=10,
            label_font=Typography.bold()
        )
        self.results_area.pack(fill="both", expand=True, pady=10)

    # ── BÚSQUEDA ───────────────────────────────────────────────────────────────

    def perform_search(self):
        query = self.entry_search.get().strip()
        if not query:
            self.show_toast("Por favor ingresa un término de búsqueda", "warning")
            return
        self.btn_search.configure(state="disabled", text="Buscando...")
        for w in self.results_area.winfo_children():
            w.destroy()
        self.run_in_thread(self._search_thread_logic, (query,))

    def _search_thread_logic(self, query):
        try:
            if self.app.engine is None:
                raise RuntimeError("Motor de búsqueda no disponible. Verifique la instalación.")
            result = self.app.engine.search_safe(query)
            self.update_ui(self._display_results, result)
        except Exception as e:
            self.update_ui(self.show_toast, f"Error en búsqueda: {e}", "error")
        finally:
            self.update_ui(lambda: self.btn_search.configure(state="normal", text="  Buscar"))

    def _display_results(self, result):
        self.last_results = result.results or []
        count = len(self.last_results)

        self.results_area.configure(label_text=f"Resultados ({count})")

        if not self.last_results:
            self._show_no_results(result.query)
            self.btn_export.configure(state="disabled")
            return

        self.btn_export.configure(state="normal")
        for res in self.last_results:
            self._create_result_row(res)

    # ── FILAS DE RESULTADO ─────────────────────────────────────────────────────

    def _create_result_row(self, res):
        row_frame = ctk.CTkFrame(
            self.results_area,
            fg_color="transparent",
            corner_radius=8,
            border_width=1,
            border_color=Colors.BORDER
        )
        row_frame.pack(fill="x", pady=5, padx=5)

        # Nombre del archivo
        filename = os.path.basename(res.get("file", ""))
        title_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        ctk.CTkLabel(
            title_frame,
            text=res.get("norma_titulo", "Documento"),
            font=Typography.bold(), text_color=Colors.ACCENT_BLUE, anchor="w"
        ).pack(side="left")

        # Badge si es coincidencia de título (rank < -1)
        if res.get("relevance", 0) < -1:
            badge = ctk.CTkFrame(title_frame, fg_color=Colors.SUCCESS, corner_radius=12)
            badge.pack(side="left", padx=10)
            ctk.CTkLabel(badge, text=" LEY ENCONTRADA ", font=Typography.get_font(10, "bold"), text_color="white").pack(padx=5, pady=2)

        # Metadatos
        relevance = res.get("relevance", 0)
        ctk.CTkLabel(
            row_frame,
            text=f"Página: {res.get('page', '?')} | Relevancia: {relevance:.2f}",
            font=Typography.caption(),
            text_color=Colors.TEXT_SECONDARY, anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 5))

        # Fragmento de contexto
        ctk.CTkLabel(
            row_frame,
            text=res.get("context", "..."),
            font=Typography.body(),
            wraplength=700, justify="left", anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 10))

        # Acciones
        action_row = ctk.CTkFrame(row_frame, fg_color="transparent")
        action_row.pack(fill="x", padx=15, pady=(0, 10))

        # Botón Abrir PDF
        ctk.CTkButton(
            action_row, text="📄 Abrir PDF",
            command=lambda r=res: self._handle_open_pdf(r),
            height=30, width=110,
            fg_color="transparent", border_width=2,
            border_color=Colors.ACCENT_BLUE, text_color=Colors.ACCENT_BLUE,
            hover_color=Colors.WINDOW_BG_LIGHT
        ).pack(side="left", padx=(0, 8))

        # Botón Ver detalle
        ctk.CTkButton(
            action_row, text="🔍 Ver Detalle",
            command=lambda r=res: self._show_article_detail(r),
            height=30, width=110,
            fg_color="transparent", border_width=2,
            border_color=Colors.PRIMARY, text_color=Colors.PRIMARY,
            hover_color=Colors.WINDOW_BG_LIGHT
        ).pack(side="left", padx=(0, 8))

        # Botón Favorito
        try:
            is_fav = self.app.engine.is_favorite(res.get("id"))
        except Exception:
            is_fav = False

        fav_text = "★ Favorito" if is_fav else "☆ Favorito"
        fav_color = Colors.ACCENT_BLUE if is_fav else "transparent"
        fav_btn = ctk.CTkButton(
            action_row, text=fav_text,
            width=100, height=30,
            fg_color=fav_color, border_width=1,
            border_color=Colors.ACCENT_BLUE,
            text_color="white" if is_fav else Colors.ACCENT_BLUE,
            hover_color=Colors.BORDER,
            command=lambda r=res: self._toggle_fav(r)
        )
        fav_btn.pack(side="right")

    def _toggle_fav(self, res):
        try:
            was_added = self.app.engine.toggle_favorite(res.get("id"))
            msg = "Agregado a favoritos ★" if was_added else "Eliminado de favoritos"
            self.show_toast(msg, "success" if was_added else "info")
        except Exception as e:
            self.show_toast(f"Error: {e}", "error")

    # ── VISTA DE DETALLE DEL ARTÍCULO ──────────────────────────────────────────

    def _show_article_detail(self, res):
        """Muestra un Toplevel con el contenido completo del artículo."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Detalle del Artículo")
        dlg.geometry("700x550")
        dlg.attributes("-topmost", True)
        dlg.resizable(True, True)
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth() // 2) - 350
        y = (dlg.winfo_screenheight() // 2) - 275
        dlg.geometry(f"+{x}+{y}")

        # Encabezado
        hdr = ctk.CTkFrame(dlg, fg_color=Colors.PRIMARY, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr,
            text=os.path.basename(res.get("file", "Artículo")),
            font=Typography.bold(), text_color="white", anchor="w"
        ).pack(side="left", padx=20, pady=12)
        ctk.CTkLabel(
            hdr,
            text=f"Pág. {res.get('page', '?')}",
            font=Typography.caption(), text_color="white"
        ).pack(side="right", padx=20)

        # Contenido
        txt = ctk.CTkTextbox(
            dlg, wrap="word",
            font=Typography.body(),
            fg_color=(Colors.SURFACE_LIGHT, Colors.SURFACE_DARK),
            border_width=0
        )
        txt.pack(fill="both", expand=True, padx=15, pady=10)
        full_text = res.get("full_text") or res.get("context", "Sin contenido disponible.")
        txt.insert("end", full_text)
        txt.configure(state="disabled")
        self.add_context_menu(txt)

        # Botones de acción
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="📄 Abrir PDF",
            fg_color=Colors.ACCENT_BLUE, height=38, corner_radius=8,
            command=lambda: self._handle_open_pdf(res)
        ).pack(side="left", padx=5)

        # Favorito
        try:
            is_fav = self.app.engine.is_favorite(res.get("id"))
        except Exception:
            is_fav = False

        fav_text = "★ Quitar Favorito" if is_fav else "☆ Agregar Favorito"
        ctk.CTkButton(
            btn_frame, text=fav_text,
            fg_color=Colors.PRIMARY if is_fav else "transparent",
            border_width=1 if not is_fav else 0,
            border_color=Colors.PRIMARY,
            text_color="white" if is_fav else Colors.PRIMARY,
            height=38, corner_radius=8,
            command=lambda: self._toggle_fav(res)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="📤 Exportar TXT",
            fg_color="transparent", border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY, height=38, corner_radius=8,
            command=lambda: self._export_single(res)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Cerrar",
            fg_color="transparent", border_width=1, border_color=Colors.BORDER,
            text_color=Colors.TEXT_SECONDARY, height=38, corner_radius=8,
            command=dlg.destroy
        ).pack(side="right", padx=5)

    def _export_single(self, res):
        from ..utils.export_manager import ExportManager
        ExportManager.export(
            [res], format_type="TXT",
            query=self.entry_search.get().strip() or "Artículo",
            origin="Buscador",
            callback=lambda ok, info: (
                self.update_ui(self.show_export_success_dialog, info) if ok
                else self.update_ui(self.show_toast, f"Fallo: {info}", "error")
            )
        )

    # ── APERTURA DE PDF ────────────────────────────────────────────────────────

    def _handle_open_pdf(self, res):
        from ..config import config
        from ..pdf_highlighter import PDFHighlighter

        # 1. Resolver ruta del PDF
        file_field = res.get("file", "") or ""
        original_path = None

        if file_field and file_field != "None" and os.path.exists(file_field):
            original_path = file_field
        else:
            # Fallback: buscar por nombre de archivo en PDF_DIR
            filename = os.path.basename(file_field) if file_field and file_field != "None" else ""
            if not filename:
                filename = res.get("archivo_pdf", "") or os.path.basename(res.get("file", ""))
            candidate = config.get_pdf_absolute_path(filename)
            if candidate and candidate.exists():
                original_path = str(candidate)

        if not original_path:
            self.show_toast("Archivo PDF no encontrado", "error")
            return

        # 2. Resaltar y abrir
        try:
            term = self.entry_search.get().strip()
            final_path = PDFHighlighter.highlight_terms(original_path, term)
            os.startfile(final_path)
        except Exception as e:
            self.show_toast(f"No se pudo abrir: {e}", "error")

    # ── EXPORTACIÓN ────────────────────────────────────────────────────────────

    def export_results(self):
        if not self.last_results:
            self.show_toast("No hay resultados para exportar", "warning")
            return
        from ..utils.export_manager import ExportManager
        query = self.entry_search.get().strip() or "General"
        fmt = self.format_menu.get()

        ExportManager.export(
            self.last_results, format_type=fmt,
            query=query, origin="Buscador",
            callback=lambda ok, info: (
                self.update_ui(self.show_export_success_dialog, info) if ok
                else self.update_ui(self.show_toast, f"Fallo al exportar: {info}", "error")
            )
        )

    # ── SIN RESULTADOS ─────────────────────────────────────────────────────────

    def _show_no_results(self, query):
        frame = ctk.CTkFrame(self.results_area, fg_color="transparent")
        frame.pack(expand=True, fill="both")
        ctk.CTkLabel(
            frame,
            text=f"🔍  No hay resultados para '{query}'",
            font=Typography.subtitle(), text_color=Colors.TEXT_SECONDARY
        ).pack(pady=50)
        ctk.CTkLabel(
            frame,
            text="Intenta con otros términos o verifica la base de datos.",
            font=Typography.body(), text_color=Colors.TEXT_SECONDARY
        ).pack()
