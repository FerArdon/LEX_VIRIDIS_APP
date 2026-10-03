"""Pruebas del asistente legal con RAG: fuentes reales, sin inventar citas."""

from types import SimpleNamespace

from lexviridis.ai_assistant import SIN_FUENTES, LegalAIAssistant


class MotorFalso:
    def __init__(self, articulos):
        self.articulos = articulos  # id -> dict
        self.consultas = []

    def search_safe(self, consulta, page_size=5):
        self.consultas.append(consulta)
        resultados = [{"id": i, "file": "ley.pdf", "page": 7, "context": "frag"} for i in self.articulos]
        return SimpleNamespace(results=resultados[:page_size])

    def get_article_by_id(self, article_id):
        return self.articulos.get(article_id)


class IAFalsa:
    def __init__(self, respuesta="Respuesta [Art. 172, Ley Forestal]."):
        self.respuesta = respuesta
        self.prompts = []

    def consultar(self, prompt):
        self.prompts.append(prompt)
        return self.respuesta


ART_172 = {
    "id": 1,
    "numero_articulo": "172",
    "contenido": "CORTE O APROVECHAMIENTO ILEGAL. Quien sin autorizacion corte producto forestal sera sancionado.",
    "pagina": 50,
    "norma_titulo": "Ley Forestal",
    "archivo_pdf": "ley.pdf",
}


def test_la_consulta_de_busqueda_quita_signos_y_palabras_de_relleno():
    q = LegalAIAssistant._consulta_de_busqueda("¿Cuál es la multa por tala ilegal?")
    assert q == "multa tala ilegal"


def test_pregunta_con_signos_llega_al_motor_sin_ellos():
    motor, ia = MotorFalso({1: ART_172}), IAFalsa()
    LegalAIAssistant(motor, ia).answer_question("¿Cuál es la multa por tala ilegal?")
    assert motor.consultas[0] == "multa tala ilegal"
    assert not any("¿" in q or "?" in q for q in motor.consultas)


def test_se_busca_tambien_con_una_palabra_menos():
    q = LegalAIAssistant._consultas("¿Cuál es la multa por tala ilegal?")
    assert q[0] == "multa tala ilegal"
    assert {"tala ilegal", "multa ilegal", "multa tala"} <= set(q)


def test_pregunta_de_multas_agrega_el_regimen_de_sanciones_del_tema():
    assert "multas sanciones administrativas forestal" in LegalAIAssistant._consultas("multa por tala ilegal")
    assert not any(
        "sanciones administrativas" in x for x in LegalAIAssistant._consultas("requisitos licencia ambiental")
    )


def test_el_prompt_lleva_el_texto_completo_del_articulo():
    motor, ia = MotorFalso({1: ART_172}), IAFalsa()
    r = LegalAIAssistant(motor, ia).answer_question("multa tala ilegal")
    assert "Ley Forestal — Art. 172" in ia.prompts[0]
    assert "sin autorizacion corte producto forestal" in ia.prompts[0]
    assert r["sources"][0]["numero_articulo"] == "172" and r["sources"][0]["file"] == "ley.pdf"


def test_sin_fuentes_no_se_consulta_a_la_ia():
    motor, ia = MotorFalso({}), IAFalsa()
    r = LegalAIAssistant(motor, ia).answer_question("¿asunto sin relacion alguna?")
    assert r["answer"] == SIN_FUENTES
    assert ia.prompts == [] and r["sources"] == []


def test_cita_inventada_se_marca_como_no_verificada():
    motor = MotorFalso({1: ART_172})
    ia = IAFalsa("Dice [Art. 172, Ley Forestal] y también [Art. 168, Ley Forestal].")
    r = LegalAIAssistant(motor, ia).answer_question("multa tala ilegal")
    assert "Verifica estas citas" in r["answer"]
    avisos = r["answer"].split("Verifica estas citas")[1]
    assert "Art. 168" in avisos and "Art. 172" not in avisos


def test_cita_respaldada_no_genera_aviso(  # noqa: D103
):
    motor, ia = MotorFalso({1: ART_172}), IAFalsa("Ver [Art. 172, Ley Forestal].")
    r = LegalAIAssistant(motor, ia).answer_question("multa tala ilegal")
    assert "Verifica" not in r["answer"]


def test_el_mismo_articulo_en_varios_documentos_ocupa_un_solo_cupo():
    copia = {
        **ART_172,
        "id": 2,
        "norma_titulo": "Ley Organica del COLPROFORH",
        "contenido": "ARTÍCULO 172.- " + ART_172["contenido"].lower(),
    }
    otro = {**ART_172, "id": 3, "numero_articulo": "166", "contenido": "Multas desde un mes de salario minimo."}
    motor, ia = MotorFalso({1: ART_172, 2: copia, 3: otro}), IAFalsa()
    r = LegalAIAssistant(motor, ia).answer_question("multa tala ilegal")
    assert [s["numero_articulo"] for s in r["sources"]] == ["172", "166"]
    assert r["sources"][0]["also_in"] == ["Ley Organica del COLPROFORH"]


def test_articulo_pegado_dentro_del_bloque_no_se_marca_como_dudoso():
    bloque = {
        **ART_172,
        "contenido": ART_172["contenido"] + " ARTÍCULO 173.- TRANSPORTE ILEGAL. Pena de cuatro a siete anos.",
    }
    ia = IAFalsa("El transporte ilegal se castiga [Art. 173, Ley Forestal].")
    r = LegalAIAssistant(MotorFalso({1: bloque}), ia).answer_question("transporte ilegal")
    assert "Verifica" not in r["answer"]
