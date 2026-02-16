"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 FEMA Honduras. Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: License Validator (Watchdog periódico)
"""
import threading
import time
import logging
from .LEX_VIRIDIS_LICENCIA.license_system import LicenseManager

logger = logging.getLogger(__name__)


class LicenseWatchdog:
    """
    Valida la licencia periódicamente en segundo plano.

    Si detecta que la licencia fue eliminada, expiró o fue manipulada,
    ejecuta un callback de seguridad para cerrar la aplicación.

    Intervalo de verificación: 1 hora por defecto.
    """

    def __init__(self, page, on_invalid_callback, interval=3600):
        self.page = page
        self.on_invalid = on_invalid_callback
        self.interval = interval
        self.running = True
        self._start_watchdog()

    def _start_watchdog(self):
        threading.Thread(target=self._check_loop, daemon=True).start()

    def _check_loop(self):
        logger.info("LicenseWatchdog: Iniciado - validación cada %d segundos", self.interval)
        while self.running:
            time.sleep(self.interval)
            
            try:
                # 1. Verificar existencia de archivo
                saved_license = LicenseManager.load_saved_license()
                if not saved_license:
                    logging.warning("Watchdog: License file missing.")
                    self._trigger_invalid("Licencia eliminada o no encontrada.")
                    break

                # 2. Validar criptográficamente
                result = LicenseManager.validate_license(saved_license)
                if not result.get("valid"):
                    logging.warning(f"Watchdog: License invalid. {result.get('error')}")
                    self._trigger_invalid(result.get("error", "Licencia inválida."))
                    break
                    
            except Exception as e:
                logging.error(f"Watchdog error: {e}")
                # En caso de error severo, asumimos compromiso (fail-safe)
                # self._trigger_invalid("Error de verficación de seguridad.")
                # Opcional: no romper en errores transitorios, pero loguear.

    def _trigger_invalid(self, reason):
        if self.running:
            # Ejecutar callback en el main thread de UI si es posible, o thread-safe
            self.on_invalid(reason)
            self.running = False

    def stop(self):
        self.running = False
