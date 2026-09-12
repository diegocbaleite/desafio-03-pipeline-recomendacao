from src.ingestao.pipeline import _processar
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


def test_normalizacao_e_validacao_conteudo():
    bruto = {
        "conteudo_id": "1",
        "titulo": "  Python   para Dados ",
        "tipo": "curso",
        "categoria": "programação",
        "nivel": "basico",
        "carga_horaria_min": "120",
        "data_publicacao": "01/08/2026",
        "descricao": "Introdução a Python",
        "autor": "Equipe",
    }

    tratado = normalizar_conteudo(bruto)
    classificacao, erros = validar_conteudo(tratado)

    assert classificacao == "válido"
    assert erros == []
    assert tratado["tipo"] == "Curso"
    assert tratado["nivel"] == "Básico"
    assert tratado["data_publicacao"] == "2026-08-01"
    assert tratado["conteudo_id"] == 1
    assert tratado["carga_horaria_min"] == 120


def test_interacao_formato_oficial_e_valida():
    bruto = {
        "usuario_id": 3,
        "conteudo_id": 614,
        "tipo_interacao": "conclusão",
        "data_hora": "2026-03-21T10:54:52",
        "tempo_consumido": 28,
        "percentual_conclusao": 100.0,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {614})

    assert classificacao == "válido"
    assert erros == []
    assert tratado["tempo_consumido_min"] == 28.0
    assert tratado["avaliacao"] is None
    assert "tempo_consumido" not in tratado
    assert "avaliacao_atribuida" not in tratado


def test_interacao_rejeita_referencia_inexistente():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 999,
        "tipo_interacao": "visualizacao",
        "data_hora": "2026-09-01 10:00:00",
        "tempo_consumido": 10,
        "percentual_conclusao": 20,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1, 2, 3})

    assert classificacao == "inválido"
    assert "referência a conteúdo inexistente" in erros


def test_interacao_rejeita_avaliacao_fora_do_intervalo():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 1,
        "tipo_interacao": "avaliacao",
        "data_hora": "2026-09-01 10:00:00",
        "tempo_consumido": 10,
        "percentual_conclusao": 100,
        "avaliacao_atribuida": 7,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1})

    assert classificacao == "inválido"
    assert "avaliação deve estar entre 1 e 5" in erros


def test_comentario_incompleto():
    bruto = {
        "usuario_id": 10,
        "conteudo_id": 1,
        "avaliacao": 5,
        "comentario": "",
        "tags": ["python", "didático"],
        "data": "2026-08-20",
    }

    tratado = normalizar_comentario(bruto)
    classificacao, erros = validar_comentario(tratado, {1})

    assert classificacao == "incompleto"
    assert "campo obrigatório ausente: comentario" in erros


def test_pipeline_identifica_duplicado():
    registros = [
        {
            "conteudo_id": "1",
            "titulo": "Python para Dados",
            "tipo": "curso",
            "categoria": "programação",
            "nivel": "basico",
            "carga_horaria_min": "120",
            "data_publicacao": "01/08/2026",
            "descricao": "Introdução a Python",
            "autor": "Equipe",
        },
        {
            "conteudo_id": "1",
            "titulo": "Python para Dados",
            "tipo": "curso",
            "categoria": "programação",
            "nivel": "basico",
            "carga_horaria_min": "120",
            "data_publicacao": "01/08/2026",
            "descricao": "Introdução a Python",
            "autor": "Equipe",
        },
    ]

    validos, rejeitados, resumo = _processar(
        registros,
        normalizar_conteudo,
        validar_conteudo,
        "conteudo_id",
    )

    assert len(validos) == 1
    assert len(rejeitados) == 1
    assert resumo["válidos"] == 1
    assert resumo["duplicados"] == 1
    assert rejeitados[0]["classificacao"] == "duplicado"


def test_id_decimal_nao_e_truncado_para_inteiro():
    bruto = {
        "conteudo_id": "5.7",
        "titulo": "Conteúdo",
        "tipo": "curso",
        "categoria": "dados",
        "nivel": "basico",
        "carga_horaria_min": "60",
        "data_publicacao": "2026-08-01",
        "descricao": "Descrição",
        "autor": "Equipe",
    }

    tratado = normalizar_conteudo(bruto)
    classificacao, erros = validar_conteudo(tratado)

    assert tratado["conteudo_id"] == "5.7"
    assert classificacao == "inválido"
    assert "conteudo_id inválido" in erros


def test_data_hora_sem_horario_e_invalida():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 1,
        "tipo_interacao": "visualizacao",
        "data_hora": "2026-09-01",
        "tempo_consumido": 10,
        "percentual_conclusao": 20,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1})

    assert classificacao == "inválido"
    assert "data_hora inválida" in erros


def test_interacao_rejeita_tempo_negativo():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 1,
        "tipo_interacao": "visualizacao",
        "data_hora": "2026-09-01T10:00:00",
        "tempo_consumido": -1,
        "percentual_conclusao": 20,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1})

    assert classificacao == "inválido"
    assert "tempo_consumido_min inválido" in erros


def test_interacao_rejeita_percentual_acima_de_100():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 1,
        "tipo_interacao": "conclusao",
        "data_hora": "2026-09-01T10:00:00",
        "tempo_consumido": 10,
        "percentual_conclusao": 101,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1})

    assert classificacao == "inválido"
    assert "percentual_conclusao deve estar entre 0 e 100" in erros


def test_conteudo_rejeita_tipo_nivel_e_carga_invalidos():
    bruto = {
        "conteudo_id": "1",
        "titulo": "Conteúdo",
        "tipo": "ebook",
        "categoria": "dados",
        "nivel": "especialista",
        "carga_horaria_min": "-10",
        "data_publicacao": "2026-08-01",
        "descricao": "Descrição",
        "autor": "Equipe",
    }

    tratado = normalizar_conteudo(bruto)
    classificacao, erros = validar_conteudo(tratado)

    assert classificacao == "inválido"
    assert "tipo fora do domínio permitido" in erros
    assert "nível fora do domínio permitido" in erros
    assert "carga_horaria_min deve ser positiva" in erros


def test_pipeline_identifica_interacao_duplicada_por_chave_composta():
    registros = [
        {
            "usuario_id": 1,
            "conteudo_id": 1,
            "tipo_interacao": "visualizacao",
            "data_hora": "2026-09-01T10:00:00",
            "tempo_consumido": 10,
            "percentual_conclusao": 20,
            "avaliacao_atribuida": None,
        },
        {
            "usuario_id": 1,
            "conteudo_id": 1,
            "tipo_interacao": "visualização",
            "data_hora": "2026-09-01T10:00:00",
            "tempo_consumido": 20,
            "percentual_conclusao": 40,
            "avaliacao_atribuida": None,
        },
    ]

    validos, rejeitados, resumo = _processar(
        registros,
        normalizar_interacao,
        lambda r: validar_interacao(r, {1}),
        ("usuario_id", "conteudo_id", "tipo_interacao", "data_hora"),
    )

    assert len(validos) == 1
    assert len(rejeitados) == 1
    assert resumo["duplicados"] == 1


def test_pipeline_identifica_comentario_duplicado_por_chave_composta():
    registros = [
        {
            "usuario_id": 1,
            "conteudo_id": 1,
            "avaliacao": 5,
            "comentario": "Muito bom",
            "tags": ["dados"],
            "data": "2026-09-01",
        },
        {
            "usuario_id": 1,
            "conteudo_id": 1,
            "avaliacao": 4,
            "comentario": "  Muito   bom ",
            "tags": ["dados"],
            "data": "2026-09-01",
        },
    ]

    validos, rejeitados, resumo = _processar(
        registros,
        normalizar_comentario,
        lambda r: validar_comentario(r, {1}),
        ("usuario_id", "conteudo_id", "data", "comentario"),
    )

    assert len(validos) == 1
    assert len(rejeitados) == 1
    assert resumo["duplicados"] == 1


def test_interacao_rejeita_numero_nao_finito():
    bruto = {
        "usuario_id": 1,
        "conteudo_id": 1,
        "tipo_interacao": "visualizacao",
        "data_hora": "2026-09-01T10:00:00",
        "tempo_consumido": "NaN",
        "percentual_conclusao": 20,
        "avaliacao_atribuida": None,
    }

    tratado = normalizar_interacao(bruto)
    classificacao, erros = validar_interacao(tratado, {1})

    assert classificacao == "inválido"
    assert "tempo_consumido_min inválido" in erros
