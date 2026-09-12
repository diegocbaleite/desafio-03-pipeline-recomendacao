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

    postgres = config.setdefault("postgres", {})
    postgres["host"] = os.getenv("POSTGRES_HOST", "localhost")
    postgres["port"] = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres["database"] = os.getenv("POSTGRES_DB", "ficdev_recomendacao")
    postgres["user"] = os.getenv("POSTGRES_USER", "postgres")
    postgres["password"] = os.getenv("POSTGRES_PASSWORD", "")

    mongodb = config.setdefault("mongodb", {})
    mongodb["uri"] = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongodb["database"] = os.getenv("MONGO_DB", "ficdev_recomendacao")
    mongodb["user"] = os.getenv("MONGO_USER", "admin")
    mongodb["password"] = os.getenv("MONGO_PASSWORD", "admin123")
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
