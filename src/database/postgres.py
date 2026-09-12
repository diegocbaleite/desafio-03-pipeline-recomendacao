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
    comentarios: list[dict[str, Any]] | None = None,
) -> int:
    """Carrega dados em uma única transação e retorna o total processado."""
    usuarios = sorted(
        {r["usuario_id"] for r in interacoes}
        | ({r["usuario_id"] for r in comentarios} if comentarios else set())
    )
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


def atualizar_embeddings_postgres(
    config: dict[str, Any],
    embeddings: dict[int, Any],
) -> int:
    """Atualiza os vetores de embedding na tabela conteudos via pgvector (RF08)."""
    if not embeddings:
        return 0

    dados = []
    for cid, vetor in embeddings.items():
        lista_vetor = vetor.tolist() if hasattr(vetor, "tolist") else list(vetor)
        dados.append((str(lista_vetor), int(cid)))

    with _conectar(config) as conexao:
        with conexao.cursor() as cursor:
            execute_values(
                cursor,
                """
                UPDATE conteudos AS c
                SET embedding = v.vetor::vector
                FROM (VALUES %s) AS v(vetor, conteudo_id)
                WHERE c.conteudo_id = v.conteudo_id
                """,
                dados,
            )
    return len(dados)


def carregar_recomendacoes_postgres(
    config: dict[str, Any],
    recomendacoes: list[dict[str, Any]],
) -> int:
    """Persiste recomendações personalizadas na tabela recomendacoes do PostgreSQL (RF11)."""
    if not recomendacoes:
        return 0

    valores = [
        (
            int(r["usuario_id"]),
            int(r["conteudo_id"]),
            float(r["pontuacao"]),
            int(r["posicao"]),
            str(r.get("status", "")),
            r.get("data_geracao"),
        )
        for r in recomendacoes
    ]

    with _conectar(config) as conexao:
        with conexao.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO recomendacoes (
                    usuario_id, conteudo_id, pontuacao, posicao, status, data_geracao
                ) VALUES %s
                ON CONFLICT (usuario_id, conteudo_id, data_geracao) DO UPDATE SET
                    pontuacao = EXCLUDED.pontuacao,
                    posicao = EXCLUDED.posicao,
                    status = EXCLUDED.status
                """,
                valores,
            )
    return len(valores)


def consultar_conteudos_similares_pgvector(
    config: dict[str, Any],
    vetor_consulta: Any,
    limite: int = 5,
) -> list[dict[str, Any]]:
    """Consulta os conteúdos mais similares usando pgvector e operador <=> (RF09)."""
    lista_vetor = (
        vetor_consulta.tolist()
        if hasattr(vetor_consulta, "tolist")
        else list(vetor_consulta)
    )
    str_vetor = str(lista_vetor)

    with _conectar(config) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    c.conteudo_id,
                    c.titulo,
                    cat.nome AS categoria,
                    c.tipo,
                    ROUND((1 - (c.embedding <=> %s::vector))::numeric, 4) AS similaridade,
                    ROUND((c.embedding <=> %s::vector)::numeric, 4) AS distancia
                FROM conteudos c
                JOIN categorias cat ON cat.categoria_id = c.categoria_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (str_vetor, str_vetor, str_vetor, limite),
            )
            linhas = cursor.fetchall()

    resultados = []
    for pos, row in enumerate(linhas, start=1):
        resultados.append(
            {
                "posicao": pos,
                "conteudo_id": row[0],
                "titulo": row[1],
                "categoria": row[2],
                "tipo": row[3],
                "similaridade": float(row[4]),
                "distancia": float(row[5]),
            }
        )
    return resultados

