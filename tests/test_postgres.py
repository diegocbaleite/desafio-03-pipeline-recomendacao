"""Testes unitários e de integração do PostgreSQL e pgvector (RF06, RF08, RF11)."""
from __future__ import annotations

import numpy as np
import pytest

from src.database.postgres import (
    _conectar,
    atualizar_embeddings_postgres,
    carregar_postgres,
    carregar_recomendacoes_postgres,
    consultar_conteudos_similares_pgvector,
    criar_estrutura,
)


def test_postgres_conexao_e_ddl(config_global: dict):
    """Testa conexão ativa e criação da estrutura relacional com extensão vector."""
    criar_estrutura(config_global)
    with _conectar(config_global) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
            )
            tabelas = {row[0] for row in cur.fetchall()}

    assert "usuarios" in tabelas
    assert "categorias" in tabelas
    assert "conteudos" in tabelas
    assert "interacoes" in tabelas
    assert "recomendacoes" in tabelas


def test_postgres_carga_transacional_e_idempotencia(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
):
    """Testa carga relacional com integridade referencial e idempotência (ON CONFLICT)."""
    criar_estrutura(config_global)
    total_1 = carregar_postgres(
        config_global,
        catalogo=catalogo_exemplo,
        interacoes=interacoes_exemplo,
    )
    assert total_1 > 0

    # Segunda carga não deve duplicar registros nem levantar erro de PK
    total_2 = carregar_postgres(
        config_global,
        catalogo=catalogo_exemplo,
        interacoes=interacoes_exemplo,
    )
    assert total_2 == total_1


def test_postgres_atualizar_embeddings_pgvector(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
    embeddings_mock: dict[int, np.ndarray],
):
    """Testa gravação e persistência de vetores de 384 dimensões no pgvector."""
    criar_estrutura(config_global)
    carregar_postgres(config_global, catalogo=catalogo_exemplo, interacoes=interacoes_exemplo)

    total_atualizados = atualizar_embeddings_postgres(config_global, embeddings_mock)
    assert total_atualizados == len(embeddings_mock)

    with _conectar(config_global) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM conteudos WHERE embedding IS NOT NULL")
            qtd = cur.fetchone()[0]
            assert qtd >= len(embeddings_mock)


def test_postgres_carregar_recomendacoes(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
):
    """Testa persistência de recomendações na tabela recomendacoes (RF11)."""
    criar_estrutura(config_global)
    carregar_postgres(config_global, catalogo=catalogo_exemplo, interacoes=interacoes_exemplo)

    recomendacoes_teste = [
        {
            "usuario_id": 10,
            "conteudo_id": 2,
            "pontuacao": 85.50,
            "posicao": 1,
            "status": "Positivo",
            "data_geracao": "2026-09-12 10:00:00",
        },
        {
            "usuario_id": 10,
            "conteudo_id": 3,
            "pontuacao": 55.00,
            "posicao": 2,
            "status": "Estável",
            "data_geracao": "2026-09-12 10:00:00",
        },
    ]

    total = carregar_recomendacoes_postgres(config_global, recomendacoes_teste)
    assert total == 2

    with _conectar(config_global) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT usuario_id, conteudo_id, pontuacao, status FROM recomendacoes WHERE usuario_id = 10")
            rows = cur.fetchall()
            assert len(rows) >= 2


def test_postgres_consultar_similares_pgvector(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
    embeddings_mock: dict[int, np.ndarray],
):
    """Testa consulta por similaridade vetorial com operador <=> do pgvector (RF09)."""
    criar_estrutura(config_global)
    carregar_postgres(config_global, catalogo=catalogo_exemplo, interacoes=interacoes_exemplo)
    atualizar_embeddings_postgres(config_global, embeddings_mock)

    vetor_consulta = embeddings_mock[1]
    resultados = consultar_conteudos_similares_pgvector(config_global, vetor_consulta, limite=2)

    assert len(resultados) > 0
    assert resultados[0]["posicao"] == 1
    assert "similaridade" in resultados[0]
    assert "distancia" in resultados[0]
    assert "categoria" in resultados[0]
