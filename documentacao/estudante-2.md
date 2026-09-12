# Estudante 2 — MongoDB, Embeddings, Busca Semântica e Recomendações

Responsável: **Gabriel Moreira Branco**

## Status

Parte concluída e integrada à branch `feature/estudante-2-mongodb-embeddings-recomendacoes`.

## Escopo implementado

A implementação cobre a ingestão e consultas de dados semiestruturados no MongoDB, a representação vetorial por embeddings e persistência no pgvector, a recuperação semântica em linguagem natural e o motor de recomendação personalizada com persistência no PostgreSQL:

- **RF07 — Persistência no MongoDB:** Carga de comentários e avaliações, desnormalização da categoria, criação de índices e consultas obrigatórias (via Python e script `mongodb/consultas.js`).
- **RF08 — Geração e armazenamento de embeddings:** Geração de embeddings densos de 384 dimensões com `sentence-transformers`, preparação textual e armazenamento no PostgreSQL com `pgvector`.
- **RF09 — Busca por similaridade semântica:** Recuperação de conteúdos por similaridade de cosseno em linguagem natural e demonstração das 3 consultas obrigatórias.
- **RF10 — Geração de recomendações:** Motor de recomendação baseado na fórmula de negócio ponderando índices de visualização ($Ivis$), curtidas ($Icur$) e filtro eliminatório de conclusão ($Iconc$), com classificação em Positivo, Estável e Negativo.
- **RF11 — Persistência das recomendações:** Armazenamento das recomendações geradas na tabela `recomendacoes` do PostgreSQL e em arquivo JSON processado.

---

## 1. MongoDB e Dados Semiestruturados (RF07)

### 1.1 Por que utilizar o MongoDB para Comentários e Avaliações?
Os comentários e avaliações possuem características típicas de dados semiestruturados:
- Presença de campos vetoriais de cardinalidade variável (`tags: ["didático", "iniciante", "python"]`);
- Textos dissertativos livres com comprimentos variáveis (`comentario`);
- Esquema flexível com evolução dinâmica (suporte a reações futuras, votos ou metadados de moderação).

O armazenamento em documentos BSON no MongoDB simplifica o modelo, eliminando a necessidade de tabelas associativas relacionais complexas para tags.

### 1.2 Desnormalização da Categoria nos Documentos
Durante a ingestão no MongoDB (`src/database/mongo.py`), cada comentário é enriquecido com o campo `categoria` correspondente ao seu `conteudo_id` (obtido a partir do catálogo tratado pelo Estudante 1).
- **Justificativa:** O RF07 exige expressamente *"agregar a quantidade de comentários ou avaliações por categoria"*. Como o arquivo bruto de comentários não possuía a categoria, a desnormalização na ingestão evita operações computacionalmente custosas de junção (`$lookup`) em tempo de leitura, permitindo agregações nativas de alta performance.

### 1.3 Operações Implementadas e Índices
Foram implementados índices em `conteudo_id`, `tags`, `avaliacao` e `categoria`. As 5 operações exigidas pelo RF07 estão demonstradas em:
1. `src/database/mongo.py` (via driver PyMongo integrado ao pipeline);
2. `mongodb/consultas.js` (script interativo para execução direta no `mongosh`).

---

## 2. Embeddings Vetoriais e pgvector (RF08)

### 2.1 Modelo Adotado
- **Modelo:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensão Vetorial:** 384 dimensões
- **Justificativas:**
  1. **Aderência ao Português:** O catálogo é inteiramente em português. Modelos multilíngues capturam relações semânticas e variações morfológicas da língua portuguesa com fidelidade muito superior a modelos exclusivamente em inglês;
  2. **Compatibilidade com o Banco:** A coluna `conteudos.embedding vector(384)` criada pelo Estudante 1 em `sql/criar_banco.sql` exige exatamente vetores de 384 dimensões;
  3. **Eficiência Computacional:** Modelo altamente otimizado para inferência rápida em CPU, viabilizando execução completa e reproduzível em poucos segundos.

### 2.2 Estratégia de Preparação Textual e Enriquecimento Semântico
Para capturar tanto a temática quanto a modalidade e a complexidade do material, o texto de entrada do embedding é enriquecido com metadados estruturados:
$$\text{Texto} = \text{"[Tipo | Categoria: Nome | Nível: Nível] Título do Conteúdo. Descrição do Conteúdo"}$$
*Exemplo:* `[Curso | Categoria: DevOps & Cloud | Nível: Avançado] Curso Completo de Segurança de Redes. Neste curso...`

Essa abordagem contextualiza o modelo de linguagem sobre a profundidade e formato do material sem recorrer a chunking arbitrário, preservando 1 embedding por conteúdo na coluna `conteudos.embedding` (384d).

> **Decisão sobre Chunking e Transcrições Longas:** No catálogo fornecido pelo desafio, os textos são descrições concisas de 1 parágrafo (~250 caracteres), cabendo com folga na janela de contexto de 128 tokens do modelo. Em cenários de produção com transcrições de áudio/vídeo extensas, a abordagem recomendada seria a segmentação semântica por tópicos/seções (sem cortes arbitrários de tamanho fixo), mantendo a referência ao `conteudo_id`.

### 2.3 Persistência no PostgreSQL com pgvector
Os vetores calculados são atualizados na coluna `embedding` da tabela `conteudos` do PostgreSQL através da função `atualizar_embeddings_postgres` em `src/database/postgres.py`, além de manter cópia serializada em `dados/processados/embeddings.json`.

---

## 3. Busca por Similaridade Semântica (RF09)

O módulo `src/recomendacao/busca.py` realiza buscas em linguagem natural:
1. Converte a consulta do usuário em embedding normalizado de 384d;
2. Calcula a similaridade de cosseno contra os conteúdos cadastrados (via pgvector com operador `<=>` ou em memória);
3. Retorna a lista ranqueada contendo posição, ID, título, categoria, tipo, valor de similaridade e distância.

### Consultas Obrigatórias Demonstradas no Pipeline:
1. *"Quero aprender os fundamentos de banco de dados para inteligência artificial."*
2. *"Pipelines de dados, orquestração de workflows e processamento distribuído com Apache Spark."*
3. *"Segurança da informação, conformidade com LGPD e controle de acesso a redes e APIs."*

---

## 4. Motor de Recomendação Personalizada (RF10 & RF11)

### 4.1 Formulação Matemática e Perfil Ponderado do Usuário (`user_embedding`)
A pontuação final atribuída a um conteúdo candidato $c$ para um usuário $u$ segue estritamente a formulação oficial do desafio:

$$\text{Pontuação}(u, c) = \left(\frac{Ivis + Icur}{2}\right) \times 100 \times Iconc$$

Onde:
- **$Ivis$ (Índice de Visualizações — $0.0$ a $1.0$):**
  A especificação do desafio (Seção 7, p. 7) faculta opções de cálculo para o $Ivis$:
  > *"Índice de Visualizações (Ivis): Mede o nível de afinidade temática com os conteúdos que o usuário consome e visualiza com frequência (calculado por similaridade vetorial via pgvector ou pela proporção de tempo consumido na mesma categoria), assumindo valores contínuos na faixa de 0.0 a 1.0."*

  #### Análise Técnica Comparativa das 3 Abordagens Propostas:
  1. **Opção 1 — Proporção de tempo consumido na mesma categoria (Abordagem Relacional Clássica):**
     Calcula $\frac{\text{tempo consumido na categoria}}{\text{tempo total de consumo}}$.
     *Limitação crítica:* É uma métrica estritamente categórica. Se o discente assiste a vídeos de "Machine Learning" (categoria *Inteligência Artificial*), a métrica atribui afinidade nula ($0.0$) para um curso de "Estatística e Probabilidade" (categoria *Matemática*) ou "Python para Análise de Dados" (categoria *Programação*), mesmo havendo forte correlação temática.
  2. **Opção 2 — Similaridade vetorial pontual (conteúdo a conteúdo isolado):**
     Calcula a similaridade apenas contra o item mais recente.
     *Limitação:* Ignora o histórico acumulado e torna o sistema suscetível a ruídos passageiros.
  3. **Opção 3 (ESCOLHIDA) — Similaridade Vetorial Semântica via pgvector / Embeddings Ponderados:**
     Constrói o perfil semântico latente do usuário ($\vec{v}_{\text{perfil}}$ ou `user_embedding`) no espaço vetorial denso de 384 dimensões gerado pelo modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, ponderado pela intensidade de consumo (tempo consumido e percentual de conclusão):
     $$\vec{v}_{\text{perfil}} = \frac{\sum w_i \cdot \vec{e}_i}{\|\sum w_i \cdot \vec{e}_i\|}$$
     Onde o peso $w_i$ reflete o engajamento:
     $$w_i = 1.0 + \min\left(1.0, \frac{\text{percentual\_conclusao}}{100}\right) + (0.5 \text{ se concluído})$$
     A afinidade temática $Ivis$ é calculada pela similaridade de cosseno normalizada contra os vetores indexados no banco vetorial (`pgvector`):
     $$Ivis = \max\left(0.0, \min\left(1.0, \frac{\cos(\vec{v}_{\text{perfil}}, \vec{e}_c) + 1}{2}\right)\right)$$

  > **Justificativa da Escolha da Opção 3:**
  > - **Alinhamento com a Ementa de IA:** O módulo cursado é *Fundamentos de Dados para IA*. Optar por embeddings semânticos e busca vetorial valida na prática o aprendizado de representações densas e bancos vetoriais, em contraste com métricas estatísticas puramente relacionais.
  > - **Generalização Cross-Category:** Identifica afinidade real entre materiais complementares, mesmo quando categorizados com rótulos distintos.
  > - **Precisão e Nuance:** A similaridade cosseno mapeia sutilmente a proximidade temática de $0.0$ a $1.0$, conferindo maior assertividade às recomendações.

- **$Icur$ (Índice de Curtidas e Avaliações — $0.0$ a $1.0$):**
  Mede o interesse explícito baseado em materiais curtidos ou com nota $\ge 4.0$:
  $$Icur = \frac{\text{Conteúdos curtidos/bem avaliados na mesma categoria do candidato}}{\text{Total de conteúdos curtidos/bem avaliados pelo usuário}}$$
  Caso o usuário não possua histórico de curtidas/avaliações, adota-se $Icur = 0.0$.
- **$Iconc$ (Filtro Eliminatório de Concluídos):**
  $$Iconc = \begin{cases} 0, & \text{se o usuário já concluiu o conteúdo (anula a pontuação)} \\ 1, & \text{se o conteúdo ainda não foi concluído} \end{cases}$$

### 4.2 Regra de Classificação e Nomenclatura Oficial (Tipo de Recomendação)
Com base na pontuação calculada, o sistema atribui o status com as nomenclaturas estritas do documento de avaliação:
- **Positivo ($\text{Pontuação} \ge 70.0$):**
  Forte afinidade. O usuário visualiza ativamente conteúdos desse tema e costuma curtir/avaliar positivamente.
- **Estável ($40.0 < \text{Pontuação} < 70.0$):**
  Afinidade moderada. O usuário demonstrou interesse parcial (ou apenas visualizou pouco, ou ainda não avaliou conteúdos semelhantes).
- **Negativo ($\text{Pontuação} \le 40.0$ ou $Iconc = 0$):**
  Baixo interesse ou conteúdo já concluído. Conforme a regra de negócio do enunciado, **é descartado da lista de sugestões**, garantindo que apenas recomendações ativas (`Positivo` e `Estável`) sejam sugeridas ao estudante.

### 4.3 Persistência Integral sem Limitação Arbitrária (RF11)
Atendendo à especificação do desafio e à diretriz de arquitetura de dados:
- O sistema não restringe a lista a um corte arbitrário (ex: Top-10), configurando `recomendacao.limite: null` em `config/config.yaml`.
- Todas as sugestões ativas (`Positivo` e `Estável`) são ordenadas por pontuação decrescente ($1, 2, \dots, N$) e persistidas na tabela `recomendacoes` do PostgreSQL (`usuario_id`, `conteudo_id`, `pontuacao`, `posicao`, `status`, `data_geracao`) através de carga transacional eficiente em lote (`execute_values`), além de cópia serializada em `dados/processados/recomendacoes.json`.
- A integridade é garantida pela constraint `UNIQUE (usuario_id, conteudo_id, data_geracao)`.

---

##  5. Estrutura Modular dos Componentes sob `src/`

- `src/database/mongo.py`: Cliente MongoDB, carga enriquecida e agregações (RF07).
- `src/database/postgres.py`: Estendido para incluir persistência pgvector (RF08) e carga de recomendações (RF11).
- `src/recomendacao/embeddings.py`: Geração de embeddings vetoriais com SentenceTransformers (RF08).
- `src/recomendacao/busca.py`: Recuperação semântica e 3 consultas demonstrativas (RF09).
- `src/recomendacao/motor.py`: Motor de cálculo da fórmula oficial e classificação (RF10).
- `src/recomendacao/persistencia.py`: Persistência transacional e em arquivo (RF11).
- `mongodb/consultas.js`: Script executável no `mongosh` com as 5 consultas demonstrativas do MongoDB (RF07).

---

## 6. Execução e Testes

### Execução Completa do Pipeline:
```bash
python -m src.main
```

### Testes Automatizados por Domínio:
A suíte foi modularizada permitindo execução especializada por componente:
```bash
# Testes do MongoDB (RF07)
python -m pytest tests/test_mongo.py -v

# Testes de Embeddings e Busca Semântica (RF08, RF09)
python -m pytest tests/test_embeddings.py -v

# Testes do Motor de Recomendação e Persistência (RF10, RF11)
python -m pytest tests/test_recomendacao.py -v

# Testes do Banco Relacional e pgvector (RF06, RF08, RF11)
python -m pytest tests/test_postgres.py -v

# Execução de toda a suíte de testes (53 testes aprovados)
python -m pytest -v
```

Todos os testes validam o cálculo matemático da pontuação, as faixas de classificação de recomendação, o filtro de conclusão, a preparação de textos, a persistência no pgvector e o enriquecimento de categorias no MongoDB.
