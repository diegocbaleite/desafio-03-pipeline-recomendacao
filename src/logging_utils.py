"""Configuração de logs do pipeline."""
from __future__ import annotations

import logging
from pathlib import Path


def configurar_logger(caminho_log: Path) -> logging.Logger:
    caminho_log.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ficdev_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    arquivo.setFormatter(formato)
    logger.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setFormatter(formato)
    logger.addHandler(console)
    return logger
