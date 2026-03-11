"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 FEMA Honduras. Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: ui_v2.py
"""

import logging
import threading
from pathlib import Path

import flet as ft

# Monkey Patch para compatibilidad con versiones antiguas de Flet que no tienen page.open
if not hasattr(ft.Page, "open"):

    def _page_open_patch(self, control):
        if isinstance(control, ft.SnackBar):
            self.snack_bar = control
            control.open = True
            self.update()
        elif isinstance(control, ft.AlertDialog):
            self.dialog = control
            control.open = True
            self.update()
        else:
            logging.getLogger("LEX VIRIDIS").debug(f"page.open called with unsupported control: {type(control)}")

    ft.Page.open = _page_open_patch

# App Core
from .app.dependencies import DependencyContainer
from .app.navigation import NavigationManager
from .config import config
from .design_system import Colors, Radius, Spacing, Theme, create_theme

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
from .views.search_history import SearchHistoryView
from .views.settings import SettingsView


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

        # 2. Backend ready event for synchronization
        self.backend_ready = threading.Event()

        # 3. State
        self.current_user = None
        self.license_info = None
        self.license_watchdog = None

        # 4. Check License & Start
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
        logging.debug("Checking license on startup...")
        self.license_info = check_license_on_startup(self.page)
        logging.debug(f"License check result: {self.license_info}")

        if self.license_info and self.license_info.get("valid"):
            logging.debug("License valid. Starting watchdog and login UI...")
            self._start_watchdog()
            self._show_login_ui()
            # Initialize backend in background
            logging.debug("Starting backend init thread...")

            def _init_and_signal():
                self._init_backend_async()
                self.backend_ready.set()  # Señalizar que está listo
                logging.debug("Backend initialization completed and signaled")

            threading.Thread(target=_init_and_signal, daemon=True).start()
        elif self.license_info and self.license_info.get("expired"):
            logging.debug("License expired.")
            LicenseExpiredDialog.show(
                self.page, on_renew=self._show_activation, on_exit=lambda: self.page.window_close()
            )
        else:
            logging.debug("No valid license. Showing activation screen.")
            self._show_activation()

    def _start_watchdog(self):
        self.license_watchdog = LicenseWatchdog(self.page, on_invalid_callback=self._handle_license_invalidated)

    def _handle_license_invalidated(self, reason):
        # Callback safe para UI
        logging.warning(f"SECURITY ALERT: {reason}")
        logging.critical(f"License invalidated at runtime: {reason}")
        try:
            self.page.window_close()
        except Exception:
            import os

            os._exit(1)

    def _show_activation(self):
        def on_success(lic_data):
            self.license_info = lic_data
            self._start_watchdog()
            self._show_login_ui()

            def _init_and_signal():
                self._init_backend_async()
                self.backend_ready.set()

            threading.Thread(target=_init_and_signal, daemon=True).start()

        screen = LicenseActivationScreen(self.page, on_success)
        self.page.clean()
        self.page.add(screen.build())
        self.page.update()

    def _init_backend_async(self):
        try:
            self.deps.initialize()
            # Asegurar que existe el usuario admin por defecto
            try:
                self.deps.auth_manager.create_user("admin", "admin123", "admin@lexviridis.com", role="admin")
            except Exception:
                pass  # El usuario ya existe
        except Exception as e:
            logging.error(f"Backend init error: {e}")

    def _show_login_ui(self):
        try:
            logging.debug("_show_login_ui started")
            self.page.clean()
            self.page.window_maximized = False
            self.page.window_width, self.page.window_height = 500, 650
            self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
            self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
            self.page.update()
            logging.debug("Page cleaned and resized")

            # Logo
            logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")
            logo = ft.Image(src=str(logo_path), width=120, height=120, fit="contain")

            user_field = ft.TextField(
                label="Usuario", prefix_icon="person", width=350, border_radius=Radius.MD, text_size=14
            )
            pass_field = ft.TextField(
                label="Contraseña",
                password=True,
                can_reveal_password=True,
                prefix_icon="lock",
                width=350,
                border_radius=Radius.MD,
                text_size=14,
                on_submit=lambda _: self._handle_login(user_field.value, pass_field.value),
            )

            # Login card with professional design
            login_card = ft.Container(
                content=ft.Column(
                    [
                        # Logo section
                        ft.Container(content=logo, padding=ft.padding.only(bottom=10)),
                        # Title
                        ft.Text("LEX VIRIDIS", size=28, weight="bold", color=Theme.PRIMARY, text_align="center"),
                        ft.Text("Compendio Legal Ambiental", size=14, color=Theme.TEXT_SECONDARY, text_align="center"),
                        ft.Container(height=20),
                        ft.Divider(height=1, color=Theme.BORDER),
                        ft.Container(height=20),
                        # Login fields
                        ft.Text("Iniciar Sesión", size=18, weight="bold", color=Theme.TEXT_PRIMARY),
                        ft.Container(height=10),
                        user_field,
                        ft.Container(height=15),
                        pass_field,
                        ft.Container(height=25),
                        # Login button
                        ft.ElevatedButton(
                            "Entrar",
                            width=350,
                            height=45,
                            style=ft.ButtonStyle(
                                bgcolor=Theme.PRIMARY, color="white", shape=ft.RoundedRectangleBorder(radius=Radius.MD)
                            ),
                            on_click=lambda _: self._handle_login(user_field.value, pass_field.value),
                        ),
                        ft.Container(height=20),
                        # Footer
                        ft.Text("FEMA Honduras © 2026", size=12, color=Theme.TEXT_SECONDARY, text_align="center"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                bgcolor=Theme.SURFACE,
                padding=40,
                border_radius=Radius.LG,
                shadow=ft.BoxShadow(blur_radius=20, spread_radius=2, color=Colors.with_opacity(0.1, Colors.BLACK)),
                width=450,
            )

            logging.debug("Adding centered login_card to page")
            # Center the login card both horizontally and vertically
            self.page.add(ft.Container(content=login_card, alignment=ft.alignment.center, expand=True))
            self.page.update()
            logging.debug("_show_login_ui completed")
        except Exception as e:
            logging.error(f"Error in _show_login_ui: {e}", exc_info=True)

    def _handle_login(self, user, pwd):
        self._show_toast("El sistema se está iniciando, intenta en unos segundos...")

        user_obj = self.deps.auth_manager.login(user, pwd)

        if user_obj:
            self.current_user = user_obj
            self._show_main_ui()
        else:
            self._show_toast("Credenciales incorrectas", bgcolor=Theme.ERROR)

    def _show_main_ui(self):
        # Esperar a que el backend esté listo (timeout 10 segundos)
        logging.debug("Waiting for backend to be ready...")
        if not self.backend_ready.wait(timeout=10):
            logging.error("Backend initialization timeout")
            self._show_toast("Error: El sistema no pudo inicializarse. Reinicie la aplicación.", bgcolor=Theme.ERROR)
            return

        logging.debug("Backend ready, building main UI...")
        self.page.window_maximized = True
        self.page.clean()

        # Layout Components
        self.content_area = ft.Container(padding=Spacing.LG, bgcolor=Theme.BACKGROUND, expand=True)
        self.nav_manager = NavigationManager(self.page, self.content_area)

        # Register Routes / Views
        self.nav_manager.register_route(0, lambda: DashboardView(self.deps.get_stats_repository()))
        self.nav_manager.register_route(
            1, lambda: SearchView(self.deps.search_engine, self._open_pdf, self._open_article_detail)
        )
        self.nav_manager.register_route(
            2, lambda: AIChatView(self.deps.gemini_client, self.deps.ai_assistant, self._open_article_detail)
        )

        # 3: Favoritos
        self.nav_manager.register_route(3, lambda: FavoritesView(self.deps.search_engine, self._open_article_detail))

        # 4: Casos y Expedientes
        from .views.casos import CasosView

        self.nav_manager.register_route(4, lambda: CasosView(self.deps.casos_repo, self._open_caso_detail, self.page))

        # 5: Biblioteca
        self.nav_manager.register_route(5, lambda: LibraryView(self.deps.get_library_repository(), self._open_pdf))

        # 6: Historial de Búsquedas
        self.nav_manager.register_route(
            6, lambda: SearchHistoryView(self.deps.search_engine, self._repeat_search_from_history)
        )

        # 7: Configuración
        self.nav_manager.register_route(7, lambda: SettingsView(self.deps, self._change_language))

        # Build Shell Layout
        self._build_shell_layout()

        # Initial View
        self.nav_manager.navigate_to(0)

    def _build_shell_layout(self):
        logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")

        nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=90,
            min_extended_width=180,
            group_alignment=-0.9,
            leading=ft.Container(content=ft.Image(src=str(logo_path), width=80), padding=10),
            destinations=[
                ft.NavigationRailDestination(icon="dashboard", label=i18n.t("nav.dashboard")),
                ft.NavigationRailDestination(icon="search", label=i18n.t("nav.search")),
                ft.NavigationRailDestination(icon="auto_awesome", label=i18n.t("nav.ai_assistant")),
                ft.NavigationRailDestination(icon="star", label=i18n.t("nav.favorites")),
                ft.NavigationRailDestination(icon="folder_special", label="Casos"),
                ft.NavigationRailDestination(icon="library_books", label=i18n.t("nav.library")),
                ft.NavigationRailDestination(icon="history", label="Historial"),
                ft.NavigationRailDestination(icon="settings", label=i18n.t("nav.settings")),
            ],
            on_change=lambda e: self.nav_manager.navigate_to(e.control.selected_index),
        )

        # Profile picture or default icon
        profile_pic = self.current_user.get("profile_picture")
        if profile_pic and Path(profile_pic).exists():
            avatar = ft.CircleAvatar(
                foreground_image_src=str(profile_pic), radius=18, content=ft.Icon("person", size=20)
            )
        else:
            avatar = ft.CircleAvatar(
                bgcolor=Theme.PRIMARY, radius=18, content=ft.Icon("person", size=20, color="white")
            )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=avatar,
                        on_click=lambda _: self._show_profile_dialog(),
                        tooltip="Click para cambiar foto de perfil",
                    ),
                    ft.Text(f" {self.current_user['username'].upper()}", weight="bold"),
                    ft.Container(expand=True),
                    ft.IconButton("logout", icon_color=Theme.ERROR, on_click=lambda _: self._show_login_ui()),
                ]
            ),
            padding=Spacing.SM,
            bgcolor=Theme.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER)),
        )

        layout = ft.Row(
            [
                nav_rail,
                ft.VerticalDivider(width=1, color=Theme.BORDER),
                ft.Column([header, self.content_area], expand=True, spacing=0),
            ],
            expand=True,
        )

        self.page.add(layout)

    # --- Global Callbacks ---
    def _open_pdf(self, article_or_norma):
        try:
            path_str = article_or_norma.get("archivo_pdf") or article_or_norma.get("file")

            from .pdf_viewer_fixed import open_pdf_with_highlight_fixed
            from .utils import find_pdf_path

            resolved_path = find_pdf_path(path_str)

            if resolved_path and resolved_path.exists():
                # Obtener término de búsqueda y página si existen
                search_term = article_or_norma.get("term", "")
                page_number = article_or_norma.get("page", 1) or article_or_norma.get("pagina", 1)

                # Si hay término de búsqueda, abrir con resaltado
                if search_term:
                    logging.info(
                        f"Abriendo PDF con resaltado: {resolved_path}, página {page_number}, término '{search_term}'"
                    )
                    open_pdf_with_highlight_fixed(resolved_path, page_number, search_term)
                else:
                    # Sin término de búsqueda, abrir simple
                    PDFViewerFixed.open_pdf_simple(resolved_path, page_number)
            else:
                self._show_toast(f"PDF no encontrado: {path_str}", bgcolor=Theme.ERROR)
                logging.warning(f"PDF not found: {path_str}")
        except Exception as e:
            self._show_toast(f"Error abriendo PDF: {e}", bgcolor=Theme.ERROR)
            logging.error(f"Error opening PDF: {e}", exc_info=True)

    def _open_article_detail(self, article, query=""):
        # Replace content area with detail view
        view = ArticleDetailView(
            article, query, on_close=lambda: self.nav_manager.navigate_to(1), on_open_pdf=self._open_pdf
        )
        self.content_area.content = view
        self.page.update()

    def _open_caso_detail(self, caso):
        """Abre la vista de detalle de un caso."""
        from .views.caso_detail import CasoDetailView

        view = CasoDetailView(
            caso, self.deps.casos_repo, on_close=lambda: self.nav_manager.navigate_to(4), on_open_pdf=self._open_pdf
        )
        self.content_area.content = view
        self.page.update()

    def _change_language(self, lang_code):
        i18n.set_language(lang_code)
        self._show_toast("Idioma cambiado", bgcolor=Theme.SUCCESS)
        self._show_main_ui()  # Re-render

    def _repeat_search_from_history(self, query):
        """Repite una búsqueda desde el historial navegando a la vista de búsqueda."""
        # Navegar a la vista de búsqueda
        self.nav_manager.navigate_to(1)
        # La búsqueda se ejecutará automáticamente en la vista de búsqueda
        # si implementamos un mecanismo de pre-fill
        self._show_toast(f"Buscar: {query}", bgcolor=Theme.INFO)

    def _show_profile_dialog(self):
        """Muestra un diálogo para cambiar la foto de perfil."""
        file_picker = ft.FilePicker(on_result=self._on_profile_picture_selected)
        self.page.overlay.append(file_picker)
        self.page.update()

        def pick_file(e):
            file_picker.pick_files(
                dialog_title="Seleccionar foto de perfil",
                allowed_extensions=["png", "jpg", "jpeg", "gif"],
                allow_multiple=False,
            )

        def remove_picture(e):
            """Elimina la foto de perfil actual."""
            try:
                self.deps.auth_manager.update_profile_picture(self.current_user["id"], None)
                self.current_user["profile_picture"] = None
                self._show_toast("✓ Foto de perfil eliminada", bgcolor=Theme.SUCCESS)
                dialog.open = False
                self.page.update()
                self._show_main_ui()  # Refresh UI
            except Exception as ex:
                self._show_toast(f"Error: {ex}", bgcolor=Theme.ERROR)

        # Get current profile picture
        current_pic = self.current_user.get("profile_picture")
        if current_pic and Path(current_pic).exists():
            current_avatar = ft.CircleAvatar(
                foreground_image_src=str(current_pic), radius=50, content=ft.Icon("person", size=40)
            )
        else:
            current_avatar = ft.CircleAvatar(
                bgcolor=Theme.PRIMARY, radius=50, content=ft.Icon("person", size=40, color="white")
            )

        # Build actions list
        actions = [
            ft.TextButton("Seleccionar imagen", on_click=pick_file),
        ]
        if current_pic:
            actions.append(ft.TextButton("Eliminar foto", on_click=remove_picture))
        actions.append(ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog(dialog)))

        dialog = ft.AlertDialog(
            title=ft.Text("Foto de Perfil"),
            content=ft.Column(
                [
                    ft.Container(content=current_avatar, alignment=ft.alignment.center),
                    ft.Container(height=Spacing.MD),
                    ft.Text(
                        "Selecciona una imagen (PNG, JPG, JPEG, GIF)",
                        size=12,
                        color=Theme.TEXT_SECONDARY,
                        text_align="center",
                    ),
                ],
                tight=True,
                horizontal_alignment="center",
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_profile_picture_selected(self, e):
        """Maneja la selección de la foto de perfil."""
        if not e.files:
            return

        try:
            source_path = Path(e.files[0].path)

            # Create profile pictures directory
            profile_dir = Path.home() / "Documents" / "LEX_VIRIDIS" / "ProfilePictures"
            profile_dir.mkdir(parents=True, exist_ok=True)

            # Copy image to profile directory
            dest_path = profile_dir / f"user_{self.current_user['id']}_{source_path.name}"

            import shutil

            shutil.copy2(source_path, dest_path)

            # Update database
            self.deps.auth_manager.update_profile_picture(self.current_user["id"], str(dest_path))
            self.current_user["profile_picture"] = str(dest_path)

            self._show_toast("✓ Foto de perfil actualizada", bgcolor=Theme.SUCCESS)

            # Refresh UI
            self._show_main_ui()

        except Exception as ex:
            logging.error(f"Error actualizando foto de perfil: {ex}")
            self._show_toast(f"Error: {ex}", bgcolor=Theme.ERROR)

    def _show_toast(self, msg: str, bgcolor=None):
        """Muestra un SnackBar de notificación."""
        self.page.open(ft.SnackBar(ft.Text(msg), bgcolor=bgcolor))

    def _close_dialog(self, dialog):
        """Cierra un diálogo."""
        dialog.open = False
        self.page.update()


def main(page: ft.Page):
    LexViridisShell(page)


if __name__ == "__main__":
    ft.app(target=main)
