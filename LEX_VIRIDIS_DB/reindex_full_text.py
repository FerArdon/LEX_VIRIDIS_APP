"""
Reindexa la base de datos con el TEXTO COMPLETO de cada articulo.

Problema que corrige: el importador anterior (reimport_with_pages.py) guardaba solo los 200 caracteres
posteriores a cada mencion de "Articulo N" (incluidas las citas dentro de otros articulos), de modo que
el buscador solo veia fragmentos sueltos y mal numerados.

Aqui cada articulo se detecta SOLO cuando "ARTICULO N" abre una linea y va seguido de puntuacion
(``ARTICULO 177.-``), y su contenido llega hasta el siguiente encabezado. Los articulos muy largos se
parten en bloques de ~6000 caracteres; los PDF sin encabezados se indexan pagina por pagina.

Uso (genera una base nueva, no toca la original):
    python LEX_VIRIDIS_DB/reindex_full_text.py --out ruta/nueva.db
"""

from __future__ import annotations

import argparse
import bisect
import logging
import re
import shutil
import sqlite3
import sys
from pathlib import Path

import fitz  # PyMuPDF

RAIZ = Path(__file__).resolve().parent.parent
DB_ORIGINAL = RAIZ / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
MAX_BLOQUE = 6000
MIN_ENCABEZADOS = 3  # menos que esto: el PDF se considera "sin articulos" y se indexa por pagina
MIN_CHARS_PAGINA = 80

ORDINALES = r"PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[EÉ]PTIMO|OCTAVO|NOVENO|D[EÉ]CIMO"
# Encabezado: inicio de linea + "ARTICULO" + numero (opcional sufijo -A) + puntuacion obligatoria.
ENCABEZADO = re.compile(
    rf"^[ \t]*(?:ART[ÍI]CULO|Art[íi]culo|Art\.)[ \t]*((?:\d+(?:[ \t]*[-–][ \t]*[A-Za-z]{{1,2}})?)|{ORDINALES})"
    r"[ \t]*(?:[ºo°])?[ \t]*[.\-–:]",
    re.MULTILINE | re.IGNORECASE,
)


CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f�]")


def limpiar(texto: str) -> str:
    """Quita caracteres de control, guiones de fin de linea y colapsa espacios."""
    texto = CONTROL.sub("", texto)
    texto = re.sub(r"-\n(?=[a-záéíóúñ])", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def partir(texto: str, maximo: int = MAX_BLOQUE) -> list[tuple[int, str]]:
    """Parte un texto largo en bloques; devuelve (desplazamiento, bloque)."""
    bloques, inicio = [], 0
    while len(texto) - inicio > maximo:
        corte = texto.rfind(". ", inicio + int(maximo * 0.6), inicio + maximo)
        if corte == -1:
            corte = texto.rfind(" ", inicio + int(maximo * 0.6), inicio + maximo)
        corte = corte + 1 if corte != -1 else inicio + maximo
        bloques.append((inicio, texto[inicio:corte]))
        inicio = corte
    bloques.append((inicio, texto[inicio:]))
    return bloques


def extraer_articulos(ruta_pdf: Path) -> tuple[list[tuple[str, str, int]], int]:
    """Devuelve ([(numero, contenido, pagina)], paginas_sin_texto)."""
    with fitz.open(ruta_pdf) as doc:
        paginas = [doc[i].get_text() or "" for i in range(doc.page_count)]
    sin_texto = sum(1 for p in paginas if len(p.strip()) < MIN_CHARS_PAGINA)

    inicios, texto = [], ""
    for p in paginas:
        inicios.append(len(texto))
        texto += p + "\n"

    def pagina_de(pos: int) -> int:
        return max(bisect.bisect_right(inicios, pos), 1)

    encabezados = list(ENCABEZADO.finditer(texto))
    segmentos: list[tuple[str, int, str]] = []  # (numero, posicion_inicio, texto_crudo)

    if len(encabezados) >= MIN_ENCABEZADOS:
        if len(limpiar(texto[: encabezados[0].start()])) >= 200:
            segmentos.append(("Preámbulo", 0, texto[: encabezados[0].start()]))
        for i, m in enumerate(encabezados):
            fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(texto)
            numero = re.sub(r"\s+", "", m.group(1)).replace("–", "-").upper()
            segmentos.append((numero, m.start(), texto[m.start() : fin]))
    else:
        for n, p in enumerate(paginas):
            if len(p.strip()) >= MIN_CHARS_PAGINA:
                segmentos.append((f"Pág. {n + 1}", inicios[n], p))

    resultado = []
    for numero, pos, crudo in segmentos:
        for desplazamiento, bloque in partir(limpiar(crudo)):
            if sum(c.isalpha() for c in bloque) < 20:  # sin letras utiles: basura de PDF mal codificado
                continue
            # La pagina del bloque se aproxima por su posicion relativa dentro del segmento
            pagina = pagina_de(pos + int(desplazamiento * len(crudo) / max(len(limpiar(crudo)), 1)))
            resultado.append((numero, bloque, pagina))
    return resultado, sin_texto


def reindexar(db_origen: Path, pdf_dir: Path, db_salida: Path) -> dict:
    if db_salida.exists():
        raise SystemExit(f"La salida ya existe: {db_salida}")
    db_salida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(db_origen, db_salida)

    con = sqlite3.connect(db_salida)
    cur = con.cursor()
    # El trigger heredado inserta en una columna inexistente (tags) y haria fallar cualquier INSERT
    cur.execute("DROP TRIGGER IF EXISTS insert_articulo_fts")
    cur.execute("DELETE FROM busqueda_fts")
    cur.execute("DELETE FROM articulos")

    por_nombre = {}
    for nid, ruta in cur.execute("SELECT id, archivo_pdf FROM normas WHERE archivo_pdf IS NOT NULL"):
        por_nombre[Path(ruta.replace("\\", "/")).name.lower()] = nid

    stats = {"pdfs": 0, "normas_nuevas": 0, "articulos": 0, "pdfs_sin_texto": 0, "errores": 0}
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        nid = por_nombre.get(pdf.name.lower())
        if nid is None:
            tipo = "Decreto" if "decreto" in pdf.name.lower() else "Ley"
            cur.execute("INSERT INTO normas (tipo, titulo, archivo_pdf) VALUES (?, ?, ?)", (tipo, pdf.stem, str(pdf)))
            nid = cur.lastrowid
            stats["normas_nuevas"] += 1
        try:
            articulos, sin_texto = extraer_articulos(pdf)
        except Exception as e:  # PDF danado o protegido: se registra y se sigue
            logging.error("%s: %s", pdf.name, e)
            stats["errores"] += 1
            continue
        stats["pdfs"] += 1
        if not articulos:
            stats["pdfs_sin_texto"] += 1
        cur.executemany(
            "INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina) VALUES (?, ?, ?, ?)",
            [(nid, numero, contenido, pagina) for numero, contenido, pagina in articulos],
        )
        stats["articulos"] += len(articulos)

    cur.execute(
        """INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id)
           SELECT n.titulo, a.contenido, a.numero_articulo, a.id
           FROM articulos a JOIN normas n ON n.id = a.norma_id"""
    )
    # Trigger corregido: mantiene el indice al agregar articulos (p. ej. importando un PDF desde la app)
    cur.execute(
        """CREATE TRIGGER insert_articulo_fts AFTER INSERT ON articulos BEGIN
               INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id)
               SELECT n.titulo, new.contenido, new.numero_articulo, new.id FROM normas n WHERE n.id = new.norma_id;
           END"""
    )
    cur.execute("INSERT INTO busqueda_fts(busqueda_fts) VALUES('optimize')")
    con.commit()
    cur.execute("ANALYZE")
    con.commit()
    con.close()
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DB_ORIGINAL, help="base de origen (se copia, no se modifica)")
    ap.add_argument("--pdf-dir", type=Path, default=RAIZ / "COMPENDIO LEYES FEMA")
    ap.add_argument("--out", type=Path, required=True, help="base nueva a generar")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    stats = reindexar(args.db, args.pdf_dir, args.out)
    logging.info("Listo: %s", stats)


if __name__ == "__main__":
    main()
