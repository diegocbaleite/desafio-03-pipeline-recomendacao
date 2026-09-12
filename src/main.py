"""Ponto de entrada reproduzível do Desafio 03."""
from __future__ import annotations

import json
from time import perf_counter

from src.config import caminho_absoluto, carregar_config
from src.database.postgres import carregar_postgres, criar_estrutura
from src.ingestao.pipeline import executar_ingestao
from src.logging_utils import configurar_logger


def _salvar_resumo(config, resultado, inicio_total: float) -> None:
    resultado["resumo"]["tempo_total_segundos"] = round(
        perf_counter() - inicio_total, 4
    )
    caminho_resumo = caminho_absoluto(config["dados"]["resumo_ingestao"])
    caminho_resumo.write_text(
        json.dumps(resultado["resumo"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    inicio_total = perf_counter()
    config = carregar_config()
    logger = configurar_logger(caminho_absoluto(config["logs"]["arquivo"]))
    logger.info("Início do processamento do Desafio 03")

    resultado = None
    try:
        try:
            resultado = executar_ingestao(config, logger)
        except Exception:
            logger.exception("Falha na etapa de ingestão")
            raise

        if config["postgres"].get("carregar_automaticamente", True):
            inicio_postgres = perf_counter()
            try:
                criar_estrutura(config)
                total = carregar_postgres(
                    config,
                    resultado["catalogo"],
                    resultado["interacoes"],
                )
                resultado["resumo"]["carregados_banco"]["postgresql"] = total
                logger.info(
                    "Carga PostgreSQL concluída: %s registros processados | tempo=%.4fs",
                    total,
                    perf_counter() - inicio_postgres,
                )
            except Exception:
                logger.exception("Falha de conexão/persistência no PostgreSQL")
                raise
    finally:
        tempo_total = perf_counter() - inicio_total
        if resultado is not None:
            _salvar_resumo(config, resultado, inicio_total)
        logger.info("Tempo total do processamento: %.4fs", tempo_total)
        logger.info("Término do processamento")


if __name__ == "__main__":
    main()
