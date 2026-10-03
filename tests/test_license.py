"""Pruebas del sistema de licencias (firma HMAC, clave fuera del repositorio)."""

import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
COPIAS = [
    RAIZ / "LEX_VIRIDIS_LICENCIA" / "license_system.py",
    RAIZ / "lexviridis" / "LEX_VIRIDIS_LICENCIA" / "license_system.py",
]


def _cargar(ruta: Path):
    spec = importlib.util.spec_from_file_location(f"license_system_{abs(hash(ruta))}", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.LicenseManager


@pytest.fixture(params=COPIAS, ids=["raiz", "paquete"])
def lm(request, tmp_path, monkeypatch):
    clase = _cargar(request.param)
    monkeypatch.setenv("LEXVIRIDIS_LICENSE_SECRET", "clave-de-prueba-A")
    monkeypatch.setattr(clase, "LICENSE_FILE", tmp_path / "license.dat")
    monkeypatch.setattr(clase, "ACTIVATIONS_FILE", tmp_path / "activations.json")
    return clase


@pytest.mark.parametrize("ruta", COPIAS, ids=["raiz", "paquete"])
def test_el_codigo_fuente_no_contiene_la_clave(ruta):
    texto = ruta.read_text(encoding="utf-8")
    assert "_SECRET_KEY" not in texto
    assert "lexviridis_license_secret" in texto


def test_generar_y_validar(lm):
    clave = lm.generate_license("ANUAL", "Cliente Demo", 2)
    r = lm.validate_license(clave)
    assert r["valid"] is True
    assert r["type"] == "ANUAL" and r["client"] == "Cliente Demo" and r["max_seats"] == 2


def test_licencia_manipulada_es_rechazada(lm):
    import base64
    import json

    clave = lm.generate_license("PRUEBA", "Cliente Demo", 1)
    payload_b64, firma = clave.split(".")
    datos = json.loads(base64.urlsafe_b64decode(payload_b64))
    datos["type"] = "PERMANENTE"
    falso = base64.urlsafe_b64encode(json.dumps(datos, separators=(",", ":")).encode()).decode()
    assert lm.validate_license(f"{falso}.{firma}")["valid"] is False


def test_firma_con_otra_clave_es_rechazada(lm, monkeypatch):
    clave = lm.generate_license("ANUAL", "Cliente Demo", 1)
    monkeypatch.setenv("LEXVIRIDIS_LICENSE_SECRET", "clave-de-prueba-B")
    assert lm.validate_license(clave)["valid"] is False


def test_licencia_expirada(lm, monkeypatch):
    monkeypatch.setitem(lm.LICENSE_TYPES, "PRUEBA", -1)
    r = lm.validate_license(lm.generate_license("PRUEBA", "Cliente Demo", 1))
    assert r["valid"] is False and r.get("expired") is True


def test_limite_de_equipos(lm):
    clave = lm.generate_license("ANUAL", "Cliente Demo", 1)
    lm._save_activations(clave, ["otro-equipo"])
    r = lm.validate_license(clave)
    assert r["valid"] is False and r.get("seats_exhausted") is True


def test_sin_clave_falla_cerrado(lm, monkeypatch):
    clave = lm.generate_license("ANUAL", "Cliente Demo", 1)
    monkeypatch.delenv("LEXVIRIDIS_LICENSE_SECRET")
    monkeypatch.setitem(sys.modules, "lexviridis_license_secret", None)  # fuerza ImportError
    with pytest.raises(RuntimeError):
        lm.generate_license("ANUAL", "Cliente Demo", 1)
    r = lm.validate_license(clave)
    assert r["valid"] is False and "no disponible" in r["error"]
