-- Consultas de verificação da carga do Estudante 1

SELECT COUNT(*) AS total_usuarios FROM usuarios;
SELECT COUNT(*) AS total_categorias FROM categorias;
SELECT COUNT(*) AS total_conteudos FROM conteudos;
SELECT COUNT(*) AS total_interacoes FROM interacoes;

SELECT
    c.nome AS categoria,
    COUNT(*) AS quantidade_conteudos
FROM conteudos co
JOIN categorias c ON c.categoria_id = co.categoria_id
GROUP BY c.nome
ORDER BY quantidade_conteudos DESC, c.nome;

SELECT
    tipo_interacao,
    COUNT(*) AS quantidade
FROM interacoes
GROUP BY tipo_interacao
ORDER BY quantidade DESC;
