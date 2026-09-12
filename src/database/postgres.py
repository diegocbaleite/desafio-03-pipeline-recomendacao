"""Persistência transacional dos dados estruturados no PostgreSQL."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

from src.config import caminho_absoluto


def _conectar(config: dict[str, Any]):
    pg = config["postgres"]
    return psycopg2.connect(
        host=pg["host"],
        port=pg["port"],
        dbname=pg["database"],
        user=pg["user"],
        password=pg["password"],
    )


def criar_estrutura(config: dict[str, Any]) -> None:
    caminho_sql = caminho_absoluto(config["postgres"]["script_criacao"])
    sql = Path(caminho_sql).read_text(encoding="utf-8")
    with _conectar(config) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)


def carregar_postgres(
    config: dict[str, Any],
    catalogo: list[dict[str, Any]],
    interacoes: list[dict[str, Any]],
) -> int:
    """Carrega dados em uma única transação e retorna o total processado."""
    usuarios = sorted({r["usuario_id"] for r in interacoes})
    categorias = sorted({r["categoria"] for r in catalogo})
    total = 0

    with _conectar(config) as conexao:
        with conexao.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO usuarios (usuario_id)
                VALUES %s
                ON CONFLICT (usuario_id) DO NOTHING
                """,
                [(u,) for u in usuarios],
            )
            total += len(usuarios)

            execute_values(
                cursor,
                """
                INSERT INTO categorias (nome)
                VALUES %s
                ON CONFLICT (nome) DO NOTHING
                """,
                [(c,) for c in categorias],
            )
            total += len(categorias)

            cursor.execute("SELECT categoria_id, nome FROM categorias")
            categorias_ids = {nome: cid for cid, nome in cursor.fetchall()}

            conteudos_valores = [
                (
                    r["conteudo_id"],
                    r["titulo"],
                    r["tipo"],
                    categorias_ids[r["categoria"]],
                    r["nivel"],
                    r["carga_horaria_min"],
                    r["data_publicacao"],
                    r["descricao"],
                    r["autor"],
                )
                for r in catalogo
            ]
            execute_values(
                cursor,
                """
                INSERT INTO conteudos (
                    conteudo_id, titulo, tipo, categoria_id, nivel,
                    carga_horaria_min, data_publicacao, descricao, autor
                ) VALUES %s
                ON CONFLICT (conteudo_id) DO UPDATE SET
                    titulo = EXCLUDED.titulo,
                    tipo = EXCLUDED.tipo,
                    categoria_id = EXCLUDED.categoria_id,
                    nivel = EXCLUDED.nivel,
                    carga_horaria_min = EXCLUDED.carga_horaria_min,
                    data_publicacao = EXCLUDED.data_publicacao,
                    descricao = EXCLUDED.descricao,
                    autor = EXCLUDED.autor
                """,
                conteudos_valores,
            )
            total += len(conteudos_valores)

            interacoes_valores = [
                (
                    r["interacao_id"],
                    r["usuario_id"],
                    r["conteudo_id"],
                    r["tipo_interacao"],
                    r["data_hora"],
                    r["tempo_consumido_min"],
                    r["percentual_conclusao"],
                    r.get("avaliacao"),
                )
                for r in interacoes
            ]
            execute_values(
                cursor,
                """
                INSERT INTO interacoes (
                    interacao_id, usuario_id, conteudo_id, tipo_interacao,
                    data_hora, tempo_consumido_min, percentual_conclusao, avaliacao
                ) VALUES %s
                ON CONFLICT (interacao_id) DO UPDATE SET
                    usuario_id = EXCLUDED.usuario_id,
                    conteudo_id = EXCLUDED.conteudo_id,
                    tipo_interacao = EXCLUDED.tipo_interacao,
                    data_hora = EXCLUDED.data_hora,
                    tempo_consumido_min = EXCLUDED.tempo_consumido_min,
                    percentual_conclusao = EXCLUDED.percentual_conclusao,
                    avaliacao = EXCLUDED.avaliacao
                """,
                interacoes_valores,
            )
            total += len(interacoes_valores)
    return total
