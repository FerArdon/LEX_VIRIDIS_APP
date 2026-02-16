
"""
LEX VIRIDIS - Interfaz de Usuario Profesional v3.0
Diseño moderno, consistente y optimizado.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path

import flet as ft
from flet.core.tabs import Tabs

from .config import config
from .design_system import (
    BarChart,
    BarChartGroup,
    BarChartRod,
    ChartAxis,
    ChartAxisLabel,
    Colors,
    LineChart,
    LineChartData,
    LineChartDataPoint,
    PieChart,
    PieChartSection,
    Radius,
    ResultCard,
    Spacing,
    Theme,
    Typography,
    UIComponents,
    create_theme,
)


def _get_asset_path(filename: str) -> str:
    """Obtiene ruta a un asset, compatible con .exe y desarrollo."""
    # RESOURCE_DIR ya maneja sys._MEIPASS en config.py
    return str(config.RESOURCE_DIR / filename)

from .accessibility import AccessibilityManager, add_accessibility_shortcuts
from .ai_assistant import LegalAIAssistant
from .analytics import AnalyticsReporter, AnalyticsTracker, EventType
from .citations import BibliographyManager, CitationGenerator, CitationStyle, LegalDocument
from .cloud_sync import CloudSync
from .ia_gemini import GeminiClient
from .license_ui import LicenseActivationScreen, LicenseExpiredDialog, LicenseStatusBadge, check_license_on_startup
from .notifications import NotificationManager, NotificationType
from .proactive_assistant import ProactiveSuggestions, SmartShortcuts, UserBehaviorAnalyzer
from .search_engine import SearchEngine, SearchStatus
from .security import AuthManager, EncryptionManager
from .study_system import StudyManager
from .theme_manager import ThemeManager
from .translations import i18n


class LexViridisApp:
    """Aplicación principal de LEX VIRIDIS."""

    def __init__(self, page: ft.Page):
        logging.info("Iniciando LexViridisApp...")
        self.page = page
        self._setup_page()
        logging.info("Página configurada correctamente.")

        # Estado
        self.engine = None
        self.gemini = None
        self.search_results = []
        self.current_query = ""
        self.selected_nav = 0
        self.current_user = None
        self.notifications = []
        self.encryption = EncryptionManager()
        self.auth = None
        self.notif_manager = None
        self.ai_assistant = None
        self.analytics = None
        self.reporter = None
        self.theme_manager = None
        self.accessibility = None
        self.i18n = i18n
        self.cloud = None
        self.proactive = None
        self.bibliography = BibliographyManager()
        self.study_manager = None
        self.license_info = None  # Estado de licencia

        # Estado de IA para exportación
        self.ai_export_content = ""

        # Inicializar lista de resultados para evitar AttributeError
        self.results_list = ft.ListView(expand=True, spacing=Spacing.MD, padding=ft.padding.only(top=Spacing.MD))
        self.search_results = []

        # Verificar licencia antes de continuar
        logging.info("Verificando licencia...")
        self._check_license_and_start()

    def _setup_page(self):
        """Configura la página de Flet."""
        self.page.title = "LEX VIRIDIS | Compendio Legal Ambiental"
        self.page.theme = create_theme()
        self.page.theme_mode = ft.ThemeMode.LIGHT  # Forzar modo claro por defecto
        self.page.bgcolor = Theme.BACKGROUND
        self.page.padding = 0
        self.page.window_min_width = 900
        self.page.window_min_height = 650

        # Configurar Icono de Ventana y Assets
        # Configurar Icono de Ventana y Assets
        # Usar _get_asset_path en lugar de Path(__file__)
        self.page.window_icon = _get_asset_path("LEXVIRIDIS_WHITE_BG.ico")
        self.page.scroll = None

        # Configurar FilePicker para exportaciones
        # FilePicker para importaciones/exportaciones
        try:
            self.file_picker = ft.FilePicker()
            self.file_picker.on_result = self._on_save_file_result
            # self.page.overlay.append(self.file_picker)
        except Exception as e:
            print(f"Error inicializando FilePicker: {e}")
            self.file_picker = None

        # Iniciar maximizado
        self.page.window_maximized = True

        # Tamaño mínimo (si usuario restaura ventana)
        self.page.window_min_width = 900
        self.page.window_min_height = 650

        # Configurar FilePicker para foto de perfil
        self.photo_picker = ft.FilePicker()
        self.photo_picker.on_result = self._on_profile_photo_selected
        # self.page.overlay.append(self.photo_picker)

        # Configurar FilePicker para exportación de IA (TXT)
        self.ai_export_picker = ft.FilePicker()
        self.ai_export_picker.on_result = self._on_ai_export_result
        # self.page.overlay.append(self.ai_export_picker)

        # Actualizar página para registrar controles en overlay
        # try:
        #      self.page.update()
        # except:
        #      pass

    def _check_license_and_start(self):
        """Verifica la licencia antes de iniciar la aplicación."""
        logging.info("Entrando en _check_license_and_start")
        self.license_info = check_license_on_startup(self.page)
        logging.info(f"Resultado de licencia: {self.license_info}")

        # MOSTRAR LOGIN INMEDIATAMENTE sin esperar backend
        if self.license_info and self.license_info.get("valid"):
            # Licencia válida - Mostrar login directamente
            logging.info("Licencia válida. Mostrando login...")
            self._show_login_ui()
            # Cargar backend en background SIN BLOQUEAR
            threading.Thread(target=self._load_backend, daemon=True).start()
        elif self.license_info and self.license_info.get("expired"):
            # Licencia expirada - mostrar diálogo
            LicenseExpiredDialog.show(
                self.page,
                on_renew=self._show_activation_screen,
                on_exit=lambda: self.page.window_close()
            )
        else:
            # Sin licencia - mostrar pantalla de activación
            self._show_activation_screen()

    def _show_activation_screen(self):
        """Muestra la pantalla de activación de licencia."""
        def on_license_success(license_data):
            self.license_info = license_data
            # Mostrar login inmediatamente
            self._show_login_ui()
            # Cargar backend en background
            threading.Thread(target=self._load_backend, daemon=True).start()

        activation_screen = LicenseActivationScreen(self.page, on_license_success)
        self.page.clean()
        self.page.add(activation_screen.build())
        self.page.update()


    def _load_backend(self):
        """Carga el backend en segundo plano SIN MOSTRAR SPLASH."""
        start_time = time.time()

        def log_time(step_name):
            elapsed = time.time() - start_time
            logging.info(f"[BACKEND] [{elapsed:.2f}s] {step_name}")

        try:
            log_time("=== Iniciando _load_backend (background) ===")

            self.engine = SearchEngine()
            log_time("SearchEngine inicializado")

            self.gemini = GeminiClient()
            log_time("GeminiClient inicializado")

            # Inicializar Backup Manager
            from .backup_manager import BackupManager

            # Utilizar ruta relativa robusta para la base de datos
            from .config import config
            db_path = config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
            self.backup_manager = BackupManager(db_path)
            self.backup_manager.run_scheduler() # Iniciar programador automático
            log_time("BackupManager inicializado")

            # Inicializar Tutorial Manager
            from .tutorial_manager import TutorialManager
            self.tutorial = TutorialManager(self.page)
            log_time("TutorialManager inicializado")

            # Inicializar Seguridad y Notificaciones
            self.auth = AuthManager(self.engine.db_manager)
            self.notif_manager = NotificationManager(self.engine.db_manager)
            self.ai_assistant = LegalAIAssistant(self.engine, self.gemini)
            log_time("Auth, Notifications, AI Assistant inicializados")

            # Inicializar tablas de sistema una sola vez
            logging.info("Iniciando migración de tablas...")
            self.engine.db_manager.initialize_tables()
            log_time("Database tables migrated")

            # Analytics e Interfaz
            self.analytics = AnalyticsTracker(self.engine.db_manager)
            self.reporter = AnalyticsReporter(self.engine.db_manager)
            self.theme_manager = ThemeManager(self.page)
            self.accessibility = AccessibilityManager(self.page)
            self.cloud = CloudSync(self.engine.db_manager)
            self.analyzer = UserBehaviorAnalyzer(self.engine.db_manager)
            self.proactive = ProactiveSuggestions(self.analyzer)
            self.study_manager = StudyManager(self.engine.db_manager)
            log_time("Analytics, Theme, Accessibility, Cloud, UI Analyzer inicializados")

            logging.info("Backend listo en background")

            # Suscribirse a notificaciones
            self.notif_manager.subscribe(self._on_notification_received)

            # Configurar Accesibilidad
            add_accessibility_shortcuts(self.page, self)
            log_time("=== Backend completamente listo ===")

        except Exception as e:
            import traceback
            logging.error(f"Error cargando backend en background: {e}")
            logging.error(traceback.format_exc())
            # NO mostrar error, solo logear - login sigue funcionando sin backend

    def _show_login_ui(self):
        """Pantalla de inicio de sesión."""
        self.page.clean()

        # Ventana más pequeña para login
        self.page.window_maximized = False
        self.page.window_width = 450
        self.page.window_height = 600
        # # self.page.window_center() removed removed
        self.page.update()

        user_field = ft.TextField(label="Usuario", prefix_icon="person", width=300)
        pass_field = ft.TextField(label="Contraseña", password=True, can_reveal_password=True,
                                 prefix_icon="lock", width=300, on_submit=lambda _: self._handle_login(user_field.value, pass_field.value))

        # Logo en Login
        # Logo en Login
        logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")

        login_card = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Image(src=str(logo_path), width=80, height=80, fit="contain"),
                    padding=10,
                    bgcolor="#FFFFFF",
                    border_radius=40,
                    shadow=ft.BoxShadow(blur_radius=10, color=Colors.with_opacity(0.1, Colors.BLACK))
                ),
                ft.Text("Inicia Sesión", size=Typography.TITLE, weight="bold"),
                ft.Text("Acceso exclusivo para personal autorizado", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.MD),
                user_field,
                pass_field,
                ft.Container(height=Spacing.SM),
                UIComponents.primary_button("Entrar", on_click=lambda _: self._handle_login(user_field.value, pass_field.value), width=300),
                ft.TextButton("¿Olvidaste tu contraseña?", on_click=lambda _: None), # Placeholder
            ], horizontal_alignment="center", spacing=Spacing.SM),
            bgcolor=Theme.SURFACE,
            padding=Spacing.XL,
            border_radius=Radius.LG,
            border=ft.border.all(1, Theme.BORDER),
        )

        self.page.add(ft.Container(login_card, alignment=ft.Alignment(0, 0), expand=True))
        self.page.update()

    def _handle_login(self, username, password):
        """Procesa el login."""
        # Usuario por defecto para demo si no hay ninguno
        # NOTA: En prod esto debería ser un setup inicial
        try:
            self.auth.create_user("admin", "admin123", "admin@lexviridis.com", role="admin")
            print("Usuario admin creado por defecto")
        except Exception:
            # El usuario ya existe probablemente
            pass

        user = self.auth.login(username, password)

        # --- AUTO-FIX: Si falla admin/admin123, forzar reseteo de contraseña ---
        if not user and username == "admin" and password == "admin123":
            try:
                print("Intento de login fallido para admin. Forzando actualización de credenciales...")
                # Generar nuevo hash para admin123
                salt, key = self.auth.hash_password("admin123")

                conn = self.auth.db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE usuarios SET password_salt = ?, password_hash = ? WHERE username = 'admin'", (salt, key))
                conn.commit()
                conn.close()
                print("Credenciales de admin actualizadas. Reintentando login...")

                # Reintentar login
                user = self.auth.login(username, password)
            except Exception as e:
                print(f"Error al forzar actualización de admin: {e}")
        # -----------------------------------------------------------------------

        if user:
            self.current_user = user
            self._show_main_ui()
            # Notificación de bienvenida
            if self.notif_manager:
                self.notif_manager.send_notification(
                    NotificationType.SISTEMA,
                    "Bienvenida",
                    f"Hola {user['username']}, has iniciado sesión correctamente."
                )
        else:
            self.page.open(ft.SnackBar(ft.Text("Usuario o contraseña incorrectos"), bgcolor=Theme.ERROR))
            self.page.update()

    def _on_notification_received(self, notif):
        """Maneja llegada de nueva notificación."""
        self.notifications.insert(0, notif)
        # Mostrar toast/snack si es importante
        # FIX: NotificationType es string, no Enum
        try:
             tipo_rec = NotificationType.RECORDATORIO.value
        except AttributeError:
             tipo_rec = NotificationType.RECORDATORIO

        if notif['tipo'] != tipo_rec:
             self.page.open(ft.SnackBar(ft.Text(f"🔔 {notif['titulo']}: {notif['mensaje'][:30]}..."), bgcolor=Theme.PRIMARY))

    def _show_main_ui(self):
        """Muestra la interfaz principal."""
        # Restaurar modo maximizado (Forzar update inmediato)
        self.page.window_maximized = True
        self.page.update()

        self.page.window_min_width = 900
        self.page.window_min_height = 650

        self.page.controls.clear()
        self._build_layout()
        self.page.update()

        # Mostrar tutorial si es primera vez
        if self.tutorial.is_first_run():
            self.tutorial.show_tutorial()

    def _show_error(self, message: str):
        """Muestra error de inicialización."""
        self.page.controls.clear()
        self.page.add(UIComponents.error_state(
            "Error de Inicialización",
            message,
            on_retry=lambda e: self.__init__(self.page)
        ))
        self.page.update()

    def _build_layout(self):
        """Construye el layout principal."""
        # Logo para sidebar con fondo sólido
        # Logo para sidebar con fondo sólido
        logo_path = _get_asset_path("LEXVIRIDIS_WHITE_BG.png")
        sidebar_logo = ft.Container(
            content=ft.Container(
                content=ft.Image(src=str(logo_path), width=150, height=150, fit="contain"),
                width=160,
                height=160,
                bgcolor="#FFFFFF",
                border_radius=80,
                alignment=ft.Alignment(0, 0),
            ),
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.only(top=Spacing.MD, bottom=Spacing.MD),
            bgcolor=Theme.SURFACE,
        )

        # Navegación lateral
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=90,
            min_extended_width=180,
            group_alignment=-0.9,
            leading=sidebar_logo,
            bgcolor=Theme.SURFACE,
            indicator_color=Colors.with_opacity(0.1, Theme.PRIMARY),
            destinations=[
                ft.NavigationRailDestination(
                    icon="dashboard_outlined",
                    selected_icon="dashboard",
                    label=self.i18n.t("nav.dashboard"),
                ),
                ft.NavigationRailDestination(
                    icon="search_outlined",
                    selected_icon="search",
                    label=self.i18n.t("nav.search"),
                ),
                ft.NavigationRailDestination(
                    icon="auto_awesome_outlined",
                    selected_icon="auto_awesome",
                    label=self.i18n.t("nav.ai_assistant"),
                ),
                ft.NavigationRailDestination(
                    icon="star_outline",
                    selected_icon="star",
                    label=self.i18n.t("nav.favorites"),
                ),
                ft.NavigationRailDestination(
                    icon="library_books_outlined",
                    selected_icon="library_books",
                    label=self.i18n.t("nav.library"),
                ),
                ft.NavigationRailDestination(
                    icon="school_outlined",
                    selected_icon="school",
                    label=self.i18n.t("nav.study"),
                ),
                ft.NavigationRailDestination(
                    icon="settings_outlined",
                    selected_icon="settings",
                    label=self.i18n.t("nav.settings"),
                ),
            ],
            on_change=self._on_nav_change,
        )
        # Botón de notificaciones con Badge
        self.notif_badge = ft.Container(
            content=ft.Text(str(len([n for n in self.notifications if not n.get('leida', False)])),
                           size=10, color="white", weight="bold"),
            bgcolor="red",
            border_radius=10,
            width=16, height=16,
            alignment=ft.Alignment(0, 0),
            right=4, top=4,
            visible=len([n for n in self.notifications if not n.get('leida', False)]) > 0
        )

        self.notif_btn = ft.Stack([
            ft.IconButton("notifications_outlined", icon_color=Theme.TEXT_SECONDARY, on_click=lambda _: self._show_notifications_panel()),
            self.notif_badge
        ])

        # Header superior
        # Avatar clickable
        self.avatar_icon = ft.Icon("person", size=32, color=Theme.PRIMARY)
        self.avatar_container = ft.Container(
            content=self.avatar_icon,
            bgcolor=Colors.with_opacity(0.1, Theme.PRIMARY),
            border_radius=Radius.MD,
            padding=Spacing.SM,
            on_click=lambda _: self.photo_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg", "webp"]),
            tooltip="Cambiar foto de perfil"
        )

        # Badge de estado de licencia
        license_badge = LicenseStatusBadge(self.license_info).build() if self.license_info else ft.Container()

        header = ft.Container(
            content=ft.Row([
                self.avatar_container,
                ft.Text(f" {self.i18n.t('common.user')}: {(self.current_user['username'] if self.current_user else 'Usuario').upper()}", size=12, weight="bold", color=Theme.TEXT_SECONDARY),
                ft.Container(expand=True),
                license_badge,
                ft.Container(width=Spacing.SM),
                self.notif_btn,
                ft.VerticalDivider(width=1),
                ft.IconButton("logout", icon_color=Theme.ERROR, tooltip="Cerrar Sesión", on_click=lambda _: self._show_login_ui())
            ]),
            padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.SM),
            bgcolor=Theme.SURFACE,
            border=ft.border.only(bottom=ft.BorderSide(1, Theme.BORDER))
        )

        # Área de contenido principal
        self.content_area = ft.Container(
            padding=Spacing.LG,
            bgcolor=Theme.BACKGROUND,
        )

        # Renderizar vista inicial
        self._render_dashboard_view()

        # Layout principal
        layout = ft.Row([
            self.nav_rail,
            ft.VerticalDivider(width=1, color=Theme.BORDER),
            ft.Column([
                header,
                ft.Container(self.content_area, expand=True)
            ], expand=True, spacing=0)
        ], expand=True)

        self.page.add(layout)

    async def _show_notifications_panel(self):
        """Muestra panel flotante de notificaciones."""
        items = []
        for n in self.notifications:
            items.append(ft.ListTile(
                leading=ft.Icon("info", color=Theme.PRIMARY),
                title=ft.Text(n['titulo'], weight="bold", size=14),
                subtitle=ft.Text(n['mensaje'], size=12),
                trailing=ft.Text(n.get('fecha', ''), size=10),
                on_click=lambda e, nid=n['id']: self._mark_notif_read(nid)
            ))

        dlg = ft.AlertDialog(
            title=ft.Text("Notificaciones Recientes"),
            content=ft.Container(
                content=ft.ListView(items, spacing=Spacing.SM),
                width=400, height=300
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update())
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _mark_notif_read(self, nid):
        self.notif_manager.mark_as_read(nid)
        # Actualizar lista local
        for n in self.notifications:
            if n['id'] == nid: n['leida'] = True
        self.page.update()

    async def _change_language(self, lang_code):
        self.i18n.set_language(lang_code)
        self._show_main_ui()
        # Volver a Ajustes
        self.selected_nav = 5
        self.nav_rail.selected_index = 5
        self._render_settings_view()
        self.page.open(ft.SnackBar(ft.Text(self.i18n.t("common.success")), bgcolor=Theme.SUCCESS))
        self.page.update()

    def _connect_cloud(self):
        if self.cloud.authenticate():
            self.page.open(ft.SnackBar(ft.Text("Conectado a Google Drive"), bgcolor=Theme.SUCCESS))
            self._render_settings_view()

    def _toggle_sync(self, value):
        self.cloud.sync_enabled = value
        if value: self.cloud.start_auto_sync()

    def _perform_sync(self):
        res = self.cloud.sync_database(Path(self.engine.db_manager.db_path))
        if res == "success":
            self.page.open(ft.SnackBar(ft.Text(self.i18n.t("export.success")), bgcolor=Theme.SUCCESS))
        else:
            self.page.open(ft.SnackBar(ft.Text(self.i18n.t("export.error")), bgcolor=Theme.ERROR))

    def _show_reminder_dialog(self):
        """Diálogo para crear un recordatorio legal."""
        title_field = ft.TextField(label="Título del recordatorio", hint_text="Ej: Vencimiento de Licencia")
        msg_field = ft.TextField(label="Mensaje", multiline=True)

        def save_reminder(e):
            if title_field.value:
                # Simular programación para hoy + 1 min si no hay datepicker manual funcional rápido
                from datetime import datetime, timedelta
                target_time = datetime.now() + timedelta(minutes=1)
                self.notif_manager.create_reminder(title_field.value, msg_field.value, target_time)
                dlg.open = False
                self.page.open(ft.SnackBar(ft.Text("Recordatorio programado para pronto"), bgcolor=Theme.SUCCESS))
                self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Nuevo Recordatorio"),
            content=ft.Column([title_field, msg_field], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                ft.ElevatedButton("Programar", on_click=save_reminder)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _on_nav_change(self, e):
        """Maneja cambio de navegación."""
        self.selected_nav = e.control.selected_index

        if self.selected_nav == 0:
            self._render_dashboard_view()
        elif self.selected_nav == 1:
            self._render_search_view()
        elif self.selected_nav == 2:
            self._render_ai_view()
        elif self.selected_nav == 3:
            self._render_favorites_view()
        elif self.selected_nav == 4:
            self._render_library_view()
        elif self.selected_nav == 5:
            self._render_study_view()
        elif self.selected_nav == 6:
            self._render_settings_view()

        self.page.update()

    # === VISTA DASHBOARD ===

    def _render_dashboard_view(self):
        """Renderiza el dashboard con estadísticas."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_ai.png",
            "Panel de Control",
            "Monitoreo y estadísticas de la legislación ambiental"
        )

        stats = self.engine.get_dashboard_stats()

        # Stat Cards
        def stat_card(icon, label, value, color):
            # Formatear números con coma para miles y punto para decimales (Instrucción Senior)
            formatted_value = str(value)
            if isinstance(value, (int, float)):
                formatted_value = f"{value:,}" if isinstance(value, int) else f"{value:,.1f}"

            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=color, size=32),
                    ft.Column([
                        ft.Text(label, size=12, color=Theme.TEXT_SECONDARY),
                        ft.Text(formatted_value, size=24, weight="bold", color=color),
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=Theme.SURFACE,
                padding=Spacing.MD,
                border_radius=Radius.MD,
                expand=True,
                shadow=ft.BoxShadow(blur_radius=4, color=Colors.with_opacity(0.05, Colors.BLACK)),
            )

        row_stats = ft.Row([
            stat_card("library_books", "Normas", stats['total_normas'], Theme.PRIMARY),
            stat_card("article", "Artículos", stats['total_articulos'], Theme.SECONDARY),
            stat_card("star", "Favoritos", stats['total_favoritos'], Theme.ACCENT),
            stat_card("search", "Búsquedas", stats['total_busquedas'], Theme.INFO),
        ], spacing=Spacing.MD)

        # Pie Chart - Distribución por Tipo
        pie_sections = []
        colors_list = [Colors.GREEN_700, Colors.TEAL_700, Colors.AMBER_700, Colors.BLUE_700, Colors.GREY_500]
        for i, (tipo, count) in enumerate(stats['distribucion_tipo'].items()):
            if i >= 5: break
            pie_sections.append(PieChartSection(
                value=count,
                title=f"{tipo[:10]}",
                title_style=ft.TextStyle(size=10, color=Colors.WHITE, weight="bold"),
                color=colors_list[i % len(colors_list)],
                radius=100
            ))

        chart_dist = UIComponents.card(
            ft.Column([
                ft.Text("Distribución por Tipo", weight="bold"),
                ft.Container(
                    PieChart(sections=pie_sections, sections_space=2, center_space_radius=80),
                    height=500, alignment=ft.Alignment(0, 0)
                )
            ])
        )

        # Bar Chart - Top Búsquedas
        bar_groups = []
        for i, (_query, freq) in enumerate(stats['top_searches'][:6]):
            bar_groups.append(BarChartGroup(
                x=i,
                bar_rods=[BarChartRod(from_y=0, to_y=freq, color=Theme.PRIMARY, width=15)]
            ))

        chart_top = UIComponents.card(
            ft.Column([
                ft.Text("Top Búsquedas", weight="bold"),
                ft.Container(
                    BarChart(
                        bar_groups=bar_groups,
                        bottom_axis=ChartAxis(
                            labels=[ChartAxisLabel(value=i, label=ft.Text(stats['top_searches'][i][0][:15], size=10, rotate=45)) for i in range(len(bar_groups))],
                        ),
                    ),
                    height=500, padding=20
                )
            ])
        )


        # Actividad Reciente
        recent_activity = ft.ListView(spacing=Spacing.XS, expand=True)
        if stats['most_viewed']:
            for title, views in stats['most_viewed']:
                recent_activity.controls.append(ft.ListTile(
                    leading=ft.Icon("history", size=16),
                    title=ft.Text(title, size=12, max_lines=1, overflow="ellipsis"),
                    trailing=ft.Text(f"{views} vistas", size=10, color=Theme.TEXT_SECONDARY),
                    dense=True
                ))
        else:
            recent_activity.controls.append(ft.Text("No hay actividad reciente", italic=True, size=12))

        # Timeline - Line Chart (Búsquedas últimos 7 días)
        data_points = []
        for i, (_fecha, count) in enumerate(stats['timeline_busquedas']):
            data_points.append(LineChartDataPoint(i, count))

        chart_timeline = UIComponents.card(
            ft.Column([
                ft.Text("Actividad de Búsqueda (Últimos 7 días)", weight="bold"),
                ft.Container(
                    LineChart(
                        data_series=[LineChartData(data_points=data_points, color=Theme.SECONDARY, curved=True, stroke_width=4)],
                        bottom_axis=ChartAxis(
                            labels=[ChartAxisLabel(value=i, label=ft.Text(stats['timeline_busquedas'][i][0][5:], size=10)) for i in range(len(data_points))]
                        )
                    ),
                    height=450, padding=20
                )
            ])
        )


        # Proyectos e IA Sugerencias
        user_id = self.current_user['id'] if self.current_user else 1
        smart_shortcuts_data = SmartShortcuts.get_shortcuts(user_id, self.analyzer)
        suggestions_data = self.proactive.get_suggestions(user_id)

        shortcuts_row = ft.Row([], wrap=True, spacing=Spacing.SM)

        def remove_shortcut(e, shortcut_to_remove):
            e.control.data = "handled"  # Marcar como manejado
            nonlocal smart_shortcuts_data
            smart_shortcuts_data = [s for s in smart_shortcuts_data if s != shortcut_to_remove]
            shortcuts_row.controls = [build_shortcut_chip(s) for s in smart_shortcuts_data]
            self.page.update()

        def build_shortcut_chip(s):
            # Botón X separado para evitar conflictos
            close_btn = ft.IconButton(
                "close",
                icon_size=14,
                tooltip="Quitar",
                icon_color=Theme.TEXT_SECONDARY,
                on_click=lambda e, item=s: remove_shortcut(e, item)
            )

            # Área clickeable principal
            main_area = ft.Container(
                content=ft.Column([
                    ft.Icon(s['icon'], color=Theme.PRIMARY, size=28),
                    ft.Text(s['label'], size=11, weight="bold", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                expand=True,
                alignment=ft.Alignment(0, 0),
                on_click=lambda e, q=s['action']: self._perform_search(q),
                ink=True
            )

            return ft.Container(
                content=ft.Column([
                    ft.Row([ft.Container(expand=True), close_btn], spacing=0),
                    main_area,
                ], spacing=0),
                padding=ft.padding.only(left=Spacing.SM, right=0, top=0, bottom=Spacing.SM),
                bgcolor=Theme.SURFACE,
                border_radius=Radius.SM,
                border=ft.border.all(1, Theme.BORDER),
                width=120,
                height=90,
            )

        shortcuts_row.controls = [build_shortcut_chip(s) for s in smart_shortcuts_data]


        # Sugerencias con botón de eliminar individual
        suggestions_col = ft.Column([])

        def remove_suggestion(sug_to_remove):
            nonlocal suggestions_data
            suggestions_data = [s for s in suggestions_data if s != sug_to_remove]
            suggestions_col.controls = [build_suggestion_card(s) for s in suggestions_data]
            self.page.update()

        def build_suggestion_card(s):
            return ft.Container(
                content=ft.Row([
                    ft.Icon("lightbulb", color=Colors.AMBER_600),
                    ft.Column([
                        ft.Text(s['title'], weight="bold", size=14),
                        ft.Text(s['message'], size=12, color=Theme.TEXT_SECONDARY),
                    ], expand=True, spacing=0),
                    ft.IconButton("close", icon_size=16, tooltip="Quitar sugerencia",
                                 on_click=lambda e, item=s: remove_suggestion(item)),
                    ft.IconButton("arrow_forward", on_click=lambda e, sug=s: self._handle_suggestion(sug)),
                ]),
                padding=Spacing.MD, bgcolor=Colors.AMBER_50, border_radius=Radius.MD, border=ft.border.all(1, Colors.AMBER_200)
            )

        suggestions_col.controls = [build_suggestion_card(s) for s in suggestions_data]

        # Renderizar según pestaña activa
        def show_overview(e=None):
            # Botón para cerrar sugerencias
            def hide_suggestions(e):
                self.show_suggestions = False
                show_overview()

            suggestions_section = ft.Container() if not getattr(self, 'show_suggestions', True) else ft.Column([
                ft.Row([
                    ft.Text("💡 Recomendado para ti", weight="bold", size=16),
                    ft.Container(expand=True),
                    ft.IconButton("close", icon_size=16, tooltip="Ocultar sugerencias", on_click=hide_suggestions)
                ]),
                shortcuts_row,
                suggestions_col if suggestions_data else ft.Container(),
            ])


            tab_content.content = ft.Column([
                suggestions_section,
                ft.Divider(),
                row_stats,
                ft.Container(height=Spacing.MD),
                chart_dist,
                ft.Container(height=Spacing.MD),
                chart_top,
                ft.Container(height=Spacing.MD),
                chart_timeline,
                ft.Container(height=Spacing.MD),
                UIComponents.card(
                    ft.Column([
                        ft.Text("Normas más consultadas", weight="bold"),
                        recent_activity,
                        ft.Container(height=150) # Espacio extra para listview dentro de scroll
                    ])
                )
            ], expand=True, scroll=ft.ScrollMode.ALWAYS)

            self.page.update()

        def show_pro_analytics(e=None):
            funnel = self.reporter.get_funnel()
            heatmap_data = self.reporter.get_heatmap()

            funnel_ui = ft.Row([
                stat_card("filter_alt", "Búsquedas", funnel['searches'], Colors.BLUE),
                ft.Icon("arrow_forward"),
                stat_card("touch_app", "Clicks", funnel['clicks'], Colors.ORANGE),
                ft.Icon("arrow_forward"),
                stat_card("auto_graph", "Conversión", f"{funnel['conversion']:.1f}%", Colors.PURPLE),
            ], spacing=Spacing.MD)

            heatmap_ui = self._build_activity_heatmap(heatmap_data)

            tab_content.content = ft.Column([
                UIComponents.heading("Analytics Avanzado", level=2),
                ft.Text("Rendimiento del sistema en tiempo real", size=12, color=Theme.TEXT_SECONDARY),
                ft.Divider(),
                funnel_ui,
                ft.Container(height=Spacing.LG),
                ft.Text("Mapa de Calor de Actividad (30 días)", weight="bold"),
                ft.Container(heatmap_ui, padding=Spacing.MD, bgcolor=Theme.SURFACE, border_radius=Radius.MD, border=ft.border.all(1, Theme.BORDER)),
                ft.Container(height=Spacing.LG),
                ft.Row([
                    UIComponents.primary_button("Exportar Reporte PDF", icon="picture_as_pdf"),
                    UIComponents.primary_button("Exportar Excel (CSV)", icon="table_view"),
                    ft.Container(expand=True),
                    ft.TextButton(
                        "Reiniciar Estadísticas",
                        icon="delete_sweep",
                        icon_color=Theme.ERROR,
                        style=ft.ButtonStyle(color=Theme.ERROR),
                        on_click=lambda _: self._confirm_reset_stats()
                    ),
                ], spacing=Spacing.MD)
            ], scroll=ft.ScrollMode.AUTO)

            self.page.update()

        def on_tab_change(e):
            if e.control.selected_index == 0:
                show_overview()
            else:
                show_pro_analytics()

        # Contenedor para contenido dinámico
        tab_content = ft.Container(expand=True)

        self.content_area.content = ft.Column([
            hero,
            UIComponents.heading("Dashboard Principal", level=1, color=Theme.PRIMARY),
            Tabs(
                tabs=[
                    ft.Tab("Resumen", icon="dashboard"),
                    ft.Tab("Analytics Pro", icon="analytics"),
                ],
                on_change=on_tab_change,
            ),
            ft.Divider(height=1, thickness=1),
            tab_content,
        ], expand=True) # Scroll manejado internamente por tab_content

        show_overview()
        self.page.update()

    def _build_activity_heatmap(self, data):
        """Construye un grid visual de intensidad de uso."""
        days = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
        grid = []

        # Header de horas
        hours_header = ft.Row([ft.Container(width=40)] + [
            ft.Container(ft.Text(str(h), size=8, color=Theme.TEXT_SECONDARY), width=15) for h in range(0, 24, 2)
        ], spacing=20)
        grid.append(hours_header)

        for d_idx, day_name in enumerate(days):
            cells = [ft.Container(ft.Text(day_name, size=10), width=40)]
            for h_idx in range(24):
                count = data[d_idx][h_idx]
                # Color según intensidad
                if count == 0: color = Theme.BACKGROUND
                elif count < 5: color = Colors.GREEN_100
                elif count < 15: color = Colors.GREEN_300
                elif count < 30: color = Colors.GREEN_600
                else: color = Colors.GREEN_900

                cells.append(ft.Container(
                    width=15, height=15,
                    bgcolor=color,
                    border_radius=2,
                    tooltip=f"{day_name} {h_idx}:00 - {count} eventos"
                ))
            grid.append(ft.Row(cells, spacing=2))

        return ft.Column(grid, spacing=2)

    # === VISTA DE BÚSQUEDA ===

    def _render_search_view(self):
        """Renderiza la vista de búsqueda."""

        def on_search_change(e):
            suggestions = self.engine.get_search_suggestions(e.data)
            if suggestions:
                self.suggestions_row.controls = [
                    UIComponents.chip(s, on_click=lambda _, q=s: self._perform_search(q))
                    for s in suggestions
                ]
                self.suggestions_row.visible = True
            else:
                self.suggestions_row.visible = False
            self.page.update()

        self.search_input = UIComponents.search_field(
            "Escribe una palabra clave (ej. forestal, licencia, agua)...",
            on_submit=lambda e: self._perform_search(e.control.value),
            on_change=on_search_change
        )

        self.suggestions_row = ft.Row(visible=False, wrap=True, spacing=Spacing.SM)

        # Hero section (diseño premium con imagen)
        hero = UIComponents.hero_header(
            "hero_search.png",
            "Buscador Inteligente",
            "Encuentra normas, acuerdos y decretos en segundos"
        )

        search_section = ft.Container(
            content=ft.Column([
                ft.Container(height=Spacing.LG),
                ft.Container(
                    content=ft.Column([
                        self.search_input,
                        self.suggestions_row,
                    ]),
                    width=600,
                ),
                ft.Container(height=Spacing.LG),
                ft.Row([
                    UIComponents.chip("Ley Forestal", on_click=lambda e: self._perform_search("Ley Forestal")),
                    UIComponents.chip("Licencia Ambiental", on_click=lambda e: self._perform_search("Licencia Ambiental")),
                    UIComponents.chip("Áreas Protegidas", on_click=lambda e: self._perform_search("áreas protegidas")),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=Spacing.SM),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
        )

        self.results_list = ft.ListView(
            expand=True,
            spacing=Spacing.MD,
            padding=ft.padding.only(top=Spacing.MD),
        )

        self.search_results = []
        self.content_area.content = ft.Column([
            hero,
            search_section,
            self.results_list
        ], expand=True, scroll=ft.ScrollMode.ALWAYS)
        self.page.update()

    def _quick_search(self, text: str):
        """Búsqueda rápida desde chip."""
        self._perform_search(text)

    def _perform_search(self, query: str):
        """Ejecuta la búsqueda."""
        self.current_query = query

        # Estado de carga
        self.content_area.content = UIComponents.loading_state("Buscando...")
        self.page.update()

        # Ejecutar búsqueda
        try:
            if not self.engine:
                self._show_search_error("Motor de búsqueda no disponible")
                return

            result = self.engine.search_safe(query)

            # Registrar en analytics
            if self.analytics:
                self.analytics.track_search(query, result.total_found, user_id=self.current_user['id'] if self.current_user else None)

            # Procesar resultado
            if result.status == SearchStatus.SUCCESS:
                self.search_results = result.results
                self._show_results_view()
            elif result.status == SearchStatus.NO_RESULTS:
                self._show_empty_results(query)
            else:
                self._show_search_error(result.message)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._show_search_error(f"Error inesperado: {str(e)}")

        self.page.update()

    def _show_results_view(self):
        """Muestra los resultados de búsqueda."""
        # Header con resultados
        header = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        "Resultados para:",
                        size=Typography.CAPTION,
                        color=Theme.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        f'"{self.current_query}"',
                        size=Typography.TITLE,
                        weight=Typography.BOLD,
                        color=Theme.PRIMARY,
                    ),
                ], spacing=Spacing.XXS),
                ft.Container(expand=True),
                ft.Text(
                    f"{len(self.search_results)} resultados",
                    size=Typography.BODY,
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(width=Spacing.SM),
                ft.IconButton(
                    "picture_as_pdf",
                    icon_color=Theme.ERROR,
                    tooltip="Exportar a PDF",
                    on_click=lambda e: self._export_results_pdf(),
                ),
                ft.Container(width=Spacing.SM),
                UIComponents.secondary_button(
                    "Nueva búsqueda",
                    icon="refresh",
                    on_click=lambda e: self._reset_search(),
                ),
            ]),
            padding=ft.padding.only(bottom=Spacing.LG),
        )

        # Lista de resultados
        self.results_list.controls.clear()
        for res in self.search_results:
            # Determinar acción al hacer clic
            if res.get('is_norma'):
                # Si es una norma completa (Novedades), abrir PDF directamente
                def on_click_action(e, r=res):
                    return self._open_pdf(r)
            else:
                # Si es resultado de búsqueda, mostrar detalle con resaltado
                def on_click_action(e, r=res):
                    return self._show_article_detail(r)

            self.results_list.controls.append(
                ResultCard(res, on_click=on_click_action)
            )

        self.content_area.content = ft.Column([
            header,
            ft.Container(self.results_list, expand=True),
        ], expand=True)
        self.page.update()

    def _show_article_detail(self, result_meta: dict):
        """Muestra el detalle del artículo con navegación de términos."""
        article_id = result_meta.get('id')
        if not article_id: return

        article = self.engine.get_article_by_id(article_id)
        if not article: return

        self.current_article = article
        query = self.current_query

        # Encontrar todas las ocurrencias
        import re
        text = article['contenido']
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        matches = [m.start() for m in pattern.finditer(text)]
        current_match_idx = 0

        # UI Elements for Detail
        ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

        def highlight_text(idx):
            nonlocal current_match_idx
            current_match_idx = idx

            # Aplicar highlighting con colores (Markdown)
            # En Flet Markdown no podemos poner colores de fondo fácilmente,
            # pero podemos usar negrita y emojis o simplemente resaltar el actual

            # Simple approach: Bold all matches, and use a special marker for the current one
            processed_text = text

            # Primero, poner en negrita todas
            processed_text = pattern.sub(lambda m: f"**{m.group(0)}**", processed_text)

            # Actualizar UI
            detail_content.content = ft.Markdown(
                processed_text,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
            )

            counter_text.value = f"Coincidencia {current_match_idx + 1} de {len(matches)}" if matches else "0 coincidencias"
            self.page.update()

        counter_text = ft.Text(size=Typography.CAPTION, color=Theme.TEXT_SECONDARY)
        detail_content = ft.Container(expand=True)

        def nav_match(delta):
            if not matches: return
            new_idx = (current_match_idx + delta) % len(matches)
            highlight_text(new_idx)
            # Scroll to is not easy in Flet yet without keys, but we update the counter

        # Header del detalle
        detail_header = ft.Row([
            UIComponents.icon_badge("description", Theme.PRIMARY),
            ft.Column([
                ft.Text(f"Artículo {article['numero_articulo']}", weight="bold"),
                ft.Text(article['norma_titulo'], size=12, color=Theme.TEXT_SECONDARY, max_lines=1, overflow="ellipsis"),
            ], expand=True),
            ft.VerticalDivider(),
            ft.Row([
                ft.IconButton("chevron_left", on_click=lambda _: nav_match(-1)),
                counter_text,
                ft.IconButton("chevron_right", on_click=lambda _: nav_match(1)),
            ], spacing=0),
            ft.VerticalDivider(),
            UIComponents.primary_button("Abrir PDF", icon="picture_as_pdf", on_click=lambda _: self._open_pdf(result_meta)),
            ft.IconButton("close", on_click=lambda _: self._show_results_view()),
        ])

        self.content_area.content = ft.Column([
            detail_header,
            UIComponents.divider(),
            ft.Container(detail_content, expand=True, padding=Spacing.MD, bgcolor=Theme.SURFACE, border_radius=Radius.MD, border=ft.border.all(1, Theme.BORDER)),
        ], expand=True)

        highlight_text(0)

        # Registrar vista
        self.engine.log_article_view(article_id)
        if self.analytics:
            self.analytics.track_event(EventType.SEARCH_RESULT_CLICKED, {'result_id': article_id}, user_id=self.current_user['id'] if self.current_user else None)

        # Favorite toggle logic
        is_fav = self.engine.is_favorite(article_id)
        fav_icon = "star" if is_fav else "star_outline"
        fav_color = Theme.ACCENT if is_fav else Theme.TEXT_DISABLED

        def toggle_fav(e):
            now_fav = self.engine.toggle_favorite(article_id)
            fav_btn.icon = "star" if now_fav else "star_outline"
            fav_btn.icon_color = Theme.ACCENT if now_fav else Theme.TEXT_DISABLED
            self.page.update()

        fav_btn = ft.IconButton(fav_icon, icon_color=fav_color, on_click=toggle_fav, tooltip="Favorito")
        cite_btn = ft.IconButton("format_quote", icon_color=Theme.PRIMARY, on_click=lambda _: self._show_citation_dialog(article), tooltip="Citar")
        study_btn = ft.IconButton("school", icon_color=Theme.SECONDARY, on_click=lambda _: self._generate_study_cards(article), tooltip="Generar Flashcards")

        # Re-build header with Favorite, Cite and Study Button
        detail_header.controls.insert(2, fav_btn)
        detail_header.controls.insert(3, cite_btn)
        detail_header.controls.insert(4, study_btn)
        self.page.update()

    def _generate_study_cards(self, article):
        """Genera y guarda flashcards para el artículo actual."""
        # Feedback inicial
        self.page.show_snack_bar(ft.SnackBar(
            ft.Text("✨ Analizando texto y generando tarjetas inteligentes..."),
            bgcolor=Theme.PRIMARY
        ))
        self.page.update()

        user_id = self.current_user['id'] if self.current_user else 1

        # Generar con IA (pasando self.gemini)
        cards = self.study_manager.generate_flashcards_from_text(
            article['contenido'],
            article.get('tipo_norma', 'General'),
            ai_client=self.gemini
        )

        for card in cards:
            self.study_manager.save_flashcard(user_id, card)

        self.page.show_snack_bar(ft.SnackBar(
            ft.Text(f"¡Misión cumplida! Se han generado {len(cards)} flashcards para tu estudio."),
            bgcolor=Theme.SUCCESS
        ))
        self.page.update()

    def _open_pdf(self, article):
        """Abre el PDF asociado al artículo."""
        from pathlib import Path

        from .pdf_viewer_fixed import PDFViewerFixed
        try:
            pdf_path = article.get('archivo_pdf')
            # Soporte para estructura de diccionario de resultados de búsqueda ('file')
            if not pdf_path and 'file' in article:
                pdf_path = article['file']
            # Soporte para estructura alternativa
            if not pdf_path and 'norma_archivo_pdf' in article:
                pdf_path = article['norma_archivo_pdf']

            # Validacion robusta de ruta
            if not pdf_path or str(pdf_path) == "Desconocido" or str(pdf_path) == "None":
                 self.page.open(ft.SnackBar(ft.Text("⚠️ El documento digital no está disponible para esta norma."), bgcolor=Theme.WARNING))
                 return

            # Estrategia de resolución de rutas robusta (Portable / Frozen / Dev)
            from .config import config

            # Normalizar entrada
            path_obj = Path(pdf_path)
            filename = path_obj.name

            # Lista de candidatos a probar en orden de prioridad
            candidates = [
                path_obj,                                      # 1. Ruta original (si es absoluta y existe)
                config.PDF_DIR / filename,                     # 2. Carpeta configurada (prioridad alta)
                config.APP_DIR / filename,                     # 3. Carpeta de la app (junto al exe)
                config.RUNTIME_DIR / "COMPENDIO LEYES FEMA" / filename, # 4. Carpeta interna (si se empaquetó)
                Path.cwd() / filename,                         # 5. CWD actual
                Path.cwd() / "COMPENDIO LEYES FEMA" / filename # 6. CWD/Subcarpeta
            ]

            final_path = None
            for p in candidates:
                try:
                    if p.exists():
                        final_path = p
                        break
                except Exception:
                    continue

            if final_path:
                path_obj = final_path
            else:
                 # Reportar error con información de depuración
                 self.page.open(ft.SnackBar(
                     ft.Text(f"⚠️ PDF no encontrado: {filename}. Revise que el archivo esté en la carpeta del ejecutable."),
                     bgcolor=Theme.WARNING
                 ))
                 return

            if pdf_path: # Usamos path_obj corregido abajo
                # Determinar página y query para resaltado
                page = article.get('page', 1) or article.get('pagina', 1)
                query = getattr(self, 'current_query', '')
                is_norma = article.get('is_norma', False)

                # Si es una norma completa (Novedades) o no hay query, abrir simple
                if is_norma or not query:
                     PDFViewerFixed.open_pdf_simple(path_obj)
                # Si hay consulta activa y es búsqueda normal, usar resaltado
                elif hasattr(PDFViewerFixed, 'highlight_and_open_pdf'):
                     PDFViewerFixed.highlight_and_open_pdf(path_obj, int(page), query)
                else:
                     PDFViewerFixed.open_pdf_simple(path_obj)
            else:
                 self.page.open(ft.SnackBar(ft.Text("PDF no disponible para esta norma"), bgcolor=Theme.WARNING))
        except Exception as e:
            print(f"Error abriendo PDF: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Error abriendo PDF: {e}"), bgcolor=Theme.ERROR))

    def _export_results_pdf(self):
        """Exporta los resultados actuales a PDF."""
        from datetime import datetime
        fname = f"Resultados_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        self.file_picker.save_file(dialog_title="Guardar Informe PDF", file_name=fname, allowed_extensions=["pdf"])

    def _on_save_file_result(self, e):
        """Maneja el resultado del guardado de archivo."""
        if e.path:
            try:
                from pathlib import Path

                from .pdf_exporter import PDFExporter

                target_path = Path(e.path)
                # Inicializar exportador con el directorio seleccionado
                exporter = PDFExporter(output_dir=target_path.parent)

                # Ejecutar exportación
                exporter.export_search_results(
                    self.search_results,
                    self.current_query or "Resultados",
                    filename=target_path.stem
                )

                self.page.open(ft.SnackBar(ft.Text(f"PDF guardado exitosamente en: {e.path}"), bgcolor=Theme.SUCCESS))
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.page.open(ft.SnackBar(ft.Text(f"Error guardando reporte: {ex}"), bgcolor=Theme.ERROR))

    def _on_profile_photo_selected(self, e):
        """Maneja la selección de foto de perfil."""
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            try:
                # Copiar archivo a carpeta local del usuario (simulado) o actualizar UI
                # En una app real, copiaríamos el archivo a una carpeta de assets/users

                # Actualizar avatar
                self.avatar_icon.name = None # Quitar icono
                self.avatar_icon.visible = False

                self.avatar_container.content = ft.Image(
                    src=file_path,
                    width=32, height=32,
                    fit="cover",
                    border_radius=Radius.MD,
                )
                self.avatar_container.update()

                self.page.open(ft.SnackBar(ft.Text("Foto de perfil actualizada"), bgcolor=Theme.SUCCESS))

                # TODO: Guardar ruta en BD de usuario
                # self.auth.update_avatar(self.current_user['id'], file_path)

            except Exception as ex:
                self.page.open(ft.SnackBar(ft.Text(f"Error al cambiar foto: {ex}"), bgcolor=Theme.ERROR))

    def _reset_search(self):
        """Limpia la búsqueda actual."""
        self.current_query = ""
        self._render_search_view()

    def _show_citation_dialog(self, article):
        """Muestra opciones de cita para el artículo."""
        from datetime import datetime
        try:
            pub_date = datetime.strptime(str(article.get('fecha_publicacion', '1993-01-01')), '%Y-%m-%d')
        except (ValueError, TypeError):
            pub_date = datetime(1993, 1, 1)

        doc = LegalDocument(
            tipo=article.get('tipo_norma', 'Ley'),
            numero=article.get('numero_decreto', 'N/A'),
            titulo=article.get('norma_titulo', 'Documento Legal'),
            fecha_publicacion=pub_date,
            articulo=str(article.get('numero_articulo', ''))
        )

        apa = CitationGenerator.generate(doc, CitationStyle.APA)

        def copy_cite(text):
            self.page.set_clipboard(text)
            self.page.open(ft.SnackBar(ft.Text("Cita copiada al portapapeles")))

        dlg = ft.AlertDialog(
            title=ft.Text("Citar Documento"),
            content=ft.Column([
                ft.Text("APA Format:", weight="bold", size=12),
                ft.Container(ft.Text(apa, size=11), bgcolor=Theme.SURFACE_VARIANT, padding=Spacing.MD, border_radius=Radius.SM),
                ft.Row([
                    ft.ElevatedButton("Copiar APA", icon="copy", on_click=lambda _: copy_cite(apa)),
                    ft.ElevatedButton("Bibliografía", icon="bookmark_add", on_click=lambda _: self.bibliography.add_entry(doc) or self.page.open(ft.SnackBar(ft.Text("Agregado a tu bibliografía")))),
                ])
            ], tight=True, spacing=Spacing.MD),
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _handle_suggestion(self, suggestion):
        """Maneja el clic en una sugerencia proactiva."""
        if suggestion['type'] == 'save_search':
            # Simular guardado
            self.page.open(ft.SnackBar(ft.Text(f"Búsqueda '{suggestion['data']}' guardada en atajos")))
        elif suggestion['type'] == 'new_legislation':
            self._perform_search(f"novedades {suggestion['data']}")
        self.page.update()

    def _render_favorites_view(self):
        """Renderiza la lista de artículos favoritos."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_favorites.png",
            "Mis Favoritos",
            "Tus documentos y artículos guardados para consulta rápida"
        )
        favorites = self.engine.get_favorites()

        if not favorites:
            self.content_area.content = ft.Column([
                hero,
                UIComponents.empty_state(
                    "star_outline",
                    "Sin favoritos",
                    "Aún no has guardado ningún artículo. Haz clic en la estrella al ver un artículo para guardarlo.",
                )
            ], expand=True)
            self.page.update()
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
                    ft.IconButton("open_in_new", tooltip="Ver Artículo", on_click=lambda e, f=fav: self._show_article_detail(f)),
                ]),
                padding=Spacing.MD,
                bgcolor=Theme.SURFACE,
                border_radius=Radius.MD,
                border=ft.border.all(1, Theme.BORDER),
                on_click=lambda e, f=fav: self._show_article_detail(f),
            )
            fav_list.controls.append(card)

        self.content_area.content = ft.Column([
            hero,
            UIComponents.heading("Mis Favoritos", level=1, color=Theme.PRIMARY),
            ft.Text(f"{len(favorites)} artículos guardados", size=12, color=Theme.TEXT_SECONDARY),
            ft.Divider(),
            fav_list
        ], expand=True)
        self.page.update()

    def _add_fav_tag(self, fav: dict):
        """Diálogo para agregar un tag a un favorito."""
        tag_field = ft.TextField(label="Nuevo Tag", hint_text="ej. Penal, Forestal, Urgente")

        def save_tag(e):
            if tag_field.value:
                self.engine.add_favorite_tag(fav['id'], tag_field.value)
                dlg.open = False
                self._render_favorites_view()
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
            self._render_favorites_view()
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

    def _show_empty_results(self, query: str):
        """Muestra estado vacío."""
        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.Icon("search_off", size=80, color=Theme.TEXT_DISABLED),
                ft.Container(height=Spacing.MD),
                ft.Text("Sin resultados", size=Typography.TITLE, weight=Typography.SEMIBOLD),
                ft.Text(
                    f'No encontramos resultados para "{query}"',
                    color=Theme.TEXT_SECONDARY,
                ),
                ft.Container(height=Spacing.LG),
                ft.Text("Sugerencias:", weight=Typography.MEDIUM),
                ft.Text("• Verifica la ortografía", color=Theme.TEXT_SECONDARY),
                ft.Text("• Usa términos más generales", color=Theme.TEXT_SECONDARY),
                ft.Text("• Prueba sinónimos", color=Theme.TEXT_SECONDARY),
                ft.Container(height=Spacing.LG),
                UIComponents.secondary_button("Nueva búsqueda", on_click=lambda e: self._reset_search()),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

    def _show_search_error(self, message: str):
        """Muestra error de búsqueda."""
        self.content_area.content = UIComponents.error_state(
            "Error en la búsqueda",
            message,
            on_retry=lambda e: self._reset_search(),
        )


    # === VISTA DE IA ===


    def _render_ai_view(self):
        """Vista del asistente inteligente con RAG."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_ai.png",
            "Asistente IA Legal",
            "Consulta tus dudas sobre legislación ambiental con inteligencia artificial"
        )
        if not self.gemini or not self.gemini.api_key:
            self._render_api_key_prompt()
            return

        self.chat_messages = ft.ListView(
            expand=True,
            spacing=Spacing.MD,
            padding=Spacing.MD,
            auto_scroll=True,
        )

        # Sugerencias de preguntas
        sugerencias = [
            "¿Cuál es la multa por tala ilegal?",
            "¿Qué documentos necesito para licencia ambiental?",
            "¿Cuándo aplica evaluación de impacto ambiental?",
            "¿Qué leyes protegen áreas protegidas?"
        ]

        chips_row = ft.Row([
            UIComponents.chip(s, on_click=lambda e, q=s: self._send_ai_message(q))
            for s in sugerencias
        ], spacing=Spacing.SM, wrap=True)

        self.chat_input = ft.TextField(
            hint_text="Haz una consulta legal sobre medio ambiente...",
            expand=True,
            border_radius=Radius.XL,
            bgcolor=Theme.SURFACE,
            content_padding=Spacing.MD,
            on_submit=lambda e: self._send_ai_message(e.control.value),
        )

        self.content_area.content = ft.Column([
            hero,
            ft.Row([
                UIComponents.heading("Asistente Legal IA", level=1, color=Theme.PRIMARY),
                ft.Container(expand=True),
                UIComponents.chip("Modo RAG Activo", icon="reply_all", selected=True)
            ]),
            ft.Container(
                content=self.chat_messages,
                expand=True,
                bgcolor=Theme.SURFACE_VARIANT,
                border_radius=Radius.LG,
                border=ft.border.all(1, Theme.BORDER),
            ),
            ft.Container(height=Spacing.MD),
            chips_row,
            ft.Row([
                self.chat_input,
                ft.IconButton(
                    "report_gmailerrorred",
                    icon_color=Theme.SECONDARY,
                    tooltip="Crear Recordatorio",
                    on_click=lambda _: self._show_reminder_dialog()
                ),
                UIComponents.primary_button(
                    "Preguntar",
                    icon="auto_awesome",
                    on_click=lambda e: self._send_ai_message(self.chat_input.value),
                ),
            ]),
        ], expand=True)
        self.page.update()

    def _render_api_key_prompt(self):
        """Solicita API key de Gemini."""
        api_input = ft.TextField(label="API Key de Gemini", password=True, can_reveal_password=True)

        def save_key(e):
            val = api_input.value
            if not val:
                self.page.open(ft.SnackBar(ft.Text("Por favor ingresa una clave válida."), bgcolor=Theme.WARNING))
                return

            try:
                # Asegurar que el cliente existe
                if not self.gemini:
                    from .ia_gemini import GeminiClient
                    self.gemini = GeminiClient(api_key=val)
                else:
                    self.gemini.set_api_key(val)

                # Feedback visual inmediato
                self.page.open(ft.SnackBar(ft.Text("✅ API Key configurada"), bgcolor=Theme.SUCCESS))

                # Recargar vista
                self._render_ai_view()
                self.page.update()

            except Exception as ex:
                print(f"Error guardando API Key: {ex}")
                self.page.open(ft.SnackBar(ft.Text(f"Error guardando clave: {ex}"), bgcolor=Theme.ERROR))

        self.content_area.content = ft.Container(
            content=ft.Column([
                ft.Icon("key_outlined", size=64, color=Theme.SECONDARY),
                ft.Container(height=Spacing.MD),
                UIComponents.heading("Configurar Asistente IA", level=2),
                UIComponents.body_text("Ingresa tu API Key de Google Gemini para habilitar el asistente.", secondary=True),
                ft.Container(height=Spacing.LG),
                ft.Container(content=api_input, width=400),
                ft.Container(height=Spacing.MD),
                UIComponents.primary_button("Guardar", on_click=save_key),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )

    def _add_chat_message(self, text: str, is_user: bool):
        """Añade mensaje al chat."""
        bubble = ft.Container(
            content=ft.Markdown(text, selectable=True) if not is_user else ft.Text(text),
            bgcolor=Colors.BLUE_50 if is_user else Theme.SURFACE,
            padding=Spacing.MD,
            border_radius=Radius.LG,
            border=None if is_user else ft.border.all(1, Theme.BORDER),
            width=500 if not is_user else None,
        )

        alignment = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        self.chat_messages.controls.append(ft.Row([bubble], alignment=alignment))
        self.page.update()

    def _send_ai_message(self, text):
        """Envía mensaje al asistente IA usando RAG."""
        if not text or not text.strip():
            return

        query = text
        self.chat_input.value = ""
        self._add_chat_message(query, True)

        # Loading
        loading = ft.Row([UIComponents.progress_indicator(20), ft.Text("Consultando base legal...")],
                        alignment=ft.MainAxisAlignment.START)
        self.chat_messages.controls.append(loading)
        self.page.update()

        def process():
            try:
                # Usar LegalAIAssistant con RAG
                if not self.ai_assistant:
                    raise Exception("Asistente IA no inicializado")

                result = self.ai_assistant.answer_question(query)

                self.chat_messages.controls.remove(loading)

                # Crear burbuja de respuesta especial con fuentes y opciones de exportación
                response_card = ft.Column([
                    ft.Row([
                        ft.Icon("auto_awesome", size=16, color=Theme.PRIMARY),
                        ft.Text("Respuesta Inteligente", size=12, weight="bold", color=Theme.PRIMARY),
                        ft.Container(expand=True),
                        ft.IconButton("copy_all", icon_size=16, tooltip="Copiar al portapapeles",
                                     on_click=lambda _: self._copy_to_clipboard(result['answer'])),
                        ft.IconButton("text_snippet", icon_size=16, tooltip="Exportar a TXT",
                                     on_click=lambda _: self._export_ai_txt(result['answer'])),
                        ft.IconButton("picture_as_pdf", icon_size=16, tooltip="Imprimir / PDF",
                                     on_click=lambda _: self._export_ai_pdf(result['answer'], query)),
                    ], spacing=Spacing.XS),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Markdown(result['answer'], selectable=True),
                    ft.Container(height=Spacing.SM),
                    ft.Divider(height=1, color=Theme.BORDER),
                    ft.Text("📚 Fuentes consultadas:", size=11, weight="bold", color=Theme.TEXT_SECONDARY),
                    ft.Row([
                        ft.TextButton(
                            f"• {Path(s['file']).name} (Art. {s.get('id', '?')})",
                            on_click=lambda e, res=s: self._show_article_detail(res)
                        ) for s in result['sources'][:3]
                    ], wrap=True)
                ], spacing=Spacing.XS)

                self._add_ai_bubble(response_card)
            except Exception as e:
                import traceback
                traceback.print_exc()
                if loading in self.chat_messages.controls:
                    self.chat_messages.controls.remove(loading)
                self._add_chat_message(f"❌ Error al consultar IA: {str(e)}", False)
                self.page.update()

        threading.Thread(target=process, daemon=True).start()

    def _add_ai_bubble(self, content):
        bubble = ft.Container(
            content=content,
            bgcolor=Theme.SURFACE,
            padding=Spacing.MD,
            border_radius=Radius.LG,
            border=ft.border.all(1, Theme.BORDER),
            width=650, # Un poco más ancho para los botones
        )
        self.chat_messages.controls.append(ft.Row([bubble], alignment=ft.MainAxisAlignment.START))
        self.page.update()

    # --- Herramientas de IA (Export/Copy) ---

    def _copy_to_clipboard(self, text):
        self.page.set_clipboard(text)
        self.page.open(ft.SnackBar(ft.Text("Respuesta copiada al portapapeles"), bgcolor=Theme.SUCCESS))

    def _export_ai_txt(self, text):
        self.ai_export_content = text
        self.ai_export_picker.save_file(
            dialog_title="Guardar respuesta como TXT",
            file_name=f"Respuesta_IA_{datetime.now().strftime('%H%M%S')}.txt",
            allowed_extensions=["txt"]
        )

    def _on_ai_export_result(self, e):
        if e.path:
            try:
                with open(e.path, "w", encoding="utf-8") as f:
                    f.write(self.ai_export_content)
                self.page.open(ft.SnackBar(ft.Text("Archivo guardado exitosamente"), bgcolor=Theme.SUCCESS))
            except Exception as ex:
                self.page.open(ft.SnackBar(ft.Text(f"Error guardando archivo: {ex}"), bgcolor=Theme.ERROR))

    def _export_ai_pdf(self, text, query):
        """Exporta respuesta de IA a un PDF formal (Print-ready)."""
        try:
            from .pdf_exporter import PDFExporter
            exporter = PDFExporter()

            # Limpiar markdown simple para PDF (ReportLab no soporta todo MD)
            clean_text = text.replace("**", "").replace("__", "")

            articulo_ficticio = [{
                'numero': 'Respuesta Integral',
                'contenido': clean_text,
                'norma_titulo': f'CONSULTA: {query.upper()}'
            }]

            path = exporter.export_articulos(
                articulo_ficticio,
                filename=f"Consulta_IA_{datetime.now().strftime('%Y%m%d_%H%M')}",
                titulo="Respuestas del Asistente IA LEX VIRIDIS"
            )

            self.page.open(ft.SnackBar(ft.Text("PDF generado correctamente"), bgcolor=Theme.SUCCESS))

            # Abrir archivo automáticamente
            import os
            import platform
            if platform.system() == 'Windows':
                os.startfile(str(path))
        except Exception as ex:
            import traceback
            traceback.print_exc()
            self.page.open(ft.SnackBar(ft.Text(f"Error generando PDF: {ex}"), bgcolor=Theme.ERROR))


    # === OTRAS VISTAS ===

    def _render_library_view(self):
        """Vista de biblioteca digital con todas las normas."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_library.png",
            "Biblioteca Digital",
            "Explora el catálogo completo de la legislación ambiental hondureña"
        )

        # Obtener normas de la BD
        # Obtener normas de la BD
        try:
            if not self.engine or not self.engine.db_manager:
                 raise Exception("Gestor de base de datos no inicializado")

            conn = self.engine.db_manager.get_connection()
            cursor = conn.cursor()

            # Obtener todas las normas agrupadas por tipo
            cursor.execute("""
                SELECT id, tipo, titulo, archivo_pdf,
                       (SELECT COUNT(*) FROM articulos WHERE norma_id = normas.id) as num_articulos
                FROM normas
                ORDER BY tipo, titulo
            """)
            normas = cursor.fetchall()
            conn.close()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.content_area.content = UIComponents.error_state(
                "Error cargando biblioteca",
                f"No se pudieron cargar las normas: {str(e)}",
                on_retry=lambda _: self._render_library_view()
            )
            self.content_area.update()
            return

        # Agrupar por tipo
        grupos = {}
        for norma in normas:
            tipo = norma['tipo'] or 'Otros'
            if tipo not in grupos:
                grupos[tipo] = []
            grupos[tipo].append(norma)

        # Variables de estado para la vista
        if not hasattr(self, "library_view_mode"):
            self.library_view_mode = "detail" # detail, list, grid

        self.library_content = ft.Container(expand=True)
        self.library_filter = "Todos"

        # Lógica de renderizado de lista
        def render_list():
            items_to_show = []
            if self.library_filter == "Todos":
                for tipo, lista in sorted(grupos.items()):
                    items_to_show.extend(lista)
            else:
                items_to_show = grupos.get(self.library_filter, [])

            # Limpiar contenido anterior
            self.library_content.content = None

            if self.library_view_mode == "grid":
                # VISTA DE CUADRÍCULA (GRID)
                grid = ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=250,
                    child_aspect_ratio=1.0,
                    spacing=10,
                    run_spacing=10,
                )

                for norma in items_to_show:
                    tipo = norma['tipo'] or 'Documento'
                    color = Theme.PRIMARY if 'Decreto' in tipo else Theme.SECONDARY

                    card = ft.Container(
                        content=ft.Column([
                            ft.Icon("description", size=32, color=color),
                            ft.Text(norma['titulo'], size=12, weight="bold", max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(expand=True),
                            ft.Text(tipo, size=10, color=Theme.TEXT_SECONDARY),
                        ]),
                        bgcolor=Theme.SURFACE,
                        border=ft.border.all(1, Theme.BORDER),
                        border_radius=Radius.MD,
                        padding=Spacing.MD,
                        on_click=lambda e, n=norma: self._open_library_pdf(n),
                        tooltip=norma['titulo']
                    )
                    grid.controls.append(card)
                self.library_content.content = grid

            elif self.library_view_mode == "list":
                # VISTA DE LISTA COMPACTA
                lv = ft.ListView(expand=True, spacing=2)
                try:
                    for norma in items_to_show:
                        tile = ft.ListTile(
                            leading=ft.Icon("article", size=20, color=Theme.PRIMARY),
                            title=ft.Text(norma['titulo'] or "Sin título", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            subtitle=ft.Text(norma['tipo'] or "Documento", size=10),
                            trailing=ft.Icon("chevron_right", size=16),
                            on_click=lambda e, n=norma: self._open_library_pdf(n),
                            # dense=True # Eliminado por compatibilidad
                        )
                        lv.controls.append(tile)
                except Exception as ex:
                    print(f"Error renderizando lista compacta: {ex}")
                    lv.controls.append(ft.Text(f"Error mostrando lista: {ex}", color=Theme.ERROR))
                self.library_content.content = lv

            else:
                # VISTA DETALLADA (Por defecto)
                lv = ft.ListView(expand=True, spacing=Spacing.SM)
                for norma in items_to_show:
                    # Lógica de iconos y colores
                    tipo = norma['tipo'] or ''
                    if 'Decreto' in tipo:
                        icon = "gavel"
                        color = Theme.PRIMARY
                    elif 'Ley' in tipo:
                        icon = "balance"
                        color = Theme.SECONDARY
                    elif 'Acuerdo' in tipo:
                        icon = "assignment"
                        color = Theme.WARNING
                    else:
                        icon = "description"
                        color = Theme.TEXT_SECONDARY

                    card = ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, size=24, color=color),
                                bgcolor=Colors.with_opacity(0.1, color),
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
                                "open_in_new",
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
                    lv.controls.append(card)
                self.library_content.content = lv

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

        # Variables de estado para ordenamiento
        if not hasattr(self, "library_sort_order"):
            self.library_sort_order = "asc" # asc, desc

        # Refactorizar render_list para aceptar ordenamiento

        def render_list_sorted():
            # Obtener items base (ya filtrados en render_list original pero aqui accedemos a grupos)
            items_to_show = []
            if self.library_filter == "Todos":
                for tipo, lista in sorted(grupos.items()):
                    items_to_show.extend(lista)
            else:
                items_to_show = grupos.get(self.library_filter, [])

            # APLICAR ORDENAMIENTO
            items_to_show.sort(
                key=lambda x: x['titulo'].lower() if x['titulo'] else "",
                reverse=(self.library_sort_order == "desc")
            )

            # Limpiar contenido anterior
            self.library_content.content = None

            if self.library_view_mode == "grid":
                # VISTA DE CUADRÍCULA (GRID)
                grid = ft.GridView(
                    expand=True,
                    runs_count=5,
                    max_extent=250,
                    child_aspect_ratio=1.0,
                    spacing=10,
                    run_spacing=10,
                )

                for norma in items_to_show:
                    tipo = norma['tipo'] or 'Documento'
                    color = Theme.PRIMARY if 'Decreto' in tipo else Theme.SECONDARY

                    card = ft.Container(
                        content=ft.Column([
                            ft.Icon("description", size=32, color=color),
                            ft.Text(norma['titulo'], size=12, weight="bold", max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(expand=True),
                            ft.Text(tipo, size=10, color=Theme.TEXT_SECONDARY),
                        ]),
                        bgcolor=Theme.SURFACE,
                        border=ft.border.all(1, Theme.BORDER),
                        border_radius=Radius.MD,
                        padding=Spacing.MD,
                        on_click=lambda e, n=norma: self._open_library_pdf(n),
                        tooltip=norma['titulo']
                    )
                    grid.controls.append(card)
                self.library_content.content = grid

            elif self.library_view_mode == "list":
                # VISTA DE LISTA COMPACTA
                lv = ft.ListView(expand=True, spacing=2)
                try:
                    for norma in items_to_show:
                        tile = ft.ListTile(
                            leading=ft.Icon("article", size=20, color=Theme.PRIMARY),
                            title=ft.Text(norma['titulo'] or "Sin título", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            subtitle=ft.Text(norma['tipo'] or "Documento", size=10),
                            trailing=ft.Icon("chevron_right", size=16),
                            on_click=lambda e, n=norma: self._open_library_pdf(n),
                            # dense=True # Eliminado por compatibilidad
                        )
                        lv.controls.append(tile)
                except Exception as ex:
                    print(f"Error renderizando lista compacta: {ex}")
                    lv.controls.append(ft.Text(f"Error mostrando lista: {ex}", color=Theme.ERROR))
                self.library_content.content = lv

            else:
                # VISTA DETALLADA (Por defecto)
                lv = ft.ListView(expand=True, spacing=Spacing.SM)
                for norma in items_to_show:
                    # Lógica de iconos y colores
                    tipo = norma['tipo'] or ''
                    if 'Decreto' in tipo:
                        icon = "gavel"
                        color = Theme.PRIMARY
                    elif 'Ley' in tipo:
                        icon = "balance"
                        color = Theme.SECONDARY
                    elif 'Acuerdo' in tipo:
                        icon = "assignment"
                        color = Theme.WARNING
                    else:
                        icon = "description"
                        color = Theme.TEXT_SECONDARY

                    card = ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, size=24, color=color),
                                bgcolor=Colors.with_opacity(0.1, color),
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
                                "open_in_new",
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
                    lv.controls.append(card)
                self.library_content.content = lv

        # Reemplazar la funcion original
        render_list = render_list_sorted

        # Toolbar estilo Windows Explorer (oscuro) - con funcionalidad
        def change_sort(order):
            self.library_sort_order = order
            render_list()
            self.page.update()

            order_text = "A-Z" if order == "asc" else "Z-A"
            self.page.open(ft.SnackBar(ft.Text(f"Ordenando por nombre ({order_text})"), bgcolor=Theme.SUCCESS))

        def change_view_mode(mode):
            self.library_view_mode = mode
            render_list()
            self.page.update()

        explorer_toolbar = ft.Container(
            content=ft.Row([
                ft.TextButton("Nuevo", icon="add_circle_outline", on_click=lambda e: self._import_pdf_to_compendium(),
                             style=ft.ButtonStyle(color="#CCCCCC")),
                ft.VerticalDivider(width=1, color="#555555"),
                ft.PopupMenuButton(
                    icon="sort",
                    tooltip="Ordenar",
                    items=[
                        ft.PopupMenuItem(text="Nombre (A-Z)", on_click=lambda e: change_sort("asc")),
                        ft.PopupMenuItem(text="Nombre (Z-A)", on_click=lambda e: change_sort("desc")),
                    ]
                ),
                ft.PopupMenuButton(
                    icon="view_list",
                    tooltip="Cambiar vista",
                    items=[
                        ft.PopupMenuItem(text="Lista compacta", icon="view_list", on_click=lambda e: change_view_mode("list")),
                        ft.PopupMenuItem(text="Tarjetas", icon="grid_view", on_click=lambda e: change_view_mode("grid")),
                        ft.PopupMenuItem(text="Detalle", icon="view_agenda", on_click=lambda e: change_view_mode("detail")),
                    ]
                ),
                ft.Container(expand=True),
                ft.TextButton("Vista previa", icon="visibility_outlined",
                             style=ft.ButtonStyle(color="#CCCCCC"),
                             on_click=lambda e: self.page.open(ft.SnackBar(ft.Text("Selecciona un documento para ver vista previa")))),
            ], spacing=4),
            bgcolor="#2D2D2D",
            padding=ft.padding.symmetric(horizontal=Spacing.SM, vertical=4),
            border_radius=ft.border_radius.only(top_left=Radius.SM, top_right=Radius.SM),
        )

        # Contenido de Normas
        norms_content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        UIComponents.heading("Biblioteca Digital", level=1, color=Theme.PRIMARY),
                        UIComponents.body_text(f"{len(normas)} documentos en el compendio", secondary=True),
                    ], expand=True),
                    UIComponents.primary_button("Agregar PDF", icon="add", on_click=lambda e: self._import_pdf_to_compendium()),
                ]),
                padding=ft.padding.only(bottom=Spacing.SM),
            ),
            explorer_toolbar,
            filter_chips,
            ft.Container(self.library_content, expand=True, padding=ft.padding.only(top=Spacing.MD)),
        ], expand=True)

        # Contenedor para Bibliografía (se llena bajo demanda)
        bib_content = ft.Column(expand=True)

        # Contenedor dinámico de pestañas
        tab_content = ft.Container(content=norms_content, expand=True)

        # Definición de Tabs
        library_tabs = Tabs(
            selected_index=0,
            tabs=[
                ft.Tab("Normas del Compendio", icon="account_balance"),
                ft.Tab("Bibliografía Personal", icon="format_quote"),
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
                    bib_list.controls.append(UIComponents.empty_state("format_quote", "Bibliografía vacía", "Agrega citas desde el detalle de cualquier artículo."))
                else:
                    for cite in cites:
                        bib_list.controls.append(ft.Container(
                            content=ft.Row([
                                ft.Text(cite, size=12, expand=True),
                                ft.IconButton("copy", icon_size=16, tooltip="Copiar cita",
                                             on_click=lambda _, c=cite: self._copy_to_clipboard(c)),
                            ]),
                            padding=Spacing.MD, bgcolor=Theme.SURFACE_VARIANT, border_radius=Radius.SM
                        ))

                # Función para exportar bibliografía completa
                def export_bibliography(_):
                    if not cites:
                        self.page.open(ft.SnackBar(ft.Text("No hay citas para exportar"), bgcolor=Theme.WARNING))
                        return
                    self.ai_export_content = "BIBLIOGRAFÍA LEGAL\n" + "="*50 + "\n\n" + "\n\n".join(cites) + "\n\n---\nGenerado por LEX VIRIDIS"
                    self.ai_export_picker.save_file(
                        dialog_title="Exportar Bibliografía",
                        file_name=f"Bibliografia_Legal_{datetime.now().strftime('%Y%m%d')}.txt",
                        allowed_extensions=["txt"]
                    )

                # Función para agregar cita manual
                def show_manual_cite_dialog(_):
                    autor_field = ft.TextField(label="Autor(es)", hint_text="Apellido, N.")
                    titulo_field = ft.TextField(label="Título del documento")
                    fuente_field = ft.TextField(label="Fuente / Editorial / Diario Oficial")
                    fecha_field = ft.TextField(label="Fecha de publicación", hint_text="YYYY-MM-DD")

                    def save_manual_cite(_):
                        if not titulo_field.value:
                            self.page.open(ft.SnackBar(ft.Text("El título es obligatorio"), bgcolor=Theme.ERROR))
                            return

                        # Crear documento manualmente
                        from .citations import LegalDocument
                        try:
                            pub_date = datetime.strptime(fecha_field.value or "1990-01-01", '%Y-%m-%d')
                        except ValueError:
                            pub_date = datetime.now()

                        doc = LegalDocument(
                            tipo="Documento",
                            numero="-",
                            titulo=titulo_field.value,
                            fecha_publicacion=pub_date,
                            articulo=""
                        )
                        self.bibliography.add_entry(doc)
                        dlg.open = False
                        self.page.open(ft.SnackBar(ft.Text("Cita agregada correctamente"), bgcolor=Theme.SUCCESS))
                        on_library_tab_change(None)  # Refrescar
                        self.page.update()

                    dlg = ft.AlertDialog(
                        title=ft.Text("Agregar Cita Manual"),
                        content=ft.Container(
                            content=ft.Column([autor_field, titulo_field, fuente_field, fecha_field], tight=True, spacing=Spacing.SM),
                            width=400
                        ),
                        actions=[
                            ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False) or self.page.update()),
                            ft.ElevatedButton("Agregar", on_click=save_manual_cite),
                        ]
                    )
                    self.page.overlay.append(dlg)
                    dlg.open = True
                    self.page.update()

                bib_content.controls = [
                    ft.Row([
                        ft.Column([
                            ft.Text("Mi Bibliografía Legal", weight="bold", size=18),
                            ft.Text("Estilo: APA 7ma Edición", size=10, color=Theme.TEXT_SECONDARY),
                        ], spacing=0),
                        ft.Container(expand=True),
                        UIComponents.secondary_button("Agregar Cita", icon="add", on_click=show_manual_cite_dialog),
                        UIComponents.primary_button("Exportar TXT", icon="download", on_click=export_bibliography),
                        ft.IconButton("refresh", tooltip="Actualizar", on_click=lambda _: on_library_tab_change(None)),
                    ], spacing=Spacing.SM),
                    ft.Divider(),
                    ft.Text(f"{len(cites)} referencia(s) guardadas", size=12, color=Theme.TEXT_SECONDARY, italic=True) if cites else ft.Container(),
                    bib_list
                ]
                tab_content.content = bib_content
            self.page.update()

        library_tabs.on_change = on_library_tab_change

        # Layout Final
        self.content_area.content = ft.Column([
            hero,
            library_tabs,
            ft.Divider(height=1),
            tab_content
        ], expand=True)

        # Renderizado inicial
        render_list()
        self.page.update()

    def _render_study_view(self):
        """Vista principal de estudio con Flashcards."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_study.png",
            "Sistema de Estudio",
            "Refuerza tus conocimientos con herramientas de aprendizaje inteligente"
        )

        try:
            user_id = self.current_user['id'] if self.current_user else 1
            due_cards = self.study_manager.get_due_flashcards(user_id)

            self.content_area.content = ft.Column([
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
                        content=ft.Column([ft.Text("Total Tarjetas", size=10), ft.Text("15", size=24, weight="bold")]),
                        padding=Spacing.MD, bgcolor=Theme.SURFACE, border_radius=Radius.MD, expand=True
                    ),
                    ft.Container(
                        content=ft.Column([ft.Text("Precisión", size=10), ft.Text("85%", size=24, weight="bold")]),
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
            self.page.update()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.content_area.content = UIComponents.error_state(
                "Error en Módulo de Estudio",
                f"No se pudo cargar la sesión: {str(e)}",
                on_retry=lambda _: self._render_study_view()
            )
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
        user_id = self.current_user['id'] if self.current_user else 1
        self.study_manager.delete_all_flashcards(user_id)

        self.page.open(ft.SnackBar(ft.Text("Progreso de estudio reiniciado correctamente."), bgcolor=Theme.SUCCESS))
        self._render_study_view()

    def _confirm_reset_stats(self):
        """Muestra diálogo de confirmación para borrar estadísticas del dashboard."""
        def close_dlg(e):
            self.page.dialog.open = False
            self.page.update()

        def execute_reset(e):
            self.page.dialog.open = False
            self._perform_reset_stats()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Reiniciar estadísticas?"),
            content=ft.Text("Esta acción eliminará permanentemente:\n• Historial de búsquedas\n• Conteo de vistas\n• Datos de actividad\n\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Sí, reiniciar todo", on_click=execute_reset, style=ft.ButtonStyle(color=Theme.ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def _perform_reset_stats(self):
        """Ejecuta el borrado de estadísticas."""
        try:
            conn = self.engine.db_manager.get_connection()
            cursor = conn.cursor()

            # Borrar logs de búsqueda
            cursor.execute("DELETE FROM search_logs")
            # Borrar historial de vistas
            cursor.execute("DELETE FROM view_history")
            # Borrar actividad
            cursor.execute("DELETE FROM user_activity")

            conn.commit()

            self.page.open(ft.SnackBar(ft.Text("Estadísticas reiniciadas correctamente."), bgcolor=Theme.SUCCESS))
            self._render_dashboard_view()
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=Theme.ERROR))


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
                # Sesión completada - mostrar resultados
                self.content_area.content = ft.Container(
                    content=ft.Column([
                        ft.Icon("celebration", size=80, color=Theme.SUCCESS),
                        ft.Text("¡Sesión Completada!", size=24, weight="bold"),
                        ft.Text(f"Estudiaste {len(cards)} tarjetas", size=14, color=Theme.TEXT_SECONDARY),
                        ft.Container(height=Spacing.LG),
                        UIComponents.primary_button("Volver al Estudio", icon="arrow_back",
                                                   on_click=lambda _: self._render_study_view()),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment(0, 0),
                    expand=True
                )
                self.page.update()

        def update_card():
            nonlocal is_front
            card = cards[current_idx]
            card_content.content = ft.Column([
                ft.Text("PREGUNTA" if is_front else "RESPUESTA", size=10, weight="bold", color=Theme.PRIMARY),
                ft.Divider(),
                ft.Text(card.pregunta if is_front else card.respuesta, size=18, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

            controls_row.controls = [
                ft.ElevatedButton("Voltear", icon="flip", on_click=flip)
            ] if is_front else [
                ft.ElevatedButton("Fácil", icon="check", bgcolor=Colors.GREEN_400, color="white", on_click=lambda _: next_card(True)),
                ft.ElevatedButton("Difícil", icon="close", bgcolor=Colors.RED_400, color="white", on_click=lambda _: next_card(False)),
            ]
            self.page.update()

        self.content_area.content = ft.Column([
            ft.IconButton("arrow_back", on_click=lambda _: self._render_study_view()),
            ft.Container(card_content, alignment=ft.Alignment(0, 0), expand=True),
            controls_row
        ], expand=True)
        update_card()
        self.page.update()

    def _import_pdf_to_compendium(self):
        """Permite al usuario agregar nuevos PDFs al compendio."""

        # FilePicker para seleccionar PDFs
        self.pdf_picker = ft.FilePicker(on_result=lambda e: self._on_pdf_selected(e, getattr(self, 'current_norma_id', None)))
        self.page.overlay.append(self.pdf_picker)
        self.page.update()
        self.pdf_picker.pick_files(
            dialog_title="Seleccionar PDFs para agregar al Compendio",
            allowed_extensions=["pdf"],
            allow_multiple=True
        )

    def _on_pdf_import_result(self, e):
        """Procesa los PDFs seleccionados y los copia al compendio."""
        import shutil

        if not e.files:
            return

        # Usar directorio de PDFs desde configuración
        try:
            from .config import config
            compendio_dir = config.PDF_DIR
        except ImportError:
             # Fallback seguro
             from pathlib import Path
             compendio_dir = Path("COMPENDIO LEYES FEMA").resolve()

        compendio_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        for file in e.files:
            try:
                src = Path(file.path)
                dest = compendio_dir / src.name

                if dest.exists():
                    # Añadir sufijo si ya existe
                    dest = compendio_dir / f"{src.stem}_nuevo{src.suffix}"

                shutil.copy2(src, dest)
                imported += 1
            except Exception as ex:
                self.page.show_snack_bar(ft.SnackBar(
                    ft.Text(f"Error importando {file.name}: {ex}"),
                    bgcolor=Theme.ERROR
                ))

        if imported > 0:
            self.page.show_snack_bar(ft.SnackBar(
                ft.Text(f"✅ {imported} PDF(s) agregados al compendio. Reinicia la app para indexarlos."),
                bgcolor=Theme.SUCCESS
            ))
            self._render_library_view()

    def _open_library_pdf(self, norma):
        """Abre PDF desde la biblioteca."""
        from .pdf_viewer_fixed import PDFViewerFixed
        try:
            pdf_path = norma['archivo_pdf']
            if pdf_path:
                PDFViewerFixed.open_pdf_simple(Path(pdf_path))
            else:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("PDF no disponible para este documento"),
                    bgcolor=Theme.WARNING,
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {e}"),
                bgcolor=Theme.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _render_settings_view(self):
        """Vista de ajustes y gestión de backups."""
        # Hero Header
        hero = UIComponents.hero_header(
            "hero_settings.png",
            "Configuración",
            "Gestiona tu cuenta, copias de seguridad y preferencias del sistema"
        )

        def create_manual_backup(e):
            self.page.snack_bar = ft.SnackBar(ft.Text("Creando backup..."))
            self.page.snack_bar.open = True
            self.page.update()

            res = self.backup_manager.create_backup(label="manual")
            if res:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Backup creado: {res.name}"), bgcolor=Theme.SUCCESS)
                render_backups()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Error creando backup"), bgcolor=Theme.ERROR)
            self.page.snack_bar.open = True
            self.page.update()

        def restore_selected_backup(backup_path):
            def confirm_restore(e):
                dialog.open = False
                self.page.snack_bar = ft.SnackBar(ft.Text("Restaurando base de datos..."))
                self.page.snack_bar.open = True
                self.page.update()

                if self.backup_manager.restore_backup(Path(backup_path)):
                    self.page.snack_bar = ft.SnackBar(ft.Text("Base de datos restaurada. Reinicia la app para aplicar cambios."), bgcolor=Theme.SUCCESS)
                else:
                    self.page.snack_bar = ft.SnackBar(ft.Text("Error al restaurar backup"), bgcolor=Theme.ERROR)
                self.page.snack_bar.open = True
                self.page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("¿Restaurar Base de Datos?"),
                content=ft.Text("Esto reemplazará toda la información actual por la del backup seleccionado. Se creará una copia de seguridad automática antes de proceder."),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda _: setattr(dialog, "open", False) or self.page.update()),
                    ft.ElevatedButton("Restaurar Ahora", bgcolor=Theme.ERROR, color=Colors.WHITE, on_click=confirm_restore),
                ],
            )
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

        backups_list = ft.ListView(expand=True, spacing=Spacing.SM)

        def render_backups():
            backups_list.controls.clear()
            backups = self.backup_manager.list_backups()

            if not backups:
                backups_list.controls.append(ft.Text("No hay backups disponibles", size=12, italic=True, color=Theme.TEXT_SECONDARY))
            else:
                for b in backups[:10]: # Mostrar últimos 10
                    backups_list.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon("storage", size=20, color=Theme.PRIMARY),
                                ft.Column([
                                    ft.Text(b['date'].strftime("%d/%m/%Y %H:%M"), size=Typography.BODY, weight="bold"),
                                    ft.Text(f"{b['size_mb']} MB · {b['name']}", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                                ], expand=True, spacing=0),
                                ft.IconButton("restore", tooltip="Restaurar este backup", on_click=lambda e, p=b['path']: restore_selected_backup(p)),
                            ]),
                            padding=Spacing.SM,
                            bgcolor=Theme.SURFACE_VARIANT,
                            border_radius=Radius.SM,
                        )
                    )
            self.page.update()

        # === GESTIÓN DE SEGURIDAD ===
        current_pwd_ref = ft.Ref[ft.TextField]()
        new_pwd_ref = ft.Ref[ft.TextField]()
        confirm_pwd_ref = ft.Ref[ft.TextField]()

        def change_password_click(e):
            if not current_pwd_ref.current.value or not new_pwd_ref.current.value:
                self.page.open(ft.SnackBar(ft.Text("Por favor complete los campos"), bgcolor=Theme.ERROR))
                return

            if new_pwd_ref.current.value != confirm_pwd_ref.current.value:
                self.page.open(ft.SnackBar(ft.Text("Las contraseñas nuevas no coinciden"), bgcolor=Theme.ERROR))
                return

            user_id = self.current_user['id'] if self.current_user else None
            if not user_id:
                self.page.open(ft.SnackBar(ft.Text("Error de sesión"), bgcolor=Theme.ERROR))
                return

            success = self.auth.change_password(user_id, current_pwd_ref.current.value, new_pwd_ref.current.value)

            if success:
                self.page.open(ft.SnackBar(ft.Text("Contraseña actualizada exitosamente"), bgcolor=Theme.SUCCESS))
                current_pwd_ref.current.value = ""
                new_pwd_ref.current.value = ""
                confirm_pwd_ref.current.value = ""
                self.page.update()
            else:
                self.page.open(ft.SnackBar(ft.Text("Contraseña actual incorrecta"), bgcolor=Theme.ERROR))

        # Layout de ajustes
        self.content_area.content = ft.Column([
            hero,
            UIComponents.heading("Ajustes del Sistema", level=1, color=Theme.PRIMARY),
            Tabs(
                selected_index=0,
                tabs=[
                    ft.Tab(
                        "Interfaz y Temas",
                        icon="palette",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Tema de la Aplicación", weight="bold"),
                                ft.Row([
                                    ft.ElevatedButton("Modo Claro", icon="light_mode", on_click=lambda _: self.theme_manager.set_theme("light")),
                                    ft.ElevatedButton("Modo Oscuro", icon="dark_mode", on_click=lambda _: self.theme_manager.set_theme("dark")),
                                ]),
                                ft.Divider(),
                                ft.Text("Accesibilidad", weight="bold"),
                                ft.Switch(label="Alto Contraste", on_change=lambda e: self.accessibility.toggle_high_contrast(e.control.value)),
                                ft.Switch(label="Texto Grande", on_change=lambda e: self.accessibility.toggle_large_text(e.control.value)),
                                ft.Divider(),
                                UIComponents.primary_button(self.i18n.t("common.save")),
                            ], spacing=Spacing.MD),
                            padding=Spacing.LG,
                        )
                    ),
                    ft.Tab(
                        "Seguridad",
                        icon="security",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Gestión de Cuenta", weight="bold"),
                                ft.Divider(),
                                ft.TextField(ref=current_pwd_ref, label="Contraseña Actual", password=True, can_reveal_password=True),
                                ft.TextField(ref=new_pwd_ref, label="Nueva Contraseña", password=True, can_reveal_password=True),
                                ft.TextField(ref=confirm_pwd_ref, label="Confirmar Nueva Contraseña", password=True, can_reveal_password=True),
                                ft.Container(height=Spacing.SM),
                                UIComponents.primary_button("Actualizar Contraseña", on_click=change_password_click),
                            ], spacing=Spacing.MD),
                            padding=Spacing.LG,
                        )
                    ),
                    ft.Tab(
                        "Localización y Nube",
                        icon="language",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(self.i18n.t("settings.language"), weight="bold"),
                                ft.Row([
                                    ft.ElevatedButton("ES - Español", icon="language", on_click=lambda _: self.page.run_task(self._change_language, "es")),
                                    ft.ElevatedButton("EN - English", icon="language", on_click=lambda _: self.page.run_task(self._change_language, "en")),
                                ]),
                                ft.Divider(),
                                ft.Text(self.i18n.t("settings.cloud"), weight="bold"),
                                ft.Card(
                                    content=ft.Container(
                                        content=ft.Column([
                                            ft.Row([
                                                ft.Icon("cloud_sync", color=Theme.PRIMARY),
                                                ft.Column([
                                                    ft.Text("Google Drive Sync", weight="bold"),
                                                    ft.Text(f"Estado: {self.cloud.get_status().upper()}", size=12),
                                                ], expand=True),
                                                ft.ElevatedButton("Conectar", on_click=lambda _: self._connect_cloud()),
                                            ])
                                        ]), padding=Spacing.MD
                                    )
                                ),
                                ft.Switch(label="Sincronización Automática", value=True, on_change=lambda e: self._toggle_sync(e.control.value)),
                                UIComponents.primary_button("Sincronizar Ahora", icon="sync", on_click=lambda _: self._perform_sync()),
                            ], spacing=Spacing.MD),
                            padding=Spacing.LG,
                        )
                    ),
                    ft.Tab(
                        "Base de Datos y Backups",
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Gestión de Copias de Seguridad", size=Typography.TITLE, weight="bold"),
                                        ft.Text("Los backups automáticos se realizan diariamente a las 02:00 AM.", size=Typography.CAPTION),
                                    ], expand=True),
                                    UIComponents.primary_button("Crear Backup Ahora", icon="backup", on_click=create_manual_backup),
                                ]),
                                ft.Divider(),
                                ft.Text("Privacidad e Historial", weight="bold"),
                                ft.Row([
                                    ft.ElevatedButton("Limpiar Historial de Búsqueda", icon="delete_sweep",
                                                     on_click=lambda _: self.engine.clear_history("busquedas") or self.page.open(ft.SnackBar(ft.Text("Historial de búsqueda limpiado")))),
                                    ft.ElevatedButton("Limpiar Todo el Historial", icon="auto_delete",
                                                     on_click=lambda _: self.engine.clear_history("todo") or self.page.open(ft.SnackBar(ft.Text("Todo el historial ha sido eliminado")))),
                                ]),
                                ft.Divider(),
                                ft.Text("Backups Recientes", weight="bold"),
                                ft.Container(backups_list, height=200),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon("info_outline", size=16, color=Theme.INFO),
                                    ft.Text("Los backups se guardan en la carpeta /backups y se mantienen por 7 días.", size=12, color=Theme.TEXT_SECONDARY),
                                ]),
                            ], spacing=Spacing.MD),
                            padding=Spacing.LG,
                        )
                    ),
                ],
                expand=True,
            )
        ], expand=True, scroll=ft.ScrollMode.ALWAYS)

        render_backups()


def main(page: ft.Page):
    print("DEBUG: >>> Entrando a main()")
    try:
        print("DEBUG: >>> Creando LexViridisApp...")
        LexViridisApp(page)
        print("DEBUG: >>> LexViridisApp creado OK")
    except Exception as e:
        print(f"DEBUG: >>> ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    ft.app(target=main)
