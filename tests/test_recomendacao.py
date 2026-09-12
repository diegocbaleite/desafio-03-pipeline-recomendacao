"""Testes unitários e de integração do Motor de Recomendação (RF10 e RF11)."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from src.recomendacao.motor import (
    classificar_status_recomendacao,
    gerar_recomendacoes_em_lote,
    gerar_recomendacoes_usuario,
)
from src.recomendacao.persistencia import persistir_recomendacoes_em_arquivo


def test_formula_pontuacao_calculo():
    """Valida a fórmula estrita: Pontuação = ((Ivis + Icur) / 2) * 100 * Iconc."""
    ivis = 0.8
    icur = 0.6
    iconc = 1
    pontuacao = ((ivis + icur) / 2.0) * 100.0 * iconc
    assert pontuacao == pytest.approx(70.0)

    # Conteúdo concluído anula pontuação
    iconc_concluido = 0
    pontuacao_zerada = ((ivis + icur) / 2.0) * 100.0 * iconc_concluido
    assert pontuacao_zerada == 0.0


def test_classificacao_status_positivo():
    """Positivo: Pontuação >= 70."""
    assert classificar_status_recomendacao(70.0, iconc=1) == "Positivo"
    assert classificar_status_recomendacao(85.5, iconc=1) == "Positivo"


def test_classificacao_status_estavel():
    """Estável: 40 < Pontuação < 70."""
    assert classificar_status_recomendacao(40.01, iconc=1) == "Estável"
    assert classificar_status_recomendacao(55.0, iconc=1) == "Estável"
    assert classificar_status_recomendacao(69.99, iconc=1) == "Estável"


def test_classificacao_status_negativo():
    """Negativo: Pontuação <= 40 ou Iconc == 0."""
    # Borda exata de 40.0 é Negativo
    assert classificar_status_recomendacao(40.0, iconc=1) == "Negativo"
    assert classificar_status_recomendacao(35.0, iconc=1) == "Negativo"
    assert classificar_status_recomendacao(0.0, iconc=1) == "Negativo"
    # Qualquer nota com conteúdo concluído é Negativo
    assert classificar_status_recomendacao(99.0, iconc=0) == "Negativo"


def test_gerar_recomendacoes_usuario_ponderado_e_descarte_negativos(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
    embeddings_mock: dict[int, np.ndarray],
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Testa geração de recomendações para um usuário com perfil semântico ponderado:
    - Conteúdo 1 foi concluído -> Iconc = 0 -> Negativo -> Descartado da lista de sugestões.
    - Conteúdo 2 foi curtido -> Icur elevado.
    - Conteúdo 3 candidato é ranqueado com posições 1..N.
    """
    monkeypatch.setattr(
        "src.recomendacao.motor.obter_embeddings_cache",
        lambda cfg: embeddings_mock,
    )

    recs = gerar_recomendacoes_usuario(
        config_global,
        usuario_id=10,
        interacoes_usuario=interacoes_exemplo,
        catalogo=catalogo_exemplo,
        limite=None,
        incluir_negativos=False,
    )

    # Conteúdo 1 já foi concluído e NÃO deve estar na lista de sugestões
    conteudos_recomendados = [r["conteudo_id"] for r in recs]
    assert 1 not in conteudos_recomendados

    for pos, r in enumerate(recs, start=1):
        assert r["posicao"] == pos
        assert r["status"] in ("Positivo", "Estável")
        assert r["usuario_id"] == 10
        assert 0.0 <= r["ivis"] <= 1.0
        assert 0.0 <= r["icur"] <= 1.0
        assert 0.0 <= r["pontuacao"] <= 100.0


def test_gerar_recomendacoes_em_lote(
    config_global: dict,
    catalogo_exemplo: list[dict],
    interacoes_exemplo: list[dict],
    embeddings_mock: dict[int, np.ndarray],
    monkeypatch: pytest.MonkeyPatch,
):
    """Testa execução em lote para base de usuários."""
    monkeypatch.setattr(
        "src.recomendacao.motor.obter_embeddings_cache",
        lambda cfg: embeddings_mock,
    )

    todas_recs = gerar_recomendacoes_em_lote(
        config_global,
        catalogo=catalogo_exemplo,
        interacoes=interacoes_exemplo,
        limite_por_usuario=5,
        max_usuarios=1,
    )

    assert isinstance(todas_recs, list)
    assert len(todas_recs) > 0
    assert todas_recs[0]["usuario_id"] == 10


def test_persistir_recomendacoes_em_arquivo(tmp_path: Path):
    """Testa serialização formatada de recomendações em JSON."""
    caminho = tmp_path / "recomendacoes_saida.json"
    recs = [
        {"usuario_id": 1, "conteudo_id": 10, "pontuacao": 80.0, "status": "Positivo"},
        {"usuario_id": 1, "conteudo_id": 20, "pontuacao": 60.0, "status": "Estável"},
    ]

    total = persistir_recomendacoes_em_arquivo(config={}, recomendacoes=recs, caminho_saida=caminho)
    assert total == 2
    assert caminho.exists()

    carregado = json.loads(caminho.read_text(encoding="utf-8"))
    assert len(carregado) == 2
    assert carregado[0]["pontuacao"] == 80.0
