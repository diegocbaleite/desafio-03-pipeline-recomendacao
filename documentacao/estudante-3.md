# Estudante 3 — Métricas, consultas e dashboard no Superset

Responsável: **Gabriel André de Siqueira Nonato**

## Status

Parte concluída e integrada à branch `feature/estudante-3-metricas-superset`.

## Escopo implementado

Descrição:

* **RF12 — Produção de métricas e KPIs:** definição e implementação de métricas operacionais e de tomada de decisão para análise dos dados da plataforma.
* **RF13 — Dashboard no Apache Superset:** criação de um dashboard interativo para visualização dos KPIs e análise dos dados por período e categoria, respondendo a perguntas de negócio e justificando a escolha dos gráficos.

---

## 1. Produção de métricas e KPIs (RF12)

Foram definidos e implementados quatro indicadores para análise da utilização da plataforma, consumo de conteúdos e efetividade das recomendações.

Os KPIs implementados foram:

1. Usuários Ativos em um Período;
2. Número de Visualizações por Categoria;
3. Taxa de Conclusão de Conteúdo por Categoria;
4. Taxa de Conversão das Recomendações.

---

### 1.1 Usuários Ativos em um Período

**Objetivo:** identificar a quantidade de usuários distintos que realizaram pelo menos uma interação durante o período selecionado.

**Fórmula:**

```sql
COUNT(DISTINCT usuario_id)
```

**Fonte dos dados:**

Tabela:

```text
interacoes
```

Campos utilizados:

* `usuario_id`;
* `data_hora`.

**Periodicidade:**

```text
Por demanda / Tempo real (orientada pelo filtro temporal 'Time Range' no dashboard).
```

**Interpretação:**

O indicador apresenta a quantidade de usuários únicos que engajaram na plataforma no período analisado, servindo como termômetro da tração da plataforma educacional.

---

### 1.2 Número de Visualizações por Categoria

**Objetivo:** identificar a quantidade de visualizações realizadas em conteúdos de cada categoria ao longo do tempo.

**Fórmula:**

```text
Número de Visualizações = COUNT(*)
```

São consideradas apenas as interações do tipo `visualização`.

**Fonte dos dados:**

Tabelas:

* `interacoes`;
* `conteudos`;
* `categorias`.

Para disponibilizar os dados no Apache Superset, foi criada a seguinte view no PostgreSQL (registrada em `sql/criar_banco.sql`):

```sql
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
```

A view relaciona as interações com os conteúdos e suas respectivas categorias.

**Periodicidade:**

```text
Mensal na agregação do gráfico de linhas temporal, com atualização contínua sob demanda na view.
```

**Interpretação:**

Permite avaliar quais áreas temáticas concentram o maior interesse inicial dos alunos e identificar tendências sazonais de interesse.

---

### 1.3 Taxa de Conclusão de Conteúdo por Categoria

**Objetivo:** identificar a proporção de conteúdos concluídos em relação aos conteúdos iniciados para cada categoria temática.

**Fórmula:**

```text
Taxa de Conclusão =
(Número de Conteúdos Concluídos / Número de Conteúdos Iniciados) × 100
```

**Fonte dos dados:**

Tabelas:

* `interacoes`;
* `conteudos`;
* `categorias`.

São consideradas as interações dos tipos:

* `início`;
* `conclusão`.

Foi criada a seguinte view no PostgreSQL (registrada em `sql/criar_banco.sql`):

```sql
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
```

No Apache Superset, a métrica foi calculada utilizando:

```sql
(
    COUNT(*) FILTER (
        WHERE tipo_interacao = 'conclusão'
    )::NUMERIC
    /
    NULLIF(
        COUNT(*) FILTER (
            WHERE tipo_interacao = 'início'
        ),
        0
    )
) * 100
```

A utilização de `NULLIF` evita erros de divisão por zero.

**Periodicidade:**

```text
Agregação contínua/diária por categoria temática.
```

**Interpretação:**

Mede a retenção pedagógica e o engajamento de término de cursos. Taxas baixas sinalizam conteúdos excessivamente difíceis, longos ou com problemas didáticos.

---

### 1.4 Taxa de Conversão das Recomendações

**Objetivo:** avaliar a efetividade real das recomendações geradas pelo algoritmo de IA da plataforma.

Uma recomendação é considerada convertida quando o usuário realiza uma interação com o conteúdo recomendado em instante posterior à geração da recomendação (`data_hora > data_geracao`).

**Fórmula:**

```text
Taxa de Conversão =
(Recomendações Convertidas / Total de Recomendações) × 100
```

**Fonte dos dados:**

Tabelas:

* `recomendacoes` (persistidas pelo Estudante 2 no RF11);
* `interacoes`.

Foi criada a seguinte view no PostgreSQL (registrada em `sql/criar_banco.sql`):

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

O campo `conversao` possui os seguintes valores:

```text
1 = Recomendação convertida
0 = Recomendação não convertida
```

No Apache Superset, a taxa de conversão foi calculada utilizando:

```sql
SUM(conversao)::FLOAT
/
NULLIF(COUNT(recomendacao_id), 0)
* 100
```

**Periodicidade:**

```text
Atualização por safra de recomendações geradas / consulta em tempo real sob demanda.
```

**Interpretação:**

Indica se as sugestões personalizadas por similaridade semântica e histórico ($Ivis, Icur, Iconc$) de fato despertam a ação dos usuários.

---

## 2. Dashboard no Apache Superset (RF13)

Foi desenvolvido um dashboard no Apache Superset para centralizar a visualização dos indicadores operacionais e estratégicos.

### 2.1 Visualizações implementadas

| KPI / Métrica                         | Visualização           | Natureza do Dado |
| ------------------------------------- | ---------------------- | ---------------- |
| Total de Usuários                     | Big Number             | Escalar Acumulado|
| Média de Tempo por Interação          | Big Number             | Escalar Médio    |
| Total de Conteúdos                    | Big Number             | Escalar Acumulado|
| Usuários Ativos em um Período         | Big Number             | Escalar no Tempo |
| Número de Visualizações por Categoria | Time-series Line Chart | Temporal Contínuo|
| Taxa de Conclusão por Categoria       | Bar Chart              | Categórico       |
| Taxa de Conversão das Recomendações   | Big Number             | Percentual Global|

---

### 2.2 Perguntas de Negócio Respondidas pelo Dashboard

O dashboard foi projetado para responder especificamente a duas perguntas estratégicas da gestão educacional:

1. **Pergunta 1 (Alocação de Investimentos e Qualidade Pedagógica):**  
   *Quais categorias educacionais possuem alto volume de interesse inicial, mas baixa taxa de conclusão, demandando reformulação didática antes de novos investimentos?*  
   - **Resposta:** O gestor cruza o gráfico temporal de *Visualizações por Categoria* com o gráfico de barras da *Taxa de Conclusão*. Categorias com muitas visualizações e baixa conclusão exigem revisão metodológica, enquanto categorias com alta conclusão e visualizações crescentes são candidatas ideais a expansão de catálogo.

2. **Pergunta 2 (Retorno do Investimento do Motor de IA):**  
   *O sistema de recomendação por embeddings vetoriais está realmente gerando engajamento adicional mensurável após ser entregue aos alunos?*  
   - **Resposta:** O cartão de *Taxa de Conversão das Recomendações* isola exatamente se os usuários consumiram os itens recomendados após a sua geração, validando o impacto do motor construído pelo Estudante 2.

---

### 2.3 Justificativa da Escolha dos Tipos de Gráficos

A escolha de cada componente visual considerou estritamente a natureza dos dados e a comunicação executiva:

* **Big Number (Cartões de Indicadores):** Utilizado para métricas escalares agregadas (*Total de Usuários, Conteúdos, Média de Tempo, Usuários Ativos e Conversão*). Permite leitura cognitiva instantânea sem exigir interpretação de eixos.
* **Gráfico de Linhas Temporal (`echarts_timeseries_line`):** Utilizado para o *Número de Visualizações por Categoria*. É o padrão ideal para dados sequenciais contínuos no tempo, facilitando a identificação de tendências, picos e quedas sazonais por categoria.
* **Gráfico de Barras (`echarts_timeseries_bar`):** Utilizado para a *Taxa de Conclusão por Categoria*. É a visualização mais indicada para comparar grandezas discretas entre categorias nominais não ordenadas, permitindo ranqueamento visual imediato.

---

## 3. Filtros interativos

* **Filtro de Período (`Time Range`):** Permite fatiar dinamicamente os dados por intervalos temporais (últimos dias, meses ou intervalos customizados).
* **Filtro de Categoria (`Value / Select`):** Permite isolar uma ou mais categorias temáticas simultaneamente em todos os gráficos correlacionados.

---

## 4. Views criadas no PostgreSQL

As views criadas no PostgreSQL e consolidadas no arquivo `sql/criar_banco.sql` são:

| View                                | Finalidade                                                    |
| ----------------------------------- | ------------------------------------------------------------- |
| `vw_content_views_by_category`      | Disponibilizar visualizações de conteúdos por categoria       |
| `vw_content_completion_by_category` | Disponibilizar interações de início e conclusão por categoria |
| `vw_recommendation_conversion`      | Identificar recomendações convertidas pós-geração             |

---

## 5. Importação e Execução do Dashboard

O dashboard foi exportado para o arquivo:
```text
dashboard/dashboard_export.zip
```

Com o container do Superset adicionado ao `docker-compose.yml`, basta executar:
```powershell
docker compose up -d
```
Acessar `http://localhost:8088` (login: `admin` / `admin`) e importar o arquivo zip em **Settings → Import Dashboards**. O passo a passo completo e detalhado encontra-se em [dashboard/README.md](../dashboard/README.md).

---

## 6. Resultado

Foram plenamente atendidos os requisitos **RF12** e **RF13**:
* 3 métricas operacionais e 4 KPIs de decisão modelados com suas respectivas fichas técnicas completas;
* 3 Views relacionais criadas no PostgreSQL;
* Container Docker do Superset integrado ao ecossistema da aplicação;
* Dashboard interativo com 5 cartões, gráfico de linhas temporal, gráfico de barras comparativo e 2 filtros nativos;
* Suíte de testes automatizados integrada em `tests/test_dashboard_metricas.py`.
