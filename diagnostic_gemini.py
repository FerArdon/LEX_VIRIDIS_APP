import google.generativeai as genai
import os
import json
from pathlib import Path

def diagnostic():
    # Intentar cargar la key de la misma forma que la app
    data_dir = Path(os.environ.get('APPDATA', '')) / "LEX_VIRIDIS"
    key_file = data_dir / "api_key.json"
    
    api_key = None
    if key_file.exists():
        with open(key_file, 'r') as f:
            api_key = json.load(f).get("gemini_api_key")
    
    if not api_key:
        print("Error: No se encontró API Key en la ruta esperada.")
        return

    genai.configure(api_key=api_key)
    
    print("--- Modelos Disponibles ---")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"ID: {m.name}, Display: {m.display_name}")
    except Exception as e:
        print(f"Error listando modelos: {e}")

if __name__ == "__main__":
    diagnostic()
