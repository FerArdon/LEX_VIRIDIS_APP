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
                    UIComponents.primary_button("Agregar PDF", icon="add", on_click=lambda e: print("TODO: Implement Import")),
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
                    ft.IconButton("open_in_new", icon_color=Theme.PRIMARY, on_click=lambda e, n=norma: self.on_open_pdf(n)),
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
