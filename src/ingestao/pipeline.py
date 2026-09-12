"""Pipeline de ingestão, validação, tratamento e geração do resumo."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from src.config import caminho_absoluto
from src.ingestao.leitura import ler_csv, ler_json
from src.ingestao.tratamento import (
    normalizar_comentario,
    normalizar_conteudo,
    normalizar_interacao,
)
from src.ingestao.validacao import (
    validar_comentario,
    validar_conteudo,
    validar_interacao,
)

ChaveRegistro = str | tuple[str, ...]


def _gravar_csv(caminho: Path, registros: list[dict[str, Any]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not registros:
        caminho.write_text("", encoding="utf-8")
        return
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0].keys()))
        escritor.writeheader()
        escritor.writerows(registros)


def _gravar_json(caminho: Path, dados: Any) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def _obter_valor_chave(registro: dict[str, Any], chave: ChaveRegistro) -> Any:
    if isinstance(chave, tuple):
        valores = tuple(registro.get(campo) for campo in chave)
        if any(valor is None for valor in valores):
            return None
        return valores
    return registro.get(chave)


def _descricao_chave(chave: ChaveRegistro) -> str:
    if isinstance(chave, tuple):
        return "+".join(chave)
    return chave


def _processar(
    registros: list[dict[str, Any]],
    normalizador: Callable[[dict[str, Any]], dict[str, Any]],
    validador: Callable[[dict[str, Any]], tuple[str, list[str]]],
    chave: ChaveRegistro,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    validos: list[dict[str, Any]] = []
    rejeitados: list[dict[str, Any]] = []
    vistos: set[Any] = set()
    contagem = {
        "lidos": len(registros),
        "válidos": 0,
        "inválidos": 0,
        "incompletos": 0,
        "duplicados": 0,
        "corrigidos": 0,
    }

    for numero_linha, original in enumerate(registros, start=1):
        tratado = normalizador(original)
        valor_chave = _obter_valor_chave(tratado, chave)

        if valor_chave in vistos and valor_chave is not None:
            classificacao = "duplicado"
            motivos = [f"{_descricao_chave(chave)} repetido"]
        else:
            classificacao, motivos = validador(tratado)

        if valor_chave is not None:
            vistos.add(valor_chave)

        if classificacao == "válido":
            contagem["válidos"] += 1
            if tratado != original:
                contagem["corrigidos"] += 1
            validos.append(tratado)
        else:
            mapa = {
                "inválido": "inválidos",
                "incompleto": "incompletos",
                "duplicado": "duplicados",
            }
            contagem[mapa[classificacao]] += 1
            rejeitados.append(
                {
                    "linha": numero_linha,
                    "classificacao": classificacao,
                    "motivos": motivos,
                    "registro": tratado,
                }
            )

    return validos, rejeitados, contagem


def _gerar_ids_internos(registros: list[dict[str, Any]], campo: str) -> None:
    for identificador, registro in enumerate(registros, start=1):
        registro[campo] = identificador


def _total_rejeitados(resumo: dict[str, int]) -> int:
    return resumo["inválidos"] + resumo["incompletos"] + resumo["duplicados"]


def executar_ingestao(config: dict[str, Any], logger) -> dict[str, Any]:
    inicio = perf_counter()
    dados_cfg = config["dados"]

    fontes = {
        "catalogo": caminho_absoluto(dados_cfg["catalogo"]),
        "interacoes": caminho_absoluto(dados_cfg["interacoes"]),
        "comentarios": caminho_absoluto(dados_cfg["comentarios"]),
    }
    for nome, caminho in fontes.items():
        logger.info("Lendo fonte %s: %s", nome, caminho)

    inicio_leitura = perf_counter()
    catalogo_bruto = ler_csv(fontes["catalogo"])
    interacoes_brutas = ler_json(fontes["interacoes"])
    comentarios_brutos = ler_json(fontes["comentarios"])
    tempo_leitura = perf_counter() - inicio_leitura

    logger.info(
        "Registros encontrados | catálogo=%s | interações=%s | comentários=%s",
        len(catalogo_bruto),
        len(interacoes_brutas),
        len(comentarios_brutos),
    )
    logger.info("Etapa leitura concluída em %.4fs", tempo_leitura)

    inicio_processamento = perf_counter()

    inicio_catalogo = perf_counter()
    catalogo, rejeitados_catalogo, resumo_catalogo = _processar(
        catalogo_bruto,
        normalizar_conteudo,
        validar_conteudo,
        "conteudo_id",
    )
    tempo_catalogo = perf_counter() - inicio_catalogo
    conteudos_validos = {r["conteudo_id"] for r in catalogo}

    inicio_interacoes = perf_counter()
    interacoes, rejeitados_interacoes, resumo_interacoes = _processar(
        interacoes_brutas,
        normalizar_interacao,
        lambda r: validar_interacao(r, conteudos_validos),
        ("usuario_id", "conteudo_id", "tipo_interacao", "data_hora"),
    )
    tempo_interacoes = perf_counter() - inicio_interacoes

    inicio_comentarios = perf_counter()
    comentarios, rejeitados_comentarios, resumo_comentarios = _processar(
        comentarios_brutos,
        normalizar_comentario,
        lambda r: validar_comentario(r, conteudos_validos),
        ("usuario_id", "conteudo_id", "data", "comentario"),
    )
    tempo_comentarios = perf_counter() - inicio_comentarios
    tempo_processamento = perf_counter() - inicio_processamento

    logger.info(
        "Qualidade catálogo | válidos=%s | inválidos=%s | incompletos=%s | "
        "duplicados=%s | rejeitados=%s | tempo=%.4fs",
        resumo_catalogo["válidos"],
        resumo_catalogo["inválidos"],
        resumo_catalogo["incompletos"],
        resumo_catalogo["duplicados"],
        _total_rejeitados(resumo_catalogo),
        tempo_catalogo,
    )
    logger.info(
        "Qualidade interações | válidos=%s | inválidos=%s | incompletos=%s | "
        "duplicados=%s | rejeitados=%s | tempo=%.4fs",
        resumo_interacoes["válidos"],
        resumo_interacoes["inválidos"],
        resumo_interacoes["incompletos"],
        resumo_interacoes["duplicados"],
        _total_rejeitados(resumo_interacoes),
        tempo_interacoes,
    )
    logger.info(
        "Qualidade comentários | válidos=%s | inválidos=%s | incompletos=%s | "
        "duplicados=%s | rejeitados=%s | tempo=%.4fs",
        resumo_comentarios["válidos"],
        resumo_comentarios["inválidos"],
        resumo_comentarios["incompletos"],
        resumo_comentarios["duplicados"],
        _total_rejeitados(resumo_comentarios),
        tempo_comentarios,
    )
    logger.info("Etapa tratamento/validação concluída em %.4fs", tempo_processamento)

    _gerar_ids_internos(interacoes, "interacao_id")
    _gerar_ids_internos(comentarios, "comentario_id")

    inicio_gravacao = perf_counter()
    saidas = dados_cfg["processados"]
    _gravar_csv(caminho_absoluto(saidas["catalogo"]), catalogo)
    _gravar_json(caminho_absoluto(saidas["interacoes"]), interacoes)
    _gravar_json(caminho_absoluto(saidas["comentarios"]), comentarios)

    rejeitados = {
        "catalogo": rejeitados_catalogo,
        "interacoes": rejeitados_interacoes,
        "comentarios": rejeitados_comentarios,
    }
    _gravar_json(caminho_absoluto(dados_cfg["rejeitados"]), rejeitados)

    tempo_gravacao = perf_counter() - inicio_gravacao
    tempo_ingestao = perf_counter() - inicio

    resumo = {
        "fontes": {
            "catalogo": resumo_catalogo,
            "interacoes": resumo_interacoes,
            "comentarios": resumo_comentarios,
        },
        "detalhamento_correcoes": {
            "catalogo": {
                "descricao": "Conversão de tipos (str para int em IDs e carga horária) e padronização de maiúsculas/minúsculas em categorias",
                "total_corrigidos": resumo_catalogo["corrigidos"],
            },
            "interacoes": {
                "descricao": "Adequação dos campos oficiais (tempo_consumido -> tempo_consumido_min, avaliacao_atribuida -> avaliacao) e conversão para float",
                "total_corrigidos": resumo_interacoes["corrigidos"],
            },
            "comentarios": {
                "descricao": "Padronização das tags (remoção de duplicatas, conversão para minúsculas e ordenação alfabética)",
                "total_corrigidos": resumo_comentarios["corrigidos"],
            },
        },
        "carregados_banco": {
            "postgresql": 0,
            "mongodb": 0,
        },
        "tempos_etapas_segundos": {
            "leitura": round(tempo_leitura, 4),
            "tratamento_validacao": round(tempo_processamento, 4),
            "gravacao_saidas": round(tempo_gravacao, 4),
        },
        "tempo_total_segundos": round(tempo_ingestao, 4),
    }
    _gravar_json(caminho_absoluto(dados_cfg["resumo_ingestao"]), resumo)

    logger.info("Etapa gravação de saídas concluída em %.4fs", tempo_gravacao)
    logger.info(
        "Ingestão concluída | catálogo=%s | interações=%s | comentários=%s",
        len(catalogo),
        len(interacoes),
        len(comentarios),
    )
    return {
        "catalogo": catalogo,
        "interacoes": interacoes,
        "comentarios": comentarios,
        "resumo": resumo,
    }
