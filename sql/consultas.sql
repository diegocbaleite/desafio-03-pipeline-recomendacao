-- Consultas de verificação e auditoria do PostgreSQL (Desafio Prático 1)

-- 1. Contagens gerais de integridade relacional (Estudante 1 - RF06)
SELECT COUNT(*) AS total_usuarios FROM usuarios;
SELECT COUNT(*) AS total_categorias FROM categorias;
SELECT COUNT(*) AS total_conteudos FROM conteudos;
SELECT COUNT(*) AS total_interacoes FROM interacoes;

-- 2. Distribuição de conteúdos por categoria
SELECT
    c.nome AS categoria,
    COUNT(*) AS quantidade_conteudos
FROM conteudos co
JOIN categorias c ON c.categoria_id = co.categoria_id
GROUP BY c.nome
ORDER BY quantidade_conteudos DESC, c.nome;

-- 3. Distribuição de interações por tipo
SELECT
    tipo_interacao,
    COUNT(*) AS quantidade
FROM interacoes
GROUP BY tipo_interacao
ORDER BY quantidade DESC;

-- 4. Verificação de Embeddings e pgvector (Estudante 2 - RF08)
SELECT 
    COUNT(*) AS conteudos_com_embedding
FROM conteudos 
WHERE embedding IS NOT NULL;

-- 5. Total de recomendações persistidas e distribuição por status (Estudante 2 - RF11)
SELECT 
    status,
    COUNT(*) AS total_recomendacoes,
    ROUND(AVG(pontuacao), 2) AS pontuacao_media,
    ROUND(MIN(pontuacao), 2) AS pontuacao_minima,
    ROUND(MAX(pontuacao), 2) AS pontuacao_maxima
FROM recomendacoes
GROUP BY status
ORDER BY total_recomendacoes DESC;

-- 6. Consulta do Top-5 de Recomendações para o Usuário 1 (RF10 & RF11)
SELECT 
    r.posicao,
    r.conteudo_id,
    c.titulo,
    cat.nome AS categoria,
    c.tipo,
    r.pontuacao AS score_afinidade,
    r.status
FROM recomendacoes r
JOIN conteudos c ON c.conteudo_id = r.conteudo_id
JOIN categorias cat ON cat.categoria_id = c.categoria_id
WHERE r.usuario_id = 1
ORDER BY r.posicao ASC
LIMIT 5;

-- 7. Exemplo de Busca por Similaridade Vetorial via pgvector (RF09)
-- Recupera os 3 conteúdos mais próximos do embedding do primeiro conteúdo cadastrado
SELECT 
    c2.conteudo_id,
    c2.titulo,
    ROUND((1 - (c2.embedding <=> c1.embedding))::numeric, 4) AS similaridade_cosseno
FROM conteudos c1, conteudos c2
WHERE c1.conteudo_id = 1 
  AND c2.conteudo_id != 1
  AND c1.embedding IS NOT NULL 
  AND c2.embedding IS NOT NULL
ORDER BY c2.embedding <=> c1.embedding
LIMIT 3;
