"""Leitura das fontes CSV e JSON."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def ler_csv(caminho: Path) -> list[dict[str, Any]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def ler_json(caminho: Path) -> list[dict[str, Any]]:
    with caminho.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        for valor in dados.values():
            if isinstance(valor, list):
                return valor
    raise ValueError(f"JSON precisa conter uma lista de registros: {caminho}")
