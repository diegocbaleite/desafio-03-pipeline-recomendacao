# 🎓 Desafio 03 — Desafio Prático 1

## Pipeline de Recomendação e Dashboard de Conteúdos Educacionais

Projeto desenvolvido no **FIC_DEV — Programador de Sistemas com IA**, no módulo **Fundamentos de Dados para IA**.

- **Desafio oficial:** Desafio Prático 1 — Fundamentos de Dados para IA
- **Repositório da equipe:** Desafio 03
- **Carga horária recomendada:** 12 horas
- **Modalidade:** equipe de 3 estudantes
- **Versão do enunciado:** 1.0 — 2026

---

## 👨‍💻 Equipe

| Integrante | Responsabilidade inicial | Branch |
|---|---|---|
| **Diego Assunção Leite** | Ingestão, tratamento e PostgreSQL | `feature/estudante-1-ingestao-postgresql` |
| **Gabriel André de Siqueira Nonato** | MongoDB, embeddings e recomendações | `feature/estudante-2-mongodb-embeddings-recomendacoes` |
| **Gabriel Moreira Branco** (`@Gabriel-M-Branco`) | Métricas, consultas e dashboard no Superset | `feature/estudante-3-metricas-superset` |

> A divisão serve apenas como organização inicial do trabalho. Todos os integrantes devem compreender e saber explicar a solução completa.

---

## 🎯 Objetivo do projeto

Construir um **pipeline reproduzível de dados** para uma plataforma fictícia de conteúdos educacionais, integrando todo o fluxo desde a leitura dos arquivos de origem até a disponibilização de indicadores em um dashboard.

O produto final deverá integrar:

- ingestão e validação de arquivos CSV e JSON;
- tratamento e padronização dos dados;
- armazenamento estruturado no PostgreSQL;
- armazenamento semiestruturado no MongoDB;
- geração e persistência de embeddings no PostgreSQL com `pgvector`;
- busca por similaridade semântica;
- geração e persistência de recomendações;
- métricas e KPIs;
- dashboard no Apache Superset;
- registros de execução, práticas de DataOps e documentação do uso de Inteligência Artificial.

---

## 🧩 Situação-problema

Uma plataforma fictícia disponibiliza cursos, vídeos, artigos, podcasts e outros materiais educacionais. Os dados estão distribuídos em arquivos e formatos diferentes, dificultando a análise do comportamento dos usuários, a identificação de conteúdos procurados, a avaliação da qualidade dos materiais, a geração de recomendações e a criação de indicadores para apoiar decisões.

A solução deste projeto organiza esses dados em um fluxo integrado e reproduzível.

---

## 🏗️ Arquitetura mínima

```text
┌─────────────────────────────┐
│         FONTES              │
│  catalogo.csv               │
│  interacoes.json            │
│  comentarios.json           │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      INGESTÃO / PYTHON      │
│ leitura                     │
│ validação                   │
│ tratamento                  │
│ classificação de registros │
│ logs e resumo da ingestão   │
└──────────────┬──────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │   MongoDB    │
│ estruturados │  │ comentários  │
│ métricas     │  │ avaliações   │
└──────┬───────┘  └──────────────┘
       │
       ▼
┌─────────────────────────────┐
│ pgvector / EMBEDDINGS       │
│ título + descrição          │
│ busca semântica             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ MOTOR DE RECOMENDAÇÃO       │
│ Ivis + Icur + Iconc         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ MÉTRICAS / KPIs             │
│ tabelas ou views PostgreSQL │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      APACHE SUPERSET        │
│ dashboard e filtros         │
└─────────────────────────────┘
```

---

## 📂 Fontes de dados

O desafio utiliza pelo menos três fontes fictícias, preservando os arquivos originais:

### `catalogo.csv`

Catálogo de conteúdos educacionais contendo campos como `conteudo_id`, título, tipo, categoria, nível, carga horária, data de publicação, descrição e autor.

### `interacoes.json`

Histórico das interações dos usuários com os conteúdos, incluindo usuário, conteúdo, tipo de interação, data/hora, tempo consumido, percentual de conclusão e avaliação atribuída.

### `comentarios.json`

Comentários e avaliações semiestruturadas, incluindo usuário, conteúdo, avaliação, comentário, tags e data.

---

## ✅ Requisitos funcionais obrigatórios

| RF | Requisito | Situação |
|---|---|---|
| **RF01** | Inicialização por `python -m src.main`, configuração JSON/YAML, conexões separadas e dados sensíveis fora do código | 🟡 Em desenvolvimento |
| **RF02** | Leitura do CSV do catálogo e dos JSONs de interações e comentários | 🟡 Branch Estudante 1 |
| **RF03** | Classificação em válido, inválido, incompleto ou duplicado, com registro do motivo | 🟡 Branch Estudante 1 |
| **RF04** | Tratamento, padronização, conversões, ausentes, duplicidades e preservação dos originais | 🟡 Branch Estudante 1 |
| **RF05** | Geração de `resumo_ingestao.json` com contagens e tempo de processamento | 🟡 Branch Estudante 1 |
| **RF06** | Persistência estruturada no PostgreSQL com PK, FK, integridade e transações | 🟡 Branch Estudante 1 |
| **RF07** | Persistência e consultas dos dados semiestruturados no MongoDB | ⚪ Planejado |
| **RF08** | Embeddings de título + descrição armazenados no PostgreSQL com `pgvector` | ⚪ Planejado |
| **RF09** | Busca semântica configurável, demonstrada com pelo menos 3 consultas | ⚪ Planejado |
| **RF10** | Geração de recomendações considerando visualizações, avaliações/curtidas e conclusão | ⚪ Planejado |
| **RF11** | Persistência das recomendações no PostgreSQL | ⚪ Planejado |
| **RF12** | No mínimo 2 métricas operacionais e 2 KPIs orientados à decisão | ⚪ Planejado |
| **RF13** | Dashboard no Apache Superset com 3 cartões, barras, linhas e 2 filtros | ⚪ Planejado |
| **RF14** | Registro de execução, rejeições, falhas e tempos das principais etapas | 🟡 Em desenvolvimento |

> O status acima representa o estágio atual do repositório. Funcionalidades em branches só serão consideradas integradas quando passarem por revisão e merge na `main`.

---

## 🧠 Regra de recomendação

A fórmula exigida pelo enunciado é:

```text
Pontuação = ((Ivis + Icur) / 2) × 100 × Iconc
```

Onde:

- **Ivis** — índice de visualizações/afinidade temática, variando de `0.0` a `1.0`;
- **Icur** — índice de curtidas e avaliações positivas, considerando nota igual ou superior a 4, variando de `0.0` a `1.0`;
- **Iconc** — filtro binário: `0` se o conteúdo já foi concluído e `1` se ainda não foi concluído.

O enunciado registra as classificações como **Positivo (Pontuação >= 70)**, **Estável (40 > Pontuação < 70)** e **Negativo (Pontuação <= 40 ou Iconc = 0)**. A expressão da faixa “Estável” será mantida documentada e sua interpretação prática será validada pela equipe antes da versão final.

---

## 📊 Métricas, KPIs e dashboard

A solução deverá disponibilizar no PostgreSQL tabelas ou views para uso no Apache Superset.

O dashboard deverá conter no mínimo:

- 3 cartões de indicadores;
- 1 gráfico de barras;
- 1 gráfico de linhas;
- 2 filtros interativos;
- respostas para pelo menos 2 perguntas de negócio definidas pela equipe.

Cada KPI será documentado com **nome, objetivo, fórmula, fonte dos dados, periodicidade e interpretação**.

---

## 📁 Estrutura do repositório

```text
.
├── config/
│   └── config.yaml
├── dados/
│   ├── brutos/
│   └── processados/
├── dashboard/
│   └── evidencias/
├── documentacao/
│   ├── arquitetura.pdf
│   ├── modelo_de_dados.pdf
│   ├── kpis.md
│   └── uso_da_ia.md
├── logs/
├── mongodb/
│   └── consultas.js
├── sql/
│   ├── criar_banco.sql
│   └── consultas.sql
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── ingestao/
│   ├── database/
│   ├── embeddings/
│   ├── recomendacao/
│   └── metricas/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

A estrutura pode evoluir durante a implementação, mantendo código organizado, dependências registradas e responsabilidades separadas.

---

## 🌿 Estratégia de branches

```text
main
├── feature/estudante-1-ingestao-postgresql
├── feature/estudante-2-mongodb-embeddings-recomendacoes
└── feature/estudante-3-metricas-superset
```

A `main` representa a versão integrada e estável. Cada integrante desenvolve inicialmente em sua branch e as alterações são revisadas por Pull Request antes da integração.

---

## 🛠️ Tecnologias previstas

- Python 3
- Pandas
- PostgreSQL
- `psycopg2`
- MongoDB
- `pymongo`
- `pgvector`
- Sentence Transformers
- YAML
- `python-dotenv`
- Apache Superset
- Git e GitHub
- Pytest

---

## ⚙️ Configuração do ambiente

### 1. Clonar o repositório

```bash
git clone https://github.com/diegocbaleite/desafio-03-pipeline-recomendacao.git
cd desafio-03-pipeline-recomendacao
```

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows:

```powershell
.venv\Scripts\activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com os parâmetros locais do PostgreSQL e MongoDB. O arquivo `.env` não deve ser versionado.

### 5. Preparar o PostgreSQL

Utilize o script:

```text
sql/criar_banco.sql
```

A solução utilizará PostgreSQL para os dados estruturados e `pgvector` para os vetores de embeddings.

### 6. Executar o pipeline

O comando oficial de execução é:

```bash
python -m src.main
```

---

## 📝 DataOps e registros de execução

O projeto adotará práticas básicas de DataOps, incluindo organização em diretórios, controle de versão, configuração externa, dependências registradas, tratamento de erros, logs e instruções de reprodução.

Os logs deverão permitir identificar:

- início e término do processamento;
- arquivos processados;
- quantidade de registros lidos;
- registros rejeitados;
- falhas de conexão;
- falhas na geração de embeddings;
- falhas de persistência;
- tempo de execução das principais etapas;
- origem e causa provável dos problemas.

---

## 🤖 Uso de Inteligência Artificial

A Inteligência Artificial pode apoiar explicação de erros, SQL, modelagem, validações, tratamento dos dados, revisão de código, métricas, embeddings e documentação. A equipe permanece responsável por **testar, compreender e justificar** tudo o que entregar.

O registro detalhado será mantido em:

```text
documentacao/uso_da_ia.md
```

Esse documento deverá registrar a ferramenta utilizada, exemplos de solicitações, decisões apoiadas pela IA, erros ou inadequações encontrados e alterações realizadas pela equipe.

---

## 📦 Entregáveis obrigatórios

Ao final, a equipe deverá apresentar:

1. código de ingestão;
2. arquivos de dados utilizados;
3. modelo conceitual e lógico;
4. scripts do PostgreSQL;
5. documentos e consultas do MongoDB;
6. implementação da busca vetorial;
7. implementação da recomendação;
8. exportação/evidências do dashboard do Superset;
9. documentação para instalação e execução.

---

## ⚠️ Decisões e limitações

- Os dados utilizados no projeto são fictícios.
- Os arquivos brutos devem ser preservados sem alterações.
- Credenciais e senhas ficam fora do código-fonte e fora do Git.
- O repositório está em desenvolvimento e os requisitos ainda não integrados estão explicitamente marcados como planejados.
- A faixa “Estável” da regra de classificação será validada com o professor/equipe por apresentar uma expressão ambígua no enunciado.
- As decisões de tratamento, modelagem, embeddings, métricas e arquitetura serão atualizadas na documentação conforme a implementação for consolidada.

---

## 🎤 Apresentação final

A apresentação deverá ter no máximo **10 minutos**, organizada da seguinte forma:

| Tempo | Conteúdo |
|---|---|
| 2 min | Problema e arquitetura |
| 3 min | Ingestão e armazenamento |
| 2 min | Busca vetorial e recomendação |
| 2 min | Dashboard e principais descobertas |
| 1 min | Dificuldades, limitações e uso da IA |

Qualquer integrante poderá ser solicitado a explicar qualquer parte da solução.

---

## 📌 Status do projeto

🚧 **Em desenvolvimento**

A estrutura base está na `main`. A implementação está sendo realizada pelas três branches da equipe e será integrada por Pull Requests após revisão e testes.