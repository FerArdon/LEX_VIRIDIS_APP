import os
import re

directorio = r"E:\LEX_VIRIDIS_APP\COMPENDIO LEYES FEMA"

def capitalizar_titulo(texto):
    excepciones = ['de', 'la', 'el', 'los', 'las', 'y', 'en', 'para', 'con', 'del', 'al', 'por', 'a', 'o', 'u']
    palabras = texto.replace('_', ' ').split()
    resultado = []
    for i, p in enumerate(palabras):
        p = p.strip('-').lower()
        if not p: continue
        if i == 0 or p not in excepciones:
            resultado.append(p.capitalize())
        else:
            resultado.append(p)
    return " ".join(resultado)

def limpiar_titulo(titulo):
    # Quitar siglas institucionales sueltas
    titulo = re.sub(r'\b(sag|senasa|inhgeomin|cipf|mp|dcha|de|pw|ch)\b', '', titulo, flags=re.IGNORECASE)
    # Quitar texto entre parentesis o corchetes
    titulo = re.sub(r'[\(\[\{].*?[\)\]\}]', '', titulo)
    # Limpiar caracteres especiales
    titulo = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.\-]', ' ', titulo)
    # Quitar palabras sueltas remanentes al final
    titulo = re.sub(r'\b(Decreto|Acuerdo|Resolucion|PCM|Numero|No|Num|Ley)\s*$', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s+', ' ', titulo).strip(" -_.")
    return capitalizar_titulo(titulo)

def ejecutar_renombrado():
    print("Iniciando análisis y renombrado masivo...\n")
    if not os.path.exists(directorio):
        print(f"Error: No se encontró el directorio {directorio}")
        return

    archivos = [f for f in os.listdir(directorio) if f.lower().endswith('.pdf')]
    
    # 1. Encontrar el índice más alto (XX-) para continuar desde ahí
    max_idx = 0
    for f in archivos:
        m = re.match(r'^(\d{2,3})-', f)
        if m:
            val = int(m.group(1))
            if val > max_idx:
                max_idx = val

    start_index = max_idx + 1
    renombrados = []
    errores = []

    for archivo in archivos:
        # Ignorar los que ya tienen formato impecable (ej: 40-AE 002-2023_hn - Titulo.pdf)
        if re.match(r'^\d{2,3}-[A-Z]{2,4} \d{3}-\d{4}_hn - .*\.pdf$', archivo, re.IGNORECASE):
            continue
            
        base_name = archivo[:-4]
        
        # Caso 1: Tiene formato _hn - pero prefijo sucio o numérico incorrecto (ej: 1A_31-DL...)
        match_format = re.search(r'([A-Z]{2,4})\s+(\d{3}-\d{4})_hn\s*-\s*(.*)', base_name, re.IGNORECASE)
        if match_format:
            tipo = match_format.group(1).upper()
            numero_anio = match_format.group(2)
            titulo_raw = match_format.group(3)
            titulo_limpio = limpiar_titulo(titulo_raw) or "Documento Sin Titulo"
            nuevo_nombre = f"{start_index:02d}-{tipo} {numero_anio}_hn - {titulo_limpio}.pdf"
            
        # Caso 2: Formato totalmente libre
        else:
            tipo = "DL" # Por defecto
            if re.search(r'\bacuerdo\b', base_name, re.IGNORECASE):
                tipo = "AE"
            elif re.search(r'\b(pcm|decreto ejecutivo)\b', base_name, re.IGNORECASE):
                tipo = "PCM"
            elif re.search(r'\bresolucion\b', base_name, re.IGNORECASE):
                tipo = "RES"

            # Extraer num y año
            match_num = re.search(r'(?:no\.?|num\.?|numero|n°)?\s*(\d{1,4})[\s\-_]+(19\d{2}|20\d{2}|\d{2})\b', base_name, re.IGNORECASE)
            numero, anio = "000", "0000"
            
            if match_num:
                num_raw, anio_raw = match_num.group(1), match_num.group(2)
                anio = ("19" if int(anio_raw) > 50 else "20") + anio_raw if len(anio_raw) == 2 else anio_raw
                numero = num_raw.zfill(3)
                base_name = base_name.replace(match_num.group(0), ' ')

            # Limpiar el prefijo de tipo al inicio para no repetirlo
            base_name = re.sub(r'^(acuerdo|decreto ejecutivo|decreto|resolucion|pcm)[\s\-]*', '', base_name, flags=re.IGNORECASE)
            titulo_limpio = limpiar_titulo(base_name) or "Documento Sin Titulo"
            
            nuevo_nombre = f"{start_index:02d}-{tipo} {numero}-{anio}_hn - {titulo_limpio}.pdf"
        
        # Prevenir colisiones si nombres idénticos se generan
        ruta_original = os.path.join(directorio, archivo)
        ruta_nueva = os.path.join(directorio, nuevo_nombre)
        
        counter = 1
        while os.path.exists(ruta_nueva):
            if archivo.lower() == nuevo_nombre.lower():
                break
            nuevo_nombre = f"{nuevo_nombre[:-4]}_{counter}.pdf"
            ruta_nueva = os.path.join(directorio, nuevo_nombre)
            counter += 1

        if archivo != nuevo_nombre:
            try:
                os.rename(ruta_original, ruta_nueva)
                renombrados.append((archivo, nuevo_nombre))
                start_index += 1
            except Exception as e:
                errores.append((archivo, str(e)))

    # Resultados
    print(f"=== REPORTE DE RENOMBRADO ===")
    print(f"Archivos procesados y renombrados exitosamente: {len(renombrados)}")
    for orig, nuev in renombrados:
        print(f"  [OK] {orig}\n       -> {nuev}\n")

    if errores:
        print(f"\nErrores encontrados: {len(errores)}")
        for orig, err in errores:
            print(f"  [Error] {orig}: {err}")

if __name__ == "__main__":
    ejecutar_renombrado()
