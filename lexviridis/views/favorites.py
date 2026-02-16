import flet as ft

from ..design_system import Colors, Radius, Spacing, Theme, UIComponents
from ..search_engine import SearchEngine


class FavoritesView(ft.Container):
    """
    Vista de Favoritos.
    Muestra lista de artículos guardados y permite gestionar notas y tags.
    """
    def __init__(self, search_engine: SearchEngine, on_open_article=None):
        super().__init__(expand=True)
        self.engine = search_engine
        self.on_open_article = on_open_article
        self._build_ui()

    def _build_ui(self):
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_favorites.png",
            "Mis Favoritos",
            "Tus documentos y artículos guardados para consulta rápida"
        )

        favorites = self.engine.get_favorites()

        if not favorites:
            self.content = ft.Column([
                hero,
                UIComponents.empty_state(
                    "star_outline",
                    "Sin favoritos",
                    "Aún no has guardado ningún artículo. Haz clic en la estrella al ver un artículo para guardarlo.",
                )
            ], expand=True)
            return

        fav_list = ft.ListView(expand=True, spacing=Spacing.SM)
        for fav in favorites:
            tags = self.engine.get_favorite_tags(fav['id'])
            tags_row = ft.Row([ft.Container(ft.Text(t, size=9), bgcolor=Colors.with_opacity(0.1, Theme.PRIMARY), padding=2, border_radius=4) for t in tags], spacing=4)

            card = ft.Container(
                content=ft.Row([
                    ft.Icon("star", color=Theme.ACCENT),
                    ft.Column([
                        ft.Row([
                            ft.Text(f"Artículo {fav['numero_articulo']}", weight="bold"),
                            ft.Container(width=Spacing.SM),
                            tags_row,
                        ]),
                        ft.Text(fav['norma_titulo'], size=12, color=Theme.TEXT_SECONDARY, max_lines=1),
                        ft.Text(fav['nota'] or "Sin notas personales", size=11, italic=True, color=Theme.PRIMARY_LIGHT if fav['nota'] else Theme.TEXT_DISABLED),
                    ], expand=True, spacing=0),
                    ft.IconButton("label_outlined", tooltip="Agregar Tag", on_click=lambda e, f=fav: self._add_fav_tag(f)),
                    ft.IconButton("edit", tooltip="Editar Nota", on_click=lambda e, f=fav: self._edit_fav_note(f)),
                    ft.IconButton("open_in_new", tooltip="Ver Artículo", on_click=lambda e, f=fav: self._open_article(f)),
                ]),
                padding=Spacing.MD,
                bgcolor=Theme.SURFACE,
                border_radius=Radius.MD,
                border=ft.border.all(1, Theme.BORDER),
                on_click=lambda e, f=fav: self._open_article(f),
            )
            fav_list.controls.append(card)

        self.content = ft.Column([
            hero,
            UIComponents.heading("Mis Favoritos", level=1, color=Theme.PRIMARY),
            ft.Text(f"{len(favorites)} artículos guardados", size=12, color=Theme.TEXT_SECONDARY),
            ft.Divider(),
            fav_list
        ], expand=True)

    def _open_article(self, fav):
        if self.on_open_article:
            # Adaptar dict de favorito al formato esperado por article_detail si es necesario
            # get_favorites devuelve dicts compatibles con keys: id, numero_articulo, norma_titulo, contenido, pagina, file
            self.on_open_article(fav)

    def _add_fav_tag(self, fav: dict):
        """Diálogo para agregar un tag a un favorito."""
        tag_field = ft.TextField(label="Nuevo Tag", hint_text="ej. Penal, Forestal, Urgente")

        def save_tag(e):
            if tag_field.value:
                self.engine.add_favorite_tag(fav['id'], tag_field.value)
                dlg.open = False
                self._build_ui() # Recargar
                self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Agregar Etiqueta"),
            content=tag_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("Agregar", on_click=save_tag),
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _edit_fav_note(self, fav: dict):
        """Diálogo para editar la nota de un favorito."""
        note_field = ft.TextField(
            label="Nota personal",
            multiline=True,
            value=fav['nota'] or "",
            hint_text="Escribe algo sobre este artículo...",
        )

        def save_note(e):
            self.engine.update_favorite_note(fav['id'], note_field.value)
            dlg.open = False
            self._build_ui() # Recargar
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Nota"),
            content=note_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("Guardar", on_click=save_note),
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()
