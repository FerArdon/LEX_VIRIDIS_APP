"""
LEX VIRIDIS - Library View (CustomTkinter)
Catálogo legal con acceso a documentos PDF.
"""

import os
import shutil
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography
from ..config import config


PAGE_SIZE_CATALOG = 50  # Documentos visibles por página en el catálogo


class LibraryView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self._favs_loaded = False  # Cache flag: evita recargar favoritos en cada cambio de pestaña
        self._catalog_page = 0    # Página actual (0-indexed) para paginación del catálogo
        self._catalog_total = 0   # Total de normas para la búsqueda activa
        self.setup_ui()

    def setup_ui(self):
        # 0. Banner de Sección
        if "banner_library" in self.app.icons:
            ctk.CTkLabel(self, image=self.app.icons["banner_library"], text="").pack(fill="x", pady=(0, 10))

        # 1. Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="Biblioteca Institucional",
            font=Typography.get_font(22, "bold"),
            text_color=Colors.PRIMARY,
            anchor="w"
        ).pack(side="left")

        self.btn_sync = ctk.CTkButton(
            header_frame,
            text=" Sincronizar",
            width=140, height=32,
            fg_color=Colors.PRIMARY,
            command=self._sincronizar_biblioteca
        )
        self.btn_sync.pack(side="right")

        ctk.CTkButton(
            header_frame,
            text="＋ Agregar PDF",
            width=140, height=32,
            fg_color=Colors.SUCCESS,
            command=self._agregar_pdf
        ).pack(side="right", padx=(0, 10))

        # 2. Pestañas: Catálogo | Favoritos
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        tab_catalogo  = self.tabs.add("Catálogo Legal")
        tab_favoritos = self.tabs.add("★ Favoritos")

        # Catálogo
        self.search_frame_lib = ctk.CTkFrame(tab_catalogo, fg_color="transparent")
        self.search_frame_lib.pack(fill="x", padx=10, pady=(10, 5))
        
        self.entry_filter_lib = ctk.CTkEntry(
            self.search_frame_lib, 
            placeholder_text="🔍 Filtrar leyes por título, número o decreto...", 
            height=35
        )
        self.entry_filter_lib.pack(side="left", fill="x", expand=True)
        self.entry_filter_lib.bind("<KeyRelease>", lambda e: self._on_filter_changed())
        
        self.lbl_count_lib = ctk.CTkLabel(self.search_frame_lib, text="", font=Typography.caption(), text_color=Colors.TEXT_SECONDARY)
        self.lbl_count_lib.pack(side="right", padx=(10, 0))

        self.scroll_catalogo = ctk.CTkScrollableFrame(tab_catalogo, fg_color="transparent")
        self.scroll_catalogo.pack(fill="both", expand=True)

        # Favoritos
        fav_header = ctk.CTkFrame(tab_favoritos, fg_color="transparent")
        fav_header.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(fav_header, text="Artículos guardados como favoritos",
                     font=Typography.body(), text_color=Colors.TEXT_SECONDARY, anchor="w").pack(side="left")
        ctk.CTkButton(fav_header, text="↻ Actualizar", width=110, height=28,
                      fg_color="transparent", border_width=1, border_color=Colors.BORDER,
                      text_color=Colors.TEXT_SECONDARY,
                      command=self._load_favoritos).pack(side="right")

        self.scroll_favoritos = ctk.CTkScrollableFrame(tab_favoritos, fg_color="transparent")
        self.scroll_favoritos.pack(fill="both", expand=True)

        # Cargar catálogo en segundo plano (página 0)
        self.run_in_thread(self._fetch_catalogo, ("", 0))
        self.tabs.configure(command=self._on_tab_change)

    # ── CATÁLOGO LEGAL ─────────────────────────────────────────────────────────

    def _on_filter_changed(self):
        # Debounce simple — reinicia paginación al cambiar el filtro
        if hasattr(self, "_filter_after_id"):
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(300, self._load_catalogo)

    def _load_catalogo(self, page=0):
        self._catalog_page = page
        filter_text = self.entry_filter_lib.get().strip()
        self.run_in_thread(self._fetch_catalogo, (filter_text, page))

    def _fetch_catalogo(self, filter_text="", page=0):
        try:
            conn = self.app.engine.db_manager.get_connection()
            cursor = conn.cursor()

            base = "FROM normas n"
            params_where = []
            where = ""
            if filter_text:
                where = " WHERE n.titulo LIKE ? OR n.numero LIKE ? OR n.tipo LIKE ?"
                p = f"%{filter_text}%"
                params_where = [p, p, p]

            # Contar total para mostrar paginación
            cursor.execute(f"SELECT COUNT(*) {base}{where}", params_where)
            total = cursor.fetchone()[0]

            offset = page * PAGE_SIZE_CATALOG
            query = (
                f"SELECT n.id, n.titulo, n.numero, n.tipo, n.archivo_pdf "
                f"{base}{where} ORDER BY n.titulo ASC LIMIT ? OFFSET ?"
            )
            cursor.execute(query, params_where + [PAGE_SIZE_CATALOG, offset])
            normas = cursor.fetchall()
            conn.close()
        except Exception:
            normas = []
            total = 0
        self.update_ui(self._render_catalogo, normas, total, page)

    def _render_catalogo(self, normas, total=0, page=0):
        for w in self.scroll_catalogo.winfo_children():
            w.destroy()

        self._catalog_total = total

        if not normas and total == 0:
            self.lbl_count_lib.configure(text="0 documentos")
            ctk.CTkLabel(
                self.scroll_catalogo,
                text="No se encontraron leyes en la base de datos.",
                font=Typography.body()
            ).pack(pady=40)
            return

        start = page * PAGE_SIZE_CATALOG + 1
        end = min(start + len(normas) - 1, total)
        self.lbl_count_lib.configure(text=f"{start}–{end} de {total} documentos")

        # Renderizar en lotes de 8 para no congelar la UI
        LOTE = 8
        listas = list(normas)

        def _render_lote(off):
            lote = listas[off:off + LOTE]
            for norma in lote:
                titulo   = norma['titulo']      if isinstance(norma, dict) else norma[1]
                numero   = norma['numero']      if isinstance(norma, dict) else norma[2]
                tipo     = norma['tipo']        if isinstance(norma, dict) else norma[3]
                pdf_path = norma['archivo_pdf'] if isinstance(norma, dict) else norma[4]
                decreto  = f"{tipo} {numero}".strip() if numero else (tipo or "")

                item = ctk.CTkFrame(
                    self.scroll_catalogo, corner_radius=8,
                    border_width=1, border_color=Colors.BORDER
                )
                item.pack(fill="x", pady=4, padx=5)

                info_col = ctk.CTkFrame(item, fg_color="transparent")
                info_col.pack(side="left", fill="x", expand=True, padx=15, pady=8)
                ctk.CTkLabel(info_col, text=titulo, font=Typography.bold(), anchor="w").pack(fill="x")
                if decreto:
                    ctk.CTkLabel(
                        info_col, text=decreto,
                        font=Typography.caption(), text_color=Colors.TEXT_SECONDARY, anchor="w"
                    ).pack(fill="x")

                if pdf_path:
                    ctk.CTkButton(
                        item, text="Abrir",
                        width=65, height=28,
                        fg_color=Colors.ACCENT_BLUE,
                        command=lambda p=pdf_path: self._abrir_documento(p)
                    ).pack(side="right", padx=15)

            if off + LOTE < len(listas):
                self.after(5, lambda: _render_lote(off + LOTE))
            else:
                # Botones de paginación al final
                self._render_pagination(page, total)

        _render_lote(0)

    def _render_pagination(self, page, total):
        """Agrega controles de paginación al final del scroll del catálogo."""
        total_pages = max(1, -(-total // PAGE_SIZE_CATALOG))  # ceil division
        if total_pages <= 1:
            return

        nav = ctk.CTkFrame(self.scroll_catalogo, fg_color="transparent")
        nav.pack(fill="x", pady=(8, 4))

        if page > 0:
            ctk.CTkButton(
                nav, text="← Anterior", width=110, height=30,
                fg_color="transparent", border_width=1, border_color=Colors.BORDER,
                text_color=Colors.TEXT_SECONDARY,
                command=lambda: self._load_catalogo(page - 1)
            ).pack(side="left", padx=(5, 0))

        ctk.CTkLabel(
            nav,
            text=f"Página {page + 1} de {total_pages}",
            font=Typography.caption(),
            text_color=Colors.TEXT_SECONDARY
        ).pack(side="left", expand=True)

        if (page + 1) < total_pages:
            ctk.CTkButton(
                nav, text="Siguiente →", width=110, height=30,
                fg_color=Colors.ACCENT_BLUE,
                command=lambda: self._load_catalogo(page + 1)
            ).pack(side="right", padx=(0, 5))

    def _on_tab_change(self):
        if self.tabs.get() == "★ Favoritos" and not self._favs_loaded:
            self._load_favoritos()

    # ── FAVORITOS ───────────────────────────────────────────────────────────────

    def _load_favoritos(self):
        self.run_in_thread(self._fetch_favoritos)

    def _fetch_favoritos(self):
        try:
            favs = self.app.engine.get_favorites()
        except Exception:
            favs = []
        self.update_ui(self._render_favoritos, favs)

    def _render_favoritos(self, favs):
        self._favs_loaded = True  # Marcar como cargado para no repetir la consulta
        for w in self.scroll_favoritos.winfo_children():
            w.destroy()

        if not favs:
            ctk.CTkLabel(
                self.scroll_favoritos,
                text="No tienes favoritos aún.\nMarca documentos con ★ desde el Buscador.",
                font=Typography.body(), text_color=Colors.TEXT_SECONDARY, justify="center"
            ).pack(pady=60)
            return

        for fav in favs:
            art_num   = fav.get("numero_articulo") or ""
            norma     = fav.get("norma_titulo") or "Documento desconocido"
            contenido = fav.get("contenido") or ""
            nota      = fav.get("nota") or ""
            pdf_path  = fav.get("archivo_pdf") or ""
            fav_id    = fav.get("id")
            art_id    = fav.get("articulo_id")

            card = ctk.CTkFrame(self.scroll_favoritos, corner_radius=8,
                                border_width=1, border_color=Colors.BORDER)
            card.pack(fill="x", pady=4, padx=5)

            # Encabezado de la tarjeta
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(10, 4))
            header_text = f"Art. {art_num} — {norma}" if art_num else norma
            ctk.CTkLabel(top, text=header_text,
                         font=Typography.bold(), anchor="w",
                         wraplength=900).pack(side="left", fill="x", expand=True)

            # Botones de acción
            btn_row = ctk.CTkFrame(top, fg_color="transparent")
            btn_row.pack(side="right")

            if pdf_path:
                ctk.CTkButton(btn_row, text="Abrir PDF", width=80, height=26,
                              fg_color=Colors.ACCENT_BLUE,
                              command=lambda p=pdf_path: self._abrir_documento(p)
                              ).pack(side="left", padx=(0, 4))

            ctk.CTkButton(btn_row, text="✕ Quitar", width=80, height=26,
                          fg_color="#c42b1c",
                          command=lambda aid=art_id: self._quitar_favorito(aid)
                          ).pack(side="left")

            # Extracto del contenido
            if contenido:
                extracto = contenido[:180] + ("…" if len(contenido) > 180 else "")
                ctk.CTkLabel(card, text=extracto, font=Typography.caption(),
                             text_color=Colors.TEXT_SECONDARY, anchor="w",
                             wraplength=680, justify="left"
                             ).pack(fill="x", padx=12, pady=(0, 6))

            # Nota personal editable
            nota_frame = ctk.CTkFrame(card, fg_color="transparent")
            nota_frame.pack(fill="x", padx=12, pady=(0, 10))
            ctk.CTkLabel(nota_frame, text="Nota:", font=Typography.caption(),
                         text_color=Colors.TEXT_SECONDARY).pack(side="left", padx=(0, 6))
            nota_entry = ctk.CTkEntry(nota_frame, placeholder_text="Escribe una nota…", height=28)
            nota_entry.insert(0, nota)
            nota_entry.pack(side="left", fill="x", expand=True)
            ctk.CTkButton(nota_frame, text="Guardar", width=70, height=28,
                          fg_color=Colors.PRIMARY,
                          command=lambda fid=fav_id, e=nota_entry: self._guardar_nota(fid, e.get())
                          ).pack(side="left", padx=(6, 0))

    def _quitar_favorito(self, article_id):
        try:
            self.app.engine.remove_favorite(article_id)
            self.show_toast("Favorito eliminado", "info")
            self._favs_loaded = False  # Forzar recarga en el siguiente acceso
            self._load_favoritos()
        except Exception as e:
            self.show_toast(f"Error: {e}", "error")

    def _guardar_nota(self, favorito_id, texto):
        try:
            self.app.engine.update_favorite_note(favorito_id, texto)
            self.show_toast("Nota guardada", "success")
        except Exception as e:
            self.show_toast(f"Error al guardar nota: {e}", "error")

    def _abrir_documento(self, filename):
        try:
            path = config.get_pdf_absolute_path(filename)
            if path and path.exists():
                os.startfile(str(path))
                return
        except Exception:
            pass
        from pathlib import Path
        direct_path = Path(filename)
        if direct_path.exists():
            os.startfile(str(direct_path))
        else:
            self.show_toast(f"Archivo no encontrado: {filename}", "error")

    def _sincronizar_biblioteca(self):
        self.btn_sync.configure(state="disabled", text=" Sincronizando...")
        self.show_toast("Iniciando sincronización de leyes...", "info")
        self.run_in_thread(self._sync_thread_logic)

    def _sync_thread_logic(self):
        try:
            from ..LEX_VIRIDIS_DB.import_pdfs import PDFImporter
            importer = PDFImporter(
                self.app.engine.db_manager.db_path,
                config.PDF_DIR
            )
            importer.run()
            self.update_ui(self._on_sync_complete)
        except Exception as e:
            self.update_ui(self.show_toast, f"Error en sincronización: {e}", "error")
        finally:
            self.update_ui(lambda: self.btn_sync.configure(state="normal", text=" Sincronizar"))

    def _on_sync_complete(self):
        self.show_toast("Sincronización completada", "success")
        self._load_catalogo()
        self.tabs.set("Catálogo Legal")

    # ── AGREGAR PDF INDIVIDUAL ──────────────────────────────────────────────────

    def _agregar_pdf(self):
        """Abre selector de archivo y muestra formulario de metadatos."""
        filepath = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("Archivos PDF", "*.pdf")],
            parent=self.winfo_toplevel()
        )
        if not filepath:
            return
        self._mostrar_dialogo_agregar(Path(filepath))

    def _mostrar_dialogo_agregar(self, pdf_path: Path):
        """Ventana modal para confirmar/editar metadatos del PDF."""
        from ..LEX_VIRIDIS_DB.import_pdfs import PDFImporter

        # Inferir metadatos iniciales desde el nombre del archivo
        _tmp_imp = PDFImporter.__new__(PDFImporter)
        tipo_inf, num_inf, titulo_inf, cat_inf = _tmp_imp.extract_metadata_from_filename(pdf_path.name)

        dialog = ctk.CTkToplevel(self.winfo_toplevel())
        dialog.title("Agregar Documento a la Biblioteca")
        dialog.geometry("500x420")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.focus()

        ctk.CTkLabel(dialog, text="Agregar nuevo documento legal",
                     font=Typography.get_font(16, "bold"),
                     text_color=Colors.PRIMARY).pack(pady=(20, 4))
        ctk.CTkLabel(dialog, text=f"Archivo: {pdf_path.name}",
                     font=Typography.caption(), text_color=Colors.TEXT_SECONDARY).pack()

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=30, pady=15)

        def _row(label, placeholder, default=""):
            ctk.CTkLabel(form, text=label, font=Typography.body(), anchor="w").pack(fill="x", pady=(8, 2))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=36)
            entry.insert(0, default)
            entry.pack(fill="x")
            return entry

        ent_titulo = _row("Título *", "Nombre completo de la ley o decreto", titulo_inf)
        ent_tipo   = _row("Tipo", "Ley / Decreto / Reglamento / Acuerdo", tipo_inf)
        ent_numero = _row("Número", "Ej: 104-1993", num_inf)

        status_lbl = ctk.CTkLabel(dialog, text="", font=Typography.caption())
        status_lbl.pack(pady=(4, 0))

        def _confirmar():
            titulo = ent_titulo.get().strip()
            if not titulo:
                status_lbl.configure(text="⚠ El título es obligatorio.", text_color="orange")
                return

            tipo   = ent_tipo.get().strip() or "Desconocido"
            numero = ent_numero.get().strip()

            btn_ok.configure(state="disabled", text="Importando...")
            status_lbl.configure(text="Copiando archivo...", text_color=Colors.TEXT_SECONDARY)
            dialog.update()

            def _do_import():
                try:
                    # 1. Copiar PDF al directorio de PDFs de la app
                    dest_dir = config.PDF_DIR
                    dest_path = dest_dir / pdf_path.name
                    if pdf_path.resolve() != dest_path.resolve():
                        shutil.copy2(str(pdf_path), str(dest_path))

                    # 2. Importar a la BD usando PDFImporter
                    importer = PDFImporter(
                        self.app.engine.db_manager.db_path,
                        dest_dir
                    )
                    importer.connect_db()

                    # Sobrescribir metadatos con los del formulario
                    importer.cursor.execute(
                        "SELECT id FROM normas WHERE titulo = ?", (titulo,)
                    )
                    existing = importer.cursor.fetchone()

                    import fitz
                    doc = fitz.open(str(dest_path))
                    full_text = "".join(p.get_text() + "\n" for p in doc)
                    doc.close()
                    clean = importer.clean_text(full_text)

                    rel_pdf = f"COMPENDIO LEYES FEMA/{dest_path.name}"
                    if existing:
                        norma_id = existing[0]
                        importer.cursor.execute("DELETE FROM articulos WHERE norma_id=?", (norma_id,))
                        importer.cursor.execute(
                            "UPDATE normas SET tipo=?, numero=?, texto_completo=?, archivo_pdf=? WHERE id=?",
                            (tipo, numero, clean, rel_pdf, norma_id)
                        )
                    else:
                        import re
                        categoria = "General"
                        lower = titulo.lower()
                        for k, v in [("forestal","Forestal"),("agua","Agua"),("penal","Penal"),("mina","Minería")]:
                            if k in lower:
                                categoria = v; break
                        importer.cursor.execute(
                            "INSERT INTO normas (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado)"
                            " VALUES (?,?,?,?,?,?,'VIGENTE')",
                            (tipo, numero, titulo, categoria, clean, rel_pdf)
                        )
                        norma_id = importer.cursor.lastrowid

                    articles = importer.extract_articles(full_text)
                    for num_art, content in articles:
                        importer.cursor.execute(
                            "INSERT INTO articulos (norma_id, numero_articulo, contenido) VALUES (?,?,?)",
                            (norma_id, num_art, content)
                        )

                    importer.close_db()

                    self.update_ui(_done)
                except Exception as e:
                    self.update_ui(_error, str(e))

            def _done():
                dialog.destroy()
                # Invalidar caché para que la nueva norma aparezca en búsquedas
                if self.app.engine and hasattr(self.app.engine, 'cache'):
                    self.app.engine.cache.invalidate()
                self.show_toast(f"'{titulo}' agregado correctamente", "success")
                self._load_catalogo()

            def _error(msg):
                btn_ok.configure(state="normal", text="Importar")
                status_lbl.configure(text=f"Error: {msg[:80]}", text_color="red")

            self.run_in_thread(_do_import)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Cancelar", width=110, height=36,
                      fg_color="gray", command=dialog.destroy).pack(side="left", padx=8)
        btn_ok = ctk.CTkButton(btn_frame, text="Importar", width=110, height=36,
                               fg_color=Colors.SUCCESS, command=_confirmar)
        btn_ok.pack(side="left", padx=8)
