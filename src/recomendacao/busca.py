"""Busca por similaridade semântica (RF09) — Estudante 2."""
from __future__ import annotations

import logging
from typing import Any
import numpy as np

from src.recomendacao.embeddings import (
    carregar_catalogo,
    carregar_modelo_embedding,
    obter_embeddings_cache,
)


def executar_busca_semantica(
    config: dict[str, Any],
    texto_consulta: str,
    limite: int = 5,
    usar_pgvector: bool = False,
) -> list[dict[str, Any]]:
    """
    Realiza busca por similaridade semântica a partir de consulta em linguagem natural:
    1. Converte o texto da consulta em embedding usando SentenceTransformer.
    2. Consulta via pgvector (se solicitado e disponível) ou calcula produto escalar direto.
    3. Retorna os top-K conteúdos mais similares formatados com distância e similaridade.
    """
    nome_modelo = config["embeddings"]["modelo"]
    modelo = carregar_modelo_embedding(nome_modelo)

    # Embedding normalizado da consulta
    vetor_query = np.array(
        modelo.encode(texto_consulta, normalize_embeddings=True),
        dtype=np.float32,
    )

    if usar_pgvector:
        try:
            from src.database.postgres import consultar_conteudos_similares_pgvector
            return consultar_conteudos_similares_pgvector(config, vetor_query, limite=limite)
        except Exception:
            pass  # Fallback para busca em memória caso Postgres/pgvector não esteja acessível

    embeddings = obter_embeddings_cache(config)
    catalogo = carregar_catalogo(config)
    mapa_catalogo = {int(c["conteudo_id"]): c for c in catalogo}

    resultados_pontuados = []
    for cid, vetor_conteudo in embeddings.items():
        if cid not in mapa_catalogo:
            continue
        sim = float(np.dot(vetor_query, vetor_conteudo))
        dist = max(0.0, 1.0 - sim)

        info = mapa_catalogo[cid]
        resultados_pontuados.append(
            {
                "conteudo_id": cid,
                "titulo": info.get("titulo", ""),
                "categoria": info.get("categoria", ""),
                "tipo": info.get("tipo", ""),
                "similaridade": round(sim, 4),
                "distancia": round(dist, 4),
            }
        )

    resultados_pontuados.sort(key=lambda x: x["similaridade"], reverse=True)

    top_k = resultados_pontuados[:limite]
    for pos, item in enumerate(top_k, start=1):
        item["posicao"] = pos

    return top_k


def demonstrar_consultas_semanticas(
    config: dict[str, Any],
    logger: logging.Logger | None = None,
    usar_pgvector: bool = False,
) -> list[dict[str, Any]]:
    """
    Demonstra as 3 consultas semânticas exigidas pelo RF09 e imprime os resultados formatados.
    """
    log = logger or logging.getLogger("ficdev_pipeline")

    consultas_demonstracao = [
        "Quero aprender os fundamentos de banco de dados para inteligência artificial.",
        "Pipelines de dados, orquestração de workflows e processamento distribuído com Apache Spark.",
        "Segurança da informação, conformidade com LGPD e controle de acesso a redes e APIs.",
    ]

    historico_consultas = []

    for idx, texto in enumerate(consultas_demonstracao, start=1):
        log.info("")
        log.info("--- Consulta Semântica %d: '%s' ---", idx, texto)
        resultados = executar_busca_semantica(config, texto, limite=5, usar_pgvector=usar_pgvector)

        for res in resultados:
            log.info(
                "  [%d] ID: %-3d | Similaridade: %.4f | Distância: %.4f | [%s / %s] %s",
                res["posicao"],
                res["conteudo_id"],
                res["similaridade"],
                res["distancia"],
                res["categoria"],
                res["tipo"],
                res["titulo"],
            )

        historico_consultas.append(
            {
                "consulta": texto,
                "resultados": resultados,
            }
        )

    return historico_consultas
