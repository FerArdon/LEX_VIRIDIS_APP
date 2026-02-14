"""
Pruebas del modulo de seguridad (security.py).
Cubre: AuthManager (hash, login, sesiones), EncryptionManager.
"""

import pytest
from lexviridis.security import AuthManager, EncryptionManager


# ============================================================
# AuthManager - Password Hashing
# ============================================================

class TestAuthManagerHashing:

    def test_hash_password_returns_salt_and_key(self):
        salt, key = AuthManager.hash_password("mi_contraseña")
        assert isinstance(salt, bytes)
        assert isinstance(key, bytes)
        assert len(salt) == 32
        assert len(key) > 0

    def test_hash_with_same_salt_gives_same_key(self):
        salt, key1 = AuthManager.hash_password("password123")
        _, key2 = AuthManager.hash_password("password123", salt)
        assert key1 == key2

    def test_different_passwords_give_different_keys(self):
        salt, key1 = AuthManager.hash_password("password1")
        _, key2 = AuthManager.hash_password("password2", salt)
        assert key1 != key2

    def test_verify_password_correct(self):
        salt, key = AuthManager.hash_password("correct_password")
        assert AuthManager.verify_password("correct_password", salt, key) is True

    def test_verify_password_incorrect(self):
        salt, key = AuthManager.hash_password("correct_password")
        assert AuthManager.verify_password("wrong_password", salt, key) is False

    def test_empty_password_hashes(self):
        salt, key = AuthManager.hash_password("")
        assert isinstance(key, bytes)


# ============================================================
# AuthManager - User CRUD (con BD temporal)
# ============================================================

class TestAuthManagerUsers:

    def test_create_user(self, db_manager):
        auth = AuthManager(db_manager)
        user_id = auth.create_user("testuser", "password123", "test@example.com")
        assert user_id > 0

    def test_login_success(self, db_manager):
        auth = AuthManager(db_manager)
        auth.create_user("loginuser", "mypassword", "login@test.com")
        result = auth.login("loginuser", "mypassword")
        assert result is not None
        assert result["username"] == "loginuser"
        assert "token" in result

    def test_login_wrong_password(self, db_manager):
        auth = AuthManager(db_manager)
        auth.create_user("user1", "correct", "u1@test.com")
        result = auth.login("user1", "wrong")
        assert result is None

    def test_login_nonexistent_user(self, db_manager):
        auth = AuthManager(db_manager)
        result = auth.login("noexiste", "password")
        assert result is None

    def test_validate_session(self, db_manager):
        auth = AuthManager(db_manager)
        auth.create_user("sessuser", "pass123", "sess@test.com")
        login_result = auth.login("sessuser", "pass123")
        token = login_result["token"]
        session = auth.validate_session(token)
        assert session is not None
        assert session["username"] == "sessuser"

    def test_validate_invalid_session(self, db_manager):
        auth = AuthManager(db_manager)
        result = auth.validate_session("token_invalido_12345")
        assert result is None

    def test_change_password(self, db_manager):
        auth = AuthManager(db_manager)
        user_id = auth.create_user("chguser", "oldpass", "chg@test.com")
        assert auth.change_password(user_id, "oldpass", "newpass") is True
        # Verificar que el nuevo password funciona
        assert auth.login("chguser", "newpass") is not None
        # Verificar que el viejo ya no funciona
        assert auth.login("chguser", "oldpass") is None

    def test_change_password_wrong_current(self, db_manager):
        auth = AuthManager(db_manager)
        user_id = auth.create_user("chguser2", "correct", "chg2@test.com")
        assert auth.change_password(user_id, "wrong", "new") is False


# ============================================================
# EncryptionManager
# ============================================================

class TestEncryptionManager:

    def test_encrypt_and_decrypt(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        em = EncryptionManager()
        original = "datos sensibles"
        encrypted = em.encrypt(original)
        assert encrypted != original
        decrypted = em.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_empty_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        em = EncryptionManager()
        assert em.encrypt("") == ""

    def test_decrypt_empty_string(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        em = EncryptionManager()
        assert em.decrypt("") == ""

    def test_decrypt_invalid_data_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        em = EncryptionManager()
        assert em.decrypt("datos_invalidos_no_base64!!!") == ""

    def test_key_persists_across_instances(self, tmp_path, monkeypatch):
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        em1 = EncryptionManager()
        encrypted = em1.encrypt("test data")
        em2 = EncryptionManager()
        assert em2.decrypt(encrypted) == "test data"
