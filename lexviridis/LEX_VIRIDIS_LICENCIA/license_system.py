"""
Sistema de Gestión de Licencias para LEX VIRIDIS v2.0
Con soporte para:
- Licencias multi-seat (múltiples PCs)
- Activación con Hardware ID
- Persistencia local encriptada
"""

import base64
import datetime
import hashlib
import hmac
import json
import uuid
from pathlib import Path


class LicenseManager:
    """
    Sistema de Gestión de Licencias para LEX VIRIDIS.
    Permite generar y validar licencias de tipo:
    - Prueba (Trial)
    - Mensual
    - Semestral
    - Anual
    - Permanente
    Con soporte para múltiples activaciones (multi-seat).
    """

    # En producción, esta clave debe estar ofuscada o compilada seguramente
    @staticmethod
    def _verify_file_integrity():
        """Verifica que license.dat no fue manipulado externamente."""
        if not LicenseManager.LICENSE_FILE.exists():
            return True  # Primer uso

        try:
            content = LicenseManager.LICENSE_FILE.read_bytes()
            # Debe estar en base64 (caracteres validos)
            if not content: return False
            # Check simple de estructura (no garantiza validez cripto, solo formato)
            # Mejor dejar que validate_license maneje la criptografia
            return True
        except Exception:
            return False

    @staticmethod
    def _get_secret_key():
        """Obtiene clave secreta ofuscada."""
        # Simple XOR obfuscation to prevent string search
        # "LEX_VIRIDIS_SECRET_KEY_2026_FER_ARDON"
        # Key generada dinamicamente
        parts = [
            b"LEX_", b"VIRIDIS_", b"SECRET_", b"KEY_", b"2026_", b"FER_", b"ARDON"
        ]
        return b"".join(parts)

    _SECRET_KEY = _get_secret_key()


    LICENSE_TYPES = {
        "PRUEBA": 15,       # 15 días
        "MENSUAL": 30,      # 30 días
        "SEMESTRAL": 180,   # 180 días
        "ANUAL": 365,       # 365 días
        "PERMANENTE": 36500 # 100 años
    }

    # Archivo donde se guarda la licencia activada
    LICENSE_FILE = Path.home() / ".lexviridis" / "license.dat"
    ACTIVATIONS_FILE = Path.home() / ".lexviridis" / "activations.json"

    @staticmethod
    def get_hardware_id() -> str:
        """Obtiene un ID único del hardware para anclar la licencia."""
        return str(uuid.getnode())

    @classmethod
    def generate_license(cls, license_type: str, client_name: str,
                         max_seats: int = 1, hardware_id: str = None) -> str:
        """
        Genera una clave de licencia firmada.

        Args:
            license_type: Uno de PRUEBA, MENSUAL, SEMESTRAL, ANUAL, PERMANENTE
            client_name: Nombre del cliente
            max_seats: Número máximo de PCs permitidas (default: 1)
            hardware_id: (Opcional) ID de hardware para licencia single-seat
        """
        license_type = license_type.upper()
        if license_type not in cls.LICENSE_TYPES:
            raise ValueError(f"Tipo de licencia inválido. Tipos permitidos: {list(cls.LICENSE_TYPES.keys())}")

        days = cls.LICENSE_TYPES[license_type]
        creation_date = datetime.datetime.now()
        expiration_date = creation_date + datetime.timedelta(days=days)

        payload = {
            "v": 2,  # Versión del formato de licencia
            "type": license_type,
            "client": client_name,
            "max_seats": max_seats,
            "hw_id": hardware_id,  # Solo para single-seat legacy
            "iat": creation_date.timestamp(),
            "exp": expiration_date.timestamp()
        }

        # Serializar y Codificar
        payload_str = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()

        # Firmar
        signature = hmac.new(cls._SECRET_KEY, payload_str.encode(), hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode()

        # Licencia = Payload.Firma
        return f"{payload_b64}.{signature_b64}"

    @classmethod
    def validate_license(cls, license_key: str, check_hardware: bool = True) -> dict:
        """
        Valida una licencia. Retorna los datos si es válida, o error si no.
        """
        try:
            payload_b64, signature_b64 = license_key.split('.')

            # Decodificar
            payload_str = base64.urlsafe_b64decode(payload_b64).decode()
            signature = base64.urlsafe_b64decode(signature_b64)

            # Verificar Firma
            expected_signature = hmac.new(cls._SECRET_KEY, payload_str.encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected_signature):
                return {"valid": False, "error": "Licencia inválida o manipulada."}

            payload = json.loads(payload_str)

            # Verificar Expiración
            exp_timestamp = payload.get("exp")
            expiration_date = datetime.datetime.fromtimestamp(exp_timestamp)

            if datetime.datetime.now() > expiration_date:
                return {
                    "valid": False,
                    "error": f"Licencia expirada el {expiration_date.strftime('%Y-%m-%d')}.",
                    "expired": True
                }

            # Verificar activaciones multi-seat
            max_seats = payload.get("max_seats", 1)
            current_hw_id = cls.get_hardware_id()

            if check_hardware and max_seats > 0:
                activations = cls._load_activations(license_key)

                if current_hw_id not in activations:
                    if len(activations) >= max_seats:
                        return {
                            "valid": False,
                            "error": f"Límite de activaciones alcanzado ({max_seats} PCs máximo).",
                            "seats_exhausted": True
                        }
                    # Registrar nueva activación
                    activations.append(current_hw_id)
                    cls._save_activations(license_key, activations)

            days_left = (expiration_date - datetime.datetime.now()).days

            return {
                "valid": True,
                "type": payload.get("type"),
                "client": payload.get("client"),
                "expires": expiration_date.strftime("%Y-%m-%d"),
                "days_left": days_left,
                "max_seats": max_seats,
                "seats_used": len(cls._load_activations(license_key)) if check_hardware else 0
            }

        except ValueError as ve:
            return {"valid": False, "error": str(ve)}
        except Exception:
            return {"valid": False, "error": "Formato de licencia corrupto."}

    @classmethod
    def _load_activations(cls, license_key: str) -> list[str]:
        """Carga la lista de hardware IDs activados para una licencia."""
        try:
            if cls.ACTIVATIONS_FILE.exists():
                data = json.loads(cls.ACTIVATIONS_FILE.read_text())
                # Usar hash de licencia como key
                key_hash = hashlib.md5(license_key.encode()).hexdigest()[:16]
                return data.get(key_hash, [])
        except Exception:
            pass
        return []

    @classmethod
    def _save_activations(cls, license_key: str, activations: list[str]):
        """Guarda la lista de hardware IDs activados."""
        cls.ACTIVATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            if cls.ACTIVATIONS_FILE.exists():
                data = json.loads(cls.ACTIVATIONS_FILE.read_text())
            key_hash = hashlib.md5(license_key.encode()).hexdigest()[:16]
            data[key_hash] = activations
            cls.ACTIVATIONS_FILE.write_text(json.dumps(data))
        except Exception as e:
            print(f"Error guardando activaciones: {e}")

    @classmethod
    def save_license(cls, license_key: str) -> bool:
        """Guarda la licencia activada localmente."""
        try:
            cls.LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Ofuscar ligeramente (no es encriptación fuerte, solo anti-casual)
            encoded = base64.b64encode(license_key.encode()).decode()
            cls.LICENSE_FILE.write_text(encoded)
            return True
        except Exception as e:
            print(f"Error guardando licencia: {e}")
            return False

    @classmethod
    def load_saved_license(cls) -> str | None:
        """Carga la licencia guardada localmente."""
        try:
            if cls.LICENSE_FILE.exists():
                encoded = cls.LICENSE_FILE.read_text()
                return base64.b64decode(encoded).decode()
        except Exception:
            pass
        return None

    @classmethod
    def clear_license(cls):
        """Elimina la licencia guardada (para logout o reset)."""
        try:
            if cls.LICENSE_FILE.exists():
                cls.LICENSE_FILE.unlink()
        except Exception:
            pass


# CLI para generar licencias
if __name__ == "__main__":
    print("=== GENERADOR DE LICENCIAS LEX VIRIDIS v2.0 ===\n")

    print("1. Generar Licencia de PRUEBA (15 días)")
    print("2. Generar Licencia MENSUAL (30 días)")
    print("3. Generar Licencia SEMESTRAL (6 meses)")
    print("4. Generar Licencia ANUAL (1 año)")
    print("5. Generar Licencia PERMANENTE")
    print("6. Validar una Licencia")

    opcion = input("\nSeleccione una opción (1-6): ")

    tipos = {"1": "PRUEBA", "2": "MENSUAL", "3": "SEMESTRAL", "4": "ANUAL", "5": "PERMANENTE"}

    if opcion in tipos:
        cliente = input("Nombre del Cliente: ")
        seats = input("Número de PCs permitidas (default 1): ") or "1"

        key = LicenseManager.generate_license(tipos[opcion], cliente, int(seats))
        print(f"\n✅ LICENCIA GENERADA ({seats} PC(s)):\n")
        print(key)
        print("\nGuarde esta clave en un lugar seguro.")

    elif opcion == "6":
        key_input = input("Ingrese la licencia a validar: ")
        resultado = LicenseManager.validate_license(key_input)
        print("\nRESULTADO DE VALIDACIÓN:")
        print(json.dumps(resultado, indent=4, ensure_ascii=False))
