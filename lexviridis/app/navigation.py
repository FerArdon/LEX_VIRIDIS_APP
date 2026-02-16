from collections.abc import Callable
import logging

import flet as ft


class NavigationManager:
    """
    Handles navigation logic and view switching (Strategy Pattern).
    """
    def __init__(self, page: ft.Page, content_area: ft.Container):
        self.page = page
        self.content_area = content_area
        self.routes: dict[int, Callable] = {}
        self.current_index = 0

    def register_route(self, index: int, view_factory: Callable):
        """
        Registers a route index with a factory function that returns the view.
        """
        self.routes[index] = view_factory

    def navigate_to(self, index: int):
        """
        Switches the content area to the view for the given index.
        """
        if index in self.routes:
            self.current_index = index
            try:
                # Execute the factory to get/render the view
                view_content = self.routes[index]()

                # Verificar que la vista no sea None
                if view_content is None:
                    logging.warning(f"Vista {index} retornó None")
                    view_content = ft.Container(
                        content=ft.Column([
                            ft.Icon("error_outline", size=48, color="#999999"),
                            ft.Text("Vista no disponible", size=18, color="#999999")
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment="center"),
                        alignment=ft.alignment.center,
                        expand=True
                    )

                # Update content area
                self.content_area.content = view_content
                self.page.update()

            except Exception as e:
                logging.error(f"Error al navegar a vista {index}: {e}", exc_info=True)
                # Mostrar vista de error
                self.content_area.content = ft.Container(
                    content=ft.Column([
                        ft.Icon("error", size=48, color="#FF5252"),
                        ft.Text("Error al cargar la vista", size=18, color="#FF5252", weight="bold"),
                        ft.Text(f"{str(e)[:100]}", size=14, color="#FF5252", text_align="center")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment="center", spacing=10),
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=20
                )
                self.page.update()
        else:
            print(f"Route {index} not registered.")
