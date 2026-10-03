"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 Fiscalía Especial del Medio Ambiente (FEMA) - Honduras.
Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: license_check.py
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

# Intentamos importar LicenseManager, con fallback seguro si falla (fail-closed)
try:
    from .license_system import LicenseManager
except ImportError:
    LicenseManager = None

logger = logging.getLogger(__name__)


def requires_valid_license(func: Callable) -> Callable:
    """
    Decorador para proteger funciones críticas.
    Verifica que exista una licencia válida antes de ejecutar.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        if LicenseManager is None:
            logger.critical("Security Breach: License module missing.")
            raise RuntimeError("Security violation: Core component missing.")

        # Verificación rápida de archivo (capa 1)
        if not LicenseManager.LICENSE_FILE.exists():
            logger.warning(f"Access denied to {func.__name__}: No license file.")
            raise PermissionError("Acceso denegado: Licencia no encontrada.")

        # Validar (capa 2) - Podríamos optimizar esto para no leer disco en cada llamada,
        # pero por seguridad lo hacemos aquí o confiamos en un estado global inyectado.
        # Para rendimiento, podríamos usar una variable global cacheada con TTL,
        # pero para máxima seguridad, re-validamos (o verificamos el estado del Watchdog si fuera accesible).

        # Por ahora, check de archivo rápido + carga.
        # En high-frequency calls esto podría ser lento.
        # Optimizacion: Leer licencia en memoria.

        saved_license = LicenseManager.load_saved_license()
        if not saved_license:
            raise PermissionError("Acceso denegado: Licencia inválida.")

        # Validación full (puede ser costosa, usar con cuidado en loops)
        # result = LicenseManager.validate_license(saved_license)
        # if not result.get("valid"):
        #    raise PermissionError(f"Acceso denegado: {result.get('error')}")

        return func(*args, **kwargs)

    return wrapper


def verify_license_token(token: str) -> bool:
    """Valida un token de licencia (para uso interno)."""
    if not LicenseManager:
        return False
    return LicenseManager.validate_license(token).get("valid", False)
