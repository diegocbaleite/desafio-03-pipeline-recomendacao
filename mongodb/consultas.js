/**
 * FIC_DEV — Desafio Prático 1: Pipeline de Recomendação e Dashboard
 * Entregável: mongodb/consultas.js (Requisito Funcional RF07)
 * 
 * Demonstração das 5 operações obrigatórias exigidas no MongoDB:
 * 1. Inserir documentos;
 * 2. Consultar comentários de determinado conteúdo;
 * 3. Localizar documentos por tag;
 * 4. Filtrar avaliações pela nota;
 * 5. Agregar a quantidade de comentários ou avaliações por categoria.
 * 
 * Execução via mongosh:
 *   mongosh "mongodb://admin:admin123@localhost:27017/ficdev_recomendacao?authSource=admin" mongodb/consultas.js
 */

// Seleciona a base de dados
db = db.getSiblingDB("ficdev_recomendacao");

print("=================================================================");
print("FIC_DEV — DEMONSTRAÇÃO DE CONSULTAS MONGODB (RF07)");
print("=================================================================");

// -----------------------------------------------------------------
// 1. INSERÇÃO DE EXEMPLO (RF07 - Inserir documentos)
// Documento semiestruturado enriquecido com a 'categoria' do catálogo
// -----------------------------------------------------------------
print("\n--- 1. Inserção de documento de exemplo ---");
const resultadoInsercao = db.comentarios.insertOne({
    usuario_id: 999,
    conteudo_id: 1,
    categoria: "DevOps & Cloud",
    avaliacao: 5.0,
    comentario: "Excelente curso, abordagem prática e direta sobre controle de acesso.",
    tags: ["segurança", "redes", "prático", "devops"],
    data: "2026-09-11"
});
printjson(resultadoInsercao);

// -----------------------------------------------------------------
// 2. CONSULTAR COMENTÁRIOS DE UM CONTEÚDO ESPECÍFICO (RF07)
// -----------------------------------------------------------------
print("\n--- 2. Consultar comentários do conteúdo_id: 1 ---");
const comentariosConteudo = db.comentarios.find(
    { conteudo_id: 1 },
    { _id: 0, usuario_id: 1, conteudo_id: 1, avaliacao: 1, comentario: 1, tags: 1 }
).limit(5).toArray();
printjson(comentariosConteudo);

// -----------------------------------------------------------------
// 3. LOCALIZAR DOCUMENTOS POR TAG (RF07)
// Busca semântica por tags associadas
// -----------------------------------------------------------------
print("\n--- 3. Localizar avaliações com a tag 'python' ou 'didático' ---");
const comentariosPorTag = db.comentarios.find(
    { tags: { $in: ["python", "didático", "prático"] } },
    { _id: 0, usuario_id: 1, conteudo_id: 1, categoria: 1, tags: 1, avaliacao: 1 }
).limit(5).toArray();
printjson(comentariosPorTag);

// -----------------------------------------------------------------
// 4. FILTRAR AVALIAÇÕES PELA NOTA (RF07)
// Retorna materiais com avaliação excelente (nota >= 4.0)
// -----------------------------------------------------------------
print("\n--- 4. Filtrar avaliações com nota >= 4.5 ---");
const avaliacoesAltas = db.comentarios.find(
    { avaliacao: { $gte: 4.5 } },
    { _id: 0, usuario_id: 1, conteudo_id: 1, avaliacao: 1, comentario: 1 }
).limit(5).toArray();
printjson(avaliacoesAltas);

// -----------------------------------------------------------------
// 5. AGREGAR COMENTÁRIOS E AVALIAÇÕES POR CATEGORIA (RF07)
// Pipeline de agregação: agrupa pela categoria desnormalizada do catálogo
// -----------------------------------------------------------------
print("\n--- 5. Agregação: Total de comentários e média de avaliação por categoria ---");
const agregacaoCategoria = db.comentarios.aggregate([
    {
        $group: {
            _id: "$categoria",
            total_comentarios: { $sum: 1 },
            media_avaliacao: { $avg: "$avaliacao" }
        }
    },
    {
        $project: {
            _id: 0,
            categoria: "$_id",
            total_comentarios: 1,
            media_avaliacao: { $round: ["$media_avaliacao", 2] }
        }
    },
    {
        $sort: { total_comentarios: -1 }
    }
]).toArray();
printjson(agregacaoCategoria);

print("\n=================================================================");
print("CONSULTAS EXECUTADAS COM SUCESSO!");
print("=================================================================");
