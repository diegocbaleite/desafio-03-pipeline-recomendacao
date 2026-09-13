# Especificação Técnica e Decisões de Arquitetura do Pipeline

Este documento consolida as especificações técnicas, premissas de modelagem e decisões de engenharia de software adotadas no desenvolvimento do **Pipeline de Recomendação e Dashboard de Conteúdos Educacionais (Desafio Prático 1 — FIC_DEV)**.

A solução foi projetada como um ecossistema de dados coeso, resiliente e reproduzível, combinando armazenamento relacional (PostgreSQL), NoSQL orientado a documentos (MongoDB), processamento vetorial para inteligência artificial (`pgvector`), motor de recomendação personalizada e análise de indicadores no Apache Superset.

---

## 1. Visão Geral da Arquitetura

O fluxo de dados é estruturado em seis camadas sequenciais e desacopladas:

```text
┌────────────────┐     ┌──────────────────────┐     ┌────────────────────────────────┐
│ Fontes Brutas  │ ──> │ Ingestão & Qualidade │ ──> │ Armazenamento Híbrido          │
│ CSV / JSON     │     │ Limpeza, Validação   │     │ PostgreSQL (Dados Estruturados)│
└────────────────┘     └──────────────────────┘     │ MongoDB (Semiestruturados)     │
                                                    └────────────────────────────────┘
                                                                   │
                                                                   ▼
┌────────────────┐     ┌──────────────────────┐     ┌────────────────────────────────┐
│ Apache Superset│ <── │ Motor de Recomendação│ <── │ Camada Vetorial & IA           │
│ Dashboard/KPIs │     │ Ivis, Icur, Iconc    │     │ SentenceTransformers (384d)    │
│ Views SQL      │     │ Classificação Status │     │ pgvector (Distância Cosseno)   │
└────────────────┘     └──────────────────────┘     └────────────────────────────────┘
```

---

## 2. Ingestão, Tratamento e Qualidade dos Dados

### 2.1 Fontes Processadas e Preservação dos Dados Originais
O pipeline consome três fontes primárias situadas em `dados/brutos/`, contendo 1.000 registros cada:
- `catalogo.csv`: catálogo descritivo dos conteúdos educacionais;
- `interacoes.json`: eventos de consumo e engajamento dos estudantes;
- `comentarios.json`: avaliações textuais e tags atribuídas aos materiais.

> **Decisão de Engenharia:** Preservação estrita dos arquivos brutos. O pipeline opera em modo somente-leitura sobre `dados/brutos/`, direcionando todos os dados tratados e enriquecidos para `dados/processados/`.

### 2.2 Compatibilidade e Normalização dos Formatos Oficiais
As fontes originais apresentavam divergências de nomenclatura e ausência de identificadores únicos próprios para interações e comentários:
- **Adequação de campos:** `tempo_consumido` $\to$ `tempo_consumido_min` e `avaliacao_atribuida` $\to$ `avaliacao` (com conversão estrita para ponto flutuante `float`);
- **Geração de IDs sintéticos:** Geração de identificadores sequenciais reproduzíveis (`interacao_id` e `comentario_id`), iniciando em 1, atribuídos aos registros válidos após a etapa de validação;
- **Padronização textual:** Remoção de espaços sobressalentes (`strip()`), normalização de caixa alta/baixa e padronização categórica (`strip().title()`);
- **Padronização de tags:** Conversão para minúsculas, remoção de duplicatas e ordenação alfabética em listas de tags.

### 2.3 Regras de Validação Defensiva (Classificação de Registros)
Cada registro é avaliado e categorizado em quatro estados mutuamente exclusivos:
1. **`válido`:** atende a todos os critérios estruturais, semânticos e referenciais;
2. **`inválido`:** viola limites de domínio, regras de negócio ou tipos de dados;
3. **`incompleto`:** ausência de campos obrigatórios;
4. **`duplicado`:** repetição de chave identificadora primária ou composta.

#### Critérios Estritos de Validação Aplicados:
- **Não-truncamento de IDs:** IDs com casas decimais (ex: `5.7`) são rejeitados como inválidos, repudiando conversões silenciosas como `int(float(x))`;
- **Defesa contra Não-Finitos:** Rejeição ativa de valores `NaN` e infinito (`math.isfinite()`);
- **Integridade Referencial em Memória:** Interações ou comentários que referenciam `conteudo_id` inexistente no catálogo válido são rejeitados com motivo registrado;
- **Validação Temporal:** Exigência de formato ISO 8601 estrito (`YYYY-MM-DD` para catálogo e comentários; `YYYY-MM-DDTHH:MM:SS` com componente de horário para interações);
- **Limites Numéricos:** Avaliações no intervalo $[1.0, 5.0]$, percentual de conclusão em $[0.0, 100.0]$, carga horária positiva $> 0$ e tempo consumido não-negativo $\ge 0$.

### 2.4 Estratégia de Deduplicação
- **Catálogo:** Deduplicação baseada na chave unívoca `conteudo_id`;
- **Interações:** Deduplicação por chave composta `(usuario_id, conteudo_id, tipo_interacao, data_hora)`;
- **Comentários:** Deduplicação por chave composta `(usuario_id, conteudo_id, data, comentario)`.

---

## 3. Persistência Híbrida: Relacional (PostgreSQL) e NoSQL (MongoDB)

### 3.1 Persistência Estruturada no PostgreSQL
O modelo relacional suporta o núcleo transacional e analítico da plataforma:
- **Tabelas Implementadas:** `usuarios`, `categorias`, `conteudos`, `interacoes` e `recomendacoes`;
- **Chaves e Integridade:** Chaves primárias (`BIGINT`), chaves estrangeiras (`REFERENCES`) e constraints de domínio (`CHECK`);
- **Carga Transacional em Lote:** Inserção atômica via `psycopg2.extras.execute_values` em um único bloco de transação com proteção de idempotência (`ON CONFLICT DO UPDATE` / `DO NOTHING`).

### 3.2 Persistência Semiestruturada no MongoDB
O MongoDB armazena as avaliações dissertativas e metadados flexíveis:
- **Justificativa Arquitetural:** Documentos BSON acomodam naturalmente estruturas de cardinalidade dinâmica (vetores de `tags: ["python", "didático"]`) e textos livres longos, dispensando a complexidade de tabelas associativas relacionais;
- **Desnormalização da Categoria:** Durante a ingestão no MongoDB, cada comentário é enriquecido com o campo `categoria` correspondente ao seu `conteudo_id`. Essa decisão de modelagem elimina a necessidade de junções custosas (`$lookup`) em tempo de consulta, viabilizando agregações nativas de alta velocidade por categoria;
- **Indexação:** Criação de índices em `conteudo_id`, `tags`, `avaliacao` e `categoria`.

---

## 4. Representação Vetorial e Busca Semântica

### 4.1 Modelo de Embeddings
- **Modelo Adotado:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Dimensionalidade:** 384 dimensões densas
- **Justificativas da Escolha:**
  1. **Fidelidade ao Português:** O catálogo é em português; modelos multilíngues capturam nuances sintáticas e semânticas com precisão substancialmente superior a modelos anglo-cêntricos;
  2. **Eficiência Computacional:** Inferência ultrarrápida em CPU (processando 1.000 conteúdos em ~22 segundos sem GPU);
  3. **Compatibilidade de Schema:** Alinhamento exato com a definição `embedding vector(384)` no PostgreSQL.

### 4.2 Preparação Textual e Enriquecimento Semântico
Para evitar segmentação (*chunking*) artificial em textos concisos (~250 caracteres), cada conteúdo é estruturado com seus metadados contextuais antes da vetorização:
$$\text{Texto} = \text{"[Tipo | Categoria: Nome | Nível: Nível] Título. Descrição"}$$
*Exemplo:* `[Curso | Categoria: Inteligência Artificial | Nível: Avançado] Masterclass de IA Generativa. Neste curso...`

### 4.3 Busca por Similaridade Vetorial
- Utilização da extensão `pgvector` com o operador de distância de cosseno (`<=>`);
- Implementação de fallback vetorial em memória via produto escalar normalizado com `numpy` para ambientes sem extensão instalada;
- Suporte a consultas em linguagem natural retornando rank, ID, título, categoria, tipo, similaridade e distância.

---

## 5. Motor de Recomendação Personalizada

### 5.1 Formulação Matemática Oficial (RF10)
A pontuação final de afinidade entre o usuário $u$ e o conteúdo candidato $c$ obedece à equação:

$$\text{Pontuação}(u, c) = \left( \frac{Ivis + Icur}{2} \right) \times 100 \times Iconc$$

Onde:
1. **$Ivis$ (Índice de Visualizações — $0.0$ a $1.0$):**
   Calculado pela **Similaridade Vetorial Semântica via Embeddings Ponderados**. Constrói o perfil latente do usuário ($\vec{v}_{\text{perfil}}$ ou `user_embedding`) no espaço denso de 384 dimensões, onde cada conteúdo consumido é ponderado pela profundidade de engajamento:
   $$w_i = 1.0 + \min\left(1.0, \frac{\text{percentual de conclusão}}{100}\right) + (0.5 \text{ se concluído})$$
   $$\vec{v}_{\text{perfil}} = \frac{\sum w_i \cdot \vec{e}_i}{\|\sum w_i \cdot \vec{e}_i\|}$$
   O índice $Ivis$ é a similaridade cosseno normalizada do perfil contra o vetor do candidato $\vec{e}_c$:
   $$Ivis = \max\left(0.0, \min\left(1.0, \frac{\cos(\vec{v}_{\text{perfil}}, \vec{e}_c) + 1}{2}\right)\right)$$
2. **$Icur$ (Índice de Curtidas e Avaliações — $0.0$ a $1.0$):**
   Mede a proporção de conteúdos explicitamente aprovados (curtidos ou com nota $\ge 4.0$) na mesma categoria do candidato:
   $$Icur = \frac{\text{Aprovações na mesma categoria}}{\text{Total de aprovações do usuário}}$$
3. **$Iconc$ (Filtro Eliminatório de Conclusão):**
   Filtro binário obrigatório. Assume valor $0$ se o aluno já concluiu o material (anulando a pontuação), e $1$ se o conteúdo permanece pendente.

### 5.2 Regras de Classificação e Descarte
- **Positivo ($\text{Pontuação} \ge 70.0$):** Forte afinidade temática e aprovação prévia;
- **Estável ($40.0 < \text{Pontuação} < 70.0$):** Afinidade moderada ou interesse parcial;
- **Negativo ($\text{Pontuação} \le 40.0$ ou $Iconc = 0$):** Descartado da lista de recomendações ativas.

### 5.3 Persistência Integral sem Truncamento Arbitrário (RF11)
Todas as recomendações com status `Positivo` e `Estável` geradas para cada discente são ordenadas decrescentemente e gravadas na íntegra na tabela `recomendacoes` do PostgreSQL e em `dados/processados/recomendacoes.json`, garantindo rastreabilidade sem perdas artificiais de ranking.

---

## 6. Camada Analítica e Visualização (Apache Superset)

### 6.1 Views SQL de Desacoplamento Analítico
Para subsidiar o Superset sem sobrecarregar as tabelas transacionais, três views foram implementadas no PostgreSQL:
1. `vw_content_views_by_category`: agrega eventos de visualização com data, categoria e identificadores;
2. `vw_content_completion_by_category`: correlaciona eventos de início e término para cálculo da taxa de conclusão;
3. `vw_recommendation_conversion`: avalia se o estudante interagiu com o conteúdo em data posterior à recomendação (`i.data_hora > r.data_geracao`).

### 6.2 Sincronização Automatizada via Docker
O utilitário `dashboard/sync_database.py` é executado automaticamente no bootstrap do contêiner:
- Extrai dinamicamente o UUID e nome do banco do pacote `dashboard/dashboard_export.zip`;
- Cria/atualiza a conexão com o PostgreSQL com base no `.env`;
- Importa o painel e publica os gráficos sem exigir nenhuma intervenção manual.

---

## 7. Práticas de DataOps e Resumo das Decisões

| Desafio Encontrado | Abordagem Tradicional / IA | Decisão de Engenharia Adotada | Benefício Obtido |
| :--- | :--- | :--- | :--- |
| **Deduplicação de Fontes sem ID** | Deduplicação apenas no banco | Chaves compostas em memória na ingestão | Auditoria preventiva e registro de rejeitados |
| **Agregação no NoSQL** | `$lookup` relacional em tempo de query | Desnormalização da categoria na ingestão | Agregações nativas com performance superior |
| **Afinidade Temática ($Ivis$)** | Proporção estatística de tempo por categoria | Centroide vetorial ponderado por engajamento | Recomendações *cross-category* com nuance de IA |
| **Isolamento de Testes** | Testar usando os caminhos oficiais de disco | Injeção de caminhos temporários via `tmp_path` | Prevenção de corrupção (*test pollution*) no resumo |
| **Importação de Dashboard** | Cadastro manual via tela web | Automação com CLI e sincronização por UUID | Reprodutibilidade (*zero configuration*) em DataOps |
