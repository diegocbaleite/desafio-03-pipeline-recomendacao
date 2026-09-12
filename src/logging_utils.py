"""Configuração de logs do pipeline."""
from __future__ import annotations

import logging
from pathlib import Path


class FormatadorPipeline(logging.Formatter):
    """Formatador customizado para manter logs alinhados e limpos."""

    def __init__(self, fmt: str = "%(asctime)s | %(levelname)-7s | %(message)s", datefmt: str = "%Y-%m-%d %H:%M:%S"):
        super().__init__(fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        # Se for uma linha separadora ou em branco, imprime sem prefixo de timestamp para manter o layout limpo
        if msg == "" or msg.startswith("===") or msg.startswith("---") or msg.startswith(">>>"):
            return msg
        return super().format(record)


def configurar_logger(caminho_log: Path) -> logging.Logger:
    caminho_log.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ficdev_pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = FormatadorPipeline()

    arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    arquivo.setFormatter(formato)
    logger.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setFormatter(formato)
    logger.addHandler(console)
    return logger
