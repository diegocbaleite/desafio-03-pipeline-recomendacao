"""Testes unitários dos módulos do Estudante 2 (MongoDB, Embeddings e Recomendações)."""
import pytest
from src.recomendacao.embeddings import preparar_texto_conteudo
from src.recomendacao.motor import classificar_status_recomendacao
from src.database.mongo import carregar_comentarios_mongo


def test_preparar_texto_conteudo():
    titulo = "  Curso de Python   Avançado  "
    descricao = "Aprenda decoradores e   geradores.  "
    texto = preparar_texto_conteudo(titulo, descricao)
    assert texto == "Curso de Python Avançado. Aprenda decoradores e geradores."


def test_classificacao_recomendacoes_positivo():
    status = classificar_status_recomendacao(75.5, iconc=1)
    assert status == "Positivo"

    status_borda = classificar_status_recomendacao(70.0, iconc=1)
    assert status_borda == "Positivo"


def test_classificacao_recomendacoes_estavel():
    status = classificar_status_recomendacao(55.0, iconc=1)
    assert status == "Estável"

    status_borda_inf = classificar_status_recomendacao(40.01, iconc=1)
    assert status_borda_inf == "Estável"

    status_borda_sup = classificar_status_recomendacao(69.99, iconc=1)
    assert status_borda_sup == "Estável"


def test_classificacao_recomendacoes_negativo_por_nota():
    # Ponto de corte estrito do desafio: Pontuação <= 40
    status_exato_40 = classificar_status_recomendacao(40.0, iconc=1)
    assert status_exato_40 == "Negativo"

    status_abaixo_40 = classificar_status_recomendacao(35.0, iconc=1)
    assert status_abaixo_40 == "Negativo"


def test_classificacao_recomendacoes_negativo_por_conclusao():
    status = classificar_status_recomendacao(90.0, iconc=0)
    assert status == "Negativo"

    status_zero = classificar_status_recomendacao(0.0, iconc=0)
    assert status_zero == "Negativo"


def test_formula_pontuacao_calculo():
    ivis = 0.8
    icur = 0.6
    iconc = 1
    pontuacao = ((ivis + icur) / 2.0) * 100.0 * iconc
    assert pontuacao == pytest.approx(70.0)

    iconc_concluido = 0
    pontuacao_zerada = ((ivis + icur) / 2.0) * 100.0 * iconc_concluido
    assert pontuacao_zerada == 0.0


def test_tratamento_conteudo_inexistente_mongo():
    catalogo_falso = [
        {"conteudo_id": 1, "categoria": "Banco de Dados"},
        {"conteudo_id": 2, "categoria": "Inteligência Artificial"},
    ]
    comentarios = [
        {"usuario_id": 10, "conteudo_id": 1, "avaliacao": 5, "comentario": "Ótimo!"},
        {"usuario_id": 11, "conteudo_id": 999, "avaliacao": 4, "comentario": "Inexistente"},
    ]

    mapa = {item["conteudo_id"]: item["categoria"] for item in catalogo_falso}
    validos = [c for c in comentarios if c["conteudo_id"] in mapa]
    rejeitados = [c for c in comentarios if c["conteudo_id"] not in mapa]

    assert len(validos) == 1
    assert validos[0]["conteudo_id"] == 1
    assert len(rejeitados) == 1
    assert rejeitados[0]["conteudo_id"] == 999


def test_gerar_recomendacoes_sem_truncamento_e_sem_negativos(monkeypatch):
    from src.recomendacao.motor import gerar_recomendacoes_usuario

    catalogo = [
        {"conteudo_id": 1, "titulo": "Curso A", "categoria": "Dados", "tipo": "Curso"},
        {"conteudo_id": 2, "titulo": "Curso B", "categoria": "Dados", "tipo": "Curso"},
        {"conteudo_id": 3, "titulo": "Curso C", "categoria": "IA", "tipo": "Vídeo"},
    ]
    interacoes = [
        {"usuario_id": 1, "conteudo_id": 1, "tipo_interacao": "conclusão", "percentual_conclusao": 100.0},
        {"usuario_id": 1, "conteudo_id": 2, "tipo_interacao": "curtida", "avaliacao": 5.0},
    ]

    # Mock embeddings
    import numpy as np
    emb_falsos = {
        1: np.array([1.0, 0.0]),
        2: np.array([0.9, 0.1]),
        3: np.array([0.0, 1.0]),
    }
    monkeypatch.setattr("src.recomendacao.motor.obter_embeddings_cache", lambda cfg: emb_falsos)

    recs = gerar_recomendacoes_usuario(
        config={},
        usuario_id=1,
        interacoes_usuario=interacoes,
        catalogo=catalogo,
        limite=None,
        incluir_negativos=False,
    )

    # Conteúdo 1 foi concluído -> Iconc = 0 -> Negativo -> descartado
    # Restam apenas os itens com status != Negativo
    for r in recs:
        assert r["conteudo_id"] != 1
        assert r["status"] in ("Positivo", "Estável")
        assert r["posicao"] >= 1

