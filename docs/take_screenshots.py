"""
take_screenshots.py — LEX VIRIDIS
===================================
Genera capturas de pantalla automáticas de cada vista principal y las guarda en:
    assets/screenshots/dashboard.png
    assets/screenshots/search.png
    assets/screenshots/ai_assistant.png
    assets/screenshots/library.png

Uso:
    python docs/take_screenshots.py

Requisitos: Pillow (ya incluido en requirements.txt)
No requiere API Key ni credenciales reales.
"""

import sys
import os
import types
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

# ── 1. Parchear license_system ANTES de importar main.py ──────────────────────
#    main.py hace `from license_system import LicenseManager` al nivel de módulo,
#    así que debemos registrar el módulo falso antes de cualquier import de main.

_MOCK_LICENSE = {
    "valid": True,
    "user":  "Demo FEMA",
    "plan":  "institucional",
    "type":  "institucional",
}

_fake_lic_mod = types.ModuleType("license_system")

class _FakeLicenseManager:
    @staticmethod
    def load_saved_license():
        return "DEMO-DEMO-DEMO-DEMO"

    @staticmethod
    def validate_license(key):
        return _MOCK_LICENSE

    @staticmethod
    def save_license(key):
        pass

_fake_lic_mod.LicenseManager = _FakeLicenseManager
sys.modules["license_system"] = _fake_lic_mod

# ── 2. Importar app ────────────────────────────────────────────────────────────
from main import MainApp  # noqa: E402  (debe ir después del patch)
from PIL import ImageGrab  # noqa: E402

# ── 3. Configuración de capturas ───────────────────────────────────────────────
SCREENSHOTS_DIR = ROOT / "assets" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Orden de captura: (view_id, archivo_destino, espera_ms)
# La espera debe cubrir: animación de transición (~300ms) + carga de datos en thread
VIEWS = [
    ("dashboard", "dashboard.png",    4000),  # consulta DB stats en background thread
    ("search",    "search.png",       2500),  # carga índice FTS + render widgets
    ("ai",        "ai_assistant.png", 2000),  # solo UI, no pre-carga datos
    ("library",   "library.png",      3000),  # lista normas desde DB
]

_MOCK_USER = {"id": 1, "username": "Demo", "role": "admin", "token": "demo-token"}


# ── 4. Subclase de MainApp con captura automática ─────────────────────────────
class ScreenshotApp(MainApp):
    """
    Hereda de MainApp pero sobreescribe _decide_initial_view para:
      - Saltarse el login y la verificación de licencia
      - Iniciar la secuencia automática de navegación + captura
    """

    def _decide_initial_view(self):
        """Override: inyectar usuario demo y arrancar secuencia de capturas."""
        self.current_user = _MOCK_USER
        # 1200ms: esperar que la ventana esté maximizada y estabilizada
        self.after(1200, lambda: self._capture_sequence(0))

    def _capture_sequence(self, idx):
        """Navega a la vista[idx], espera el render + carga de datos y captura."""
        if idx >= len(VIEWS):
            print(f"\n  Todas las capturas guardadas en: {SCREENSHOTS_DIR}\n")
            self.after(400, self.destroy)
            return

        view_id, filename, wait_ms = VIEWS[idx]
        print(f"  [{idx + 1}/{len(VIEWS)}] Vista '{view_id}' (esperando {wait_ms}ms)...",
              end="", flush=True)

        self.select_view(view_id)
        # Esperar: animación de transición + tiempo de carga de datos en thread
        self.after(wait_ms, lambda: self._do_capture(filename, idx))

    def _do_capture(self, filename, idx):
        """Captura el área de la ventana y guarda el PNG."""
        self.update_idletasks()
        self.update()  # forzar repintado pendiente antes de capturar

        x  = self.winfo_rootx()
        y  = self.winfo_rooty()
        x2 = x + self.winfo_width()
        y2 = y + self.winfo_height()

        img = ImageGrab.grab(bbox=(x, y, x2, y2))
        out_path = SCREENSHOTS_DIR / filename
        img.save(str(out_path), "PNG")

        kb = out_path.stat().st_size // 1024
        print(f" guardado ({kb} KB) -> {out_path.name}")

        # Pausa entre vistas para que la transición no interfiera
        self.after(500, lambda: self._capture_sequence(idx + 1))


# ── 5. Punto de entrada ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  LEX VIRIDIS — Generador de Capturas Automáticas")
    print("=" * 55)
    print(f"  Destino : {SCREENSHOTS_DIR}")
    print(f"  Vistas  : {', '.join(v for v, _, _ in VIEWS)}")
    print()
    total_seg = (1200 + sum(w for _, _, w in VIEWS) + 500 * len(VIEWS)) // 1000
    print(f"  La ventana se abrira maximizada. No muevas el raton")
    print(f"  ni cambies de ventana durante el proceso (~{total_seg} seg).")
    print()

    app = ScreenshotApp()
    app.mainloop()

    print("  Listo.")
