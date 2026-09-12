"""Motor de recomendação personalizada de conteúdos (RF10) — Estudante 2."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np

from src.config import caminho_absoluto
from src.recomendacao.embeddings import carregar_catalogo, obter_embeddings_cache


def classificar_status_recomendacao(pontuacao: float, iconc: int) -> str:
    """
    Classifica a recomendação com base nas regras estritas do desafio (RF10):
    - Positivo (Pontuação >= 70): Forte afinidade.
    - Estável (40 < Pontuação < 70): Afinidade moderada.
    - Negativo (Pontuação <= 40 ou Iconc == 0): Baixo interesse ou já concluído.
    """
    if iconc == 0 or pontuacao <= 40.0:
        return "Negativo"
    if pontuacao >= 70.0:
        return "Positivo"
    return "Estável"


def carregar_interacoes(
    config: dict[str, Any] | None = None,
    caminho_interacoes: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Carrega interações em memória, priorizando dados processados."""
    if caminho_interacoes:
        caminho = caminho_absoluto(caminho_interacoes)
    elif config and "processados" in config.get("dados", {}):
        c_proc = caminho_absoluto(config["dados"]["processados"]["interacoes"])
        caminho = c_proc if c_proc.exists() else caminho_absoluto(config["dados"]["interacoes"])
    else:
        caminho = caminho_absoluto("dados/processados/interacoes_processadas.json")
        if not caminho.exists():
            caminho = caminho_absoluto("dados/brutos/interacoes.json")

    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)

def gerar_recomendacoes_usuario(
    config: dict[str, Any],
    usuario_id: int,
    interacoes_usuario: list[dict[str, Any]],
    catalogo: list[dict[str, Any]] | None = None,
    limite: int | None = None,
    incluir_negativos: bool = False,
) -> list[dict[str, Any]]:
    """
    Gera recomendações de conteúdos personalizadas para um usuário segundo o RF10:
    Fórmula: Pontuação = ((Ivis + Icur) / 2) * 100 * Iconc
    
    Status descartados da lista de sugestões:
    - Negativo (Pontuação <= 40 ou Iconc == 0) é descartado da lista de sugestões
      conforme regra de negócio da Seção 7 do desafio, a menos que incluir_negativos=True.
    """
    # Data de geração da recomendação:
    # Para bases de dados estáticas, permite simulação histórica via 'data_corte_simulada'
    # para que interações posteriores possam ser avaliadas na taxa de conversão do Superset (RF12).
    cfg_rec = config.get("recomendacao", {}) if config else {}
    data_corte = cfg_rec.get("data_corte_simulada")
    if data_corte:
        data_geracao = str(data_corte)
    else:
        data_geracao = datetime.now().isoformat(timespec="seconds")
    itens_catalogo = catalogo if catalogo is not None else carregar_catalogo(config)
    embeddings = obter_embeddings_cache(config)

    # 1. Identificar conteúdos concluídos (Iconc = 0)
    concluidos_ids = {
        int(r["conteudo_id"])
        for r in interacoes_usuario
        if r.get("tipo_interacao") == "conclusão" or float(r.get("percentual_conclusao", 0.0) or 0.0) >= 100.0
    }

    # 2. Identificar conteúdos visualizados e calcular perfil semântico ponderado (user_embedding)
    vetores_vis = []
    pesos_vis = []

    for r in interacoes_usuario:
        cid = int(r["conteudo_id"])
        if cid in embeddings:
            tipo_it = r.get("tipo_interacao", "")
            perc = float(r.get("percentual_conclusao") or 0.0)
            tempo = float(r.get("tempo_consumido_min") or r.get("tempo_consumido") or 0.0)

            if tipo_it in ("visualização", "início", "conclusão") or tempo > 0 or perc > 0:
                peso = 1.0 + min(1.0, max(0.0, perc / 100.0))
                if tipo_it == "conclusão" or perc >= 100.0:
                    peso += 0.5
                vetores_vis.append(embeddings[cid])
                pesos_vis.append(peso)

    centroide_vis = None
    if vetores_vis:
        media_ponderada = np.average(vetores_vis, axis=0, weights=pesos_vis)
        norma = np.linalg.norm(media_ponderada)
        centroide_vis = media_ponderada / norma if norma > 0 else media_ponderada

    # 3. Identificar conteúdos curtidos ou com avaliação >= 4.0 para Icur
    curtidos_ids = [
        int(r["conteudo_id"])
        for r in interacoes_usuario
        if r.get("tipo_interacao") == "curtida"
        or (
            (r.get("avaliacao") is not None or r.get("avaliacao_atribuida") is not None)
            and float(r.get("avaliacao") or r.get("avaliacao_atribuida") or 0.0) >= 4.0
        )
    ]

    mapa_categorias_conteudo = {int(c["conteudo_id"]): c.get("categoria", "") for c in itens_catalogo}
    categorias_curtidas_contagem: dict[str, int] = {}
    for cid in curtidos_ids:
        cat = mapa_categorias_conteudo.get(cid, "")
        if cat:
            categorias_curtidas_contagem[cat] = categorias_curtidas_contagem.get(cat, 0) + 1

    total_curtidos = len(curtidos_ids)

    # 4. Cálculo da recomendação para cada item do catálogo
    recomendacoes_candidatas = []

    for item in itens_catalogo:
        cid = int(item["conteudo_id"])
        titulo = item.get("titulo", "")
        cat_nome = item.get("categoria", "")
        tipo = item.get("tipo", "")

        iconc = 0 if cid in concluidos_ids else 1

        # Ivis: similaridade de cosseno com o perfil de visualizações
        if centroide_vis is not None and cid in embeddings:
            sim_cosseno = float(np.dot(centroide_vis, embeddings[cid]))
            ivis = max(0.0, min(1.0, (sim_cosseno + 1.0) / 2.0))
        else:
            ivis = 0.0

        # Icur: proporção de curtidas na mesma categoria
        if total_curtidos > 0:
            qtd_mesma_cat = categorias_curtidas_contagem.get(cat_nome, 0)
            icur = min(1.0, qtd_mesma_cat / total_curtidos)
        else:
            icur = 0.0

        pontuacao = ((ivis + icur) / 2.0) * 100.0 * iconc
        pontuacao = round(pontuacao, 2)

        status = classificar_status_recomendacao(pontuacao, iconc)

        # Regra de Classificação: Negativo (Pontuação <= 40 ou Iconc= 0) é descartado da lista de sugestões
        if status != "Negativo" or incluir_negativos:
            recomendacoes_candidatas.append(
                {
                    "usuario_id": usuario_id,
                    "conteudo_id": cid,
                    "titulo": titulo,
                    "categoria": cat_nome,
                    "tipo": tipo,
                    "ivis": round(ivis, 4),
                    "icur": round(icur, 4),
                    "iconc": iconc,
                    "pontuacao": pontuacao,
                    "status": status,
                    "data_geracao": data_geracao,
                }
            )

    recomendacoes_candidatas.sort(key=lambda x: x["pontuacao"], reverse=True)

    sugestoes = (
        recomendacoes_candidatas[:limite]
        if limite is not None and limite > 0
        else recomendacoes_candidatas
    )
    for pos, it in enumerate(sugestoes, start=1):
        it["posicao"] = pos

    return sugestoes


def gerar_recomendacoes_em_lote(
    config: dict[str, Any],
    catalogo: list[dict[str, Any]] | None = None,
    interacoes: list[dict[str, Any]] | None = None,
    limite_por_usuario: int | None = None,
    max_usuarios: int | None = None,
    logger: logging.Logger | None = None,
) -> list[dict[str, Any]]:
    """Gera recomendações para a base de usuários a partir dos dados tratados."""
    log = logger or logging.getLogger("ficdev_pipeline")

    todas_interacoes = interacoes if interacoes is not None else carregar_interacoes(config)
    itens_catalogo = catalogo if catalogo is not None else carregar_catalogo(config)

    # Agrupa interações por usuario_id
    interacoes_por_usuario: dict[int, list[dict[str, Any]]] = {}
    for interacao in todas_interacoes:
        uid = int(interacao.get("usuario_id", 0))
        if uid > 0:
            interacoes_por_usuario.setdefault(uid, []).append(interacao)

    usuarios = sorted(interacoes_por_usuario.keys())
    if max_usuarios:
        usuarios = usuarios[:max_usuarios]

    log.info("Gerando recomendações personalizadas para %d usuários...", len(usuarios))
    todas_recomendacoes: list[dict[str, Any]] = []

    for uid in usuarios:
        recs = gerar_recomendacoes_usuario(
            config,
            usuario_id=uid,
            interacoes_usuario=interacoes_por_usuario[uid],
            catalogo=itens_catalogo,
            limite=limite_por_usuario,
            incluir_negativos=False,
        )
        todas_recomendacoes.extend(recs)

    log.info("Total de recomendações geradas: %d", len(todas_recomendacoes))
    return todas_recomendacoes
