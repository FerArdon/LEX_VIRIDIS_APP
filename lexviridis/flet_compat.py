"""
Capa de compatibilidad con Flet >= 0.80.

El codigo de la UI se escribio contra la API antigua de Flet (``page.dialog``,
``page.snack_bar``, ``page.show_snack_bar``, ``FilePicker(on_result=...)``) que
fue retirada en la serie 0.80. En lugar de tocar ~150 puntos de llamada, este
modulo restaura esa API sobre la nueva (``page.show_dialog`` / ``pop_dialog`` y
``FilePicker`` asincrono).

Se activa una sola vez al importar el paquete ``lexviridis``. Es idempotente.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import flet as ft

log = logging.getLogger(__name__)
_APPLIED = False


# --------------------------------------------------------------------------- #
# Dialogos y SnackBars
# --------------------------------------------------------------------------- #
def _mostrar(page, control) -> None:
    """Muestra un dialogo/snackbar sin fallar si ya estaba en la pila."""
    if control is None:
        return
    pila = getattr(page, "_dialogs", None)
    if pila is not None and control in pila.controls:
        control.open = True
        control.update()
        return
    page.show_dialog(control)


def _cerrar(control) -> None:
    if control is None:
        return
    control.open = False
    try:
        control.update()
    except Exception:  # control aun sin montar: no hay nada que cerrar
        pass


def _patch_page() -> None:
    Page = ft.Page

    def show_snack_bar(self, snack_bar):
        _mostrar(self, snack_bar)

    def open_(self, control):
        _mostrar(self, control)

    def close_(self, control):
        _cerrar(control)

    def _make_prop(attr: str):
        def getter(self):
            return self.__dict__.get(attr)

        def setter(self, value):
            previo = self.__dict__.get(attr)
            self.__dict__[attr] = value
            if value is None:
                _cerrar(previo)
            else:
                _mostrar(self, value)

        return property(getter, setter)

    def set_clipboard(self, value):
        """API antigua ``page.set_clipboard(texto)``: ahora el portapapeles es un servicio asincrono."""

        async def copiar():
            await self.clipboard.set(value)

        self.run_task(copiar)

    if not hasattr(Page, "set_clipboard"):
        Page.set_clipboard = set_clipboard
    if not hasattr(Page, "show_snack_bar"):
        Page.show_snack_bar = show_snack_bar
    if not hasattr(Page, "open"):
        Page.open = open_
    if not hasattr(Page, "close"):
        Page.close = close_
    # En la API nueva no existen estas propiedades: se emulan.
    for nombre, attr in (("snack_bar", "_compat_snack_bar"), ("dialog", "_compat_dialog")):
        if nombre not in Page.__dict__ and not hasattr(Page, nombre):
            setattr(Page, nombre, _make_prop(attr))


# --------------------------------------------------------------------------- #
# FilePicker: de callback ``on_result`` (viejo) a corrutinas (nuevo)
# --------------------------------------------------------------------------- #
def _pagina_de(picker):
    try:
        return picker.page
    except Exception:
        return ft.context.page


def _patch_file_picker() -> None:
    FP = ft.FilePicker
    if getattr(FP, "_compat_patched", False):
        return

    init_original = FP.__init__

    def __init__(self, *args, on_result=None, **kwargs):
        init_original(self, *args, **kwargs)
        self.__dict__["on_result"] = on_result

    def _lanzar(self, nombre, evento_de, **kwargs):
        """Ejecuta el metodo asincrono y entrega el resultado a ``on_result``."""
        original = getattr(FP, f"_{nombre}_async")

        async def trabajo():
            try:
                resultado = await original(self, **kwargs)
            except Exception:
                log.exception("FilePicker.%s fallo", nombre)
                resultado = None
            callback = self.__dict__.get("on_result")
            if callback:
                callback(evento_de(resultado))

        pagina = _pagina_de(self)
        servicios = getattr(pagina, "services", None)
        if servicios is not None and self not in servicios:
            servicios.append(self)
        pagina.run_task(trabajo)

    def _ev_archivos(resultado):
        archivos = list(resultado) if resultado else None
        return SimpleNamespace(files=archivos, path=None, data=None)

    def _ev_ruta(resultado):
        return SimpleNamespace(files=None, path=resultado or None, data=None)

    def pick_files(
        self,
        dialog_title=None,
        initial_directory=None,
        file_type=None,
        allowed_extensions=None,
        allow_multiple=False,
        with_data=False,
    ):
        extra = {}
        if file_type is not None:
            extra["file_type"] = file_type
        _lanzar(
            self,
            "pick_files",
            _ev_archivos,
            dialog_title=dialog_title,
            initial_directory=initial_directory,
            allowed_extensions=allowed_extensions,
            allow_multiple=allow_multiple,
            with_data=with_data,
            **extra,
        )

    def save_file(
        self,
        dialog_title=None,
        file_name=None,
        initial_directory=None,
        file_type=None,
        allowed_extensions=None,
        src_bytes=None,
    ):
        extra = {}
        if file_type is not None:
            extra["file_type"] = file_type
        _lanzar(
            self,
            "save_file",
            _ev_ruta,
            dialog_title=dialog_title,
            file_name=file_name,
            initial_directory=initial_directory,
            allowed_extensions=allowed_extensions,
            src_bytes=src_bytes,
            **extra,
        )

    def get_directory_path(self, dialog_title=None, initial_directory=None):
        _lanzar(self, "get_directory_path", _ev_ruta, dialog_title=dialog_title, initial_directory=initial_directory)

    for nombre in ("pick_files", "save_file", "get_directory_path"):
        setattr(FP, f"_{nombre}_async", getattr(FP, nombre))
    FP.__init__ = __init__
    FP.pick_files = pick_files
    FP.save_file = save_file
    FP.get_directory_path = get_directory_path
    FP._compat_patched = True


# --------------------------------------------------------------------------- #
# Parametros renombrados en los constructores
# --------------------------------------------------------------------------- #
_RENOMBRES = {
    "PopupMenuItem": {"text": "content"},
    "FloatingActionButton": {"text": "content"},
    "Chip": {"label_style": "label_text_style"},
    "TextField": {"helper_text": "helper"},
    "Dropdown": {"on_change": "on_select"},
    "ColorScheme": {"background": "surface"},
}


def _patch_renames() -> None:
    for nombre, mapa in _RENOMBRES.items():
        cls = getattr(ft, nombre, None)
        if cls is None or getattr(cls, "_compat_renames", None):
            continue
        original = cls.__init__

        def __init__(self, *args, _orig=original, _mapa=mapa, **kwargs):
            for viejo, nuevo in _mapa.items():
                if viejo in kwargs:
                    valor = kwargs.pop(viejo)
                    kwargs.setdefault(nuevo, valor)
            _orig(self, *args, **kwargs)

        cls.__init__ = __init__
        cls._compat_renames = mapa

    # Dropdown.on_change = fn  (asignacion posterior) -> on_select
    dd = getattr(ft, "Dropdown", None)
    if dd is not None and "on_change" not in dd.__dict__ and not hasattr(dd, "on_change"):
        dd.on_change = property(
            lambda self: self.on_select,
            lambda self, fn: setattr(self, "on_select", fn),
        )


# --------------------------------------------------------------------------- #
# Tabs: Tabs(tabs=[Tab(text, content)]) -> Tabs(content=Column[TabBar, TabBarView])
# --------------------------------------------------------------------------- #
def _patch_tabs() -> None:
    if getattr(ft.Tabs, "_compat_patched", False):
        return
    TabNuevo, TabsNuevo = ft.Tab, ft.Tabs

    class TabLegacy:
        """Pestana con la forma antigua (text=, icon=, content=)."""

        def __init__(self, text=None, label=None, icon=None, content=None, **_):
            self.label = label if label is not None else text
            self.icon = icon
            self.content = content

    def tabs_legacy(*args, tabs=None, **kwargs):
        if tabs is None:  # llamada con la API nueva: pasar tal cual
            return TabsNuevo(*args, **kwargs)
        items = [t if isinstance(t, TabLegacy) else TabLegacy(label=getattr(t, "label", None)) for t in tabs]
        bar_kw = {
            k: kwargs.pop(k)
            for k in (
                "scrollable",
                "tab_alignment",
                "divider_color",
                "indicator_color",
                "label_color",
                "unselected_label_color",
            )
            if k in kwargs
        }
        bar = ft.TabBar(tabs=[TabNuevo(label=t.label, icon=t.icon) for t in items], **bar_kw)
        if any(t.content is not None for t in items):
            vista = ft.TabBarView(controls=[t.content or ft.Container() for t in items], expand=True)
            contenido = ft.Column([bar, vista], spacing=0, expand=True)
        else:
            contenido = bar
        return TabsNuevo(content=contenido, length=len(items), **kwargs)

    tabs_legacy._compat_patched = True
    ft.Tab = TabLegacy
    ft.Tabs = tabs_legacy
    ft.Tabs._compat_patched = True


# --------------------------------------------------------------------------- #
# Graficos: salieron de ``flet`` al paquete ``flet-charts``
# --------------------------------------------------------------------------- #
def _patch_charts() -> None:
    try:
        import flet_charts as fch
    except ImportError:
        log.warning("flet-charts no esta instalado: los graficos del dashboard no estaran disponibles")
        return
    for nombre in (
        "BarChart",
        "BarChartGroup",
        "BarChartRod",
        "LineChart",
        "LineChartData",
        "LineChartDataPoint",
        "PieChart",
        "PieChartSection",
        "ChartAxis",
        "ChartAxisLabel",
    ):
        if not hasattr(ft, nombre) and hasattr(fch, nombre):
            setattr(ft, nombre, getattr(fch, nombre))


# --------------------------------------------------------------------------- #
# Actualizaciones de la interfaz desde hilos
# --------------------------------------------------------------------------- #
def _patch_thread_safe_updates() -> None:
    """Hace que ``page.update()`` llamado desde un hilo llegue de inmediato al cliente.

    Flet 0.82 encola los mensajes con ``asyncio.Queue.put_nowait``, que no es seguro entre hilos y no
    despierta el bucle: los cambios hechos desde un ``threading.Thread`` (splash -> login, resultados de
    busqueda...) quedaban en cola hasta que el usuario hacia clic o maximizaba la ventana.
    """
    import asyncio

    try:
        from flet.messaging.flet_socket_server import FletSocketServer
    except ImportError:
        log.warning("FletSocketServer no disponible: las actualizaciones desde hilos podrian retrasarse")
        return
    if getattr(FletSocketServer, "_compat_patched", False):
        return

    original = FletSocketServer.send_message

    def send_message(self, message):
        try:
            en_el_bucle = asyncio.get_running_loop() is self.loop
        except RuntimeError:  # sin bucle en este hilo: es un hilo de trabajo
            en_el_bucle = False
        if en_el_bucle:
            original(self, message)
        else:
            self.loop.call_soon_threadsafe(original, self, message)

    FletSocketServer.send_message = send_message
    FletSocketServer._compat_patched = True


def aplicar() -> None:
    """Activa la compatibilidad (idempotente)."""
    global _APPLIED
    if _APPLIED:
        return
    _APPLIED = True
    _patch_thread_safe_updates()
    _patch_page()
    _patch_file_picker()
    _patch_renames()
    _patch_tabs()
    _patch_charts()
    log.debug("Compatibilidad Flet aplicada (%s)", getattr(ft, "__version__", "?"))


aplicar()
