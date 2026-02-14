"""
LEX VIRIDIS - Sistema de Diseño Profesional
Elementos UI consistentes, colores y tipografía.
"""

import flet as ft
from dataclasses import dataclass

# === APILADO DE COLORES SEGURO (COMPATIBILIDAD FLET <0.21 y >=0.21) ===
class SafeColors:
    """Clase de compatibilidad para usar colores en cualquier versión de Flet."""
    # Colores Básicos
    BLACK = "black"
    WHITE = "white"
    TRANSPARENT = "transparent"
    
    # Material Colors (Definidos explícitamente para estabilidad)
    GREEN_700 = "#388E3C"
    GREEN_600 = "#43A047"
    GREEN_300 = "#81C784"
    GREEN_100 = "#C8E6C9"
    TEAL_700 = "#00796B"
    AMBER_700 = "#FFA000"
    AMBER_600 = "#FFB300"
    AMBER_200 = "#FFE082"
    AMBER_50 = "#FFF8E1"
    BLUE_700 = "#1976D2"
    BLUE = "#2196F3"
    BLUE_50 = "#E3F2FD"
    RED = "#F44336"
    RED_400 = "#EF5350"
    ORANGE = "#FF9800"
    PURPLE = "#9C27B0"
    GREEN_50 = "#E8F5E9"
    GREEN_400 = "#66BB6A"
    GREY_500 = "#9E9E9E"
    
    # Opacidad (Aproximación Hex si no existe en versión antigua)
    BLACK87 = "#DD000000" 
    
    @staticmethod
    def with_opacity(opacity: float, color: str) -> str:
        """Aplica opacidad de manera segura."""
        try:
            return ft.Colors.with_opacity(opacity, color)
        except AttributeError:
            # Fallback simple si falla la función
            return color 

Colors = SafeColors


# === TEMA DE COLORES ===
class Theme:
    """Paleta de colores institucional."""
    
    # Primarios (Verde Legal/Ambiental)
    PRIMARY = "#1B5E20"
    PRIMARY_LIGHT = "#4CAF50"
    PRIMARY_DARK = "#0D3818"
    
    # Secundarios
    SECONDARY = "#00695C"      # Teal profundo
    ACCENT = "#D4AF37"         # Dorado institucional
    
    # Estados
    SUCCESS = "#2E7D32"
    WARNING = "#F57C00"
    ERROR = "#C62828"
    INFO = "#0288D1"
    
    # Neutrales
    BACKGROUND = "#FAFAFA"
    SURFACE = "#FFFFFF"
    SURFACE_VARIANT = "#F5F5F5"
    
    # Texto
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    TEXT_ON_PRIMARY = "#FFFFFF"
    
    # Bordes
    BORDER = "#E0E0E0"
    DIVIDER = "#EEEEEE"


# === TIPOGRAFÍA ===
class Typography:
    """Sistema de tipografía consistente."""
    
    # Tamaños
    DISPLAY = 40
    HEADLINE = 28
    TITLE = 22
    SUBTITLE = 18
    BODY = 15
    CAPTION = 13
    OVERLINE = 11
    
    # Pesos
    LIGHT = ft.FontWeight.W_300
    REGULAR = ft.FontWeight.W_400
    MEDIUM = ft.FontWeight.W_500
    SEMIBOLD = ft.FontWeight.W_600
    BOLD = ft.FontWeight.W_700


# === ESPACIADO ===
class Spacing:
    """Sistema de espaciado 8pt grid."""
    
    NONE = 0
    XXS = 2
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48
    XXXL = 64


# === RADIOS ===
class Radius:
    """Radios de borde consistentes."""
    
    NONE = 0
    SM = 4
    MD = 8
    LG = 12
    XL = 16
    FULL = 100


# === COMPONENTES REUTILIZABLES ===

def create_theme() -> ft.Theme:
    """Crea el tema Flet completo. Compatible con Flet 0.25.2+ y modo .exe."""
    try:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=Theme.PRIMARY,
                secondary=Theme.SECONDARY,
                surface=Theme.SURFACE,
                error=Theme.ERROR,
            ),
            visual_density="comfortable",
        )
    except TypeError:
        # Fallback: si ColorScheme rechaza algún parámetro en esta versión de Flet
        try:
            return ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=Theme.PRIMARY,
                ),
                visual_density="comfortable",
            )
        except Exception:
            return ft.Theme()


class UIComponents:
    """Fábrica de componentes UI consistentes."""
    
    @staticmethod
    def primary_button(text: str, on_click=None, icon=None, disabled=False, **kwargs) -> ft.ElevatedButton:
        _StateClass = getattr(ft, 'ControlState', getattr(ft, 'MaterialState', None))
        bgcolor_val = Theme.PRIMARY
        if _StateClass:
            bgcolor_val = {
                _StateClass.DEFAULT: Theme.PRIMARY,
                _StateClass.HOVERED: Theme.PRIMARY_LIGHT,
                _StateClass.DISABLED: Theme.TEXT_DISABLED,
            }
        return ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            disabled=disabled,
            style=ft.ButtonStyle(
                bgcolor=bgcolor_val,
                color=Theme.TEXT_ON_PRIMARY,
                padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                elevation=2,
            ),
            **kwargs
        )

    @staticmethod
    def secondary_button(text: str, on_click=None, icon=None, **kwargs) -> ft.OutlinedButton:
        return ft.OutlinedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=Theme.PRIMARY,
                padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
                shape=ft.RoundedRectangleBorder(radius=Radius.MD),
                side=ft.BorderSide(width=1.5, color=Theme.PRIMARY),
            ),
            **kwargs
        )

    @staticmethod
    def text_button(text: str, on_click=None, icon=None, **kwargs) -> ft.TextButton:
        return ft.TextButton(
            text=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color=Theme.PRIMARY,
                padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
            ),
            **kwargs
        )
    
    @staticmethod
    def card(content, padding=Spacing.MD, elevation=1, on_click=None, **kwargs) -> ft.Container:
        shadow_blur = 4 if elevation == 1 else 8 if elevation == 2 else 12
        shadow_opacity = 0.08 if elevation == 1 else 0.12 if elevation == 2 else 0.16
        
        return ft.Container(
            content=content,
            bgcolor=Theme.SURFACE,
            border_radius=Radius.LG,
            padding=padding,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=shadow_blur,
                color=Colors.with_opacity(shadow_opacity, Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            on_click=on_click,
            animate=ft.Animation(200, "easeOut"),
            **kwargs
        )
    
    @staticmethod
    def search_field(hint_text="Buscar...", on_submit=None, on_change=None) -> ft.TextField:
        return ft.TextField(
            hint_text=hint_text,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=Radius.XL,
            bgcolor=Theme.SURFACE,
            border_color=Theme.BORDER,
            focused_border_color=Theme.PRIMARY,
            content_padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
            text_size=Typography.BODY,
            hint_style=ft.TextStyle(color=Theme.TEXT_SECONDARY),
            on_submit=on_submit,
            on_change=on_change,
        )
    
    @staticmethod
    def chip(label: str, selected=False, on_click=None, icon=None) -> ft.Chip:
        return ft.Chip(
            label=ft.Text(label, size=Typography.CAPTION),
            leading=ft.Icon(icon, size=18, color=Theme.TEXT_ON_PRIMARY if selected else Theme.TEXT_PRIMARY) if icon else None,
            bgcolor=Theme.PRIMARY if selected else Theme.SURFACE_VARIANT,
            label_style=ft.TextStyle(
                color=Theme.TEXT_ON_PRIMARY if selected else Theme.TEXT_PRIMARY
            ),
            on_click=on_click,
        )
    
    @staticmethod
    def divider() -> ft.Divider:
        return ft.Divider(height=1, color=Theme.DIVIDER)
    
    @staticmethod
    def heading(text: str, level: int = 1, color=None) -> ft.Text:
        sizes = {1: Typography.HEADLINE, 2: Typography.TITLE, 3: Typography.SUBTITLE}
        weights = {1: Typography.BOLD, 2: Typography.SEMIBOLD, 3: Typography.MEDIUM}
        
        return ft.Text(
            text,
            size=sizes.get(level, Typography.TITLE),
            weight=weights.get(level, Typography.MEDIUM),
            color=color or Theme.TEXT_PRIMARY,
        )
    
    @staticmethod
    def body_text(text: str, secondary=False) -> ft.Text:
        return ft.Text(
            text,
            size=Typography.BODY,
            color=Theme.TEXT_SECONDARY if secondary else Theme.TEXT_PRIMARY,
        )
    
    @staticmethod
    def caption(text: str) -> ft.Text:
        return ft.Text(
            text,
            size=Typography.CAPTION,
            color=Theme.TEXT_SECONDARY,
        )
    
    @staticmethod
    def icon_badge(icon, color=None, size=24) -> ft.Container:
        return ft.Container(
            content=ft.Icon(icon, size=size, color=color or Theme.PRIMARY),
            bgcolor=Colors.with_opacity(0.1, color or Theme.PRIMARY),
            border_radius=Radius.MD,
            padding=Spacing.SM,
        )
    
    @staticmethod
    def progress_indicator(size=40) -> ft.ProgressRing:
        return ft.ProgressRing(
            width=size,
            height=size,
            color=Theme.PRIMARY,
            stroke_width=3,
        )
    
    @staticmethod
    def empty_state(icon, title: str, subtitle: str, action_text: str = None, on_action=None) -> ft.Container:
        controls = [
            ft.Icon(icon, size=80, color=Theme.TEXT_DISABLED),
            ft.Container(height=Spacing.MD),
            ft.Text(title, size=Typography.TITLE, weight=Typography.SEMIBOLD, color=Theme.TEXT_PRIMARY),
            ft.Text(subtitle, size=Typography.BODY, color=Theme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
        ]
        
        if action_text and on_action:
            controls.extend([
                ft.Container(height=Spacing.LG),
                UIComponents.secondary_button(action_text, on_click=on_action),
            ])
        
        return ft.Container(
            content=ft.Column(
                controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=Spacing.XL,
        )
    
    @staticmethod
    def error_state(title: str, message: str, on_retry=None) -> ft.Container:
        return UIComponents.empty_state(
            icon=ft.Icons.ERROR_OUTLINE,
            title=title,
            subtitle=message,
            action_text="Reintentar" if on_retry else None,
            on_action=on_retry,
        )
    
    @staticmethod
    def loading_state(message: str = "Cargando...") -> ft.Container:
        return ft.Container(
            content=ft.Column([
                UIComponents.progress_indicator(),
                ft.Container(height=Spacing.MD),
                ft.Text(message, size=Typography.BODY, color=Theme.TEXT_SECONDARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
    
    @staticmethod
    def hero_header(image_src: str, title: str, subtitle: str) -> ft.Container:
        return ft.Container(
            content=ft.Stack([
                ft.Image(
                    src=image_src,
                    width=float("inf"),
                    height=110,
                    fit="cover",
                    border_radius=Radius.LG,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(title, size=Typography.HEADLINE, weight=Typography.BOLD, color=Colors.WHITE),
                        ft.Text(subtitle, size=Typography.BODY, color=Colors.with_opacity(0.9, Colors.WHITE)),
                    ], spacing=0),
                    padding=Spacing.LG,
                    alignment=ft.Alignment(-1, 1),
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(0, -1),
                        end=ft.Alignment(0, 1),
                        colors=[Colors.TRANSPARENT, Colors.with_opacity(0.8, Colors.BLACK87)],
                    ),
                    border_radius=Radius.LG,
                )
            ]),
            margin=ft.margin.only(bottom=Spacing.LG),
            border_radius=Radius.LG,
            height=110,
        )



class ResultCard(ft.Container):
    """Tarjeta de resultado de búsqueda profesional."""
    
    def __init__(self, result: dict, on_click=None, on_pdf_click=None):
        from pathlib import Path
        
        # Lógica para determinar el título a mostrar:
        # 1. 'titulo' explícito (ej: desde Novedades)
        # 2. Nombre de archivo limpio si existe
        # 3. 'Desconocido' como fallback
        raw_file = result.get('file', 'Desconocido')
        file_name = Path(raw_file).name if raw_file else "Desconocido"
        display_title = result.get('titulo') or file_name
        
        page = result.get('page', 1)
        relevance = result.get('relevance', 0)
        context = result.get('context', '...')
        
        # Determinar icono según tipo
        if "Decreto" in str(display_title) or "Decreto" in file_name:
            icon = ft.Icons.GAVEL
            icon_color = Theme.PRIMARY
        elif "Acuerdo" in str(display_title) or "Acuerdo" in file_name:
            icon = ft.Icons.ASSIGNMENT
            icon_color = Theme.WARNING
        elif "Ley" in str(display_title) or "Ley" in file_name:
            icon = ft.Icons.BALANCE
            icon_color = Theme.SECONDARY
        else:
            icon = ft.Icons.DESCRIPTION
            icon_color = Theme.TEXT_SECONDARY
        
        # Contenido
        relevance_stars = ""
        # Convertir relevancia a estrellas (0-10 -> 0-5 estrellas)
        num_stars = min(5, max(0, int(relevance / 2)))
        relevance_stars = "⭐" * num_stars + "☆" * (5 - num_stars)
        
        matches = result.get('matches', 0)
        is_norma = result.get('is_norma', False)
        
        # Construir fila de metadatos condicionalmente
        meta_row_controls = []
        if not is_norma:
            meta_row_controls = [
                ft.Text(f"Página {page}", size=Typography.CAPTION, color=Theme.ACCENT, weight=Typography.MEDIUM),
                ft.Text("•", size=Typography.CAPTION, color=Theme.TEXT_DISABLED),
                ft.Text(f"Relevancia: {relevance:.1f}", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
                ft.Text("•", size=Typography.CAPTION, color=Theme.TEXT_DISABLED),
                ft.Icon(ft.Icons.LOCATION_ON, size=12, color=Theme.PRIMARY),
                ft.Text(f"{matches} coincidencias", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY),
            ]
        else:
            # Para normas completas mostrar fecha o mensaje simple
            meta_row_controls = [
                 ft.Icon(ft.Icons.CALENDAR_MONTH, size=12, color=Theme.TEXT_SECONDARY),
                 ft.Text("Documento completo", size=Typography.CAPTION, color=Theme.TEXT_SECONDARY)
            ]

        content = ft.Row([
            UIComponents.icon_badge(icon, icon_color, size=28),
            ft.Container(width=Spacing.MD),
            ft.Column([
                ft.Row([
                    ft.Text(
                        display_title,
                        size=Typography.SUBTITLE,
                        weight=Typography.SEMIBOLD,
                        color=Theme.TEXT_PRIMARY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                    ft.Text(relevance_stars, size=Typography.CAPTION, color=Theme.ACCENT),
                ]),
                ft.Row(meta_row_controls, spacing=Spacing.SM),
                ft.Container(height=Spacing.XS),
                # Usar Markdown para permitir resaltado en negrita
                ft.Markdown(
                    context,
                    selectable=False,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                ),
            ], expand=True, spacing=Spacing.XXS),
            ft.IconButton(
                ft.Icons.PICTURE_AS_PDF,
                icon_color=Theme.ERROR,
                tooltip="Abrir PDF Original",
                on_click=on_pdf_click if on_pdf_click else on_click
            ) if result.get('file') != "Desconocido" else ft.Container(),
            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=Theme.TEXT_DISABLED),
        ], alignment=ft.MainAxisAlignment.START)
        
        super().__init__(
            content=content,
            bgcolor=Theme.SURFACE,
            border_radius=Radius.LG,
            padding=Spacing.MD,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=Colors.with_opacity(0.08, Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
            on_click=on_click,
            on_hover=self._on_hover,
            animate=ft.Animation(200, "easeOut"),
            border=ft.border.all(1, Theme.BORDER),
        )
    
    def _on_hover(self, e):
        if e.data == "true":
            self.border = ft.border.all(1, Theme.PRIMARY)
            self.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=Colors.with_opacity(0.12, Colors.BLACK),
                offset=ft.Offset(0, 4),
            )
        else:
            self.border = ft.border.all(1, Theme.BORDER)
            self.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=Colors.with_opacity(0.08, Colors.BLACK),
                offset=ft.Offset(0, 2),
            )
        self.update()