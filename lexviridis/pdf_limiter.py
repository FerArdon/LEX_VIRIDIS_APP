"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 Fiscalía Especial del Medio Ambiente (FEMA) - Honduras.
Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: pdf_limiter.py
"""

import logging
import datetime
from pathlib import Path
from .license_check import LicenseManager

logger = logging.getLogger(__name__)

class PDFAccessManager:
    """
    Controla el acceso a documentos PDF y registra auditoría.
    """
    
    AUDIT_LOG = Path.home() / ".lexviridis" / "audit_access.log"

    @staticmethod
    def can_access_pdf(pdf_path: Path, access_type: str = "read") -> bool:
        """
        Verifica si se permite el acceso al PDF.
        """
        try:
            # 1. Verificar licencia
            if not LicenseManager:
                logger.critical("Security Breach: License module missing.")
                return False

            saved = LicenseManager.load_saved_license()
            if not saved:
                PDFAccessManager._log_access(pdf_path, access_type, False, "No license")
                return False
            
            # 2. Check de integridad simple (opcional: verificar firma)
            # result = LicenseManager.validate_license(saved)
            # if not result.get("valid"):
            #     PDFAccessManager._log_access(pdf_path, access_type, False, "Invalid license")
            #     return False

            # 3. Registrar acceso exitoso
            PDFAccessManager._log_access(pdf_path, access_type, True, "Authorized")
            return True

        except Exception as e:
            logger.error(f"Access control error: {e}")
            return False

    @staticmethod
    def _log_access(pdf_path: Path, access_type: str, allowed: bool, reason: str):
        """Registra auditoría de acceso."""
        try:
            PDFAccessManager.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().isoformat()
            filename = pdf_path.name
            status = "ALLOWED" if allowed else "DENIED"
            user = "?" # En el futuro, inyectar usuario actual
            
            log_entry = f"{timestamp} | {status} | {user} | {access_type} | {filename} | {reason}\n"
            
            with open(PDFAccessManager.AUDIT_LOG, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass # No romper flujo por fallo de log
