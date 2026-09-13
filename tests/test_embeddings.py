"""Testes unitários e de integração de Embeddings e Busca Semântica (RF08 e RF09)."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

import src.recomendacao.embeddings as embeddings_mod
from src.recomendacao.busca import demonstrar_consultas_semanticas, executar_busca_semantica
from src.recomendacao.embeddings import (
    carregar_modelo_embedding,
    gerar_e_salvar_embeddings,
    obter_embeddings_cache,
    preparar_texto_conteudo,
)


def test_preparar_texto_conteudo_com_metadados():
    """Testa enriquecimento semântico textual com tipo, categoria e nível."""
    texto = preparar_texto_conteudo(
        titulo="  Curso de Python   Avançado ",
        descricao=" Aprenda decoradores e geradores. ",
        tipo="Curso",
        categoria="Programação",
        nivel="Avançado",
    )
    assert texto == "[Curso | Categoria: Programação | Nível: Avançado] Curso de Python Avançado. Aprenda decoradores e geradores."


def test_preparar_texto_conteudo_sem_metadados():
    """Testa fallback quando tipo/categoria/nível são omitidos."""
    texto = preparar_texto_conteudo(
        titulo="  Python Básico ",
        descricao=" Primeiros passos. ",
    )
    assert texto == "Python Básico. Primeiros passos."


def test_carregar_modelo_embedding_cache():
    """Testa singleton e cache de instância do SentenceTransformer."""
    modelo_1 = carregar_modelo_embedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    modelo_2 = carregar_modelo_embedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    assert modelo_1 is modelo_2


def test_gerar_e_salvar_embeddings_arquivo_saida(
    config_global: dict,
    catalogo_exemplo: list[dict],
    tmp_path: Path,
):
    """Testa cálculo de vetores normalizados e persistência em arquivo JSON."""
    caminho_saida = tmp_path / "embeddings_teste.json"

    resultado = gerar_e_salvar_embeddings(
        config_global,
        catalogo=catalogo_exemplo,
        caminho_saida=caminho_saida,
    )

    assert resultado["processados"] == len(catalogo_exemplo)
    assert caminho_saida.exists()

    embeddings = resultado["embeddings"]
    assert 1 in embeddings
    assert isinstance(embeddings[1], np.ndarray)
    assert len(embeddings[1]) == 384
    # Vetores devem estar normalizados (norma L2 ~= 1.0)
    assert np.linalg.norm(embeddings[1]) == pytest.approx(1.0, rel=1e-3)


def test_reaproveita_embeddings_persistidos_sem_regenerar(
    config_global: dict,
    catalogo_exemplo: list[dict],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """RF08: reaproveita vetores válidos mesmo após reinício do processo Python."""
    caminho_saida = tmp_path / "embeddings_existentes.json"
    vetor_valido = [1.0] + [0.0] * 383
    persistidos = {
        str(int(item["conteudo_id"])): vetor_valido
        for item in catalogo_exemplo
    }
    caminho_saida.write_text(json.dumps(persistidos), encoding="utf-8")

    # Simula nova execução do Python: sem cache em memória, mas com JSON persistido.
    monkeypatch.setattr(embeddings_mod, "_EMBEDDINGS_CACHE", None)

    def _modelo_nao_deve_ser_carregado(*args, **kwargs):
        raise AssertionError("O modelo não deve ser carregado quando todos os vetores já existem")

    monkeypatch.setattr(
        embeddings_mod,
        "carregar_modelo_embedding",
        _modelo_nao_deve_ser_carregado,
    )

    resultado = embeddings_mod.gerar_e_salvar_embeddings(
        config_global,
        catalogo=catalogo_exemplo,
        caminho_saida=caminho_saida,
    )

    assert resultado["gerados"] == 0
    assert resultado["reaproveitados"] == len(catalogo_exemplo)
    assert resultado["processados"] == len(catalogo_exemplo)


def test_executar_busca_semantica_em_memoria(config_global: dict):
    """Testa busca semântica em linguagem natural com cálculo de cosseno em memória."""
    consulta = "Quero aprender os fundamentos de banco de dados para inteligência artificial."
    resultados = executar_busca_semantica(
        config_global,
        texto_consulta=consulta,
        limite=3,
        usar_pgvector=False,
    )

    assert len(resultados) > 0
    for pos, res in enumerate(resultados, start=1):
        assert res["posicao"] == pos
        assert "conteudo_id" in res
        assert "titulo" in res
        assert "categoria" in res
        assert "tipo" in res
        assert 0.0 <= res["similaridade"] <= 1.0
        assert 0.0 <= res["distancia"] <= 2.0

    # Ordenação decrescente por similaridade
    if len(resultados) >= 2:
        assert resultados[0]["similaridade"] >= resultados[1]["similaridade"]


def test_demonstrar_consultas_semanticas_obrigatorias(config_global: dict):
    """Testa a demonstração das 3 consultas semânticas exigidas pelo RF09."""
    historico = demonstrar_consultas_semanticas(config_global, usar_pgvector=False)
    assert len(historico) == 3
    assert len(historico[0]["resultados"]) > 0
    assert len(historico[1]["resultados"]) > 0
    assert len(historico[2]["resultados"]) > 0
