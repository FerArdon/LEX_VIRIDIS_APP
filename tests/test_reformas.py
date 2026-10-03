"""Un decreto que reforma un articulo debe prevalecer sobre el texto original del codigo."""

import sqlite3

import pytest

from lexviridis.ai_assistant import LegalAIAssistant
from lexviridis.search_engine import DatabaseManager, SearchEngine

ORIGINAL = (
    "ARTÍCULO 327.- INCENDIO FORESTAL. Quien provoca un incendio en terrenos forestales debe ser castigado con "
    "las penas de prisión de cinco (5) a ocho (8) años y multa de doscientos (200) a quinientos (500) días."
)
REFORMA = (
    "3 La Gaceta Sección A “ARTÍCULO 327.- INCENDIO FORESTAL. Quien provoca un incendio en terrenos forestales "
    "debe ser castigado con las penas de prisión de seis (6) a diez (10) años y multa de quinientos (500) a "
    "ochocientos (800) días.” “ARTÍCULO 337-A. RESPONSABILIDAD DE LAS PERSONAS JURÍDICAS. Cuando una persona..."
)
OTRO_ARTICULO_327 = "ARTÍCULO 327.- NORMAS DE COMERCIO. Las empresas deben registrar sus operaciones comerciales."

NORMAS = {
    1: "Código Penal",
    2: "Decreto 59-2024 (Ref. Delitos Ambientales)",
    3: "Reglamento de Comercio con reformas",
    4: "Código Penal con reformas",
}
ARTICULOS = [
    (1, "327", ORIGINAL, 78),
    (2, "Pág. 3", REFORMA, 3),
    (3, "Pág. 9", OTRO_ARTICULO_327, 9),
    (4, "327", ORIGINAL, 80),  # copia de la misma ley "con reformas" ya incorporadas: no es una reforma
]


@pytest.fixture
def motor(tmp_path):
    ruta = tmp_path / "reformas.db"
    con = sqlite3.connect(ruta)
    con.executescript(
        """
        CREATE TABLE normas (id INTEGER PRIMARY KEY, titulo TEXT NOT NULL, tipo TEXT, archivo_pdf TEXT,
                             resumen TEXT, fecha_publicacion TEXT);
        CREATE TABLE articulos (id INTEGER PRIMARY KEY AUTOINCREMENT, norma_id INTEGER NOT NULL,
                                numero_articulo TEXT, contenido TEXT, pagina INTEGER);
        CREATE VIRTUAL TABLE busqueda_fts USING fts5(titulo_norma, contenido_articulo, numero_articulo,
                                                     articulo_id UNINDEXED);
        """
    )
    for nid, titulo in NORMAS.items():
        con.execute("INSERT INTO normas (id, titulo, archivo_pdf) VALUES (?, ?, ?)", (nid, titulo, f"{nid}.pdf"))
    for nid, numero, contenido, pagina in ARTICULOS:
        cur = con.execute(
            "INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina) VALUES (?, ?, ?, ?)",
            (nid, numero, contenido, pagina),
        )
        con.execute(
            "INSERT INTO busqueda_fts (titulo_norma, contenido_articulo, numero_articulo, articulo_id) VALUES (?, ?, ?, ?)",
            (NORMAS[nid], contenido, numero, cur.lastrowid),
        )
    con.commit()
    con.close()
    DatabaseManager._instance = None
    DatabaseManager(ruta)
    yield SearchEngine()
    DatabaseManager._instance = None


def test_encuentra_la_reforma_recortada_desde_el_articulo(motor):
    r = motor.find_reforms("327", "INCENDIO FORESTAL", "Código Penal")
    assert r["norma_titulo"].startswith("Decreto 59-2024")
    assert r["contenido"].startswith("ARTÍCULO 327")
    assert "seis (6) a diez (10)" in r["contenido"]


def test_no_confunde_otro_articulo_con_el_mismo_numero(motor):
    # El "Reglamento de Comercio con reformas" tiene un Art. 327 distinto: el encabezado no coincide
    assert motor.find_reforms("327", "NORMAS DE COMERCIO", "otra norma")["norma_titulo"].startswith("Reglamento")
    assert motor.find_reforms("327", "ESTAFA", "Código Penal") is None


def test_sin_numero_o_encabezado_no_busca(motor):
    assert motor.find_reforms("Pág. 3", "INCENDIO FORESTAL") is None
    assert motor.find_reforms("327", "") is None


class IAFalsa:
    def __init__(self):
        self.prompt = ""

    def consultar(self, prompt):
        self.prompt = prompt
        return "Según la reforma [Art. 327, Decreto 59-2024]."


def test_el_asistente_entrega_la_reforma_marcada(motor):
    ia = IAFalsa()
    res = LegalAIAssistant(motor, ia).answer_question("¿Cuántos años por incendio forestal?")
    reformas = [s for s in res["sources"] if s.get("reforma_de")]
    assert len(reformas) == 1
    assert "[REFORMA" in ia.prompt and "seis (6) a diez (10)" in ia.prompt
    # La copia "con reformas" tiene el mismo texto original: no cuenta como reforma
    assert all(s["norma_titulo"] != "Código Penal con reformas" for s in reformas)
