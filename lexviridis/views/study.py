import flet as ft

from ..design_system import Colors, Radius, Spacing, Theme, UIComponents
from ..study_system import StudyManager


class StudyView(ft.Container):
    """
    Vista de Estudio y Flashcards.
    Gestión de sesiones de estudio con repetición espaciada.
    """
    def __init__(self, study_manager: StudyManager, user_id: int):
        super().__init__(expand=True)
        self.study_manager = study_manager
        self.user_id = user_id
        self._build_ui()

    def _build_ui(self):
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_study.png",
            "Sistema de Estudio",
            "Refuerza tus conocimientos con herramientas de aprendizaje inteligente"
        )

        try:
            due_cards = self.study_manager.get_due_flashcards(self.user_id)

            # TODO: Obtener estadísticas reales si el manager lo soporta
            total_cards = 15 # Placeholder
            accuracy = "85%" # Placeholder

            self.content = ft.Column([
                hero,
                UIComponents.heading("Sistema de Estudio", level=1, color=Theme.PRIMARY),
                ft.Text("Refuerza tus conocimientos con repetición espaciada.", size=14, color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.LG),
                UIComponents.card(
                    ft.Column([
                        ft.Icon("auto_awesome", size=48, color=Theme.PRIMARY),
                        ft.Text(f"Tienes {len(due_cards)} tarjetas pendientes para hoy", weight="bold", size=18),
                        UIComponents.primary_button(
                            "Comenzar Sesión",
                            icon="play_arrow",
                            on_click=lambda _: self._start_study_session(due_cards)
                        ) if due_cards else ft.Text("¡Estás al día! Vuelve mañana para más revisiones.", color=Theme.SUCCESS),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=Spacing.MD),
                    padding=Spacing.XL
                ),
                ft.Divider(),
                ft.Text("Tus Estadísticas", weight="bold", size=16),
                ft.Row([
                    ft.Container(
                        content=ft.Column([ft.Text("Total Tarjetas", size=10), ft.Text(str(total_cards), size=24, weight="bold")]),
                        padding=Spacing.MD, bgcolor=Theme.SURFACE, border_radius=Radius.MD, expand=True
                    ),
                    ft.Container(
                        content=ft.Column([ft.Text("Precisión", size=10), ft.Text(accuracy, size=24, weight="bold")]),
                        padding=Spacing.MD, bgcolor=Theme.SURFACE, border_radius=Radius.MD, expand=True
                    )
                ], spacing=Spacing.MD),
                ft.Container(height=Spacing.LG),
                ft.Container(
                    content=ft.TextButton(
                        "Reiniciar Progreso",
                        icon="delete_forever",
                        icon_color=Theme.ERROR,
                        style=ft.ButtonStyle(color=Theme.ERROR),
                        on_click=self._confirm_delete_study_data
                    ),
                    alignment=ft.Alignment(1, 0)
                )
            ], expand=True, scroll=ft.ScrollMode.AUTO)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.content = UIComponents.error_state(
                "Error en Módulo de Estudio",
                f"No se pudo cargar la sesión: {str(e)}",
                on_retry=lambda _: self._build_ui()
            )

    def _start_study_session(self, cards):
        """Inicia el carrusel de flashcards."""
        current_idx = 0
        is_front = True

        card_content = ft.Container(
            padding=Spacing.XL, bgcolor=Theme.SURFACE, border_radius=Radius.LG,
            border=ft.border.all(2, Theme.PRIMARY), width=400, height=300,
            alignment=ft.Alignment(0, 0)
        )
        controls_row = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=Spacing.MD)

        def render_session_completed():
             self.content = ft.Container(
                content=ft.Column([
                    ft.Icon("celebration", size=80, color=Theme.SUCCESS),
                    ft.Text("¡Sesión Completada!", size=24, weight="bold"),
                    ft.Text(f"Estudiaste {len(cards)} tarjetas", size=14, color=Theme.TEXT_SECONDARY),
                    ft.Container(height=Spacing.LG),
                    UIComponents.primary_button("Volver al Estudio", icon="arrow_back",
                                               on_click=lambda _: self._build_ui()),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment(0, 0),
                expand=True
            )
             self.page.update()

        def update_card():
            nonlocal is_front
            if current_idx >= len(cards):
                render_session_completed()
                return

            card = cards[current_idx]
            card_content.content = ft.Column([
                ft.Text("PREGUNTA" if is_front else "RESPUESTA", size=10, weight="bold", color=Theme.PRIMARY),
                ft.Divider(),
                ft.Text(card.pregunta if is_front else card.respuesta, size=18, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

            def flip(e):
                nonlocal is_front
                is_front = not is_front
                update_card()

            def next_card(correct):
                nonlocal current_idx, is_front
                self.study_manager.update_flashcard_stats(cards[current_idx].id, correct)
                current_idx += 1
                if current_idx < len(cards):
                    is_front = True
                    update_card()
                else:
                    render_session_completed()

            controls_row.controls = [
                ft.ElevatedButton("Voltear", icon="flip", on_click=flip)
            ] if is_front else [
                ft.ElevatedButton("Fácil", icon="check", bgcolor=Colors.GREEN_400, color="white", on_click=lambda _: next_card(True)),
                ft.ElevatedButton("Difícil", icon="close", bgcolor=Colors.RED_400, color="white", on_click=lambda _: next_card(False)),
            ]
            self.page.update()

        self.content = ft.Column([
            ft.IconButton("arrow_back", on_click=lambda _: self._build_ui()),
            ft.Container(card_content, alignment=ft.Alignment(0, 0), expand=True),
            controls_row
        ], expand=True)

        # Need to call update_card to init content, but page might not be ready if called from constructor
        # But this is called from an event, so page is ready.
        update_card()
        self.page.update()

    def _confirm_delete_study_data(self, e):
        """Muestra diálogo de confirmación para borrar datos."""
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Reiniciar progreso de estudio?"),
            content=ft.Text("Esta acción eliminará permanentemente todas tus flashcards y estadísticas. No se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Sí, eliminar todo", on_click=lambda e: self._perform_delete_study_data(e, dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _perform_delete_study_data(self, e, dlg):
        """Ejecuta el borrado."""
        dlg.open = False
        self.study_manager.delete_all_flashcards(self.user_id)

        self.page.snack_bar = ft.SnackBar(ft.Text("Progreso de estudio reiniciado correctamente."), bgcolor=Theme.SUCCESS)
        self.page.snack_bar.open = True
        self.page.update()
        self._build_ui()
