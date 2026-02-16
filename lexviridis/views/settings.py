import flet as ft

from ..app.dependencies import DependencyContainer
from ..design_system import Spacing, Theme, Typography, UIComponents
from ..translations import i18n


class SettingsView(ft.Container):
    """
    Settings View Component.
    Handles configuration, backups, security, and cloud sync.
    """
    def __init__(self, deps: DependencyContainer, on_change_language: callable):
        super().__init__(expand=True)
        self.deps = deps
        self.on_change_language = on_change_language
        self._build_ui()

    def _build_ui(self):
        # Hero
        hero = UIComponents.hero_header(
            "hero_settings.png",
            "Configuración",
            "Gestiona tu cuenta, copias de seguridad y preferencias del sistema"
        )

        # Tabs
        settings_tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab("Interfaz y Temas", icon="palette", content=self._build_theme_tab()),
                ft.Tab("Seguridad", icon="security", content=self._build_security_tab()),
                ft.Tab("Localización y Nube", icon="language", content=self._build_cloud_tab()),
                ft.Tab("Base de Datos y Backups", content=self._build_backup_tab()),
            ],
            expand=True,
        )

        self.content = ft.Column([
            hero,
            UIComponents.heading("Ajustes del Sistema", level=1, color=Theme.PRIMARY),
            settings_tabs
        ], expand=True, scroll=ft.ScrollMode.ALWAYS)

    def _build_theme_tab(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("Tema de la Aplicación", weight="bold"),
                ft.Row([
                    ft.ElevatedButton("Modo Claro", icon="light_mode", on_click=lambda _: self.deps.theme_manager.set_theme("light")),
                    ft.ElevatedButton("Modo Oscuro", icon="dark_mode", on_click=lambda _: self.deps.theme_manager.set_theme("dark")),
                ]),
                ft.Divider(),
                ft.Text("Accesibilidad", weight="bold"),
                ft.Switch(label="Alto Contraste", on_change=lambda e: self.deps.accessibility.toggle_high_contrast(e.control.value)),
                ft.Switch(label="Texto Grande", on_change=lambda e: self.deps.accessibility.toggle_large_text(e.control.value)),
                ft.Divider(),
                UIComponents.primary_button(i18n.t("common.save")),
            ], spacing=Spacing.MD),
            padding=Spacing.LG,
        )

    def _build_security_tab(self):
        current_pwd = ft.TextField(label="Contraseña Actual", password=True, can_reveal_password=True)
        new_pwd = ft.TextField(label="Nueva Contraseña", password=True, can_reveal_password=True)
        confirm_pwd = ft.TextField(label="Confirmar Nueva Contraseña", password=True, can_reveal_password=True)

        return ft.Container(
            content=ft.Column([
                ft.Text("Gestión de Cuenta", weight="bold"),
                ft.Divider(),
                current_pwd, new_pwd, confirm_pwd,
                ft.Container(height=Spacing.SM),
                UIComponents.primary_button("Actualizar Contraseña", on_click=lambda _: print("TODO: Implementar cambio pwd")),
            ], spacing=Spacing.MD),
            padding=Spacing.LG,
        )

    def _build_cloud_tab(self):
        return ft.Container(
            content=ft.Column([
                ft.Text(i18n.t("settings.language"), weight="bold"),
                ft.Row([
                    ft.ElevatedButton("ES - Español", icon="language", on_click=lambda _: self.on_change_language("es")),
                    ft.ElevatedButton("EN - English", icon="language", on_click=lambda _: self.on_change_language("en")),
                ]),
                ft.Divider(),
                ft.Text(i18n.t("settings.cloud"), weight="bold"),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon("cloud_sync", color=Theme.PRIMARY),
                                ft.Column([
                                    ft.Text("Google Drive Sync", weight="bold"),
                                    ft.Text(f"Estado: {self.deps.cloud_sync.get_status().upper()}", size=12),
                                ], expand=True),
                                ft.ElevatedButton("Conectar", on_click=lambda _: print("TODO: Connect Cloud")),
                            ])
                        ]), padding=Spacing.MD
                    )
                ),
                ft.Switch(label="Sincronización Automática", value=True),
                UIComponents.primary_button("Sincronizar Ahora", icon="sync", on_click=lambda _: print("TODO: Sync Now")),
            ], spacing=Spacing.MD),
            padding=Spacing.LG,
        )

    def _build_backup_tab(self):
        return ft.Container(
             content=ft.Column([
                ft.Row([
                    ft.Column([
                        ft.Text("Gestión de Copias de Seguridad", size=Typography.TITLE, weight="bold"),
                        ft.Text("Los backups automáticos se realizan diariamente a las 02:00 AM.", size=Typography.CAPTION),
                    ], expand=True),
                    UIComponents.primary_button("Crear Backup Ahora", icon="backup", on_click=lambda _: print("TODO: Backup")),
                ]),
                ft.Divider(),
                ft.Text("Privacidad e Historial", weight="bold"),
                ft.Row([
                    ft.ElevatedButton("Limpiar Historial de Búsqueda", icon="delete_sweep"),
                    ft.ElevatedButton("Limpiar Todo el Historial", icon="auto_delete"),
                ]),
            ], spacing=Spacing.MD),
            padding=Spacing.LG,
        )
