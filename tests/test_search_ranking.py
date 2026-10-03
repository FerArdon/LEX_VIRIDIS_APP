"""Pruebas del orden de resultados: frase exacta, todas las palabras, alguna y sinonimos."""

import sqlite3

import pytest

from lexviridis.search_engine import DatabaseManager, SearchEngine

NIVELES = ["exacta", "frase", "todas", "alguna", "sinonimos"]

NORMAS = {
    1: "Ley General de Recursos Naturales",
    2: "Compendio Competencias Municipales",
    3: "Codigo Penal",
    4: "Competencias Municipales (copia)",
    5: "Manual de Energia",
}

# (norma_id, numero, contenido, pagina)
ARTICULOS = [
    (1, "17", "El Instituto Nacional del Recurso Hídrico regula el recurso hídrico del país.", 3),
    (2, "25", "Es prohibida la descarga de aguas negras, servidas y excretas en los cuerpos de agua.", 7),
    (
        3,
        "177",
        "Perturbación de instalaciones con alto riesgo de radiación. Quien perturba una instalación nuclear.",
        9,
    ),
    (4, "25", "Es prohibida la descarga de aguas negras, servidas y excretas en los cuerpos de agua.", 7),
    (1, "37", "Las aguas pluviales y negras deben disponerse por separado en el sistema sanitario.", 5),
    (3, "90", "Quien publique listas negras de personas incurre en responsabilidad.", 4),
    (5, "Pág. 4", "Las turbinas hidroeléctricas generan energía a partir del caudal de los ríos de la región.", 4),
]


@pytest.fixture
def motor(tmp_path):
    ruta = tmp_path / "ranking.db"
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
        con.execute(
            "INSERT INTO normas (id, titulo, tipo, archivo_pdf) VALUES (?, ?, 'Ley', ?)", (nid, titulo, f"{nid}.pdf")
        )
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
    motor = SearchEngine()
    assert motor.is_ready
    yield motor
    DatabaseManager._instance = None


def buscar(motor, consulta, pagina=1, tam=10):
    return motor._execute_search(consulta, "OR", pagina, tam)


def test_la_frase_exacta_va_primero(motor):
    res = buscar(motor, "aguas negras")
    assert res[0]["tier"] == "frase"
    assert "aguas negras" in res[0]["context"].lower().replace("*", "")


def test_los_sinonimos_no_superan_a_la_frase(motor):
    """Antes, el sinonimo generico 'hidrico' ganaba a la frase exacta."""
    res = buscar(motor, "aguas negras")
    tiers = [r["tier"] for r in res]
    assert tiers == sorted(tiers, key=NIVELES.index)
    hidrico = next(r for r in res if "Hídrico" in r["context"] or "hídrico" in r["context"].lower())
    assert hidrico["tier"] == "sinonimos"
    assert res.index(hidrico) > 0


def test_un_articulo_sin_relacion_no_aparece(motor):
    res = buscar(motor, "aguas negras")
    assert not any("radiación" in r["context"].lower() for r in res)


def test_todas_las_palabras_van_antes_que_alguna(motor):
    res = buscar(motor, "aguas negras")
    por_nivel = {r["tier"] for r in res}
    assert {"frase", "todas", "alguna"} <= por_nivel
    primero_alguna = next(i for i, r in enumerate(res) if r["tier"] == "alguna")
    assert all(r["tier"] != "todas" for r in res[primero_alguna:])


def test_el_mismo_articulo_copiado_se_muestra_una_vez(motor):
    res = buscar(motor, "aguas negras")
    descarga = [r for r in res if "descarga" in r["context"].lower()]
    assert len(descarga) == 1
    assert len(descarga[0]["also_in"]) == 1


def test_terminos_a_resaltar_incluyen_la_frase_y_las_palabras(motor):
    res = buscar(motor, "aguas negras")
    assert res[0]["highlight_terms"][0] == "aguas negras"
    assert {"aguas", "negras"} <= set(res[0]["highlight_terms"])


def test_resaltado_de_sinonimo_usa_el_termino_que_coincidio(motor):
    res = buscar(motor, "aguas negras")
    hidrico = next(r for r in res if r["tier"] == "sinonimos")
    assert any(t.lower() in ("hídrico", "hidrico") for t in hidrico["highlight_terms"])


def test_consulta_de_una_palabra_es_exacta(motor):
    res = buscar(motor, "radiación")
    assert res and res[0]["tier"] == "exacta"


def test_etiqueta_de_pagina_sin_prefijo_art(motor):
    res = buscar(motor, "turbinas hidroeléctricas")
    assert res[0]["context"].startswith("Pág. 4:")
    assert not res[0]["context"].startswith("Art. Pág.")


def test_paginacion_no_repite_resultados(motor):
    p1 = buscar(motor, "aguas negras", pagina=1, tam=2)
    p2 = buscar(motor, "aguas negras", pagina=2, tam=2)
    assert len(p1) == 2 and p2
    assert not {r["id"] for r in p1} & {r["id"] for r in p2}


def test_consulta_sin_palabras_utiles(motor):
    assert buscar(motor, "de la") == []
