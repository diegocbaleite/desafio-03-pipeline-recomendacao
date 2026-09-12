# Estudante 3 — Métricas, consultas e dashboard no Superset

Responsável: **Gabriel André de Siqueira Nonato**

## Status

Parte concluída e integrada à branch `feature/estudante-3-metricas-superset`.

## Escopo implementado

Descrição:

* **RF12 — Produção de métricas e KPIs:** definição e implementação de métricas para análise dos dados da plataforma.
* **RF13 — Dashboard no Apache Superset:** criação de um dashboard interativo para visualização dos KPIs e análise dos dados por período e categoria.

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

**Objetivo:** identificar a quantidade de usuários que realizaram pelo menos uma interação durante o período selecionado.

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

**Interpretação:**

O indicador apresenta a quantidade de usuários distintos que realizaram interações durante o período selecionado.

---

### 1.2 Número de Visualizações por Categoria

**Objetivo:** identificar a quantidade de visualizações realizadas em conteúdos de cada categoria.

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

Para disponibilizar os dados no Apache Superset, foi criada a seguinte view:

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

---

### 1.3 Taxa de Conclusão de Conteúdo por Categoria

**Objetivo:** identificar a proporção de conteúdos concluídos em relação aos conteúdos iniciados para cada categoria.

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

Foi criada a seguinte view:

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

---

### 1.4 Taxa de Conversão das Recomendações

**Objetivo:** avaliar a efetividade das recomendações realizadas pela plataforma.

Uma recomendação é considerada convertida quando o usuário realiza uma interação com o conteúdo recomendado após a geração da recomendação.

**Fórmula:**

```text
Taxa de Conversão =
(Recomendações Convertidas / Total de Recomendações) × 100
```

**Fonte dos dados:**

Tabelas:

* `recomendacoes`;
* `interacoes`.

Foi criada a seguinte view:

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

---

## 2. Dashboard no Apache Superset (RF13)

Foi desenvolvido um dashboard no Apache Superset para centralizar a visualização dos indicadores definidos no RF12.

O dashboard permite analisar os dados de forma visual e interativa.

### 2.1 Visualizações implementadas

Foram implementadas as seguintes visualizações:

| KPI                                   | Visualização           |
| ------------------------------------- | ---------------------- |
| Usuários Ativos em um Período         | Big Number             |
| Número de Visualizações por Categoria | Time-series Line Chart |
| Taxa de Conclusão por Categoria       | Bar Chart              |
| Taxa de Conversão das Recomendações   | Big Number             |

---

### 2.2 Usuários Ativos

O indicador apresenta a quantidade de usuários distintos que realizaram interações no período selecionado.

**Métrica:**

```sql
COUNT(DISTINCT usuario_id)
```

A análise pode ser alterada por meio do filtro de período do dashboard.

---

### 2.3 Visualizações por Categoria

Foi utilizado um gráfico de linhas para apresentar a evolução do número de visualizações das categorias ao longo do tempo.

Configuração utilizada:

| Configuração    | Valor                          |
| --------------- | ------------------------------ |
| Dataset         | `vw_content_views_by_category` |
| Coluna temporal | `data_hora`                    |
| Métrica         | `COUNT(*)`                     |
| Série           | `categoria`                    |
| Granularidade   | Mês                            |

---

### 2.4 Taxa de Conclusão por Categoria

Foi utilizado um gráfico de barras para comparar a taxa de conclusão entre as categorias.

Configuração utilizada:

| Configuração | Valor                               |
| ------------ | ----------------------------------- |
| Dataset      | `vw_content_completion_by_category` |
| Dimensão     | `categoria`                         |
| Métrica      | Taxa de Conclusão                   |

---

### 2.5 Taxa de Conversão das Recomendações

Foi utilizado o componente **Big Number** para apresentar diretamente a taxa de conversão das recomendações.

Configuração utilizada:

| Configuração | Valor                               |
| ------------ | ----------------------------------- |
| Dataset      | `vw_recommendation_conversion`      |
| Visualização | Big Number                          |
| Métrica      | Taxa de Conversão das Recomendações |

---

## 3. Filtros implementados

Foram implementados filtros para permitir a análise interativa dos dados do dashboard.

### 3.1 Filtro de Período

Foi utilizado o filtro do tipo:

```text
Time Range
```

Esse filtro permite selecionar um intervalo de tempo para análise dos indicadores que possuem informações temporais.

Exemplos:

* últimos dias;
* último mês;
* último ano;
* período personalizado.

---

### 3.2 Filtro de Categoria

Foi utilizado o filtro do tipo:

```text
Value
```

Utilizando a coluna:

```text
categoria
```

O filtro permite selecionar uma ou mais categorias para restringir os dados apresentados nos gráficos compatíveis.

---

## 4. Views criadas

Para facilitar a integração entre o PostgreSQL e o Apache Superset, foram criadas as seguintes views:

| View                                | Finalidade                                                    |
| ----------------------------------- | ------------------------------------------------------------- |
| `vw_content_views_by_category`      | Disponibilizar visualizações de conteúdos por categoria       |
| `vw_content_completion_by_category` | Disponibilizar interações de início e conclusão por categoria |
| `vw_recommendation_conversion`      | Identificar recomendações convertidas                         |

---

## 5. Importação do Dashboard

O dashboard desenvolvido foi exportado para o arquivo:

```text
dashboard_export_20260912T164432.zip
```

Para importá-lo no Apache Superset:

1. Acesse o Apache Superset;
2. Acesse a área de importação de dashboards;
3. Selecione o arquivo `dashboard_export_20260912T164432.zip`;
4. Clique em **Import**;
5. Após a importação, acesse a lista de dashboards e verifique o dashboard importado.

### Observação

Antes da utilização do dashboard, é necessário garantir que:

* o banco de dados esteja configurado no Apache Superset;
* as tabelas necessárias estejam disponíveis;
* as views utilizadas pelos KPIs tenham sido criadas;
* os datasets estejam corretamente configurados.

---

## 6. Resultado

Como resultado, foram implementados os requisitos **RF12** e **RF13**, contemplando:

* definição de quatro KPIs;
* criação de consultas e views para disponibilização dos dados;
* integração dos dados com o Apache Superset;
* criação de gráficos e indicadores;
* implementação de filtro de período;
* implementação de filtro de categoria;
* criação de um dashboard interativo para análise dos dados.
