# 🎓 Desafio 03 — Pipeline de Recomendação e Dashboard de Conteúdos Educacionais

Projeto do FIC_DEV voltado à construção de um pipeline de dados para conteúdos educacionais, com ingestão e tratamento de dados, persistência em PostgreSQL e MongoDB, embeddings com pgvector, mecanismo de recomendação, métricas e dashboard no Apache Superset.

## 👨‍💻 Equipe

- **Diego Assunção Leite** — Ingestão, tratamento e PostgreSQL
- **Gabriel André de Siqueira Nonato** — MongoDB, embeddings e recomendações
- **Gabriel Moreira Branco** — Métricas, consultas e dashboard no Superset

## 🌿 Estratégia de branches

- `main` — integração e versão estável
- `feature/estudante-1-ingestao-postgresql` — ingestão, validação, tratamento e PostgreSQL
- `feature/estudante-2-mongodb-embeddings-recomendacoes` — MongoDB, embeddings, pgvector e recomendações
- `feature/estudante-3-metricas-superset` — métricas, consultas SQL e dashboard no Superset

## 🧱 Arquitetura inicial

```text
dados brutos (CSV/JSON)
        │
        ▼
Python / src
        │
        ├── validação e tratamento
        ├── PostgreSQL
        ├── MongoDB
        ├── embeddings / pgvector
        ├── recomendações
        └── métricas
        │
        ▼
Apache Superset
```

## 📁 Estrutura

```text
.
├── config/
│   └── config.yaml
├── dados/
│   ├── brutos/
│   └── processados/
├── dashboard/
├── documentacao/
├── logs/
├── mongodb/
├── sql/
├── src/
│   ├── __init__.py
│   └── main.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ▶️ Execução

O ponto de entrada do projeto será:

```bash
python -m src.main
```

## 🔐 Configuração

Credenciais reais não devem ser versionadas. Copie `.env.example` para `.env` e configure PostgreSQL e MongoDB localmente.

## 📌 Status

Estrutura inicial criada. As funcionalidades serão implementadas e integradas pelas três branches da equipe.
