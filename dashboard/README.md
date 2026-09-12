# Tutorial: Execução e Importação do Dashboard no Apache Superset (RF13)

Este tutorial apresenta o procedimento completo para inicializar o Apache Superset via Docker e importar o dashboard com os KPIs do Desafio Prático 1.

---

## 1. Inicialização dos Serviços via Docker Compose

O ambiente containerizado do projeto inclui o **PostgreSQL (com pgvector)**, **MongoDB** e o **Apache Superset** pré-configurados.

1. Certifique-se de que o arquivo `.env` esteja criado na raiz:
   ```powershell
   copy .env.example .env
   ```

2. Inicie os containers com o Docker Compose:
   ```powershell
   docker compose up -d
   ```

3. O container do Superset (`superset`) executa automaticamente na inicialização:
   - Atualização das tabelas de metadados (`superset db upgrade`);
   - Criação do usuário administrador padrão;
   - Inicialização de papéis e permissões (`superset init`);
   - Inicialização do servidor web na porta **8088**.

> **Nota:** Na primeira inicialização, o Superset pode levar de 30 a 60 segundos para finalizar as migrações internas.

---

## 2. Pré-requisitos de Dados

Antes de analisar o dashboard, execute o pipeline do projeto ao menos uma vez para popular o banco de dados com os dados tratados, embeddings e recomendações:

```powershell
python -m src.main
```

As 3 views obrigatórias de apoio aos KPIs já são criadas automaticamente no PostgreSQL pelo script `sql/criar_banco.sql`:
- `vw_content_views_by_category`
- `vw_content_completion_by_category`
- `vw_recommendation_conversion`

---

## 3. Acesso ao Apache Superset

1. Abra o navegador e acesse:
   ```text
   http://localhost:8088
   ```
2. Realize o login com as credenciais administrativas padrão:
   - **Username:** `admin`
   - **Password:** `admin`

---

## 4. Disponibilização do Dashboard

### 4.1 Importação Automática (Zero Configuração)
O script `dashboard/sync_database.py` é acionado **automaticamente durante a inicialização do container**. Ele:
1. Extrai dinamicamente o UUID e o nome do banco diretamente do arquivo `.zip` presente em `dashboard/`, conectando o Superset ao PostgreSQL com as credenciais definidas no `.env`;
2. Importa o dashboard completo via CLI (`superset import-dashboards`);
3. Marca o painel como **publicado** (`published: true`).

Ao acessar `http://localhost:8088` e fazer login, basta clicar em **Dashboards**: o painel **"Dashboard - Desafio 3"** já estará pronto e carregando dados reais!

### 4.2 Reimportação Manual via Interface Web (Opcional)
Caso queira reimportar o dashboard manualmente através da interface web do Superset:

1. No menu superior direito, clique em **Settings (ícone de engrenagem) → Import Dashboards**;
2. Selecione o arquivo `dashboard/dashboard_export.zip` (ou qualquer `.zip` gerado pelo Superset);
3. **Por que o Superset solicita a senha do banco?**  
   Por diretriz de segurança de arquitetura do Apache Superset, senhas de banco de dados **nunca são exportadas em texto claro dentro de arquivos ZIP**. Por isso, a interface exibe a mensagem informativa:  
   > *"The passwords for the databases below are needed in order to import them together with the dashboards..."*
4. No campo de senha do banco **Other**, digite a senha do PostgreSQL configurada no seu `.env` (`POSTGRES_PASSWORD`, por exemplo `1234`).  
   *(Como o container já possui a conexão `Other` pré-cadastrada com UUID correspondente, o Superset aceita a importação/sobrescrita e valida a conexão imediatamente com sucesso).*
5. Clique em **Import**.

---

## 5. Visualização e Verificação dos Elementos

Acesse o menu **Dashboards** e abra o painel **"Dashboard - Desafio 3"**.

Verifique se todos os componentes obrigatórios estão presentes e funcionais:

### Estrutura do Dashboard
```text
Dashboard — Desafio 3
│
├── Filtros Nativos (Interativos)
│   ├── Filtro de Período (Time Range)
│   └── Filtro de Categoria (Dropdown / Select)
│
├── Cartões Executivos (Métricas Operacionais)
│   ├── Total de Usuários Registrados
│   ├── Total de Conteúdos Cadastrados
│   └── Média de Tempo por Interação (min)
│
├── Indicadores de Tomada de Decisão (KPIs - RF12)
│   ├── KPI 1: Usuários Ativos no Período (Big Number)
│   ├── KPI 2: Visualizações por Categoria ao Longo do Tempo (Linhas / Série Temporal)
│   ├── KPI 3: Taxa de Término / Conclusão por Categoria (Barras Comparativas)
│   └── KPI 4: Taxa de Conversão das Recomendações (Big Number)
```

---

## 6. Perguntas de Negócio Respondidas pelo Dashboard (RF13)

1. **Pergunta 1 (Priorização de Conteúdo):**  
   *Quais categorias temáticas apresentam maior interesse inicial (visualizações) versus maior taxa de conclusão efetiva, indicando quais cursos devem receber novos investimentos de produção?*  
   - **Como responder:** Compare o gráfico de linhas temporal (*Visualizações por Categoria*) com o gráfico de barras (*Taxa de Conclusão por Categoria*).

2. **Pergunta 2 (Efetividade do Motor de IA):**  
   *Qual é o percentual de recomendações geradas pelo motor vetorial que efetivamente foram convertidas em interações reais pelos alunos após a recomendação?*  
   - **Como responder:** Observe o cartão executivo **Taxa de Conversão das Recomendações** e aplique o filtro de período para avaliar a evolução após novas safras de recomendações.
