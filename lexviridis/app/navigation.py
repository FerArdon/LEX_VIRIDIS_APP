from collections.abc import Callable

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
            # Execute the factory to get/render the view
            view_content = self.routes[index]()

            # Update content area
            self.content_area.content = view_content
            self.page.update()
        else:
            print(f"Route {index} not registered.")
