import os
import subprocess
import sys
from pathlib import Path

import flet as ft

from .design_system import Spacing, Theme, UIComponents
from .manual_generator import ManualGenerator


def _open_file(path):
    """Abre un archivo con la aplicación predeterminada del sistema (multiplataforma)."""
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class HelpUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.manual_path = self._get_resource_path("docs/MANUAL_USUARIO.md")

    def _get_resource_path(self, relative_path: str) -> Path:
        """Obtiene la ruta absoluta al recurso, compatible con PyInstaller."""
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS) / relative_path
        return Path(relative_path)

    def build(self):
        """Construye y retorna la vista de ayuda con pestañas."""

        # Hero Header
        hero = UIComponents.hero_header(
            "hero_settings.png", "Centro de Ayuda", "Documentación y soporte de Lex Viridis"
        )

        # Tabs Container
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Manual de Usuario", icon=ft.Icons.MENU_BOOK, content=self._build_manual_tab()),
                ft.Tab(text="Acerca de", icon=ft.Icons.INFO, content=self._build_about_tab()),
            ],
            expand=True,
        )

        return ft.Column([hero, ft.Container(content=tabs, expand=True)], spacing=0, expand=True)

    def _build_manual_tab(self):
        """Construye el contenido de la pestaña del manual como Tutorial Interactivo."""

        # Botón de acción flotante (FAB) para descargar PDF
        fab_container = ft.Container(
            content=ft.FloatingActionButton(
                icon=ft.Icons.PICTURE_AS_PDF,
                text="Descargar Manual PDF",
                bgcolor=Theme.PRIMARY,
                on_click=lambda _: self._export_manual_pdf(),
            ),
            padding=ft.padding.only(bottom=20, right=20),
            alignment=ft.alignment.bottom_right,
        )

        return ft.Stack([TutorialView(), fab_container], expand=True)

    def _build_about_tab(self):
        """Construye el contenido de la pestaña Acerca de."""

        # Logo
        logo = ft.Image(src="/assets/LEXVIRIDIS_WHITE_BG.png", width=150, height=150, fit="contain")

        # Info
        info_column = ft.Column(
            [
                ft.Text("LEX VIRIDIS", size=32, weight=ft.FontWeight.BOLD, color=Theme.PRIMARY),
                ft.Text("Compendio Legal Ambiental de Honduras", size=16, color=Theme.TEXT_SECONDARY),
                ft.Container(height=20),
                ft.Text("Versión 3.0.0", size=14, weight=ft.FontWeight.BOLD),
                ft.Text("© 2026 Fernando Ardón - Desarrollo de Software", size=14),
                ft.Text("Con colaboración de: Gemini, Antigravity, Claude", size=14),
                ft.Text("Todos los derechos reservados.", size=14),
                ft.Container(height=30),
                ft.Text("Esta herramienta fue diseñada para fortalecer la justicia ambiental,", size=14, italic=True),
                ft.Text("facilitando el acceso a la normativa vigente para técnicos y fiscales.", size=14, italic=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                [ft.Container(height=50), logo, ft.Container(height=20), info_column],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            alignment=ft.alignment.center,
            padding=Spacing.XL,
            bgcolor=Theme.BACKGROUND,
        )

    def _export_manual_pdf(self):
        """Genera y abre el manual en PDF."""
        try:
            self.page.open(ft.SnackBar(ft.Text("Generando PDF..."), bgcolor=Theme.INFO))

            generator = ManualGenerator()
            pdf_path = generator.generate_from_markdown(self.manual_path)

            self.page.open(
                ft.SnackBar(
                    ft.Text(f"Manual exportado: {pdf_path.name}"),
                    action="Abrir",
                    on_action=lambda _: _open_file(pdf_path),
                    bgcolor=Theme.SUCCESS,
                )
            )

        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"Error al exportar: {e}"), bgcolor=Theme.ERROR))


class TutorialView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.current_scene = 0

        self.scenes = [
            {
                "image": "img_intro_hero.png",
                "title": "Bienvenido a LEX VIRIDIS",
                "narration": "Su compendio legal ambiental inteligente. Diseñado para facilitar el acceso, búsqueda y análisis de la normativa ambiental de Honduras.",
            },
            {
                "image": "img_login_screen.png",
                "title": "Inicio de Sesión Seguro",
                "narration": "Acceda con su usuario y contraseña. Si olvida sus credenciales, utilice la opción de recuperación integrada para restablecer su acceso rápidamente.",
            },
            {
                "image": "img_dashboard_main.png",
                "title": "Panel de Control (Dashboard)",
                "narration": "Su centro de comando. Visualice estadísticas de normas, gráficas de distribución y acceda a su actividad reciente de un vistazo.",
            },
            {
                "image": "img_search_demo.png",
                "title": "Búsqueda Inteligente",
                "narration": "Encuentre lo que necesita al instante. Escriba palabras clave como 'forestal' o 'licencia' y obtenga resultados resaltados y precisos.",
            },
            {
                "image": "img_ai_chat.png",
                "title": "Asistente IA Integrado",
                "narration": "Realice consultas complejas en lenguaje natural. Pregunte '¿Cuáles son los requisitos de una licencia?' y obtenga respuestas fundamentadas.",
            },
            {
                "image": "img_favorites.png",
                "title": "Favoritos y Organización",
                "narration": "Marque artículos importantes con la estrella ⭐ para crear su propia colección de referencias rápidas en la sección de Favoritos.",
            },
            {
                "image": "modo estudio.png",
                "title": "Modo Estudio y Biblioteca",
                "narration": "Acceda al compendio completo, tome notas personales y resalte textos clave para un análisis jurídico profundo.",
            },
            {
                "image": "img_export_pdf.png",
                "title": "Exportación y Reportes",
                "narration": "Genere reportes profesionales en PDF de sus búsquedas o de normas completas con un solo clic, listos para imprimir o compartir.",
            },
        ]

        # Image Control
        self.image_control = ft.Image(
            src=f"/assets/{self.scenes[self.current_scene]['image']}",
            width=600,
            height=350,
            fit="contain",
            border_radius=15,
        )

        # Narration Controls
        self.title_text = ft.Text(
            value=self.scenes[self.current_scene]["title"],
            size=28,
            weight=ft.FontWeight.BOLD,
            color=Theme.PRIMARY,
            text_align=ft.TextAlign.CENTER,
        )

        self.narration_text = ft.Text(
            value=self.scenes[self.current_scene]["narration"],
            size=16,
            color=Theme.TEXT_SECONDARY,
            text_align=ft.TextAlign.CENTER,
        )

        # Step Indicator
        self.step_text = ft.Text(
            f"Paso {self.current_scene + 1} de {len(self.scenes)}",
            weight=ft.FontWeight.W_500,
            color=Theme.TEXT_SECONDARY,
        )

        # Main Layout
        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Container(
                    content=self.image_control,
                    padding=10,
                    bgcolor=Theme.SURFACE,
                    border_radius=20,
                    shadow=ft.BoxShadow(
                        blur_radius=20, color=ft.colors.with_opacity(0.1, ft.colors.BLACK), offset=ft.Offset(0, 10)
                    ),
                ),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        self.title_text,
                        self.narration_text,
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_IOS_ROUNDED,
                            icon_color=Theme.PRIMARY,
                            on_click=self.prev_scene,
                            tooltip="Anterior",
                        ),
                        self.step_text,
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                            icon_color=Theme.PRIMARY,
                            on_click=self.next_scene,
                            tooltip="Siguiente",
                        ),
                    ],
                ),
            ],
        )

    def update_view(self):
        self.image_control.src = f"/assets/{self.scenes[self.current_scene]['image']}"
        self.title_text.value = self.scenes[self.current_scene]["title"]
        self.narration_text.value = self.scenes[self.current_scene]["narration"]
        self.step_text.value = f"Paso {self.current_scene + 1} de {len(self.scenes)}"
        self.update()

    def next_scene(self, e):
        if self.current_scene < len(self.scenes) - 1:
            self.current_scene += 1
            self.update_view()

    def prev_scene(self, e):
        if self.current_scene > 0:
            self.current_scene -= 1
            self.update_view()
