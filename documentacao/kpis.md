# Especificação Oficial de Métricas e KPIs (RF12 e RF13)

Este documento apresenta a definição, modelagem matemática, fontes de dados e interpretação de negócio dos indicadores operacionais e estratégicos desenvolvidos para a plataforma educacional, atendendo rigorosamente ao requisito funcional **RF12** e subsidiando o dashboard no Apache Superset (**RF13**).

---

## 1. Resumo dos Indicadores

| Tipo | Nome do Indicador | Visualização no Superset | Fonte / View PostgreSQL |
| :--- | :--- | :--- | :--- |
| **Operacional** | Total de Usuários Registrados | Big Number (Cartão) | Tabela `usuarios` |
| **Operacional** | Total de Conteúdos Cadastrados | Big Number (Cartão) | Tabela `conteudos` |
| **Operacional** | Média de Tempo por Interação | Big Number (Cartão) | Tabela `interacoes` |
| **Decisão (KPI 1)** | Usuários Ativos no Período | Big Number com Filtro Temporal | Tabela `interacoes` |
| **Decisão (KPI 2)** | Visualizações por Categoria | Gráfico de Linhas (Série Temporal) | View `vw_content_views_by_category` |
| **Decisão (KPI 3)** | Taxa de Conclusão por Categoria | Gráfico de Barras Comparativas | View `vw_content_completion_by_category` |
| **Decisão (KPI 4)** | Taxa de Conversão das Recomendações | Big Number (Percentual) | View `vw_recommendation_conversion` |

---

## 2. Detalhamento dos Indicadores de Tomada de Decisão (KPIs)

### KPI 1: Usuários Ativos no Período

- **Nome:** Usuários Ativos no Período (Active Users)
- **Objetivo:** Mensurar a quantidade de usuários únicos que realizaram pelo menos uma ação/interação na plataforma educacional durante o intervalo de tempo selecionado.
- **Fórmula:**
  $$\text{Usuários Ativos} = \text{COUNT}(\text{DISTINCT } \text{usuario\_id})$$
- **Fonte dos Dados:**
  - Tabela: `interacoes`
  - Campos: `usuario_id`, `data_hora`
- **Periodicidade:**
  - Dinâmica / Sob Demanda, orientada pelo componente de filtro temporal (*Time Range*) no Apache Superset.
- **Interpretação:**
  - Indica o engajamento real da base discente. Quedas abruptas sinalizam perda de interesse ou necessidade de campanhas de reativação; picos coincidem com períodos de lançamento de novos cursos ou avaliações.

---

### KPI 2: Visualizações por Categoria ao Longo do Tempo

- **Nome:** Volume de Visualizações por Categoria Temática
- **Objetivo:** Mapear a evolução temporal do consumo e a atratividade inicial dos conteúdos segmentados por área de conhecimento.
- **Fórmula:**
  $$\text{Visualizações} = \sum [\text{tipo\_interacao} = \text{'visualização'}]$$
- **Fonte dos Dados:**
  - View SQL: `vw_content_views_by_category`
  - Tabelas de Origem: `interacoes` $\bowtie$ `conteudos` $\bowtie$ `categorias`
  - Definição DDL:
    ```sql
    CREATE OR REPLACE VIEW vw_content_views_by_category AS
    SELECT
        i.data_hora,
        cat.nome AS categoria,
        i.conteudo_id,
        i.usuario_id
    FROM interacoes i
    JOIN conteudos c ON i.conteudo_id = c.conteudo_id
    JOIN categorias cat ON c.categoria_id = cat.categoria_id
    WHERE i.tipo_interacao = 'visualização';
    ```
- **Periodicidade:**
  - Agregação mensal no gráfico de linhas de série temporal com resolução diária/semanal sob demanda.
- **Interpretação:**
  - Permite aos gestores pedagógicos identificar tendências sazonais e áreas temáticas em ascensão (ex: Inteligência Artificial, Engenharia de Dados) para direcionar investimentos na contratação de instrutores e produção de materiais.

---

### KPI 3: Taxa de Conclusão de Conteúdo por Categoria

- **Nome:** Taxa de Término / Conclusão (Completion Rate)
- **Objetivo:** Avaliar a eficiência pedagógica e o índice de retenção dos alunos em cada categoria temática, contrastando o início com a finalização efetiva.
- **Fórmula:**
  $$\text{Taxa de Conclusão (\%)} = \left( \frac{\text{Quantidade de Interações de 'conclusão'}}{\text{Quantidade de Interações de 'início'}} \right) \times 100$$
  *(Com tratamento para evitar divisão por zero via `NULLIF` no SQL ou fallback para 0,0%).*
- **Fonte dos Dados:**
  - View SQL: `vw_content_completion_by_category`
  - Tabelas de Origem: `interacoes` $\bowtie$ `conteudos` $\bowtie$ `categorias`
  - Definição DDL:
    ```sql
    CREATE OR REPLACE VIEW vw_content_completion_by_category AS
    SELECT
        i.data_hora,
        cat.nome AS categoria,
        i.usuario_id,
        i.conteudo_id,
        i.tipo_interacao
    FROM interacoes i
    JOIN conteudos c ON i.conteudo_id = c.conteudo_id
    JOIN categorias cat ON c.categoria_id = cat.categoria_id
    WHERE i.tipo_interacao IN ('início', 'conclusão');
    ```
- **Periodicidade:**
  - Agregação histórica consolidada, segmentável pelo filtro de categoria no dashboard.
- **Interpretação:**
  - Categorias com alto volume de início, mas baixa taxa de conclusão (ex: conteúdos longos ou com didática deficitária) demandam revisão curricular e quebra em módulos menores. Categorias com alta taxa de conclusão representam padrões de excelência instrucional.

---

### KPI 4: Taxa de Conversão das Recomendações

- **Nome:** Taxa de Conversão do Motor Vetorial de Recomendação
- **Objetivo:** Medir a assertividade do algoritmo de recomendação semântica ($Ivis$, $Icur$, $Iconc$), verificando se o estudante efetivamente consumiu um conteúdo que lhe foi sugerido após a data da recomendação.
- **Fórmula:**
  $$\text{Taxa de Conversão (\%)} = \left( \frac{\sum \text{conversao}}{\text{Total de Recomendações Geradas}} \right) \times 100$$
  Onde $\text{conversao} = 1$ se existir interação do usuário naquele conteúdo com $\text{data\_hora} > \text{data\_geracao}$.
- **Fonte dos Dados:**
  - View SQL: `vw_recommendation_conversion`
  - Tabelas de Origem: `recomendacoes` $\bowtie$ `interacoes`
  - Definição DDL:
    ```sql
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
    ```
- **Periodicidade:**
  - Calculada por safra de geração de recomendações.
- **Interpretação:**
  - É o indicador primário de ROI técnico do sistema de IA. Uma taxa elevada comprova que os embeddings multilíngues (`MiniLM-L12-v2`) e a ponderação por afinidade temática estão gerando sugestões altamente relevantes para o perfil de cada estudante.

---

## 3. Perguntas de Negócio Respondidas pelo Dashboard

1. **Pergunta 1 (Alocação Estratégica de Conteúdo):**  
   *Quais categorias apresentam alto interesse inicial (muitas visualizações), mas sofrem com desistência prematura (baixa taxa de conclusão), indicando a necessidade de reformulação de material?*  
   - **Como responder no dashboard:** Cruzar o gráfico de linhas (*Visualizações por Categoria*) com o gráfico de barras (*Taxa de Conclusão por Categoria*).

2. **Pergunta 2 (Eficácia do Sistema de Inteligência Artificial):**  
   *O motor de recomendação vetorial personalizado está gerando valor mensurável na jornada dos discentes?*  
   - **Como responder no dashboard:** Avaliar o cartão de **Taxa de Conversão das Recomendações** e verificar sua resposta após filtragem temporal por períodos.
