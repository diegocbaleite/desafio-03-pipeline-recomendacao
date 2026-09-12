"""Carregamento centralizado das configurações do projeto."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parents[1]


def carregar_config(caminho: str | Path = "config/config.yaml") -> dict[str, Any]:
    """Carrega YAML e variáveis de ambiente sem expor segredos no código."""
    load_dotenv(RAIZ_PROJETO / ".env")
    caminho_config = RAIZ_PROJETO / caminho
    with caminho_config.open("r", encoding="utf-8") as arquivo:
        config = yaml.safe_load(arquivo) or {}

    # Credenciais e conexões obrigatórias via .env (sem valores padrão/fallback)
    variaveis_obrigatorias = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "MONGO_URI",
        "MONGO_DB",
        "MONGO_USER",
        "MONGO_PASSWORD",
    ]
    ausentes = [v for v in variaveis_obrigatorias if not os.environ.get(v)]
    if ausentes:
        raise KeyError(
            f"Variáveis de ambiente obrigatórias não configuradas: {ausentes}. "
            "Fallbacks e valores padrão estão desabilitados."
        )

    postgres = config.setdefault("postgres", {})
    postgres["host"] = os.environ["POSTGRES_HOST"]
    postgres["port"] = int(os.environ["POSTGRES_PORT"])
    postgres["database"] = os.environ["POSTGRES_DB"]
    postgres["user"] = os.environ["POSTGRES_USER"]
    postgres["password"] = os.environ["POSTGRES_PASSWORD"]

    mongodb = config.setdefault("mongodb", {})
    mongodb["uri"] = os.environ["MONGO_URI"]
    mongodb["database"] = os.environ["MONGO_DB"]
    mongodb["user"] = os.environ["MONGO_USER"]
    mongodb["password"] = os.environ["MONGO_PASSWORD"]
    mongodb["colecao_comentarios"] = mongodb.get("colecao_comentarios", "comentarios")

    embeddings = config.setdefault("embeddings", {})
    embeddings.setdefault("modelo", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embeddings.setdefault("dimensao", 384)
    embeddings.setdefault("batch_size", 64)

    recomendacao = config.setdefault("recomendacao", {})
    recomendacao.setdefault("limite", 10)
    recomendacao.setdefault("nota_minima_curtida", 4.0)

    return config


def caminho_absoluto(caminho: str | Path) -> Path:
    """Resolve caminhos relativos a partir da raiz do repositório."""
    caminho = Path(caminho)
    return caminho if caminho.is_absolute() else RAIZ_PROJETO / caminho
