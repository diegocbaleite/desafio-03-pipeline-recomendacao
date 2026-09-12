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
