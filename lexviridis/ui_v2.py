"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 FEMA Honduras. Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: ui_v2.py
"""
import logging
import threading
import time

import flet as ft

# App Core
from .app.dependencies import DependencyContainer
from .app.navigation import NavigationManager
from .config import config
from .design_system import Colors, Radius, Spacing, Theme, Typography, UIComponents, create_theme

# Utils
from .license_ui import LicenseActivationScreen, LicenseExpiredDialog, check_license_on_startup
from .license_validator import LicenseWatchdog
from .pdf_viewer_fixed import PDFViewerFixed
from .translations import i18n
from .views.ai_chat import AIChatView
from .views.article_detail import ArticleDetailView

# Views
from .views.dashboard import DashboardView
from .views.favorites import FavoritesView
from .views.library import LibraryView
from .views.search import SearchView
from .views.settings import SettingsView
from .views.study import StudyView


def _get_asset_path(filename: str) -> str:
    return str(config.RESOURCE_DIR / filename)

class LexViridisShell:
    """
    Refactored Main Application Shell.
    Orchestrates views, navigation, and global state (dependencies).
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()

        # 1. Initialize Dependencies
        self.deps = DependencyContainer(page)

        # 2. State
        self.current_user = None
        self.license_info = None
        self.license_watchdog = None

        # 3. Check License & Start
        self._check_license_and_start()

    def _setup_page(self):
        self.page.title = "LEX VIRIDIS | Compendio Legal Ambiental"
        self.page.theme = create_theme()
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = Theme.BACKGROUND
        self.page.padding = 0
        self.page.window_min_width = 900
        self.page.window_min_height = 650
        self.page.window_icon = _get_asset_path("LEXVIRIDIS_WHITE_BG.ico")
        self.page.window_maximized = True

    def _check_license_and_start(self):
        self.license_info = check_license_on_startup(self.page)

        if self.license_info and self.license_info.get("valid"):
            self._start_watchdog()
            self._show_login_ui()
            # Initialize backend in background
            threading.Thread(target=self._init_backend_async, daemon=True).start()
        elif self.license_info and self.license_info.get("expired"):
            LicenseExpiredDialog.show(self.page, on_renew=self._show_activation, on_exit=lambda: self.page.window_close())
        else:
            self._show_activation()

    def _start_watchdog(self):
        self.license_watchdog = LicenseWatchdog(
            self.page,
            on_invalid_callback=self._handle_license_invalidated
        )

    def _handle_license_invalidated(self, reason):
        # Callback safe para UI
        print(f"SECURITY ALERT: {reason}")
        # Intentar mostrar mensaje y cerrar
        # Nota: Acceder a UI desde thread puede requerir page.run_task si estuviera disponible, 
        # o simplemente usar page.open si Flet maneja concurrencia (lo hace parcialmente).
        # Para ser seguros, matamos la app tras un breve delay o log.
        logging.critical(f"License invalidated at runtime: {reason}")
        try:
             self.page.window_close()
        except:
            import os
            os._exit(1)

    def _show_activation(self):
        def on_success(lic_data):
            self.license_info = lic_data
            self._start_watchdog()
            self._show_login_ui()
            threading.Thread(target=self._init_backend_async, daemon=True).start()

        screen = LicenseActivationScreen(self.page, on_success)
        self.page.clean()
        self.page.add(screen.build())
        self.page.update()

    def _init_backend_async(self):
        try:
             self.deps.initialize()
             # Notify if running?
        except Exception as e:
            logging.error(f"Backend init error: {e}")

    def _show_login_ui(self):
        self.page.clean()
        self.page.window_maximized = False
        self.page.window_width, self.page.window_height = 450, 600
        self.page.update()

        user_field = ft.TextField(label="Usuario", prefix_icon="person", width=300)
        pass_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True, prefix_icon="lock", width=300,
                                 on_submit=lambda _: self._handle_login(user_field.value, pass_field.value))

        logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")

        login_card = ft.Container(
            content=ft.Column([
                ft.Container(content=ft.Image(src=str(logo_path), width=80, height=80, fit="contain"),
                             padding=10, bgcolor="#FFFFFF", border_radius=40, shadow=ft.BoxShadow(blur_radius=10, color=Colors.with_opacity(0.1, Colors.BLACK))),
                ft.Text("Inicia Sesión", size=Typography.TITLE, weight="bold"),
                ft.Text("Acceso exclusivo para personal autorizado", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.MD),
                user_field, pass_field,
                ft.Container(height=Spacing.SM),
                UIComponents.primary_button("Entrar", on_click=lambda _: self._handle_login(user_field.value, pass_field.value), width=300),
            ], horizontal_alignment="center", spacing=Spacing.SM),
            bgcolor=Theme.SURFACE, padding=Spacing.XL, border_radius=Radius.LG, border=ft.border.all(1, Theme.BORDER),
        )
        self.page.add(ft.Container(login_card, alignment=ft.Alignment(0, 0), expand=True))
        self.page.update()

    def _handle_login(self, user, pwd):
        # Wait for auth manager if not ready (simple poll)
        if not self.deps.auth_manager:
            self.page.open(ft.SnackBar(ft.Text("El sistema se está iniciando, intenta en unos segundos...")))
            return

        # Demo Admin creation
        try:
            self.deps.auth_manager.create_user("admin", "admin123", "admin@lexviridis.com", role="admin")
        except Exception:
            pass

        user_obj = self.deps.auth_manager.login(user, pwd)

        if user_obj:
            self.current_user = user_obj
            self._show_main_ui()
        else:
            self.page.open(ft.SnackBar(ft.Text("Credenciales incorrectas"), bgcolor=Theme.ERROR))

    def _show_main_ui(self):
        self.page.window_maximized = True
        self.page.clean()

        # Layout Components
        self.content_area = ft.Container(padding=Spacing.LG, bgcolor=Theme.BACKGROUND, expand=True)
        self.nav_manager = NavigationManager(self.page, self.content_area)

        # Register Routes / Views
        self.nav_manager.register_route(0, lambda: DashboardView(self.deps.get_stats_repository()))
        self.nav_manager.register_route(1, lambda: SearchView(self.deps.search_engine, self._open_pdf, self._open_article_detail))
        self.nav_manager.register_route(2, lambda: AIChatView(self.deps.gemini_client, self.deps.ai_assistant, self._open_article_detail))

        # 3: Favoritos
        self.nav_manager.register_route(3, lambda: FavoritesView(self.deps.search_engine, self._open_article_detail))

        # 4: Biblioteca
        self.nav_manager.register_route(4, lambda: LibraryView(self.deps.get_library_repository(), self._open_pdf))

        # 5: Estudio
        # Usar el current_user de LexViridisShell
        user_id = 1
        if self.current_user:
             user_id = self.current_user.get('id', 1)
        self.nav_manager.register_route(5, lambda: StudyView(self.deps.study_manager, user_id))
        self.nav_manager.register_route(6, lambda: SettingsView(self.deps, self._change_language))

        # Build Shell Layout
        self._build_shell_layout()

        # Initial View
        self.nav_manager.navigate_to(0)

    def _build_shell_layout(self):
        logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")

        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=90, min_extended_width=180, group_alignment=-0.9,
            leading=ft.Container(content=ft.Image(src=str(logo_path), width=80), padding=10),
            destinations=[
                ft.NavigationRailDestination(icon="dashboard", label=i18n.t("nav.dashboard")),
                ft.NavigationRailDestination(icon="search", label=i18n.t("nav.search")),
                ft.NavigationRailDestination(icon="auto_awesome", label=i18n.t("nav.ai_assistant")),
                ft.NavigationRailDestination(icon="star", label=i18n.t("nav.favorites")), # TODO
                ft.NavigationRailDestination(icon="library_books", label=i18n.t("nav.library")),
                ft.NavigationRailDestination(icon="school", label=i18n.t("nav.study")), # TODO
                ft.NavigationRailDestination(icon="settings", label=i18n.t("nav.settings")),
            ],
            on_change=lambda e: self.nav_manager.navigate_to(e.control.selected_index)
        )

        header = ft.Container(
            content=ft.Row([
                ft.Icon("person"),
                ft.Text(f" {self.current_user['username'].upper()}", weight="bold"),
                ft.Container(expand=True),
                ft.IconButton("logout", icon_color=Theme.ERROR, on_click=lambda _: self._show_login_ui())
            ]),
            padding=Spacing.SM, bgcolor=Theme.SURFACE, border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER))
        )

        layout = ft.Row([
            nav_rail,
            ft.VerticalDivider(width=1, color=Theme.BORDER),
            ft.Column([header, self.content_area], expand=True, spacing=0)
        ], expand=True)

        self.page.add(layout)

    # --- Global Callbacks ---
    def _open_pdf(self, article_or_norma):
        try:
            path_str = article_or_norma.get('archivo_pdf') or article_or_norma.get('file')

            from .utils import find_pdf_path
            resolved_path = find_pdf_path(path_str)

            if resolved_path and resolved_path.exists():
                PDFViewerFixed.open_pdf_simple(resolved_path)
            else:
                self.page.open(ft.SnackBar(ft.Text(f"PDF no encontrado: {path_str}"), bgcolor=Theme.ERROR))
                logging.warning(f"PDF not found: {path_str}")
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"Error abriendo PDF: {e}"), bgcolor=Theme.ERROR))

    def _open_article_detail(self, article, query=""):
        # Replace content area with detail view
        view = ArticleDetailView(article, query, on_close=lambda: self.nav_manager.navigate_to(1), on_open_pdf=self._open_pdf)
        self.content_area.content = view
        self.page.update()

    def _change_language(self, lang_code):
        i18n.set_language(lang_code)
        self.page.open(ft.SnackBar(ft.Text("Idioma cambiado"), bgcolor=Theme.SUCCESS))
        self._show_main_ui() # Re-render

def main(page: ft.Page):
    LexViridisShell(page)

if __name__ == "__main__":
    ft.app(target=main)
