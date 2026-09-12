"""Módulo de integração, persistência e consultas no MongoDB (RF07) — Estudante 2."""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

from src.config import caminho_absoluto


def conectar_mongo(config: dict[str, Any]) -> MongoClient:
    """Cria cliente de conexão com MongoDB com credenciais do ambiente."""
    cfg = config["mongodb"]
    uri = cfg["uri"]
    user = cfg["user"]
    password = cfg["password"]

    if user and password and "@" not in uri:
        prefixo = "mongodb://"
        if uri.startswith(prefixo):
            corpo = uri[len(prefixo):]
            uri = f"mongodb://{user}:{password}@{corpo}/?authSource=admin"

    return MongoClient(uri, serverSelectionTimeoutMS=4000)


def obter_colecao_comentarios(config: dict[str, Any]) -> Collection:
    """Retorna a coleção configurada para os comentários."""
    cliente = conectar_mongo(config)
    db = cliente[config["mongodb"]["database"]]
    return db[config["mongodb"]["colecao_comentarios"]]


def carregar_comentarios_mongo(
    config: dict[str, Any],
    comentarios: list[dict[str, Any]] | None = None,
    catalogo: list[dict[str, Any]] | None = None,
    caminho_comentarios: str | Path | None = None,
    caminho_catalogo: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> dict[str, Any]:
    """
    Ingere comentários no MongoDB:
    1. Consome comentários e catálogo tratados (em memória ou de arquivos).
    2. Valida integridade referencial com o catálogo válido.
    3. Enriquece cada comentário com a 'categoria' desnormalizada.
    4. Cria índices nos campos principais (RF07).
    """
    log = logger or logging.getLogger("ficdev_pipeline")

    # 1. Obter catálogo tratado
    if catalogo is None:
        caminho_cat_proc = config.get("dados", {}).get("processados", {}).get("catalogo")
        c_cat = caminho_absoluto(caminho_catalogo or caminho_cat_proc or config["dados"]["catalogo"])
        if c_cat.exists():
            with c_cat.open("r", encoding="utf-8-sig") as f:
                catalogo = list(csv.DictReader(f))
        else:
            catalogo = []

    mapa_categorias: dict[int, str] = {}
    for item in catalogo:
        cid = item.get("conteudo_id")
        cat = item.get("categoria")
        if cid is not None and cat:
            try:
                mapa_categorias[int(cid)] = str(cat).strip()
            except (ValueError, TypeError):
                continue

    # 2. Obter comentários
    if comentarios is None:
        caminho_com_proc = config.get("dados", {}).get("processados", {}).get("comentarios")
        c_com = caminho_absoluto(caminho_comentarios or caminho_com_proc or config["dados"]["comentarios"])
        if c_com.exists():
            with c_com.open("r", encoding="utf-8") as f:
                comentarios = json.load(f)
        else:
            comentarios = []

    colecao = obter_colecao_comentarios(config)

    validos: list[dict[str, Any]] = []
    rejeitados: list[dict[str, Any]] = []

    for idx, c in enumerate(comentarios, start=1):
        cid = c.get("conteudo_id")
        uid = c.get("usuario_id")
        avaliacao = c.get("avaliacao")
        comentario_texto = c.get("comentario", "")
        tags = c.get("tags", [])
        data = c.get("data")

        if cid is None:
            rejeitados.append(
                {
                    "indice": idx,
                    "motivo": "conteudo_id ausente",
                    "registro": c,
                }
            )
            continue

        try:
            cid_int = int(cid)
        except (ValueError, TypeError):
            rejeitados.append(
                {
                    "indice": idx,
                    "motivo": f"conteudo_id {cid} inválido",
                    "registro": c,
                }
            )
            continue

        if mapa_categorias and cid_int not in mapa_categorias:
            rejeitados.append(
                {
                    "indice": idx,
                    "motivo": f"conteudo_id {cid} inexistente no catálogo",
                    "registro": c,
                }
            )
            continue

        if uid is None:
            rejeitados.append(
                {
                    "indice": idx,
                    "motivo": "usuario_id ausente",
                    "registro": c,
                }
            )
            continue

        doc = {
            "usuario_id": int(uid),
            "conteudo_id": cid_int,
            "categoria": mapa_categorias.get(cid_int, "Geral"),
            "avaliacao": float(avaliacao) if avaliacao is not None else None,
            "comentario": str(comentario_texto).strip(),
            "tags": [str(t).strip().lower() for t in tags] if isinstance(tags, list) else [],
            "data": str(data) if data else None,
        }
        validos.append(doc)

    total_inseridos = 0
    if validos:
        colecao.delete_many({})
        resultado = colecao.insert_many(validos)
        total_inseridos = len(resultado.inserted_ids)

        colecao.create_index("conteudo_id")
        colecao.create_index("tags")
        colecao.create_index("avaliacao")
        colecao.create_index("categoria")

    log.info(
        "MongoDB: %d comentários inseridos com sucesso | %d rejeitados",
        total_inseridos,
        len(rejeitados),
    )

    return {
        "lidos": len(comentarios),
        "validos_inseridos": total_inseridos,
        "rejeitados": len(rejeitados),
        "detalhes_rejeitados": rejeitados,
    }


def consultar_por_conteudo(
    config: dict[str, Any], conteudo_id: int, limite: int = 10
) -> list[dict[str, Any]]:
    """Consulta comentários de um determinado conteúdo (RF07)."""
    colecao = obter_colecao_comentarios(config)
    cursor = colecao.find(
        {"conteudo_id": int(conteudo_id)},
        {"_id": 0}
    ).limit(limite)
    return list(cursor)


def buscar_por_tag(
    config: dict[str, Any], tag: str, limite: int = 10
) -> list[dict[str, Any]]:
    """Localiza documentos de avaliação/comentário pela tag (RF07)."""
    colecao = obter_colecao_comentarios(config)
    cursor = colecao.find(
        {"tags": tag.strip().lower()},
        {"_id": 0}
    ).limit(limite)
    return list(cursor)


def filtrar_por_nota(
    config: dict[str, Any], nota_minima: float = 4.0, limite: int = 10
) -> list[dict[str, Any]]:
    """Filtra avaliações com nota igual ou superior a um valor (RF07)."""
    colecao = obter_colecao_comentarios(config)
    cursor = colecao.find(
        {"avaliacao": {"$gte": float(nota_minima)}},
        {"_id": 0}
    ).limit(limite)
    return list(cursor)


def agregar_por_categoria(config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Agrega a quantidade de comentários e média de avaliações por categoria (RF07).
    """
    colecao = obter_colecao_comentarios(config)
    pipeline = [
        {
            "$group": {
                "_id": "$categoria",
                "total_comentarios": {"$sum": 1},
                "media_avaliacao": {"$avg": "$avaliacao"},
            }
        },
        {"$sort": {"total_comentarios": -1}},
        {
            "$project": {
                "_id": 0,
                "categoria": "$_id",
                "total_comentarios": 1,
                "media_avaliacao": {"$round": ["$media_avaliacao", 2]},
            }
        },
    ]
    return list(colecao.aggregate(pipeline))
