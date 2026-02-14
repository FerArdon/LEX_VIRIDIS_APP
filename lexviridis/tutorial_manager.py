
"""
LEX VIRIDIS - Gestor de Tutorial y Onboarding
Maneja la lógica de primera ejecución y el overlay informativo.
"""

import flet as ft
import json
from pathlib import Path
from datetime import datetime

class TutorialManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.config_path = Path.home() / ".lexviridis" / "config.json"
        self.current_step = 0
        
        self.steps = [
            {
                "title": "¡Bienvenido a LEX VIRIDIS! 🌿",
                "message": "Tu compendio legal ambiental inteligente. Encuentra leyes, decretos y artículos de forma instantánea.",
                "icon": ft.Icons.WAVING_HAND,
            },
            {
                "title": "Búsqueda Inteligente 🔍",
                "message": "Navega entre miles de artículos simplemente escribiendo. El sistema resalta términos y sugiere resultados.",
                "icon": ft.Icons.SEARCH,
            },
            {
                "title": "Dashboard y Métricas 📊",
                "message": "Visualiza el estado de la legislación ambiental y tu propia actividad con gráficas interactivas.",
                "icon": ft.Icons.DASHBOARD,
            },
            {
                "title": "Favoritos y Notas ⭐",
                "message": "Guarda artículos clave y agrega tus propias notas jurídicas para consultas rápidas.",
                "icon": ft.Icons.STAR,
            },
            {
                "title": "Exportación PDF 📄",
                "message": "Genera documentos profesionales de tus búsquedas o artículos favoritos en segundos.",
                "icon": ft.Icons.PICTURE_AS_PDF,
            },
            {
                "title": "¡Todo listo! 🚀",
                "message": "Explora la legislación ambiental de Honduras con la herramienta más avanzada. ¿Empezamos?",
                "icon": ft.Icons.ROCKET_LAUNCH,
            }
        ]

    def is_first_run(self) -> bool:
        if not self.config_path.exists():
            return True
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                return not config.get("tutorial_completed", False)
        except:
            return True

    def mark_completed(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        config = {"tutorial_completed": True, "last_run": datetime.now().isoformat()}
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def show_tutorial(self):
        self.current_step = 0
        
        def next_step(e):
            if self.current_step < len(self.steps) - 1:
                self.current_step += 1
                update_ui()
            else:
                close_tutorial()

        def close_tutorial(e=None):
            self.mark_completed()
            dialog.open = False
            self.page.update()

        def update_ui():
            step = self.steps[self.current_step]
            icon_container.content = ft.Icon(step['icon'], size=80, color=ft.Colors.GREEN_700)
            title_text.value = step['title']
            message_text.value = step['message']
            progress_text.value = f"Paso {self.current_step + 1} de {len(self.steps)}"
            btn_next.text = "Entendido" if self.current_step < len(self.steps) - 1 else "¡Empezar!"
            self.page.update()

        icon_container = ft.Container(animate=ft.Animation(300, "easeOut"))
        title_text = ft.Text(size=24, weight="bold", text_align="center")
        message_text = ft.Text(size=16, text_align="center", color=ft.Colors.GREY_700)
        progress_text = ft.Text(size=12, color=ft.Colors.GREY_500)
        btn_next = ft.ElevatedButton(on_click=next_step, bgcolor=ft.Colors.GREEN_700, color="white")
        
        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Column([
                    icon_container,
                    ft.Container(height=10),
                    title_text,
                    ft.Container(height=10),
                    message_text,
                    ft.Container(height=20),
                    ft.Row([progress_text, btn_next], alignment="spaceBetween")
                ], horizontal_alignment="center", tight=True),
                width=400,
                padding=20,
            ),
            shape=ft.RoundedRectangleBorder(radius=16),
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        update_ui()
