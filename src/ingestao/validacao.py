"""Regras de qualidade exigidas pelo desafio."""
from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any


TIPOS_VALIDOS = {"Curso", "Vídeo", "Artigo", "Podcast"}
NIVEIS_VALIDOS = {"Básico", "Intermediário", "Avançado"}
INTERACOES_VALIDAS = {
    "visualização",
    "início",
    "conclusão",
    "curtida",
    "avaliação",
    "compartilhamento",
}


def _vazio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _numero_finito(valor: Any) -> bool:
    return (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and isfinite(float(valor))
    )


def _data_iso(valor: Any, com_hora: bool = False) -> bool:
    if _vazio(valor):
        return False
    texto = str(valor).strip()
    try:
        if com_hora:
            if "T" not in texto:
                return False
            datetime.fromisoformat(texto)
        else:
            datetime.strptime(texto, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _id_positivo(valor: Any) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def validar_conteudo(registro: dict[str, Any]) -> tuple[str, list[str]]:
    obrigatorios = (
        "conteudo_id",
        "titulo",
        "tipo",
        "categoria",
        "nivel",
        "carga_horaria_min",
        "data_publicacao",
        "descricao",
        "autor",
    )
    ausentes = [campo for campo in obrigatorios if _vazio(registro.get(campo))]
    if ausentes:
        return "incompleto", [
            f"campo obrigatório ausente: {campo}" for campo in ausentes
        ]

    erros: list[str] = []
    if not _id_positivo(registro.get("conteudo_id")):
        erros.append("conteudo_id inválido")
    if registro.get("tipo") not in TIPOS_VALIDOS:
        erros.append("tipo fora do domínio permitido")
    if registro.get("nivel") not in NIVEIS_VALIDOS:
        erros.append("nível fora do domínio permitido")
    carga = registro.get("carga_horaria_min")
    if not isinstance(carga, int) or isinstance(carga, bool) or carga <= 0:
        erros.append("carga_horaria_min deve ser positiva")
    if not _data_iso(registro.get("data_publicacao")):
        erros.append("data_publicacao inválida")
    return ("inválido", erros) if erros else ("válido", [])


def validar_interacao(
    registro: dict[str, Any], conteudos_validos: set[int]
) -> tuple[str, list[str]]:
    obrigatorios = (
        "usuario_id",
        "conteudo_id",
        "tipo_interacao",
        "data_hora",
        "tempo_consumido_min",
        "percentual_conclusao",
    )
    ausentes = [campo for campo in obrigatorios if _vazio(registro.get(campo))]
    if ausentes:
        return "incompleto", [
            f"campo obrigatório ausente: {campo}" for campo in ausentes
        ]

    erros: list[str] = []
    if not _id_positivo(registro.get("usuario_id")):
        erros.append("usuario_id inválido")
    if not _id_positivo(registro.get("conteudo_id")):
        erros.append("conteudo_id inválido")
    if registro.get("conteudo_id") not in conteudos_validos:
        erros.append("referência a conteúdo inexistente")
    if registro.get("tipo_interacao") not in INTERACOES_VALIDAS:
        erros.append("tipo_interacao fora do domínio permitido")
    if not _data_iso(registro.get("data_hora"), com_hora=True):
        erros.append("data_hora inválida")

    tempo = registro.get("tempo_consumido_min")
    if not _numero_finito(tempo) or tempo < 0:
        erros.append("tempo_consumido_min inválido")

    conclusao = registro.get("percentual_conclusao")
    if not _numero_finito(conclusao) or not 0 <= conclusao <= 100:
        erros.append("percentual_conclusao deve estar entre 0 e 100")

    avaliacao = registro.get("avaliacao")
    if avaliacao is not None and (
        not _numero_finito(avaliacao) or not 1 <= avaliacao <= 5
    ):
        erros.append("avaliação deve estar entre 1 e 5")
    return ("inválido", erros) if erros else ("válido", [])


def validar_comentario(
    registro: dict[str, Any], conteudos_validos: set[int]
) -> tuple[str, list[str]]:
    obrigatorios = (
        "usuario_id",
        "conteudo_id",
        "avaliacao",
        "comentario",
        "data",
    )
    ausentes = [campo for campo in obrigatorios if _vazio(registro.get(campo))]
    if ausentes:
        return "incompleto", [
            f"campo obrigatório ausente: {campo}" for campo in ausentes
        ]

    erros: list[str] = []
    if not _id_positivo(registro.get("usuario_id")):
        erros.append("usuario_id inválido")
    if not _id_positivo(registro.get("conteudo_id")):
        erros.append("conteudo_id inválido")
    if registro.get("conteudo_id") not in conteudos_validos:
        erros.append("referência a conteúdo inexistente")

    avaliacao = registro.get("avaliacao")
    if not _numero_finito(avaliacao) or not 1 <= avaliacao <= 5:
        erros.append("avaliação deve estar entre 1 e 5")
    if not _data_iso(registro.get("data")):
        erros.append("data inválida")
    tags = registro.get("tags")
    if tags is not None and not isinstance(tags, list):
        erros.append("tags deve ser uma lista")
    return ("inválido", erros) if erros else ("válido", [])
