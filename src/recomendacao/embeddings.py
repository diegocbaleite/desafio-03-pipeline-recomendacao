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
    """Combina tipo, categoria, nível, título e descrição para representação semântica rica e contextualizada."""
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


def gerar_e_salvar_embeddings(
    config: dict[str, Any],
    catalogo: list[dict[str, Any]] | None = None,
    logger: logging.Logger | None = None,
    caminho_saida: str | Path = "dados/processados/embeddings.json",
) -> dict[str, Any]:
    """
    Gera embeddings para todos os conteúdos válidos:
    1. Lê catálogo tratado em memória ou de arquivo processado.
    2. Combina metadados semânticos (tipo, categoria, nível, título e descrição).
    3. Calcula representações densas normalizadas com SentenceTransformer.
    4. Salva em cache e persiste em arquivo JSON processado.
    """
    global _EMBEDDINGS_CACHE
    log = logger or logging.getLogger("ficdev_pipeline")
    nome_modelo = config["embeddings"]["modelo"]
    batch_size = int(config["embeddings"].get("batch_size", 64))

    itens_catalogo = catalogo if catalogo is not None else carregar_catalogo(config)
    caminho_json = caminho_absoluto(caminho_saida)
    caminho_json.parent.mkdir(parents=True, exist_ok=True)

    # Se já existir arquivo gerado e em cache, carrega diretamente
    if caminho_json.exists() and _EMBEDDINGS_CACHE is not None:
        log.info("Embeddings já carregados em memória (%d vetores).", len(_EMBEDDINGS_CACHE))
        return {
            "processados": len(_EMBEDDINGS_CACHE),
            "modelo": nome_modelo,
            "dimensao": int(config["embeddings"].get("dimensao", 384)),
            "embeddings": _EMBEDDINGS_CACHE,
        }

    log.info(
        "Carregando modelo de embeddings: %s para %d conteúdos...",
        nome_modelo,
        len(itens_catalogo),
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
        for c in itens_catalogo
    ]
    ids = [int(c["conteudo_id"]) for c in itens_catalogo]

    log.info("Calculando vetores em lotes (batch_size=%d)...", batch_size)
    vetores = modelo.encode(
        textos,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    _EMBEDDINGS_CACHE = {
        cid: np.array(vetor, dtype=np.float32) for cid, vetor in zip(ids, vetores)
    }

    # Salva versão serializada para auditoria e persistência
    dados_serializados = {
        str(cid): vetor.tolist() for cid, vetor in _EMBEDDINGS_CACHE.items()
    }
    with caminho_json.open("w", encoding="utf-8") as f:
        json.dump(dados_serializados, f)

    log.info("Embeddings concluídos com sucesso! Total gerado: %d", len(_EMBEDDINGS_CACHE))

    return {
        "processados": len(_EMBEDDINGS_CACHE),
        "modelo": nome_modelo,
        "dimensao": len(vetores[0]) if len(vetores) > 0 else 0,
        "embeddings": _EMBEDDINGS_CACHE,
    }


def obter_embeddings_cache(config: dict[str, Any]) -> dict[int, np.ndarray]:
    """Retorna dicionário mapeando conteudo_id -> vetor embedding."""
    global _EMBEDDINGS_CACHE
    if _EMBEDDINGS_CACHE is None:
        caminho_json = caminho_absoluto("dados/processados/embeddings.json")
        if caminho_json.exists():
            with caminho_json.open("r", encoding="utf-8") as f:
                dados = json.load(f)
                _EMBEDDINGS_CACHE = {int(k): np.array(v, dtype=np.float32) for k, v in dados.items()}
        else:
            res = gerar_e_salvar_embeddings(config)
            _EMBEDDINGS_CACHE = res.get("embeddings", {})
    return _EMBEDDINGS_CACHE or {}
