import os

# Directorio objetivo
directorio = r"E:\LEX_VIRIDIS_APP\COMPENDIO LEYES FEMA"

# Mapeo de archivos originales a nuevos nombres
renombrar = {
    "87-87 Ley de Bosques Nublados.pdf": "36-DL 087-1987_hn - Ley de Bosques Nublados.pdf",
    "ACUERDO  005-2022_LISTA ROJA DE ESPECIES AMENZADAS DE HONDURAS.pdf": "37-AE 005-2022_hn - Lista Roja de Especies Amenazadas de Honduras.pdf",
    "ACUERDO - 002 - 2016 NORMATIVA PARA LA EXTRACCIONNDE PROD Y SUB PROD FORESTALES.pdf": "38-AE 002-2016_hn - Normativa para la Extraccion de Productos y Subproductos Forestales.pdf",
    "ACUERDO 001-2020 precios de la madera.pdf": "39-AE 001-2020_hn - Precios de la Madera.pdf",
    "ACUERDO 002-2023 NORMATIVA PARA APROVACION DE LIMITES DE TOLERANCIA DEL SOBREPASO EN APROV DE MADE.pdf": "40-AE 002-2023_hn - Normativa para Aprobacion de Limites de Tolerancia del Sobrepaso en Aprovechamiento de Madera.pdf"
}

print("Iniciando renombrado de archivos...\n")

for original, nuevo in renombrar.items():
    ruta_original = os.path.join(directorio, original)
    ruta_nueva = os.path.join(directorio, nuevo)
    
    if os.path.exists(ruta_original):
        try:
            os.rename(ruta_original, ruta_nueva)
            print(f"Exito: {original}\n  -> {nuevo}\n")
        except Exception as e:
            print(f"Error al renombrar {original}: {e}\n")
    else:
        # Verifica si ya fue renombrado
        if os.path.exists(ruta_nueva):
            print(f"Aviso: El archivo ya estaba renombrado como {nuevo}\n")
        else:
            print(f"Error: No se encontro el archivo original: {original}\n")

print("Proceso completado.")
