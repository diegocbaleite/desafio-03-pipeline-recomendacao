"""Padronização dos registros antes da persistência."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
import unicodedata


TIPOS = {
    "curso": "Curso",
    "video": "Vídeo",
    "artigo": "Artigo",
    "podcast": "Podcast",
}
NIVEIS = {
    "basico": "Básico",
    "intermediario": "Intermediário",
    "avancado": "Avançado",
}
INTERACOES = {
    "visualizacao": "visualização",
    "inicio": "início",
    "conclusao": "conclusão",
    "curtida": "curtida",
    "avaliacao": "avaliação",
    "compartilhamento": "compartilhamento",
}


def _chave(texto: Any) -> str:
    valor = "" if texto is None else str(texto).strip().lower()
    valor = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in valor if not unicodedata.combining(c))


def _data(valor: Any) -> str:
    texto = "" if valor is None else str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            continue
    return texto


def _data_hora(valor: Any) -> str:
    texto = "" if valor is None else str(valor).strip()
    formatos = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    )
    for formato in formatos:
        try:
            return datetime.strptime(texto, formato).isoformat(timespec="seconds")
        except ValueError:
            continue
    return texto


def _decimal_seguro(valor: Any) -> Decimal | None:
    if valor is None:
        return None
    if isinstance(valor, str) and not valor.strip():
        return None
    if isinstance(valor, bool):
        return None
    try:
        numero = Decimal(str(valor).strip().replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return numero if numero.is_finite() else None


def _inteiro(valor: Any) -> Any:
    if valor in (None, ""):
        return None
    numero = _decimal_seguro(valor)
    if numero is None or numero != numero.to_integral_value():
        return valor
    return int(numero)


def _decimal(valor: Any) -> Any:
    if valor in (None, ""):
        return None
    numero = _decimal_seguro(valor)
    if numero is None:
        return valor
    return float(numero)


def normalizar_conteudo(registro: dict[str, Any]) -> dict[str, Any]:
    r = deepcopy(registro)
    for campo in ("titulo", "categoria", "descricao", "autor", "tipo", "nivel"):
        if campo in r and isinstance(r[campo], str):
            r[campo] = " ".join(r[campo].split())

    r["conteudo_id"] = _inteiro(r.get("conteudo_id"))
    r["tipo"] = TIPOS.get(_chave(r.get("tipo")), r.get("tipo"))
    r["nivel"] = NIVEIS.get(_chave(r.get("nivel")), r.get("nivel"))
    if isinstance(r.get("categoria"), str):
        r["categoria"] = r["categoria"].strip().title()
    r["carga_horaria_min"] = _inteiro(r.get("carga_horaria_min"))
    r["data_publicacao"] = _data(r.get("data_publicacao"))
    return r


def normalizar_interacao(registro: dict[str, Any]) -> dict[str, Any]:
    r = deepcopy(registro)
    if "interacao_id" in r:
        r["interacao_id"] = _inteiro(r.get("interacao_id"))
    r["usuario_id"] = _inteiro(r.get("usuario_id"))
    r["conteudo_id"] = _inteiro(r.get("conteudo_id"))
    r["tipo_interacao"] = INTERACOES.get(
        _chave(r.get("tipo_interacao")), r.get("tipo_interacao")
    )
    r["data_hora"] = _data_hora(r.get("data_hora"))

    tempo = r.pop("tempo_consumido", r.get("tempo_consumido_min"))
    r["tempo_consumido_min"] = _decimal(tempo)

    r["percentual_conclusao"] = _decimal(r.get("percentual_conclusao"))

    avaliacao = r.pop("avaliacao_atribuida", r.get("avaliacao"))
    r["avaliacao"] = _decimal(avaliacao)
    return r


def normalizar_comentario(registro: dict[str, Any]) -> dict[str, Any]:
    r = deepcopy(registro)
    if "comentario_id" in r:
        r["comentario_id"] = _inteiro(r.get("comentario_id"))
    r["usuario_id"] = _inteiro(r.get("usuario_id"))
    r["conteudo_id"] = _inteiro(r.get("conteudo_id"))
    r["avaliacao"] = _decimal(r.get("avaliacao"))
    r["data"] = _data(r.get("data"))
    if isinstance(r.get("comentario"), str):
        r["comentario"] = " ".join(r["comentario"].split())
    if isinstance(r.get("tags"), list):
        r["tags"] = sorted(
            {str(tag).strip().lower() for tag in r["tags"] if str(tag).strip()}
        )
    return r
