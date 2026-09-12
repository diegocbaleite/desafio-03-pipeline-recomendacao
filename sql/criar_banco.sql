-- Estrutura relacional mínima do Desafio Prático 1
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS categorias (
    categoria_id SERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS conteudos (
    conteudo_id BIGINT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('Curso', 'Vídeo', 'Artigo', 'Podcast')),
    categoria_id INTEGER NOT NULL REFERENCES categorias(categoria_id),
    nivel VARCHAR(30) NOT NULL CHECK (nivel IN ('Básico', 'Intermediário', 'Avançado')),
    carga_horaria_min INTEGER NOT NULL CHECK (carga_horaria_min > 0),
    data_publicacao DATE NOT NULL,
    descricao TEXT NOT NULL,
    autor VARCHAR(180) NOT NULL,
    embedding vector(384)
);

CREATE TABLE IF NOT EXISTS interacoes (
    interacao_id BIGINT PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(usuario_id),
    conteudo_id BIGINT NOT NULL REFERENCES conteudos(conteudo_id),
    tipo_interacao VARCHAR(30) NOT NULL CHECK (
        tipo_interacao IN ('visualização', 'início', 'conclusão', 'curtida', 'avaliação', 'compartilhamento')
    ),
    data_hora TIMESTAMP NOT NULL,
    tempo_consumido_min NUMERIC(10,2) NOT NULL CHECK (tempo_consumido_min >= 0),
    percentual_conclusao NUMERIC(5,2) NOT NULL CHECK (
        percentual_conclusao >= 0 AND percentual_conclusao <= 100
    ),
    avaliacao NUMERIC(2,1) CHECK (avaliacao >= 1 AND avaliacao <= 5)
);

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interacoes' AND column_name='tempo_consumido') THEN
        ALTER TABLE interacoes RENAME COLUMN tempo_consumido TO tempo_consumido_min;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interacoes' AND column_name='avaliacao_atribuida') THEN
        ALTER TABLE interacoes RENAME COLUMN avaliacao_atribuida TO avaliacao;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS recomendacoes (
    recomendacao_id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(usuario_id),
    conteudo_id BIGINT NOT NULL REFERENCES conteudos(conteudo_id),
    pontuacao NUMERIC(6,2) NOT NULL CHECK (pontuacao >= 0 AND pontuacao <= 100),
    posicao INTEGER NOT NULL CHECK (posicao > 0),
    status VARCHAR(20),
    data_geracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (usuario_id, conteudo_id, data_geracao)
);

CREATE INDEX IF NOT EXISTS idx_interacoes_usuario ON interacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_interacoes_conteudo ON interacoes(conteudo_id);
CREATE INDEX IF NOT EXISTS idx_conteudos_categoria ON conteudos(categoria_id);

-- KPI 2 - Visualizações por Categoria
CREATE OR REPLACE VIEW vw_content_views_by_category AS
SELECT
    i.data_hora,
    cat.nome AS categoria,
    i.conteudo_id,
    i.usuario_id
FROM interacoes i
JOIN conteudos c
    ON i.conteudo_id = c.conteudo_id
JOIN categorias cat
    ON c.categoria_id = cat.categoria_id
WHERE i.tipo_interacao = 'visualização';

-- KPI 3 - Taxa de Conclusão de Conteúdos por Categoria
CREATE OR REPLACE VIEW vw_content_completion_by_category AS
SELECT
    i.data_hora,
    cat.nome AS categoria,
    i.usuario_id,
    i.conteudo_id,
    i.tipo_interacao
FROM interacoes i
JOIN conteudos c
    ON i.conteudo_id = c.conteudo_id
JOIN categorias cat
    ON c.categoria_id = cat.categoria_id
WHERE i.tipo_interacao IN ('início', 'conclusão');


-- KPI 4 - Taxa de Conversão de Recomendações
CREATE OR REPLACE VIEW vw_recommendation_conversion AS
SELECT
    r.recomendacao_id,
    r.usuario_id,
    r.conteudo_id,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM interacoes i
            WHERE i.usuario_id = r.usuario_id
                AND i.conteudo_id = r.conteudo_id
			    AND i.data_hora > r.data_geracao
        )
        THEN 1
        ELSE 0
    END AS conversao

FROM recomendacoes r;