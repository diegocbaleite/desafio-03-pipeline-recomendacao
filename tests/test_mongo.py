"""Testes unitários e de integração do MongoDB (RF07)."""
from __future__ import annotations

import pytest

from src.database.mongo import (
    agregar_por_categoria,
    buscar_por_tag,
    carregar_comentarios_mongo,
    conectar_mongo,
    consultar_por_conteudo,
    filtrar_por_nota,
    obter_colecao_comentarios,
)


def test_mongo_conexao_e_ping(config_global: dict):
    """Testa cliente e conexão ativa com o servidor MongoDB."""
    cliente = conectar_mongo(config_global)
    resposta = cliente.admin.command("ping")
    assert resposta.get("ok") == 1.0


def test_mongo_carga_comentarios_e_desnormalizacao(
    config_global: dict,
    catalogo_exemplo: list[dict],
):
    """Testa ingestão no MongoDB com enriquecimento e desnormalização do campo 'categoria'."""
    comentarios = [
        {
            "usuario_id": 1,
            "conteudo_id": 1,
            "avaliacao": 5.0,
            "comentario": "Excelente curso de Python.",
            "tags": ["python", "dados"],
            "data": "2026-09-01",
        },
        {
            "usuario_id": 2,
            "conteudo_id": 2,
            "avaliacao": 4.0,
            "comentario": "Ótimo aprofundamento em PostgreSQL.",
            "tags": ["sql", "banco"],
            "data": "2026-09-02",
        },
        {
            "usuario_id": 3,
            "conteudo_id": 999,  # Inexistente
            "avaliacao": 3.0,
            "comentario": "Conteúdo fantasma.",
            "tags": ["teste"],
            "data": "2026-09-03",
        },
    ]

    res = carregar_comentarios_mongo(
        config_global,
        comentarios=comentarios,
        catalogo=catalogo_exemplo,
    )

    assert res["validos_inseridos"] == 2
    assert res["rejeitados"] == 1

    colecao = obter_colecao_comentarios(config_global)
    doc = colecao.find_one({"conteudo_id": 1})
    assert doc is not None
    assert doc["categoria"] == "Ciência De Dados"
    assert "python" in doc["tags"]


def test_mongo_indices_criados(config_global: dict):
    """Verifica se os índices obrigatórios foram criados no MongoDB."""
    colecao = obter_colecao_comentarios(config_global)
    info_indices = colecao.index_information()

    campos_indexados = set()
    for _, info in info_indices.items():
        for campo, _ in info.get("key", []):
            campos_indexados.add(campo)

    assert "conteudo_id" in campos_indexados
    assert "tags" in campos_indexados
    assert "avaliacao" in campos_indexados
    assert "categoria" in campos_indexados


def test_mongo_operacao_consultar_por_conteudo(config_global: dict):
    """Testa RF07: consultar comentários de determinado conteúdo."""
    docs = consultar_por_conteudo(config_global, conteudo_id=1, limite=5)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert docs[0]["conteudo_id"] == 1


def test_mongo_operacao_buscar_por_tag(config_global: dict):
    """Testa RF07: localizar documentos por tag."""
    docs = buscar_por_tag(config_global, tag="python", limite=5)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert "python" in docs[0]["tags"]


def test_mongo_operacao_filtrar_por_nota(config_global: dict):
    """Testa RF07: filtrar avaliações pela nota."""
    docs = filtrar_por_nota(config_global, nota_minima=4.5, limite=5)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(d["avaliacao"] >= 4.5 for d in docs)


def test_mongo_operacao_agregar_por_categoria(config_global: dict):
    """Testa RF07: agregar a quantidade de comentários ou avaliações por categoria."""
    agregacoes = agregar_por_categoria(config_global)
    assert isinstance(agregacoes, list)
    assert len(agregacoes) > 0

    primeira = agregacoes[0]
    assert "categoria" in primeira
    assert "total_comentarios" in primeira
    assert "media_avaliacao" in primeira
    assert primeira["total_comentarios"] >= 1
