"""Geração e gerenciamento de embeddings vetoriais (RF08) — Estudante 2."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import caminho_absoluto

_MODELO_CACHE: SentenceTransformer | None = None
_NOME_MODELO_CACHE: str | None = None
_EMBEDDINGS_CACHE: dict[int, np.ndarray] | None = None
_CATALOGO_CACHE: list[dict[str, Any]] | None = None


def carregar_modelo_embedding(nome_modelo: str) -> SentenceTransformer:
    """Carrega e armazena em cache o modelo SentenceTransformer."""
    global _MODELO_CACHE, _NOME_MODELO_CACHE
    if _MODELO_CACHE is None or _NOME_MODELO_CACHE != nome_modelo:
        _MODELO_CACHE = SentenceTransformer(nome_modelo)
        _NOME_MODELO_CACHE = nome_modelo
    return _MODELO_CACHE


def carregar_catalogo(
    config: dict[str, Any] | None = None,
    caminho_catalogo: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Carrega o catálogo de conteúdos em memória, priorizando dados processados."""
    global _CATALOGO_CACHE
    if _CATALOGO_CACHE is None:
        if caminho_catalogo:
            caminho = caminho_absoluto(caminho_catalogo)
        elif config and "processados" in config.get("dados", {}):
            c_proc = caminho_absoluto(config["dados"]["processados"]["catalogo"])
            caminho = c_proc if c_proc.exists() else caminho_absoluto(config["dados"]["catalogo"])
        else:
            caminho = caminho_absoluto("dados/processados/catalogo_processado.csv")
            if not caminho.exists():
                caminho = caminho_absoluto("dados/brutos/catalogo.csv")

        with caminho.open("r", encoding="utf-8-sig") as f:
            _CATALOGO_CACHE = list(csv.DictReader(f))
    return _CATALOGO_CACHE


def preparar_texto_conteudo(
    titulo: str,
    descricao: str,
    tipo: str | None = None,
    categoria: str | None = None,
    nivel: str | None = None,
) -> str:
    """Combina metadados e texto para uma representação semântica contextualizada."""
    titulo_limpo = " ".join(str(titulo).split()).strip()
    desc_limpa = " ".join(str(descricao).split()).strip()

    prefixo_partes = []
    if tipo:
        prefixo_partes.append(str(tipo).strip())
    if categoria:
        prefixo_partes.append(f"Categoria: {str(categoria).strip()}")
    if nivel:
        prefixo_partes.append(f"Nível: {str(nivel).strip()}")

    prefixo = f"[{' | '.join(prefixo_partes)}] " if prefixo_partes else ""
    return f"{prefixo}{titulo_limpo}. {desc_limpa}"


def _carregar_embeddings_existentes(
    caminho_json: Path,
    dimensao_esperada: int,
) -> dict[int, np.ndarray]:
    """Carrega apenas vetores válidos já persistidos no JSON."""
    if not caminho_json.exists():
        return {}

    try:
        with caminho_json.open("r", encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}

    if not isinstance(dados, dict):
        return {}

    existentes: dict[int, np.ndarray] = {}
    for chave, valor in dados.items():
        try:
            cid = int(chave)
            vetor = np.asarray(valor, dtype=np.float32)
        except (TypeError, ValueError):
            continue

        if vetor.ndim == 1 and vetor.size == dimensao_esperada:
            existentes[cid] = vetor

    return existentes


def gerar_e_salvar_embeddings(
    config: dict[str, Any],
    catalogo: list[dict[str, Any]] | None = None,
    logger: logging.Logger | None = None,
    caminho_saida: str | Path = "dados/processados/embeddings.json",
) -> dict[str, Any]:
    """
    Gera embeddings sem duplicar processamento desnecessário.

    Vetores válidos já existentes em ``embeddings.json`` são reaproveitados,
    inclusive em uma nova execução do Python. Somente conteúdos ausentes ou
    com vetor inválido são enviados ao SentenceTransformer.
    """
    global _EMBEDDINGS_CACHE
    log = logger or logging.getLogger("ficdev_pipeline")
    nome_modelo = config["embeddings"]["modelo"]
    dimensao = int(config["embeddings"].get("dimensao", 384))
    batch_size = int(config["embeddings"].get("batch_size", 64))

    itens_catalogo = catalogo if catalogo is not None else carregar_catalogo(config)
    caminho_json = caminho_absoluto(caminho_saida)
    caminho_json.parent.mkdir(parents=True, exist_ok=True)

    ids_catalogo = [int(c["conteudo_id"]) for c in itens_catalogo]
    ids_validos = set(ids_catalogo)

    # RF08: reaproveita o arquivo persistido mesmo em uma nova execução,
    # evitando gerar novamente embeddings para o mesmo conteúdo.
    existentes = _carregar_embeddings_existentes(caminho_json, dimensao)
    _EMBEDDINGS_CACHE = {
        cid: vetor for cid, vetor in existentes.items() if cid in ids_validos
    }

    faltantes = [
        conteudo
        for conteudo in itens_catalogo
        if int(conteudo["conteudo_id"]) not in _EMBEDDINGS_CACHE
    ]

    reaproveitados = len(_EMBEDDINGS_CACHE)
    if reaproveitados:
        log.info("Embeddings reaproveitados do arquivo: %d", reaproveitados)

    gerados = 0
    if faltantes:
        log.info(
            "Carregando modelo de embeddings: %s para %d conteúdos faltantes...",
            nome_modelo,
            len(faltantes),
        )
        modelo = carregar_modelo_embedding(nome_modelo)
        textos = [
            preparar_texto_conteudo(
                c.get("titulo", ""),
                c.get("descricao", ""),
                tipo=c.get("tipo"),
                categoria=c.get("categoria"),
                nivel=c.get("nivel"),
            )
            for c in faltantes
        ]
        ids_faltantes = [int(c["conteudo_id"]) for c in faltantes]

        log.info("Calculando vetores em lotes (batch_size=%d)...", batch_size)
        vetores = modelo.encode(
            textos,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        for cid, vetor in zip(ids_faltantes, vetores):
            arr = np.asarray(vetor, dtype=np.float32)
            if arr.ndim != 1 or arr.size != dimensao:
                raise ValueError(
                    f"Embedding do conteúdo {cid} possui dimensão {arr.size}; "
                    f"esperado: {dimensao}."
                )
            _EMBEDDINGS_CACHE[cid] = arr
        gerados = len(ids_faltantes)
    else:
        log.info("Todos os embeddings do catálogo já existem; nenhuma geração necessária.")

    # Salva somente IDs do catálogo atual, em ordem reprodutível.
    dados_serializados = {
        str(cid): _EMBEDDINGS_CACHE[cid].tolist()
        for cid in ids_catalogo
        if cid in _EMBEDDINGS_CACHE
    }
    with caminho_json.open("w", encoding="utf-8") as f:
        json.dump(dados_serializados, f)

    log.info(
        "Embeddings concluídos: total=%d | reaproveitados=%d | gerados=%d",
        len(_EMBEDDINGS_CACHE),
        reaproveitados,
        gerados,
    )

    return {
        "processados": len(_EMBEDDINGS_CACHE),
        "modelo": nome_modelo,
        "dimensao": dimensao,
        "embeddings": _EMBEDDINGS_CACHE,
        "reaproveitados": reaproveitados,
        "gerados": gerados,
    }


def obter_embeddings_cache(config: dict[str, Any]) -> dict[int, np.ndarray]:
    """Retorna dicionário mapeando conteudo_id -> vetor embedding."""
    global _EMBEDDINGS_CACHE
    if _EMBEDDINGS_CACHE is None:
        caminho_json = caminho_absoluto("dados/processados/embeddings.json")
        dimensao = int(config["embeddings"].get("dimensao", 384))
        existentes = _carregar_embeddings_existentes(caminho_json, dimensao)
        if existentes:
            _EMBEDDINGS_CACHE = existentes
        else:
            res = gerar_e_salvar_embeddings(config)
            _EMBEDDINGS_CACHE = res.get("embeddings", {})
    return _EMBEDDINGS_CACHE or {}
