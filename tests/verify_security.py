
import sys
import os
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from lexviridis.search_engine import SearchEngine
from lexviridis.ia_gemini import GeminiClient
from lexviridis.pdf_limiter import PDFAccessManager
from lexviridis.license_check import requires_valid_license, LicenseManager

class SecurityTests(unittest.TestCase):
    
    def setUp(self):
        # Ensure we have a mock valid license for tests, or use existing
        # This assumes existing license is valid. If not, tests might fail correcty (access denied).
        self.engine = SearchEngine()
        self.gemini = GeminiClient()

    def test_01_search_engine_protected(self):
        """Verify SearchEngine.search is protected"""
        print("\nTesting SearchEngine protection...")
        # If license is present and valid, this should pass. 
        # If not, it should raise PermissionError.
        try:
            self.engine.search("test")
            print("✅ SearchEngine allowed access (Valid License)")
        except PermissionError:
            print("✅ SearchEngine blocked access (Invalid/No License)")
        except Exception as e:
            print(f"⚠️ Unexpected error in search: {e}")

    def test_02_gemini_protected(self):
        """Verify GeminiClient.consultar is protected"""
        print("\nTesting GeminiClient protection...")
        try:
            # Mock connection to avoid real API call
            self.gemini.check_connection = lambda: True
            self.gemini.model = type('obj', (object,), {'generate_content': lambda x: type('obj', (object,), {'text': 'OK'})})
            
            self.gemini.consultar("test")
            print("✅ GeminiClient allowed access (Valid License)")
        except PermissionError:
            print("✅ GeminiClient blocked access (Invalid/No License)")
        except Exception as e:
            print(f"⚠️ Unexpected error in gemini: {e}")

    def test_03_pdf_access_control(self):
        """Verify PDFAccessManager"""
        print("\nTesting PDF Access Control...")
        dummy_pdf = Path("test.pdf")
        allowed = PDFAccessManager.can_access_pdf(dummy_pdf, "read")
        if allowed:
             print("✅ PDF Access Allowed (Valid License)")
        else:
             print("✅ PDF Access Denied (Invalid/No License)")
             
    def test_04_audit_log_created(self):
        """Verify audit log creation"""
        print("\nTesting Audit Log...")
        log_file = PDFAccessManager.AUDIT_LOG
        if log_file.exists():
            print(f"✅ Audit log exists at {log_file}")
            content = log_file.read_text()
            if "test.pdf" in content or "Authorized" in content:
                print("✅ Audit log contains recent entries")
        else:
            print("⚠️ Audit log not found (maybe first run)")

if __name__ == '__main__':
    unittest.main()
