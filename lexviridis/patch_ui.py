
import os

file_path = r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\lexviridis\ui_v2.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "def show_norms(e=None):" in line:
        start_idx = i
    if "async def _render_study_view(self):" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing lines {start_idx} to {end_idx}")
    
    new_code = """        # Inicializar componentes UI primero
        self.library_list = ft.ListView(expand=True, spacing=Spacing.SM, padding=ft.padding.only(top=Spacing.MD))
        self.library_filter = "Todos"
        
        # Lógica de renderizado de lista
        def render_list():
            self.library_list.controls.clear()
            items_to_show = []
            if self.library_filter == "Todos":
                for tipo, lista in sorted(grupos.items()):
                    items_to_show.extend(lista)
            else:
                items_to_show = grupos.get(self.library_filter, [])
            
            for norma in items_to_show:
                tipo = norma['tipo'] or ''
                if 'Decreto' in tipo:
                    icon = ft.icons.GAVEL
                    color = Theme.PRIMARY
                elif 'Ley' in tipo:
                    icon = ft.icons.BALANCE
                    color = Theme.SECONDARY
                elif 'Acuerdo' in tipo:
                    icon = ft.icons.ASSIGNMENT
                    color = Theme.WARNING
                else:
                    icon = ft.icons.DESCRIPTION
                    color = Theme.TEXT_SECONDARY
                
                card = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(icon, size=24, color=color),
                            bgcolor=ft.colors.with_opacity(0.1, color),
                            border_radius=Radius.SM,
                            padding=Spacing.SM,
                        ),
                        ft.Container(width=Spacing.MD),
                        ft.Column([
                            ft.Text(
                                norma['titulo'] or 'Sin título',
                                size=Typography.BODY,
                                weight=Typography.MEDIUM,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row([
                                ft.Text(tipo, size=Typography.CAPTION, color=Theme.ACCENT),
                                ft.Text("•", size=Typography.CAPTION, color=Theme.TEXT_DISABLED),
                                ft.Text(f"{norma['num_articulos']} artículos", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                            ], spacing=Spacing.SM),
                        ], expand=True, spacing=Spacing.XXS),
                        ft.IconButton(
                            ft.icons.OPEN_IN_NEW,
                            icon_color=Theme.PRIMARY,
                            icon_size=20,
                            tooltip="Abrir PDF",
                            on_click=lambda e, n=norma: self._open_library_pdf(n),
                        ),
                    ]),
                    bgcolor=Theme.SURFACE,
                    border_radius=Radius.MD,
                    padding=Spacing.MD,
                    border=ft.border.all(1, Theme.BORDER),
                    on_click=lambda e, n=norma: self._open_library_pdf(n),
                )
                self.library_list.controls.append(card)

        # Lógica de filtros
        def on_filter_change(tipo):
            self.library_filter = tipo
            render_list()
            self.page.update()

        filter_chips = ft.Row([
            UIComponents.chip("Todos", selected=True, on_click=lambda e: on_filter_change("Todos")),
        ] + [
            UIComponents.chip(tipo, on_click=lambda e, t=tipo: on_filter_change(t))
            for tipo in sorted(grupos.keys())
        ], spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO)

        # Contenido de Normas
        norms_content = ft.Column([
            ft.Container(
                content=ft.Column([
                    UIComponents.heading("Biblioteca Digital", level=1, color=Theme.PRIMARY),
                    UIComponents.body_text(f"{len(normas)} documentos en el compendio", secondary=True),
                ]),
                padding=ft.padding.only(bottom=Spacing.MD),
            ),
            filter_chips,
            ft.Container(self.library_list, expand=True, padding=ft.padding.only(top=Spacing.MD)),
        ], expand=True)

        # Contenedor para Bibliografía (se llena bajo demanda)
        bib_content = ft.Column(expand=True)

        # Contenedor dinámico de pestañas
        tab_content = ft.Container(content=norms_content, expand=True)

        # Definición de Tabs
        library_tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Normas del Compendio", icon=ft.icons.ACCOUNT_BALANCE),
                ft.Tab(text="Bibliografía Personal", icon=ft.icons.FORMAT_QUOTE),
            ],
            expand=False
        )

        def on_library_tab_change(e):
            if library_tabs.selected_index == 0:
                tab_content.content = norms_content
            else:
                # Generar Bibliografía
                cites = self.bibliography.generate_all(CitationStyle.APA)
                bib_list = ft.ListView(expand=True, spacing=Spacing.MD)
                if not cites:
                    bib_list.controls.append(UIComponents.empty_state(ft.icons.FORMAT_QUOTE, "Bibliografía vacía", "Agrega citas desde el detalle de cualquier artículo."))
                else:
                    for cite in cites:
                        bib_list.controls.append(ft.Container(
                            content=ft.Text(cite, size=12),
                            padding=Spacing.MD, bgcolor=Theme.SURFACE_VARIANT, border_radius=Radius.SM
                        ))
                
                bib_content.controls = [
                    ft.Row([
                        ft.Text("Mi Bibliografía Legal", weight="bold", size=18),
                        ft.Container(expand=True),
                        UIComponents.primary_button("Actualizar", icon=ft.icons.REFRESH, on_click=lambda _: on_library_tab_change(None)),
                    ]),
                    ft.Text("Estilo: APA 7ma Edición", size=10, color=Theme.TEXT_SECONDARY),
                    ft.Divider(),
                    bib_list
                ]
                tab_content.content = bib_content
            self.page.update()

        library_tabs.on_change = on_library_tab_change

        # Layout Final
        self.content_area.content = ft.Column([
            library_tabs,
            ft.Divider(height=1),
            tab_content
        ], expand=True)
        
        # Renderizado inicial
        render_list()
        self.page.update()

    """
    
    # We replace lines start_idx to end_idx (exclusive of end_idx, I want to insert BEFORE _render_study_view)
    # Actually end_idx is where _render_study_view starts.
    # We need to preserve _render_study_view.
    
    # Check indentation
    # Original lines have indentation. My new_code has indentation?
    # I copied it with 8 spaces indentation which matches the class method level.
    
    new_lines = lines[:start_idx] + [new_code] + lines[end_idx:]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("Sucessfully patched ui_v2.py")
else:
    print("Could not find start or end markers")
