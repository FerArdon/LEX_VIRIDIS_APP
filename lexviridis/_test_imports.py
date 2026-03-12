"""Test rápido de imports y rutas para validar correcciones de empaquetado."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

errors = []
ok = []

# Test 1: config
try:
    from lexviridis.config import config

    ok.append(f"1. config OK - BASE_DIR: {config.BASE_DIR}")
except Exception as e:
    errors.append(f"1. config FAIL: {e}")

# Test 2: design_system create_theme
try:
    from lexviridis.design_system import create_theme

    theme = create_theme()
    ok.append(f"2. create_theme OK - type: {type(theme).__name__}")
except Exception as e:
    errors.append(f"2. create_theme FAIL: {e}")

# Test 3: search_engine
try:
    from lexviridis.search_engine import DB_PATH

    ok.append(f"3. search_engine OK - DB_PATH: {DB_PATH}")
except Exception as e:
    errors.append(f"3. search_engine FAIL: {e}")

# Test 4: license_ui
try:
    from lexviridis.license_ui import LicenseManager

    ok.append(f"4. license_ui OK - LicenseManager: {type(LicenseManager).__name__}")
except Exception as e:
    errors.append(f"4. license_ui FAIL: {e}")

# Test 5: translations
try:
    from lexviridis.translations import i18n

    ok.append(f"5. translations OK - lang: {i18n.current_language}")
except Exception as e:
    errors.append(f"5. translations FAIL: {e}")

# Test 6: version consistency
try:
    from lexviridis import __version__
    from lexviridis.config import config as cfg

    v_init = __version__
    v_config = cfg.APP_VERSION
    if v_init == v_config == "3.0.0":
        ok.append("6. version OK - all 3.0.0")
    else:
        errors.append(f"6. version MISMATCH - __init__:{v_init}, config:{v_config}")
except Exception as e:
    errors.append(f"6. version FAIL: {e}")

# Test 7: asset paths
try:
    from lexviridis.config import config as cfg

    icon_path = cfg.BASE_DIR / "assets" / "LEXVIRIDIS_WHITE_BG.ico"
    logo_path = cfg.BASE_DIR / "assets" / "LEXVIRIDIS_WHITE_BG.png"
    icon_exists = icon_path.exists()
    logo_exists = logo_path.exists()
    if icon_exists and logo_exists:
        ok.append(f"7. assets OK - icon:{icon_exists}, logo:{logo_exists}")
    else:
        errors.append(f"7. assets MISSING - icon:{icon_exists}({icon_path}), logo:{logo_exists}({logo_path})")
except Exception as e:
    errors.append(f"7. assets FAIL: {e}")

# Test 8: DB exists
try:
    from lexviridis.search_engine import DB_PATH

    db_exists = DB_PATH.exists()
    if db_exists:
        ok.append(f"8. database OK - {DB_PATH}")
    else:
        errors.append(f"8. database MISSING: {DB_PATH}")
except Exception as e:
    errors.append(f"8. database FAIL: {e}")

# Test 9: ui_v2 import (sin iniciar Flet)
try:
    import importlib

    spec = importlib.util.find_spec("lexviridis.ui_v2")
    if spec:
        ok.append("9. ui_v2 module found OK")
    else:
        errors.append("9. ui_v2 module NOT FOUND")
except Exception as e:
    errors.append(f"9. ui_v2 FAIL: {e}")

print("\n" + "=" * 60)
print("  LEX VIRIDIS - Test de Validación Post-Fix")
print("=" * 60)
print(f"\nOK: {len(ok)} | ERRORS: {len(errors)}")
print()
for line in ok:
    print(f"  [OK] {line}")
for line in errors:
    print(f"  [!!] {line}")
print("\n" + "=" * 60)
if errors:
    print("  HAY ERRORES - REVISAR ANTES DE COMPILAR")
else:
    print("  TODAS LAS PRUEBAS PASARON - LISTO PARA COMPILAR")
print("=" * 60)
