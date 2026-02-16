"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 Fiscalía Especial del Medio Ambiente (FEMA) - Honduras.
Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: security.py
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from cryptography.fernet import Fernet
from .license_check import requires_valid_license


class EncryptionManager:
    """Cifrado de datos sensibles."""

    def __init__(self):
        self.key = self._load_or_create_key()
        self.cipher = Fernet(self.key)

    def _load_or_create_key(self) -> bytes:
        key_file = Path.home() / ".lexviridis" / ".key"
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt(self, data: str) -> str:
        if not data: return ""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data: return ""
        try:
            encrypted = base64.b64decode(encrypted_data.encode())
            return self.cipher.decrypt(encrypted).decode()
        except (ValueError, base64.binascii.Error, Exception) as e:
            logging.error(f"Error descifrando datos: {e}")
            return ""

class AuthManager:
    """Gestor de autenticación y usuarios."""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> tuple:
        if salt is None:
            salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt, key

    @staticmethod
    def verify_password(password: str, salt: bytes, key: bytes) -> bool:
        _, new_key = AuthManager.hash_password(password, salt)
        return secrets.compare_digest(key, new_key)

    def create_user(self, username: str, password: str, email: str, role: str = "user") -> int:
        conn = self.db_manager.get_connection()
        salt, password_hash = self.hash_password(password)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (username, password_salt, password_hash, email)
                VALUES (?, ?, ?, ?)
            """, (username, salt, password_hash, email))
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO usuarios_roles (user_id, role) VALUES (?, ?)", (user_id, role))
            conn.commit()
            return user_id
        finally:
            conn.close()

    @requires_valid_license
    def login(self, username: str, password: str) -> dict | None:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            # Try to get profile_picture if column exists
            has_profile_pic = False
            try:
                cursor.execute("SELECT id, username, password_salt, password_hash, email, profile_picture FROM usuarios WHERE username = ?", (username,))
                has_profile_pic = True
            except Exception:
                # Fallback if profile_picture column doesn't exist
                cursor.execute("SELECT id, username, password_salt, password_hash, email FROM usuarios WHERE username = ?", (username,))

            user = cursor.fetchone()
            if user and self.verify_password(password, user['password_salt'], user['password_hash']):
                token = secrets.token_urlsafe(32)
                expires = datetime.now() + timedelta(days=30)
                cursor.execute("INSERT INTO sesiones (user_id, token, expires_at) VALUES (?, ?, ?)",
                             (user['id'], token, expires.strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()

                result = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'token': token
                }

                # Add profile_picture if column exists
                if has_profile_pic:
                    try:
                        result['profile_picture'] = user['profile_picture']
                    except (KeyError, IndexError):
                        result['profile_picture'] = None
                else:
                    result['profile_picture'] = None

                return result
            return None
        finally:
            conn.close()

    def validate_session(self, token: str) -> dict | None:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.user_id, u.username, u.email, r.role
                FROM sesiones s
                JOIN usuarios u ON s.user_id = u.id
                LEFT JOIN usuarios_roles r ON u.id = r.user_id
                WHERE s.token = ? AND s.expires_at > DATETIME('now')
            """, (token,))
            res = cursor.fetchone()
            return dict(res) if res else None
        finally:
            conn.close()

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Cambia la contraseña del usuario."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT password_salt, password_hash FROM usuarios WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False

            if not self.verify_password(current_password, user['password_salt'], user['password_hash']):
                return False

            salt, new_hash = self.hash_password(new_password)
            cursor.execute("UPDATE usuarios SET password_salt = ?, password_hash = ? WHERE id = ?",
                         (salt, new_hash, user_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def update_username(self, current_username: str, current_password: str, new_username: str) -> bool:
        """Cambia el nombre de usuario verificando credenciales."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_salt, password_hash FROM usuarios WHERE username = ?", (current_username,))
            user = cursor.fetchone()
            if not user or not self.verify_password(current_password, user['password_salt'], user['password_hash']):
                return False

            cursor.execute("UPDATE usuarios SET username = ? WHERE id = ?", (new_username, user['id']))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error actualizando username: {e}")
            return False
        finally:
            conn.close()

    def set_security_credentials(self, user_id: int, current_password: str, answer: str) -> bool:
        """Configura la respuesta de seguridad para el usuario."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT password_salt, password_hash FROM usuarios WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user or not self.verify_password(current_password, user['password_salt'], user['password_hash']):
                return False

            # Usamos el mismo método de hash para la respuesta de seguridad
            salt, answer_hash = self.hash_password(answer.lower().strip())
            cursor.execute("""
                UPDATE usuarios
                SET security_question = '¿Cuál es el nombre de tu mascota?',
                    security_answer_salt = ?,
                    security_answer_hash = ?,
                    recovery_enabled = TRUE
                WHERE id = ?
            """, (salt, answer_hash, user_id))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error configurando credenciales de seguridad: {e}")
            return False
        finally:
            conn.close()

    def get_recovery_status(self, username: str) -> dict:
        """Verifica si un usuario tiene habilitada la recuperación y retorna su pregunta."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT recovery_enabled, security_question FROM usuarios WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                return {'enabled': bool(user['recovery_enabled']), 'question': user['security_question']}
            return {'enabled': False, 'question': None}
        finally:
            conn.close()

    def recovery_reset(self, username: str, answer: str, new_username: str, new_password: str) -> bool:
        """Restablece identidad completa usando la respuesta de seguridad."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, security_answer_salt, security_answer_hash FROM usuarios WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user or not user['security_answer_hash']:
                return False

            # Verificar respuesta
            if not self.verify_password(answer.lower().strip(), user['security_answer_salt'], user['security_answer_hash']):
                return False

            # Si la respuesta es correcta, actualizar usuario y contraseña
            salt, password_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE usuarios
                SET username = ?,
                    password_salt = ?,
                    password_hash = ?
                WHERE id = ?
            """, (new_username, salt, password_hash, user['id']))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error recuperando cuenta: {e}")
            return False
        finally:
            conn.close()

    def update_profile_picture(self, user_id: int, image_path: str) -> bool:
        """Actualiza la foto de perfil del usuario."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET profile_picture = ? WHERE id = ?", (image_path, user_id))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error actualizando foto de perfil: {e}")
            return False
        finally:
            conn.close()

    def get_profile_picture(self, user_id: int) -> str | None:
        """Obtiene la ruta de la foto de perfil del usuario."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_picture FROM usuarios WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result['profile_picture'] if result else None
        finally:
            conn.close()
