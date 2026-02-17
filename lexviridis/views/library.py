import flet as ft

from ..design_system import Colors, Radius, Spacing, Theme, Typography, UIComponents
from ..services.library_repository import LibraryRepository


class LibraryView(ft.Container):
    """
    Library View Component.
    Displays the catalog of norms.
    """
    def __init__(self, library_repo: LibraryRepository, on_open_pdf: callable):
        super().__init__(expand=True)
        self.library_repo = library_repo
        self.on_open_pdf = on_open_pdf
        self.library_filter = "Todos"
        self.view_mode = "detail" # list, grid, detail
        self.page = None
        self._build_ui()

    def _build_ui(self):
        # Fetch data
        self.grupos = self.library_repo.get_norms_grouped_by_type()

        # Hero
        hero = UIComponents.hero_header(
            "hero_library.png",
            "Biblioteca Digital",
            "Explora el catálogo completo de la legislación ambiental hondureña"
        )

        # Toolbar & Filters
        toolbar = self._build_toolbar()
        filters = self._build_filters()

        # Content Area
        self.content_list = ft.Container(expand=True)
        self._render_list()

        # Layout
        self.content = ft.Column([
            hero,
            ft.Container(
                 content=ft.Row([
                    ft.Column([
                        UIComponents.heading("Biblioteca Digital", level=1, color=Theme.PRIMARY),
                         # TODO: Get total count from somewhere or calculate
                        UIComponents.body_text("Catálogo Completo", secondary=True),
                    ], expand=True),
                    UIComponents.primary_button("Agregar PDF", icon="add", on_click=self._show_import_dialog),
                ]),
                padding=ft.padding.only(bottom=Spacing.SM),
            ),
            toolbar,
            filters,
            ft.Container(self.content_list, expand=True, padding=ft.padding.only(top=Spacing.MD))
        ], expand=True)

    def _build_toolbar(self):
        return ft.Container(
            content=ft.Row([
                ft.TextButton("Nuevo", icon="add_circle_outline", style=ft.ButtonStyle(color="#CCCCCC")),
                ft.VerticalDivider(width=1, color="#555555"),
                ft.PopupMenuButton(
                    icon="sort",
                    items=[
                        ft.PopupMenuItem(text="Nombre (A-Z)"),
                        ft.PopupMenuItem(text="Nombre (Z-A)"),
                    ]
                ),
                ft.PopupMenuButton(
                    icon="view_list",
                    items=[
                        ft.PopupMenuItem(text="Lista compacta", on_click=lambda e: self._change_view_mode("list")),
                        ft.PopupMenuItem(text="Tarjetas", on_click=lambda e: self._change_view_mode("grid")),
                        ft.PopupMenuItem(text="Detalle", on_click=lambda e: self._change_view_mode("detail")),
                    ]
                ),
            ], spacing=4),
            bgcolor="#2D2D2D",
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=4),
            border_radius=ft.border_radius.only(top_left=Radius.SM, top_right=Radius.SM),
        )

    def _build_filters(self):
        # Build chips
        chips = [UIComponents.chip("Todos", selected=True, on_click=lambda e: self._filter("Todos"))]
        for tipo in sorted(self.grupos.keys()):
            chips.append(UIComponents.chip(tipo, on_click=lambda e, t=tipo: self._filter(t)))

        return ft.Row(chips, spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO)

    def _filter(self, tipo):
        self.library_filter = tipo
        self._render_list()
        self.update()

    def _change_view_mode(self, mode):
        self.view_mode = mode
        self._render_list()
        self.update()

    def _render_list(self):
        items_to_show = []
        if self.library_filter == "Todos":
            for _tipo, lista in sorted(self.grupos.items()):
                items_to_show.extend(lista)
        else:
            items_to_show = self.grupos.get(self.library_filter, [])

        # Select Renderer based on view_mode
        if self.view_mode == "grid":
            content = self._render_grid_view(items_to_show)
        elif self.view_mode == "list":
            content = self._render_compact_list(items_to_show)
        else:
            content = self._render_detail_list(items_to_show)

        self.content_list.content = content

    def _render_detail_list(self, items):
        lv = ft.ListView(expand=True, spacing=Spacing.SM)
        for norma in items:
            tipo = norma.get('tipo', '')
            icon = "description"
            color = Theme.TEXT_SECONDARY

            if 'Decreto' in tipo:
                icon = "gavel"; color = Theme.PRIMARY
            elif 'Ley' in tipo:
                icon = "balance"; color = Theme.SECONDARY
            elif 'Acuerdo' in tipo:
                icon = "assignment"; color = Theme.WARNING

            card = ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=24, color=color),
                        bgcolor=Colors.with_opacity(0.1, color),
                        border_radius=Radius.SM,
                        padding=Spacing.SM,
                    ),
                    ft.Container(width=Spacing.MD),
                    ft.Column([
                        ft.Text(norma.get('titulo', 'Sin título'), size=Typography.BODY, weight=Typography.MEDIUM, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row([
                            ft.Text(tipo, size=Typography.CAPTION, color=Theme.ACCENT),
                            ft.Text("•", size=Typography.CAPTION, color=Theme.TEXT_DISABLED),
                            ft.Text(f"{norma.get('num_articulos', 0)} artículos", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                        ], spacing=Spacing.SM),
                    ], expand=True, spacing=Spacing.XXS),
                    ft.IconButton("open_in_new", icon_color=Theme.PRIMARY,
                                  tooltip="Abrir PDF",
                                  on_click=lambda e, n=norma: self.on_open_pdf(n)),
                    ft.IconButton("delete", icon_color=Theme.ERROR,
                                  tooltip="Eliminar de la biblioteca",
                                  on_click=lambda e, n=norma: self._confirmar_eliminar_norma(n)),
                ]),
                bgcolor=Theme.SURFACE,
                border_radius=Radius.MD,
                padding=Spacing.MD,
                border=ft.border.all(1, Theme.BORDER),
                on_click=lambda e, n=norma: self.on_open_pdf(n),
            )
            lv.controls.append(card)
        return lv

    def _render_grid_view(self, items):
        grid = ft.GridView(expand=True, runs_count=5, max_extent=250, child_aspect_ratio=1.0, spacing=10, run_spacing=10)
        for norma in items:
            card = ft.Container(
                content=ft.Column([
                    ft.Icon("description", size=32, color=Theme.PRIMARY),
                    ft.Text(norma.get('titulo', ''), size=12, weight="bold", max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                bgcolor=Theme.SURFACE,
                border=ft.border.all(1, Theme.BORDER),
                border_radius=Radius.MD,
                padding=Spacing.MD,
                on_click=lambda e, n=norma: self.on_open_pdf(n)
            )
            grid.controls.append(card)
        return grid

    def _render_compact_list(self, items):
        lv = ft.ListView(expand=True, spacing=2)
        for norma in items:
            tile = ft.ListTile(
                leading=ft.Icon("article", size=20, color=Theme.PRIMARY),
                title=ft.Text(norma.get('titulo', ''), size=12, max_lines=1),
                on_click=lambda e, n=norma: self.on_open_pdf(n)
            )
            lv.controls.append(tile)
        return lv

    def _confirmar_eliminar_norma(self, norma):
        """Muestra diálogo de confirmación y elimina la norma + FTS si se acepta."""
        titulo = norma.get('titulo', 'Sin título')
        norma_id = norma.get('id')

        def _eliminar(e):
            try:
                import sqlite3 as _sqlite3
                from ..config import config
                DB_PATH = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
                conn = _sqlite3.connect(str(DB_PATH))
                cur  = conn.cursor()

                # 1. Eliminar del índice FTS
                cur.execute(
                    "DELETE FROM busqueda_fts WHERE articulo_id IN "
                    "(SELECT id FROM articulos WHERE norma_id = ?)", (norma_id,)
                )
                # 2. Eliminar artículos
                cur.execute("DELETE FROM articulos WHERE norma_id = ?", (norma_id,))
                # 3. Eliminar norma
                cur.execute("DELETE FROM normas WHERE id = ?", (norma_id,))
                conn.commit()
                conn.close()

                # 4. Cerrar diálogo y recargar lista
                dialog.open = False
                self.grupos = self.library_repo.get_norms_grouped_by_type()
                self._render_list()
                if self.page:
                    self.page.update()
                    sb = ft.SnackBar(
                        content=ft.Text(f"✅ '{titulo}' eliminado de la biblioteca"),
                        bgcolor=Theme.SUCCESS,
                    )
                    self.page.overlay.append(sb)
                    sb.open = True
                    self.page.update()

            except Exception as ex:
                dialog.open = False
                if self.page:
                    self.page.update()
                    sb = ft.SnackBar(
                        content=ft.Text(f"Error al eliminar: {ex}"),
                        bgcolor=ft.Colors.RED_400,
                    )
                    self.page.overlay.append(sb)
                    sb.open = True
                    self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon("warning", color=Theme.ERROR),
                ft.Text("Eliminar documento", weight="bold"),
            ]),
            content=ft.Text(
                f"¿Eliminar '{titulo}' de la biblioteca?\n\n"
                "Esto borrará la norma, todos sus artículos y su índice de búsqueda.\n"
                "El archivo PDF original NO será eliminado de tu disco.",
                size=13,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self._close_lib_dialog(dialog)),
                ft.ElevatedButton(
                    "Eliminar",
                    icon="delete",
                    on_click=_eliminar,
                    bgcolor=Theme.ERROR,
                    color="white",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _close_lib_dialog(self, dialog):
        dialog.open = False
        if self.page:
            self.page.update()

    def _show_import_dialog(self, e):
        """Muestra el diálogo de selección de archivo PDF"""
        # Obtener la página desde el evento o desde el árbol de controles
        page = None

        # Intentar desde el evento
        if hasattr(e, 'page') and e.page:
            page = e.page
        # Intentar desde el control
        elif hasattr(e, 'control') and hasattr(e.control, 'page') and e.control.page:
            page = e.control.page
        # Buscar en el árbol de padres
        else:
            current = self
            while page is None and hasattr(current, 'parent') and current.parent:
                if hasattr(current, 'page') and current.page:
                    page = current.page
                    break
                current = current.parent

        if page is None:
            print("Error: No se pudo obtener la página para mostrar el diálogo")
            return

        self.page = page

        # Crear FilePicker
        def on_file_selected(file_picker_result):
            if file_picker_result.files:
                selected_file = file_picker_result.files[0]
                self._import_pdf(selected_file.path)

        file_picker = ft.FilePicker(on_result=on_file_selected)
        self.page.overlay.append(file_picker)
        self.page.update()

        # Abrir diálogo de selección
        file_picker.pick_files(
            dialog_title="Seleccionar archivo PDF",
            allowed_extensions=["pdf"],
            allow_multiple=False
        )

    def _import_pdf(self, file_path: str):
        """
        Importa un PDF a la biblioteca:
          1. Extrae texto y artículos con PyMuPDF
          2. Inserta/actualiza la norma en la BD
          3. Actualiza el índice FTS5 para que sea buscable de inmediato
          4. Recarga la lista de la biblioteca
        """
        import threading
        from pathlib import Path as _Path

        pdf_path = _Path(file_path)

        # ── Diálogo de progreso ──────────────────────────────────────────
        progress_text = ft.Text("Iniciando...", size=13, color=Theme.TEXT_SECONDARY)
        progress_bar  = ft.ProgressBar(width=380, color=Theme.PRIMARY, bgcolor=Theme.BORDER)
        progress_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon("upload_file", color=Theme.PRIMARY),
                ft.Text("Importando PDF...", weight="bold"),
            ]),
            content=ft.Column([
                progress_bar,
                ft.Container(height=8),
                progress_text,
            ], tight=True, width=400),
        )
        if self.page:
            self.page.dialog = progress_dialog
            progress_dialog.open = True
            self.page.update()

        def _update(msg):
            progress_text.value = msg
            if self.page:
                self.page.update()

        def _extract_sections(text: str, clean_fn) -> list:
            """
            Extractor inteligente: detecta automáticamente la estructura
            del documento y devuelve lista de (numero, contenido).

            Estrategias en orden de prioridad:
              1. ARTÍCULO / Art. N  → leyes y decretos
              2. SECCIÓN / Sección N → reglamentos técnicos
              3. CAPÍTULO N          → documentos por capítulos
              4. N. TITULO en mayús  → planes y documentos técnicos
              5. Fallback: bloques de párrafos de 300+ chars
            """
            import re as _re

            # ── Estrategia 1: Artículos ──────────────────────────────────
            pat1 = r'(?:ART[ÍI]CULO|ARTICULO|Art\.)\s*' \
                   r'((?:\d+(?:-[A-Za-z])?)|(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO))' \
                   r'\s*[\.\:\-]?'
            matches = list(_re.finditer(pat1, text, _re.IGNORECASE))
            if len(matches) >= 2:
                result = []
                for i, m in enumerate(matches):
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    c = clean_fn(text[m.end():end].strip())
                    if c:
                        result.append((m.group(1).upper(), c))
                return result

            # ── Estrategia 2: Secciones ──────────────────────────────────
            pat2 = r'(?:SECCI[ÓO]N|Sección)\s+(\d+[\.\-]?\d*)\s*[\.\:\-]?'
            matches = list(_re.finditer(pat2, text, _re.IGNORECASE))
            if len(matches) >= 2:
                result = []
                for i, m in enumerate(matches):
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    c = clean_fn(text[m.end():end].strip())
                    if c:
                        result.append((f"Sección {m.group(1)}", c))
                return result

            # ── Estrategia 3: Capítulos ───────────────────────────────────
            pat3 = r'(?:CAP[ÍI]TULO|CAPITULO)\s+([IVXLCDM\d]+)\s*[\.\:\-]?'
            matches = list(_re.finditer(pat3, text, _re.IGNORECASE))
            if len(matches) >= 2:
                result = []
                for i, m in enumerate(matches):
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    c = clean_fn(text[m.end():end].strip())
                    if c:
                        result.append((f"Capítulo {m.group(1)}", c))
                return result

            # ── Estrategia 4: Secciones numeradas "1. TITULO" ────────────
            # Cubre planes, informes, manuales: "1.\nINTRODUCCION"
            # Exige título de al menos 8 chars para evitar listas cortas
            pat4 = r'(?m)^(\d{1,2})\.\s*\n?\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{7,60})$'
            matches = list(_re.finditer(pat4, text))
            # Solo usar si hay suficientes secciones reales (mínimo 5)
            if len(matches) >= 5:
                result = []
                for i, m in enumerate(matches):
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    c = clean_fn(text[m.end():end].strip())
                    label = f"{m.group(1)}. {m.group(2).strip()}"
                    if len(c) > 50:          # descartar secciones vacías o de lista
                        result.append((label, c))
                if len(result) >= 3:
                    return result

            # ── Estrategia 5: Subsecciones "1.1 Titulo" ──────────────────
            pat5 = r'(?m)^(\d+\.\d+)\s+([A-ZÁÉÍÓÚÑ][^\n]{3,80})$'
            matches = list(_re.finditer(pat5, text))
            if len(matches) >= 2:
                result = []
                for i, m in enumerate(matches):
                    end = matches[i+1].start() if i < len(matches)-1 else len(text)
                    c = clean_fn(text[m.end():end].strip())
                    label = f"{m.group(1)} {m.group(2).strip()}"
                    if c:
                        result.append((label, c))
                return result

            # ── Estrategia 6 (Fallback): Párrafos naturales ──────────────
            # Divide por líneas en blanco dobles (estructura real del PDF).
            # Garantiza que cualquier documento sea buscable en FTS.
            paragraphs = _re.split(r'\n\s*\n', text)
            blocks = []
            block_num = 1
            for para in paragraphs:
                c = clean_fn(para.strip())
                if len(c) > 80:   # ignorar párrafos muy cortos (cabeceras, números de página)
                    blocks.append((f"Párrafo {block_num}", c))
                    block_num += 1
            # Si aún así no hay nada, un único bloque con todo el texto
            if not blocks:
                blocks.append(("Texto completo", clean_fn(text)))
            return blocks

        def _run():
            try:
                import re
                import sqlite3 as _sqlite3
                from ..config import config

                DB_PATH = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

                # ── 1. Leer PDF ──────────────────────────────────────────
                _update("📄 Leyendo PDF...")
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(str(pdf_path))
                    full_text = ""
                    for pg in doc:
                        full_text += pg.get_text() + "\n"
                    doc.close()
                except ImportError:
                    _update("❌ PyMuPDF no instalado. Ejecuta: pip install pymupdf")
                    return

                if not full_text.strip():
                    _update("⚠️ El PDF no contiene texto seleccionable (imagen escaneada).\nNo se puede indexar sin OCR.")
                    if self.page:
                        import time; time.sleep(3)
                        progress_dialog.open = False
                        self.page.update()
                    return

                # ── 2. Limpiar texto ─────────────────────────────────────
                def clean_text(t):
                    t = re.sub(r'-\n', '', t)
                    t = re.sub(r'\s+', ' ', t).strip()
                    return t

                full_text_clean = clean_text(full_text)

                # ── 3. Inferir metadatos del nombre del archivo ──────────
                _update("🔍 Analizando metadatos...")
                filename  = pdf_path.name
                titulo    = filename.replace(".pdf", "").replace(".PDF", "")
                tipo      = "Desconocido"
                numero    = ""
                categoria = "General"
                lower     = filename.lower()

                if "decreto"    in lower: tipo = "Decreto"
                elif "ley"      in lower: tipo = "Ley"
                elif "acuerdo"  in lower: tipo = "Acuerdo"
                elif "reglamento" in lower: tipo = "Reglamento"

                if "forestal"   in lower: categoria = "Forestal"
                elif "agua"     in lower: categoria = "Agua"
                elif "penal"    in lower: categoria = "Penal"
                elif "mina"     in lower: categoria = "Minería"
                elif "ambiente" in lower: categoria = "Ambiente"

                num_match = re.search(r'(\d+-\d+)', filename)
                if num_match:
                    numero = num_match.group(1)

                # ── 4. Extraer secciones/artículos (detección automática) ──
                _update("📝 Detectando estructura del documento...")
                articles = _extract_sections(full_text, clean_text)

                # ── 5. Insertar/actualizar en la BD ──────────────────────
                _update(f"💾 Guardando norma ({len(articles)} artículos)...")
                conn = _sqlite3.connect(str(DB_PATH))
                cur  = conn.cursor()

                cur.execute("SELECT id FROM normas WHERE titulo = ?", (titulo,))
                row = cur.fetchone()

                if row:
                    norma_id = row[0]
                    cur.execute("DELETE FROM articulos WHERE norma_id = ?", (norma_id,))
                    cur.execute(
                        "UPDATE normas SET texto_completo=?, archivo_pdf=?, tipo=?, numero=?, categoria=? WHERE id=?",
                        (full_text_clean, str(pdf_path), tipo, numero, categoria, norma_id)
                    )
                else:
                    cur.execute(
                        "INSERT INTO normas (tipo, numero, titulo, categoria, texto_completo, archivo_pdf, estado) VALUES (?,?,?,?,?,?,'VIGENTE')",
                        (tipo, numero, titulo, categoria, full_text_clean, str(pdf_path))
                    )
                    norma_id = cur.lastrowid

                for art_num, content in articles:
                    cur.execute(
                        "INSERT INTO articulos (norma_id, numero_articulo, contenido) VALUES (?,?,?)",
                        (norma_id, art_num, content)
                    )

                conn.commit()

                # ── 6. Actualizar índice FTS5 ────────────────────────────
                _update("🔎 Actualizando índice de búsqueda (FTS5)...")

                # Eliminar entradas viejas de esta norma en FTS
                cur.execute(
                    "DELETE FROM busqueda_fts WHERE articulo_id IN (SELECT id FROM articulos WHERE norma_id=?)",
                    (norma_id,)
                )
                # Re-insertar los nuevos artículos en FTS
                cur.execute("""
                    INSERT INTO busqueda_fts(titulo_norma, contenido_articulo, numero_articulo, articulo_id)
                    SELECT n.titulo, a.contenido, a.numero_articulo, a.id
                    FROM articulos a
                    JOIN normas n ON a.norma_id = n.id
                    WHERE n.id = ?
                """, (norma_id,))
                conn.commit()
                conn.close()

                # ── 7. Recargar la biblioteca en la UI ───────────────────
                _update("✅ Listo. Actualizando biblioteca...")
                self.grupos = self.library_repo.get_norms_grouped_by_type()
                self._render_list()

                if self.page:
                    progress_dialog.open = False
                    self.page.update()

                    snackbar = ft.SnackBar(
                        content=ft.Text(
                            f"✅ '{titulo}' importado — {len(articles)} artículos indexados y listos para buscar"
                        ),
                        bgcolor=Theme.SUCCESS,
                        duration=5000,
                    )
                    self.page.overlay.append(snackbar)
                    snackbar.open = True
                    self.page.update()

            except Exception as ex:
                import traceback
                err = traceback.format_exc()
                _update(f"❌ Error: {ex}")
                if self.page:
                    import time; time.sleep(2)
                    progress_dialog.open = False
                    self.page.update()
                    snackbar = ft.SnackBar(
                        content=ft.Text(f"Error al importar: {ex}"),
                        bgcolor=ft.Colors.RED_400,
                    )
                    self.page.overlay.append(snackbar)
                    snackbar.open = True
                    self.page.update()

        # Ejecutar en hilo separado para no bloquear la UI
        threading.Thread(target=_run, daemon=True).start()
