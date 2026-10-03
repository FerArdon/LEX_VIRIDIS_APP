"""Pruebas de la capa de compatibilidad con Flet >= 0.80 (lexviridis/flet_compat.py).

No abren ventanas: solo verifican que la API antigua que usa la UI sigue
construyendo controles validos sobre el Flet instalado.
"""

import flet as ft
import pytest

import lexviridis.flet_compat  # noqa: F401  (aplica los parches al importar)


def test_page_recupera_api_antigua():
    for nombre in ("show_snack_bar", "open", "close", "snack_bar", "dialog", "set_clipboard"):
        assert hasattr(ft.Page, nombre), nombre


def test_set_clipboard_usa_el_servicio_asincrono():
    """Copiar texto (boton 'copiar' de la IA) fallaba: page.set_clipboard ya no existe en Flet 0.80+."""
    import asyncio

    copiado = []

    class FalsoPortapapeles:
        async def set(self, valor):
            copiado.append(valor)

    class FalsaPagina:
        clipboard = FalsoPortapapeles()

        def run_task(self, manejador, *args, **kwargs):
            asyncio.run(manejador(*args, **kwargs))

    ft.Page.set_clipboard(FalsaPagina(), "Art. 25: texto copiado")
    assert copiado == ["Art. 25: texto copiado"]


@pytest.mark.parametrize(
    "fabrica",
    [
        lambda: ft.Chip(label=ft.Text("x"), label_style=ft.TextStyle(size=12)),
        lambda: ft.TextField(label="x", helper_text="ayuda"),
        lambda: ft.PopupMenuItem(text="Abrir"),
        lambda: ft.FloatingActionButton(text="Ayuda"),
        lambda: ft.Dropdown(options=[ft.dropdown.Option("a")], on_change=lambda e: None),
        lambda: ft.ColorScheme(background="#ffffff"),
    ],
    ids=["Chip", "TextField", "PopupMenuItem", "FAB", "Dropdown", "ColorScheme"],
)
def test_kwargs_renombrados_se_aceptan(fabrica):
    assert fabrica() is not None


def test_botones_con_content():
    assert ft.ElevatedButton(content="Entrar") is not None
    assert ft.Alignment.CENTER == ft.Alignment(0, 0)


def test_tabs_api_antigua_produce_tabs_nuevo():
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[ft.Tab(text="Uno", icon=ft.Icons.HOME, content=ft.Text("a")), ft.Tab(text="Dos", content=ft.Text("b"))],
        expand=True,
    )
    assert type(tabs).__name__ == "Tabs"
    assert tabs.length == 2
    assert tabs.selected_index == 0


def test_tabs_solo_encabezados():
    tabs = ft.Tabs(selected_index=0, tabs=[ft.Tab(text="A"), ft.Tab(text="B"), ft.Tab(text="C")], height=50)
    assert tabs.length == 3


def test_file_picker_acepta_on_result():
    llamadas = []
    picker = ft.FilePicker(on_result=lambda e: llamadas.append(e))
    assert picker.__dict__["on_result"] is not None
    for metodo in ("pick_files", "save_file", "get_directory_path"):
        assert callable(getattr(picker, metodo))


def test_graficos_disponibles():
    pytest.importorskip("flet_charts")
    for nombre in ("BarChart", "LineChart", "PieChart", "PieChartSection", "ChartAxis"):
        assert hasattr(ft, nombre), nombre


def test_aplicar_es_idempotente():
    antes = ft.Tabs
    lexviridis.flet_compat.aplicar()
    assert ft.Tabs is antes
