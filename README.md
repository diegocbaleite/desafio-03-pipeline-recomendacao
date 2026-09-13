# Pipeline de Recomendação e Dashboard de Conteúdos Educacionais

Projeto do **Desafio Prático 1 — Fundamentos de Dados para IA (FIC_DEV)**. A solução implementa um pipeline reproduzível de ponta a ponta, desde a ingestão de arquivos CSV/JSON até persistência em PostgreSQL e MongoDB, embeddings com pgvector, busca semântica, recomendações e dashboard no Apache Superset.

## Identificação

**Alunos:**

- Diego Assunção Leite
- Gabriel Moreira Branco
- Gabriel André de Siqueira Nonato

**Curso/Módulo:** FIC_DEV — Programador de Sistemas com IA  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Turma:** Vespertino  
**Modalidade:** Equipe de 3 estudantes  
**Versão:** 1.0 — 2026

## Status da entrega

A branch **`main`** é a versão final integrada do projeto. Ela reúne as entregas de ingestão/PostgreSQL, MongoDB/embeddings/recomendações, métricas/Superset e os ajustes finais de documentação e observabilidade.

## Objetivo

O pipeline foi desenvolvido para:

- ler as três fontes de dados obrigatórias;
- validar e classificar registros;
- normalizar e preservar os dados de origem;
- salvar dados processados e resumo de ingestão;
- persistir dados estruturados no PostgreSQL;
- persistir comentários e avaliações no MongoDB;
- gerar e reaproveitar embeddings dos conteúdos;
- armazenar vetores no PostgreSQL com pgvector;
- executar buscas por similaridade semântica;
- gerar recomendações personalizadas;
- persistir recomendações;
- disponibilizar métricas e KPIs para o Superset;
- registrar logs e falhas das principais etapas.

---

# Requisitos Funcionais — RF01 a RF14

## RF01 — Inicialização e configuração

Execução oficial:

```bash
python -m src.main
```

A configuração funcional fica em `config/config.yaml`. Credenciais e parâmetros de conexão ficam em variáveis de ambiente carregadas pelo arquivo local `.env`, que não é versionado.

## RF02 — Leitura das fontes

Fontes obrigatórias:

```text
dados/brutos/
├── catalogo.csv
├── interacoes.json
└── comentarios.json
```

O pipeline registra nos logs o caminho das fontes e a quantidade de registros encontrados.

## RF03 — Validação dos dados

Os registros são classificados como:

- válido;
- inválido;
- incompleto;
- duplicado.

As validações contemplam campos obrigatórios, identificadores, datas, domínios categóricos, avaliações, valores numéricos, referências inexistentes e duplicidades. Registros rejeitados recebem classificação e motivo.

## RF04 — Tratamento e padronização

O processamento normaliza espaços, categorias, tipos, níveis, datas, valores numéricos e tags. Os arquivos de `dados/brutos/` são preservados e as saídas são geradas em `dados/processados/`.

## RF05 — Resumo da ingestão

O arquivo:

```text
dados/processados/resumo_ingestao.json
```

registra quantidades lidas, válidas, inválidas, incompletas, duplicadas, corrigidas, cargas nos bancos e tempos de processamento.

## RF06 — PostgreSQL

O modelo relacional possui as entidades:

```text
usuarios
categorias
conteudos
interacoes
recomendacoes
```

São utilizadas PKs, FKs, constraints, transações e `ON CONFLICT` para integridade e reexecução segura. Os scripts ficam em:

```text
sql/
├── criar_banco.sql
└── consultas.sql
```

## RF07 — MongoDB

**Implementação:** comentários e avaliações são carregados no MongoDB com `usuario_id`, `conteudo_id`, categoria, avaliação, comentário, tags e data.

A aplicação e o arquivo `mongodb/consultas.js` demonstram:

- inserção de documentos;
- consulta por conteúdo;
- busca por tag;
- filtro por nota;
- agregação por categoria.

A categoria é desnormalizada no documento para permitir agregações diretas no MongoDB.

## RF08 — Embeddings e pgvector

**Implementação:** cada conteúdo válido recebe uma representação vetorial gerada com:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

O texto inclui título e descrição, com metadados contextuais do conteúdo. Os vetores possuem 384 dimensões, são associados ao `conteudo_id`, persistidos em `dados/processados/embeddings.json` e enviados ao PostgreSQL/pgvector.

Embeddings válidos já persistidos são reaproveitados em novas execuções. Apenas conteúdos ausentes ou com vetor inválido são gerados novamente.

## RF09 — Busca semântica

A busca recebe texto em linguagem natural e retorna:

- posição;
- `conteudo_id`;
- título;
- categoria;
- tipo;
- similaridade;
- distância.

O projeto demonstra três consultas semânticas diferentes em `src/recomendacao/busca.py`.

## RF10 — Recomendações

A pontuação segue a fórmula definida no desafio:

```text
Pontuação = ((Ivis + Icur) / 2) × 100 × Iconc
```

Onde:

- `Ivis`: afinidade derivada do histórico de visualizações/consumo e similaridade vetorial;
- `Icur`: interesse explícito por curtidas ou avaliações positivas;
- `Iconc`: filtro binário que remove conteúdos concluídos.

Classificação:

- Positivo: pontuação >= 70;
- Estável: 40 < pontuação < 70;
- Negativo: pontuação <= 40 ou `Iconc = 0`.

Recomendações negativas são descartadas da lista de sugestões.

## RF11 — Persistência das recomendações

Cada recomendação persistida contém usuário, conteúdo, pontuação, posição, status e data de geração.

O número máximo de sugestões por usuário é **configurável** em:

```yaml
recomendacao:
  limite: 20
```

As recomendações válidas dentro desse limite são gravadas no PostgreSQL e em `dados/processados/recomendacoes.json`.

## RF12 — Métricas e KPIs

O projeto documenta métricas operacionais e quatro KPIs de decisão em `documentacao/kpis.md`, incluindo nome, objetivo, fórmula, fonte, periodicidade e interpretação.

Indicadores utilizados incluem:

- total de usuários;
- total de conteúdos;
- média de tempo por interação;
- usuários ativos;
- visualizações por categoria;
- taxa de conclusão por categoria;
- taxa de conversão das recomendações.

## RF13 — Apache Superset

O dashboard utiliza dados consolidados no PostgreSQL e possui evidências de:

- pelo menos 3 cartões;
- gráfico de barras;
- gráfico de linhas;
- filtros interativos;
- perguntas de negócio documentadas.

O pacote exportado está em:

```text
dashboard/dashboard_export.zip
```

As evidências estão em `dashboard/evidencias/`.

## RF14 — Logs e observabilidade

O arquivo de log é configurado em `config/config.yaml` e gerado em `logs/pipeline.log`.

Os logs registram:

- início e término do pipeline;
- fontes processadas;
- quantidades lidas e rejeitadas;
- tempos das principais etapas;
- falhas de conexão/persistência no PostgreSQL;
- falhas de conexão/persistência no MongoDB;
- falhas de geração de embeddings com rastreabilidade da exceção;
- falhas de persistência dos vetores e recomendações.

---

# Estrutura do projeto

```text
desafio-03-pipeline-recomendacao/
├── config/
│   └── config.yaml
├── dados/
│   ├── brutos/
│   │   ├── catalogo.csv
│   │   ├── interacoes.json
│   │   └── comentarios.json
│   └── processados/
│       ├── catalogo_processado.csv
│       ├── interacoes_processadas.json
│       ├── comentarios_processados.json
│       ├── embeddings.json
│       ├── recomendacoes.json
│       └── resumo_ingestao.json
├── dashboard/
│   ├── dashboard_export.zip
│   ├── sync_database.py
│   └── evidencias/
├── documentacao/
│   ├── modelo_dados.pdf
│   ├── arquitetura.pdf
│   ├── especificacao_tecnica.md
│   ├── kpis.md
│   ├── uso_da_ia.md
│   └── README.md
├── mongodb/
│   └── consultas.js
├── sql/
│   ├── criar_banco.sql
│   └── consultas.sql
├── src/
│   ├── main.py
│   ├── config.py
│   ├── logging_utils.py
│   ├── ingestao/
│   ├── database/
│   └── recomendacao/
├── tests/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

`dados/processados/registros_rejeitados.json` e `logs/pipeline.log` são gerados durante a execução quando aplicável.

---

# Configuração

## 1. Clonar o repositório

```bash
git clone https://github.com/diegocbaleite/desafio-03-pipeline-recomendacao.git
cd desafio-03-pipeline-recomendacao
```

## 2. Criar e ativar o ambiente virtual

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Criar o `.env`

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Depois, **preencha os valores vazios no `.env` antes de iniciar o Docker**. O arquivo de exemplo não contém senhas reais.

Variáveis que precisam de valor no ambiente local:

```text
POSTGRES_PASSWORD=
MONGO_PASSWORD=
SUPERSET_SECRET_KEY=
SUPERSET_ADMIN_PASSWORD=
```

Os demais valores podem ser mantidos ou ajustados conforme o ambiente. Nunca versione o arquivo `.env`.

## 5. Subir os serviços

```bash
docker compose up -d
```

Verifique:

```bash
docker compose ps
```

Serviços esperados:

- PostgreSQL + pgvector;
- MongoDB;
- Apache Superset.

> Para preservar os dados persistidos em volumes Docker, não use `docker compose down -v` a menos que queira apagar os volumes deliberadamente.

---

# Execução do pipeline

Com o `.venv` ativado, `.env` configurado e bancos disponíveis:

```bash
python -m src.main
```

Fluxo executado:

1. ingestão, validação e tratamento;
2. carga PostgreSQL;
3. carga e agregação MongoDB;
4. geração/reaproveitamento dos embeddings e persistência pgvector;
5. demonstração das buscas semânticas;
6. motor de recomendação;
7. persistência das recomendações;
8. atualização do resumo e logs.

---

# Testes automatizados

A suíte possui **60 testes automatizados** após a inclusão do teste específico de reaproveitamento de embeddings do RF08.

Execução completa:

```bash
python -m pytest -q
```

Execução por domínio:

```bash
python -m pytest tests/test_ingestao.py -v
python -m pytest tests/test_validacao.py -v
python -m pytest tests/test_postgres.py -v
python -m pytest tests/test_mongo.py -v
python -m pytest tests/test_embeddings.py -v
python -m pytest tests/test_recomendacao.py -v
python -m pytest tests/test_regras_negocio.py -v
python -m pytest tests/test_dashboard_metricas.py -v
```

A aprovação da suíte completa depende dos serviços e das credenciais locais estarem configurados corretamente. Antes da entrega, execute a suíte no ambiente final e confirme que todos os testes terminam sem falhas.

---

# Apache Superset

Com os containers ativos, acesse:

```text
http://localhost:8088
```

Use o usuário e a senha definidos em:

```text
SUPERSET_ADMIN_USERNAME
SUPERSET_ADMIN_PASSWORD
```

O script `dashboard/sync_database.py` sincroniza a conexão PostgreSQL e importa o pacote `dashboard/dashboard_export.zip` durante a inicialização do serviço Superset.

Caso a importação seja feita manualmente, utilize o valor real de `POSTGRES_PASSWORD` quando o Superset solicitar a senha da conexão.

---

# Documentação e entregáveis

A pasta `documentacao/` contém:

- `modelo-dados.pdf` — modelo conceitual/lógico/relacional;
- `arquitetura.pdf` — arquitetura do pipeline;
- `especificacao_tecnica.md` — decisões e detalhes técnicos;
- `kpis.md` — métricas, KPIs, fórmulas e perguntas de negócio;
- `uso_da_ia.md` — registro do uso de IA solicitado pelo desafio.

O repositório também inclui os arquivos de dados utilizados, scripts PostgreSQL, consultas MongoDB, busca vetorial, recomendação, exportação do Superset e instruções de instalação/execução.

---

# Uso de Inteligência Artificial

As ferramentas ChatGPT e Google Gemini foram utilizadas como apoio em revisão, sintaxe, testes e documentação. O registro de solicitações, decisões, inadequações encontradas e alterações realizadas está em:

```text
documentacao/uso_da_ia.md
```

A equipe permanece responsável por testar, compreender e justificar toda a solução apresentada.

---

# Controle de versão

A `main` é a branch final de entrega. As branches abaixo registram o desenvolvimento das responsabilidades iniciais da equipe:

- `feature/estudante-1-ingestao-postgresql`;
- `feature/estudante-2-mongodb-embeddings-recomendacoes`;
- `feature/estudante-3-metricas-superset`.

---

# Checklist final de validação

Antes da apresentação/entrega, na `main` atualizada:

```bash
git status -sb
docker compose ps
python -m pytest -q
python -m src.main
```

A entrega deve ser considerada validada somente depois de confirmar a suíte completa e a execução integrada no ambiente local configurado.

---

## Autores

- **Diego Assunção Leite**
- **Gabriel Moreira Branco**
- **Gabriel André de Siqueira Nonato**

**Turma:** Vespertino — FIC_DEV  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Ano:** 2026
