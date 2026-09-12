# Tutorial: Importação do Dashboard no Apache Superset

Este tutorial apresenta o procedimento para importar o arquivo de exportação do dashboard no Apache Superset.

## Pré-requisitos

Antes de realizar a importação, certifique-se de que:

* O Apache Superset esteja em execução;
* O banco de dados utilizado pelo dashboard esteja configurado no Superset;
* As tabelas e views utilizadas pelos KPIs estejam disponíveis no banco de dados;
* O arquivo `dashboard_export_20260912T164432.zip` esteja disponível para importação.

> **Importante:** o arquivo exportado contém a configuração do dashboard. Dependendo da forma como o ambiente do Superset foi configurado, pode ser necessário criar ou configurar previamente a conexão com o banco de dados e os datasets utilizados pelos gráficos.

---

## 1. Acessar o Apache Superset

Abra o Apache Superset no navegador e realize o login.

---

## 2. Acessar a área de importação

No menu superior do Apache Superset, acesse:

```text
Settings
    ↓
Import Dashboards
```

Em algumas versões do Superset, a opção pode estar disponível na área de:

```text
Settings
    ↓
Import / Export
```

---

## 3. Selecionar o arquivo

Clique na opção para selecionar ou enviar um arquivo e escolha:

```text
dashboard_export_20260912T164432.zip
```

---

## 4. Realizar a importação

Após selecionar o arquivo, clique em:

```text
Import
```

O Apache Superset iniciará o processo de importação das configurações presentes no arquivo.

Aguarde até que o processo seja concluído.

---

## 5. Verificar o Dashboard

Após a importação, acesse:

```text
Dashboards
    ↓
Dashboards
```

Localize o dashboard importado e abra-o.

Verifique se os seguintes elementos foram importados corretamente:

* Total de Usuários;
* Média do Tempo por Interação;
* Total de Conteúdos;
* Usuários Ativos;
* Visualizações por Categoria;
* Taxa de Conclusão por Categoria;
* Taxa de Conversão das Recomendações;
* Filtro de período;
* Filtro de categoria.


# Resultado Esperado

Após concluir a importação e configurar corretamente as fontes de dados, o dashboard deverá apresentar os KPIs e filtros interativos para análise dos dados.

```text
Dashboard
│
├── Filtro de Período
│
├── Filtro de Categoria
│
├── Total de Usuários
│
├── Média do Tempo por Interação
│
├── Total de Conteúdos
│
├── Usuários Ativos
│
├── Visualizações por Categoria
│
├── Taxa de Conclusão por Categoria
│
└── Taxa de Conversão das Recomendações
```
