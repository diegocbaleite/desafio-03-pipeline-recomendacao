"""Fixtures compartilhadas para a suíte de testes do Desafio Prático 1."""
from __future__ import annotations

import numpy as np
import pytest

from src.config import carregar_config


@pytest.fixture(scope="session")
def config_global() -> dict:
    """Retorna a configuração oficial da aplicação."""
    return carregar_config()


@pytest.fixture
def catalogo_exemplo() -> list[dict]:
    """Catálogo mínimo para testes unitários isolados."""
    return [
        {
            "conteudo_id": 1,
            "titulo": "Curso de Python para Ciência de Dados",
            "tipo": "Curso",
            "categoria": "Ciência De Dados",
            "nivel": "Básico",
            "carga_horaria_min": 120,
            "data_publicacao": "2026-08-01",
            "descricao": "Aprenda manipulação com pandas e numpy.",
            "autor": "Prof. Alan",
        },
        {
            "conteudo_id": 2,
            "titulo": "Modelagem Avançada com PostgreSQL",
            "tipo": "Curso",
            "categoria": "Banco De Dados",
            "nivel": "Avançado",
            "carga_horaria_min": 180,
            "data_publicacao": "2026-08-10",
            "descricao": "Técnicas de indexação e consultas relacionais complexas.",
            "autor": "Prof. Beatriz",
        },
        {
            "conteudo_id": 3,
            "titulo": "Pipelines de Dados com Apache Spark",
            "tipo": "Artigo",
            "categoria": "Engenharia De Dados",
            "nivel": "Intermediário",
            "carga_horaria_min": 45,
            "data_publicacao": "2026-08-15",
            "descricao": "Como processar grandes volumes de forma distribuída.",
            "autor": "Prof. Carlos",
        },
    ]


@pytest.fixture
def interacoes_exemplo() -> list[dict]:
    """Interações mínimas para testes de perfil e recomendação."""
    return [
        {
            "interacao_id": 1,
            "usuario_id": 10,
            "conteudo_id": 1,
            "tipo_interacao": "conclusão",
            "data_hora": "2026-08-20T10:00:00",
            "tempo_consumido_min": 120.0,
            "percentual_conclusao": 100.0,
            "avaliacao": 5.0,
        },
        {
            "interacao_id": 2,
            "usuario_id": 10,
            "conteudo_id": 2,
            "tipo_interacao": "curtida",
            "data_hora": "2026-08-21T14:30:00",
            "tempo_consumido_min": 30.0,
            "percentual_conclusao": 25.0,
            "avaliacao": 4.5,
        },
    ]


@pytest.fixture
def embeddings_mock() -> dict[int, np.ndarray]:
    """Vetores pré-calculados de 384 dimensões para testes determinísticos rápidos."""
    np.random.seed(42)
    return {
        1: np.random.randn(384).astype(np.float32) / 10.0,
        2: np.random.randn(384).astype(np.float32) / 10.0,
        3: np.random.randn(384).astype(np.float32) / 10.0,
    }
