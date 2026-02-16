"""
Gestor de configuración segura para LEX VIRIDIS.
Almacena datos sensibles cifrados usando EncryptionManager.
"""
import json
import logging
from pathlib import Path
from typing import Any

from .security import EncryptionManager


class SecureConfigManager:
    """Gestor de configuración segura con cifrado."""

    def __init__(self, config_name: str = "secure_config.json"):
        self.config_path = Path.home() / ".lexviridis" / config_name
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption = EncryptionManager()
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Carga la configuración desde disco."""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Error cargando configuración segura: {e}")
            return {}

    def _save_config(self) -> None:
        """Guarda la configuración a disco."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
        except OSError as e:
            logging.error(f"Error guardando configuración segura: {e}")

    def set_encrypted(self, key: str, value: str) -> None:
        """Guarda un valor cifrado."""
        if not value:
            self._config[key] = ""
        else:
            encrypted_value = self.encryption.encrypt(value)
            self._config[key] = encrypted_value
        self._save_config()

    def get_decrypted(self, key: str, default: str = "") -> str:
        """Obtiene un valor descifrado."""
        encrypted_value = self._config.get(key, "")
        if not encrypted_value:
            return default

        decrypted_value = self.encryption.decrypt(encrypted_value)
        return decrypted_value if decrypted_value else default

    def set_plain(self, key: str, value: Any) -> None:
        """Guarda un valor sin cifrar (para datos no sensibles)."""
        self._config[key] = value
        self._save_config()

    def get_plain(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor sin cifrar."""
        return self._config.get(key, default)

    def delete(self, key: str) -> None:
        """Elimina una clave de la configuración."""
        if key in self._config:
            del self._config[key]
            self._save_config()

    def has_key(self, key: str) -> bool:
        """Verifica si una clave existe."""
        return key in self._config

    def clear_all(self) -> None:
        """Elimina toda la configuración."""
        self._config = {}
        self._save_config()


# Instancia global para uso en la aplicación
secure_config = SecureConfigManager()
