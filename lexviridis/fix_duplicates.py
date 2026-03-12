import shutil
import sqlite3

db_path = r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db"
backup_path = r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental_backup.db"

# 1. Crear backup
print(f"Creando backup en {backup_path}...")
shutil.copy2(db_path, backup_path)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Pares identificados: (ID_PLACEHOLDER_A_BORRAR, ID_REAL_A_RENOMBRAR)
    pairs = [
        (1, 5),  # Ley General del Ambiente
        (2, 7),  # Ley Forestal
        (3, 6),  # Ley General de Aguas
        (4, 157),  # Código Penal
    ]

    print("\nIniciando fusión...")
    for old_id, new_id in pairs:
        # Obtener titulo bonito del placeholder
        cursor.execute("SELECT titulo FROM normas WHERE id=?", (old_id,))
        row = cursor.fetchone()
        if not row:
            print(f"Skipping pair {old_id}->{new_id}: ID {old_id} no existe")
            continue

        nice_title = row[0]

        # Verificar que el ID real exista
        cursor.execute("SELECT titulo FROM normas WHERE id=?", (new_id,))
        if not cursor.fetchone():
            print(f"Skipping pair {old_id}->{new_id}: ID {new_id} no existe")
            continue

        print(f"Fucionando: '{nice_title}' (ID {old_id}) -> ID {new_id}")

        # 1. Actualizar titulo del ID real
        cursor.execute("UPDATE normas SET titulo=? WHERE id=?", (nice_title, new_id))

        # 2. Borrar placeholder
        cursor.execute("DELETE FROM normas WHERE id=?", (old_id,))

        print(f"   Success: ID {new_id} renombrado, ID {old_id} eliminado.")

    conn.commit()
    print("\nFusión completada exitosamente.")
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    # Restaurar backup si es crítico? Por seguridad imprimimos instrucción
    print(f"Si algo salió mal, restaurar desde: {backup_path}")
