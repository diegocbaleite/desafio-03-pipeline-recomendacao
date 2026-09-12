"""Testes unitários e de integração do módulo de ingestão (RF01, RF02, RF04, RF05)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from src.config import carregar_config
from src.ingestao.leitura import ler_csv, ler_json
from src.ingestao.pipeline import _gerar_ids_internos, executar_ingestao
from src.logging_utils import configurar_logger


def test_leitura_csv_valido(tmp_path: Path):
    caminho = tmp_path / "teste_catalogo.csv"
    caminho.write_text(
        "conteudo_id,titulo,tipo\n1,Curso Python,Curso\n2,Artigo SQL,Artigo\n",
        encoding="utf-8-sig",
    )
    registros = ler_csv(caminho)
    assert len(registros) == 2
    assert registros[0]["conteudo_id"] == "1"
    assert registros[0]["titulo"] == "Curso Python"
    assert registros[1]["tipo"] == "Artigo"


def test_leitura_json_lista(tmp_path: Path):
    caminho = tmp_path / "teste_interacoes.json"
    dados = [{"usuario_id": 1, "conteudo_id": 10}, {"usuario_id": 2, "conteudo_id": 20}]
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    registros = ler_json(caminho)
    assert len(registros) == 2
    assert registros[0]["usuario_id"] == 1


def test_leitura_json_dicionario_com_lista(tmp_path: Path):
    caminho = tmp_path / "teste_dict.json"
    dados = {"comentarios": [{"usuario_id": 1, "comentario": "Ótimo"}]}
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    registros = ler_json(caminho)
    assert len(registros) == 1
    assert registros[0]["comentario"] == "Ótimo"


def test_leitura_json_invalido_sem_lista(tmp_path: Path):
    caminho = tmp_path / "teste_invalido.json"
    caminho.write_text(json.dumps({"total": 0, "status": "ok"}), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON precisa conter uma lista de registros"):
        ler_json(caminho)


def test_geracao_ids_internos_sequenciais():
    registros = [{"conteudo_id": 10}, {"conteudo_id": 20}, {"conteudo_id": 30}]
    _gerar_ids_internos(registros, "interacao_id")
    assert registros[0]["interacao_id"] == 1
    assert registros[1]["interacao_id"] == 2
    assert registros[2]["interacao_id"] == 3


def test_executar_ingestao_com_dados_reais(config_global: dict, tmp_path: Path):
    log_teste = tmp_path / "teste_pipeline.log"
    logger = configurar_logger(log_teste)

    resultado = executar_ingestao(config_global, logger=logger)
    assert "catalogo" in resultado
    assert "interacoes" in resultado
    assert "comentarios" in resultado
    assert "resumo" in resultado

    resumo = resultado["resumo"]
    assert "fontes" in resumo
    assert "catalogo" in resumo["fontes"]
    assert "interacoes" in resumo["fontes"]
    assert "comentarios" in resumo["fontes"]
    assert resumo["fontes"]["catalogo"]["válidos"] == 1000
    assert resumo["fontes"]["interacoes"]["válidos"] == 1000
    assert resumo["fontes"]["comentarios"]["válidos"] == 1000
    assert "tempo_total_segundos" in resumo
