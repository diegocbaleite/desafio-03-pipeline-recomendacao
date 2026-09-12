"""Persistência de recomendações geradas (RF11) — Estudante 2."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.config import caminho_absoluto


def persistir_recomendacoes_em_arquivo(
    config: dict[str, Any],
    recomendacoes: list[dict[str, Any]],
    caminho_saida: str | Path = "dados/processados/recomendacoes.json",
    logger: logging.Logger | None = None,
) -> int:
    """Persiste a lista de recomendações geradas em arquivo JSON processado."""
    log = logger or logging.getLogger("ficdev_pipeline")
    destino = caminho_absoluto(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, ensure_ascii=False, indent=2)

    log.info(
        "Persistidas com sucesso %d recomendações em '%s'.",
        len(recomendacoes),
        destino,
    )
    return len(recomendacoes)


def persistir_recomendacoes_completas(
    config: dict[str, Any],
    recomendacoes: list[dict[str, Any]],
    logger: logging.Logger | None = None,
) -> dict[str, int]:
    """
    Persiste recomendações no PostgreSQL (RF11) e em arquivo JSON para auditoria.
    """
    log = logger or logging.getLogger("ficdev_pipeline")
    total_json = persistir_recomendacoes_em_arquivo(config, recomendacoes, logger=log)

    total_pg = 0
    try:
        from src.database.postgres import carregar_recomendacoes_postgres
        total_pg = carregar_recomendacoes_postgres(config, recomendacoes)
        log.info("Persistidas com sucesso %d recomendações no PostgreSQL.", total_pg)
    except Exception as err:
        log.warning("Não foi possível persistir recomendações no PostgreSQL: %s", err)

    return {"json": total_json, "postgresql": total_pg}
