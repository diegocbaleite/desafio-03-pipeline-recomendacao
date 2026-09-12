"""Ponto de entrada reproduzível do Desafio Prático 1 (FIC_DEV).

Execução oficial:
    python -m src.main
"""
from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from src.config import caminho_absoluto, carregar_config
from src.database.mongo import agregar_por_categoria, carregar_comentarios_mongo
from src.database.postgres import (
    atualizar_embeddings_postgres,
    carregar_postgres,
    carregar_recomendacoes_postgres,
    criar_estrutura,
)
from src.ingestao.pipeline import executar_ingestao
from src.logging_utils import configurar_logger
from src.recomendacao.busca import demonstrar_consultas_semanticas
from src.recomendacao.embeddings import gerar_e_salvar_embeddings
from src.recomendacao.motor import gerar_recomendacoes_em_lote
from src.recomendacao.persistencia import persistir_recomendacoes_em_arquivo


def _salvar_resumo(config: dict[str, Any], resultado: dict[str, Any], inicio_total: float) -> None:
    resultado["resumo"]["tempo_total_segundos"] = round(
        perf_counter() - inicio_total, 4
    )
    caminho_resumo = caminho_absoluto(config["dados"]["resumo_ingestao"])
    caminho_resumo.parent.mkdir(parents=True, exist_ok=True)
    caminho_resumo.write_text(
        json.dumps(resultado["resumo"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    inicio_total = perf_counter()
    config = carregar_config()
    logger = configurar_logger(caminho_absoluto(config["logs"]["arquivo"]))

    logger.info("=================================================================")
    logger.info("INÍCIO DO PIPELINE INTEGRADO — DESAFIO 03 (FIC_DEV)")
    logger.info("=================================================================")

    resultado = None
    try:
        # 1. Ingestão, validação e tratamento (Estudante 1 - RF02, RF03, RF04)
        logger.info("")
        logger.info(">>> [1/5] Executando ingestão, validação e tratamento de dados...")
        try:
            resultado = executar_ingestao(config, logger)
        except Exception:
            logger.exception("Falha crítica na etapa de ingestão")
            raise

        catalogo = resultado["catalogo"]
        interacoes = resultado["interacoes"]
        comentarios = resultado["comentarios"]

        # 2. Carga estruturada no PostgreSQL (Estudante 1 - RF06)
        if config.get("postgres", {}).get("carregar_automaticamente", True):
            inicio_postgres = perf_counter()
            logger.info("")
            logger.info(">>> [2/5] Persistindo dados estruturados no PostgreSQL (RF06)...")
            try:
                criar_estrutura(config)
                total_pg = carregar_postgres(config, catalogo, interacoes, comentarios)
                resultado["resumo"]["carregados_banco"]["postgresql"] = total_pg
                logger.info(
                    "Carga PostgreSQL concluída com sucesso: %d registros processados | tempo=%.4fs",
                    total_pg,
                    perf_counter() - inicio_postgres,
                )
            except Exception as err:
                logger.warning("Falha de conexão/persistência no PostgreSQL: %s", err)

        # 3. Carga e agregação no MongoDB (Estudante 2 - RF07)
        inicio_mongo = perf_counter()
        logger.info("")
        logger.info(">>> [3/5] Persistindo dados semiestruturados no MongoDB (RF07)...")
        try:
            res_mongo = carregar_comentarios_mongo(
                config,
                comentarios=comentarios,
                catalogo=catalogo,
                logger=logger,
            )
            resultado["resumo"]["carregados_banco"]["mongodb"] = res_mongo["validos_inseridos"]

            logger.info("Demonstrando agregação por categoria no MongoDB (RF07):")
            agregacoes = agregar_por_categoria(config)
            for ag in agregacoes[:5]:
                logger.info(
                    "  Categoria: %-25s | Total: %4d | Média Avaliação: %.2f / 5.0",
                    ag["categoria"],
                    ag["total_comentarios"],
                    ag["media_avaliacao"],
                )
            logger.info("Carga e agregação MongoDB concluídas | tempo=%.4fs", perf_counter() - inicio_mongo)
        except Exception as err:
            logger.warning("Falha de conexão/persistência no MongoDB: %s", err)

        # 4. Geração e armazenamento de Embeddings (Estudante 2 - RF08 & RF09)
        inicio_emb = perf_counter()
        logger.info("")
        logger.info(">>> [4/5] Gerando embeddings vetoriais com SentenceTransformers (RF08)...")
        try:
            res_emb = gerar_e_salvar_embeddings(config, catalogo=catalogo, logger=logger)
        except Exception:
            logger.exception("Falha na geração de embeddings (RF08)")
            raise
        logger.info("Embeddings calculados: %d conteúdos | tempo=%.4fs", res_emb["processados"], perf_counter() - inicio_emb)

        # Atualiza pgvector se PostgreSQL estiver ativo
        if config.get("postgres", {}).get("carregar_automaticamente", True):
            try:
                total_vetores_pg = atualizar_embeddings_postgres(config, res_emb.get("embeddings", {}))
                logger.info("Vetores pgvector persistidos no PostgreSQL: %d atualizados", total_vetores_pg)
            except Exception as err:
                logger.warning("Não foi possível atualizar embeddings no PostgreSQL com pgvector: %s", err)

        # Demonstração de Busca Semântica em Linguagem Natural (RF09)
        logger.info("")
        logger.info("--- Demonstração das Consultas Semânticas Obrigatórias (RF09) ---")
        demonstrar_consultas_semanticas(config, logger=logger, usar_pgvector=False)

        # 5. Motor de Recomendação e Persistência (Estudante 2 - RF10 & RF11)
        inicio_rec = perf_counter()
        logger.info("")
        logger.info(">>> [5/5] Executando motor de recomendação personalizada (RF10)...")
        cfg_limite = config.get("recomendacao", {}).get("limite")
        limite_rec = int(cfg_limite) if cfg_limite is not None else None
        recomendacoes = gerar_recomendacoes_em_lote(
            config,
            catalogo=catalogo,
            interacoes=interacoes,
            limite_por_usuario=limite_rec,
            max_usuarios=None,
            logger=logger,
        )

        total_recs_salvas = persistir_recomendacoes_em_arquivo(config, recomendacoes, logger=logger)
        logger.info("Recomendações salvas em arquivo processado JSON: %d", total_recs_salvas)

        if config.get("postgres", {}).get("carregar_automaticamente", True):
            try:
                total_recs_pg = carregar_recomendacoes_postgres(config, recomendacoes)
                logger.info("Recomendações persistidas na tabela 'recomendacoes' do PostgreSQL: %d", total_recs_pg)
            except Exception as err:
                logger.warning("Não foi possível persistir recomendações no PostgreSQL: %s", err)

        # Exibe amostra explicativa das escalas para quem estiver avaliando
        if recomendacoes:
            u_exemplo = recomendacoes[0]["usuario_id"]
            recs_u = [r for r in recomendacoes if r["usuario_id"] == u_exemplo][:3]
            logger.info("")
            logger.info("--- Amostra Top-3 de Recomendações (Usuário %d) | Escala: 0 a 100 pontos ---", u_exemplo)
            for r in recs_u:
                logger.info(
                    "  [#%d] ID: %-3d | Score Afinidade: %5.2f / 100 pts [%-8s] | Ivis: %.2f | Icur: %.2f | %s",
                    r["posicao"],
                    r["conteudo_id"],
                    r["pontuacao"],
                    r["status"],
                    r["ivis"],
                    r["icur"],
                    r["titulo"][:60],
                )

        logger.info("Etapa de recomendações concluída | tempo=%.4fs", perf_counter() - inicio_rec)

    finally:
        tempo_total = perf_counter() - inicio_total
        if resultado is not None:
            _salvar_resumo(config, resultado, inicio_total)
        logger.info("")
        logger.info("=================================================================")
        logger.info("TÉRMINO DO PROCESSAMENTO INTEGRADO EM %.4f SEGUNDOS", tempo_total)
        logger.info("=================================================================")


if __name__ == "__main__":
    main()
