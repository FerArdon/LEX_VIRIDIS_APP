
import flet as ft
Colors = getattr(ft, "Colors", getattr(ft, "colors", None))
if Colors is None:
    raise ImportError("No se pudo cargar el módulo de colores de Flet.")
from .search_engine import SearchEngine
from .indexer import Indexer
from .ia_gemini import GeminiClient, PromptGenerator
from .config import config
import logging
from pathlib import Path
import threading

import time
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LexViridisFletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_page()
        
        # Estado
        self.search_results = []
        self.current_query = ""
        self.is_ready = False
        self.indexer = None
        self.engine = None
        self.gemini = None
        
        # Componentes UI
        self.build_ui()
        
        # Iniciar carga en background
        self.show_loading_screen()
        # Usar timer pequeño para dar tiempo a renderizar antes de bloquear (si fuera el caso)
        # o threading real.
        threading.Thread(target=self.initialize_backend, daemon=True).start()

    def initialize_backend(self):
        """Carga componentes pesados en segundo plano."""
        try:
            time.sleep(0.5) # UI refresh
            self.indexer = Indexer()
            self.indexer.load_or_create_index()
            self.engine = SearchEngine(self.indexer.text_index)
            self.gemini = GeminiClient()
            
            self.is_ready = True
            # Llamar a UI update de forma segura
            self.finalize_loading()
        except Exception as e:
            logger.error(f"Error loading backend: {e}")
            print(f"Error loading backend: {e}")

    def finalize_loading(self):
        """Elimina pantalla de carga y muestra buscador."""
        # Flet threading safety: page.update() is usually fine if thread-safe
        # but pure Flet best practice is often page.run_task or simply calling update.
        # We'll try direct update first.
        try:
            if hasattr(self, 'loading_overlay') and self.loading_overlay in self.page.overlay:
                 self.page.overlay.remove(self.loading_overlay)
            
            self.txt_search.disabled = False
            self.btn_search.disabled = False
            self.page.update()
        except Exception as e:
            logger.error(f"Error updating UI: {e}")

    def show_loading_screen(self):
        """Muestra overlay de carga."""
        self.loading_overlay = ft.Container(
            content=ft.Column([
                ft.ProgressRing(),
                ft.Text("Iniciando LEX VIRIDIS...", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Cargando normativa ambiental...", size=12, color=Colors.GREY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            bgcolor=Colors.with_opacity(0.9, Colors.WHITE),
            expand=True
        )
        self.page.overlay.append(self.loading_overlay)
        
        # Deshabilitar inputs mientras carga
        self.txt_search.disabled = True
        self.btn_search.disabled = True
        self.page.update()

    def setup_page(self):
        """Configuración inicial de la página."""
        self.page.title = "LEX VIRIDIS - Compendio Ambiental"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        if config.ICON_PATH:
             self.page.window_icon = str(config.ICON_PATH)

    def build_ui(self):
        """Construye la interfaz principal."""
        
        # --- Header ---
        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.FOREST, size=30, color=Colors.WHITE),
                    ft.Text("LEX VIRIDIS", size=24, weight=ft.FontWeight.BOLD, color=Colors.WHITE),
                    ft.Container(expand=True), # Spacer
                    ft.IconButton(ft.Icons.SETTINGS, icon_color=Colors.WHITE, on_click=self.open_settings),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=Colors.TEAL_700,
        )

        # --- Buscador ---
        self.txt_search = ft.TextField(
            hint_text="Buscar en normativa ambiental (ej. 'licencia ambiental', 'tala')",
            expand=True,
            on_submit=self.perform_search,
            border_radius=10,
            prefix_icon=ft.Icons.SEARCH,
        )
        
        self.btn_search = ft.ElevatedButton(
            "Buscar", 
            icon=ft.Icons.SEARCH, 
            on_click=self.perform_search,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            )
        )
        
        self.btn_analyze = ft.ElevatedButton(
            "Analizar con IA", 
            icon=ft.Icons.AUTO_AWESOME, 
            on_click=self.start_ai_analysis,
            style=ft.ButtonStyle(
                color=Colors.WHITE,
                bgcolor=Colors.PURPLE_600,
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20
            ),
            visible=False # Se muestra solo cuando hay resultados
        )

        search_bar = ft.Container(
            content=ft.Column([
                ft.Text("Buscador Jurídico Ambiental", size=32, weight=ft.FontWeight.BOLD, color=Colors.TEAL_900),
                ft.Text("Encuentra leyes, reglamentos y acuerdos de FEMA al instante.", size=16, color=Colors.GREY_700),
                ft.Divider(height=20, color=Colors.TRANSPARENT),
                ft.Row([self.txt_search, self.btn_search, self.btn_analyze], alignment=ft.MainAxisAlignment.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50,
            bgcolor=Colors.WHITE,
        )

        # --- Resultados ---
        self.results_list = ft.ListView(expand=1, spacing=10, padding=20)
        self.results_container = ft.Column([
            ft.Text("Resultados", size=20, weight=ft.FontWeight.BOLD),
            self.results_list
        ], visible=False, expand=True)

        # --- Layout Principal ---
        self.page.add(
            self.header,
            search_bar,
            self.results_container
        )

    def perform_search(self, e):
        """Ejecuta la búsqueda."""
        query = self.txt_search.value.strip()
        if not query:
            return

        self.current_query = query
        self.page.splash = ft.ProgressBar()
        self.page.update()

        # Ejecutar búsqueda (simulamos async para no bloquear UI, aunque el engine es sincrono)
        # Idealmente mover engine a un thread si es muy lento, pero el engine de python es rapido en memoria.
        start_time = time.time()
        self.search_results = self.engine.search(query, operator="AND")[:50] # Limit 50
        
        self.display_results()
        
        self.page.splash = None
        self.btn_analyze.visible = True
        self.results_container.visible = True
        self.page.update()

    def display_results(self):
        """Renderiza la lista de resultados."""
        self.results_list.controls.clear()
        
        if not self.search_results:
            self.results_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=64, color=Colors.GREY_400),
                        ft.Text("No se encontraron resultados.", color=Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.Alignment.CENTER,
                    padding=50
                )
            )
            return

        for res in self.search_results:
            file_name = Path(res['file']).name
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PICTURE_AS_PDF, color=Colors.RED_500),
                            title=ft.Text(file_name, weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"Página {res['page']} • Relevancia: {res['relevance']:.1f}/10"),
                            on_click=lambda e, path=res['file'], page=res['page']: self.open_pdf(path, page)
                        ),
                        ft.Container(
                            content=ft.Text(
                                res.get('context', '...'), 
                                size=12, 
                                color=Colors.GREY_700, 
                                text_align=ft.TextAlign.JUSTIFY
                            ),
                            padding=ft.padding.only(left=20, right=20, bottom=20)
                        )
                    ]),
                    padding=5
                ),
                elevation=2,
            )
            self.results_list.controls.append(card)

    def open_pdf(self, path, page_num):
        """Maneja la apertura del PDF."""
        # Por ahora usamos el viewer nativo del sistema ya que Flet no tiene visor PDF integrado simple.
        # Podríamos usar os.startfile o similar.
        import os
        try:
             # En Windows esto abre con el visor predeterminado
             # Idealmente aquí integurariamos la lógica de resaltado de 'PDFViewerFixed'
             # pero primero probemos la UI.
             from .pdf_viewer_fixed import PDFViewerFixed
             # Llamamos al método estático (asumiendo que funciona sin TK)
             # PDFViewerFixed usa 'fitz' para crear un PDF temporal resaltado, luego usa 'open_with_native_viewer'
             PDFViewerFixed.highlight_and_open_pdf(Path(path), page_num, self.current_query)
        except Exception as e:
            self.show_snack(f"Error al abrir PDF: {e}", color=Colors.RED)

    def start_ai_analysis(self, e):
        """Inicia el análisis con Gemini."""
        if not self.gemini.api_key:
            self.prompt_api_key()
            return
            
        self.show_ai_dialog()

    def prompt_api_key(self):
        """Dialogo para pedir API Key."""
        def close_dlg(e):
             self.page.dialog.open = False
             self.page.update()

        def save_key(e):
            if txt_key.value:
                self.gemini.set_api_key(txt_key.value)
                self.show_snack("API Key guardada correctamente")
                close_dlg(e)
                self.show_ai_dialog() # Iniciar analisis inmediatamente

        txt_key = ft.TextField(label="Gemini API Key", password=True, can_reveal_password=True)
        
        dlg = ft.AlertDialog(
            title=ft.Text("Configuración de IA"),
            content=ft.Column([
                ft.Text("Se requiere una API Key de Google Gemini para continuar."),
                txt_key
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.ElevatedButton("Guardar", on_click=save_key),
            ],
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def show_ai_dialog(self):
        """Muestra el diálogo para consultar a la IA."""
        # Input para la pregunta del usuario
        self.txt_ai_query = ft.TextField(
            label="Consulta a la IA",
            value=self.current_query,  # Pre-llenar con la búsqueda
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True # TextField debe expandirse en el Row
        )
        
        # Botón para enviar consulta
        btn_ask = ft.IconButton(
            icon=ft.Icons.SEND, 
            icon_color=Colors.TEAL,
            on_click=lambda e: self.run_ai_analysis(),
            tooltip="Consultar IA"
        )
        
        # Área de respuesta
        self.response_text = ft.Markdown(
            "Escribe tu consulta arriba y presiona enviar. La IA responderá basándose en los documentos encontrados.", 
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
        )
        self.progress_bar = ft.ProgressBar(visible=False)
        
        # Contenedor de respuesta scrollable
        scroll_content = ft.ListView(
            controls=[self.response_text],
            expand=True,
            spacing=10,
            auto_scroll=False
        )
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color=Colors.PURPLE), ft.Text("Asistente Legal IA")]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Contexto: Resultados de la búsqueda actual", size=12, color=Colors.GREY),
                    ft.Row([self.txt_ai_query, btn_ask], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                    ft.Divider(),
                    self.progress_bar,
                    scroll_content
                ], expand=True),
                width=800,
                height=600,
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.close_ai_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def run_ai_analysis(self):
        """Ejecuta el análisis en un hilo."""
        query = self.txt_ai_query.value
        if not query:
            return

        self.progress_bar.visible = True
        self.response_text.value = "⏳ Analizando contexto y generando respuesta..."
        self.page.update()

        def _target():
            context = []
            # Usar más contexto si es posible, digamos top 5
            for res in self.search_results[:5]:
                context.append(f"DOC: {Path(res['file']).name}, PAG {res['page']}\n{res.get('context', '')}")
            
            prompt = PromptGenerator.generar_analisis_caso(query, context)
            response = self.gemini.consultar(prompt)
            
            self.response_text.value = response
            self.progress_bar.visible = False
            self.page.update()

        threading.Thread(target=_target, daemon=True).start()

    def close_ai_dialog(self):
        self.page.dialog.open = False
        self.page.update()
        
    def open_settings(self, e):
        """Abre el panel de configuración."""
        
        # 1. API Key Input
        current_key = self.gemini.api_key if self.gemini else ""
        txt_api_key = ft.TextField(
            label="Gemini API Key", 
            value=current_key,
            password=True, 
            can_reveal_password=True,
            expand=True
        )
        
        def save_settings(e):
            new_key = txt_api_key.value.strip()
            if new_key:
                if self.gemini:
                    self.gemini.set_api_key(new_key)
                self.show_snack("Configuración guardada", Colors.GREEN)
            self.close_dialog()

        def reindex_db(e):
            self.show_snack("Re-indexando documentos... esto puede tardar.", Colors.ORANGE)
            try:
                # Ejecutar reindexación en thread
                def _reindex():
                    self.indexer.load_or_create_index(force_rebuild=True)
                    # Recargar engine
                    self.engine = SearchEngine(self.indexer.text_index)
                    print("Index rebuild complete")
                    # No podemos llamar a show_snack directamente desde thread de forma segura en todas las versiones,
                    # pero intentaremos actualizar un estado o simplemente imprimir.
                    # En Flet 0.21+ es mejor usar page.run_task o similar.
                    # Por ahora dejamos que el usuario vea el log o confíe.
                
                threading.Thread(target=_reindex, daemon=True).start()
                self.close_dialog()
                
            except Exception as ex:
                self.show_snack(f"Error reindexando: {ex}", Colors.RED)

        dlg = ft.AlertDialog(
            title=ft.Text("Configuración"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("IA Geminis", weight=ft.FontWeight.BOLD),
                    txt_api_key,
                    ft.Divider(),
                    ft.Text("Base de Datos", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Documentos indexados: {len(self.engine.text_index) if self.engine else 0}"),
                    ft.ElevatedButton(
                        "Reconstruir Índice", 
                        icon=ft.Icons.REFRESH, 
                        color=Colors.ERROR,
                        on_click=reindex_db
                    )
                ], tight=True, spacing=20),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog()),
                ft.ElevatedButton("Guardar", on_click=save_settings)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()

    def show_snack(self, msg, color=Colors.TEAL):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    print("Initializing Flet App...")
    try:
        app = LexViridisFletApp(page)
        print("Flet App initialized.")
    except Exception as e:
        print(f"Error initializing app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ft.app(target=main)
