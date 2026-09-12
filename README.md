# Pipeline de Recomendação e Dashboard de Conteúdos Educacionais

Sistema desenvolvido em Python para ingestão, validação, tratamento, armazenamento, busca semântica, recomendação e análise de dados de uma plataforma fictícia de conteúdos educacionais.

O projeto recebe dados provenientes de arquivos CSV e JSON, realiza limpeza e padronização dos registros, armazena dados estruturados no PostgreSQL e dados semiestruturados no MongoDB, gera embeddings armazenados com pgvector, realiza buscas por similaridade semântica, produz recomendações personalizadas e disponibiliza métricas e KPIs em um dashboard no Apache Superset.

---

## Identificação

**Alunos:**

- Diego Assunção Leite
- Gabriel Moreira Branco
- Gabriel André de Siqueira Nonato

**Curso/Módulo:** FIC_DEV — Programador de Sistemas com IA  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Turma:** Vespertino  
**Modalidade:** Equipe de 03 estudantes  
**Versão:** 1.0 — 2026

---

## Objetivo

Desenvolver um pipeline de dados modular e reproduzível em Python capaz de:

- Ler arquivos CSV e JSON configurados externamente;
- Validar registros provenientes de diferentes fontes;
- Classificar registros como válidos, inválidos, incompletos ou duplicados;
- Registrar os motivos de rejeição dos registros;
- Realizar limpeza, tratamento e padronização dos dados;
- Preservar os arquivos originais de entrada;
- Gerar arquivos contendo os dados processados;
- Produzir um resumo da ingestão em formato JSON;
- Armazenar dados estruturados no PostgreSQL;
- Armazenar comentários e avaliações no MongoDB;
- Gerar embeddings dos conteúdos educacionais;
- Armazenar vetores utilizando PostgreSQL e pgvector;
- Realizar busca por similaridade semântica;
- Gerar recomendações personalizadas;
- Persistir as recomendações no PostgreSQL;
- Produzir métricas e KPIs;
- Disponibilizar dados consolidados para o Apache Superset;
- Construir um dashboard com indicadores e filtros interativos;
- Registrar logs das principais etapas do processamento.

---

## Mapeamento da Implementação dos Requisitos Funcionais

Abaixo está o detalhamento técnico dos **Requisitos Funcionais RF01 a RF14** definidos para o desafio.

### RF01 — Inicialização e Configuração

**Requisito:**  
O sistema deverá ser executado pelo comando:

```bash
python -m src.main
```

Também deverá utilizar arquivo de configuração em JSON ou YAML e manter credenciais separadas do código-fonte.

**Implementação:**

- O ponto de entrada da aplicação está localizado em `src/main.py`;
- As configurações do projeto são centralizadas em `config/config.yaml`;
- As credenciais são carregadas através de variáveis de ambiente;
- O arquivo `.env` não é versionado;
- O arquivo `.env.example` é disponibilizado como modelo de configuração.

### RF02 — Leitura das Fontes de Dados

**Requisito:**  
O sistema deverá ler no mínimo:

- Um arquivo CSV contendo o catálogo de conteúdos;
- Um arquivo JSON contendo as interações dos usuários;
- Um arquivo JSON contendo comentários ou avaliações.

**Implementação:**

Os arquivos de entrada são mantidos em:

```text
dados/brutos/
├── catalogo.csv
├── interacoes.json
└── comentarios.json
```

O módulo de ingestão é responsável por realizar a leitura das fontes e informar a quantidade de registros encontrados.

### RF03 — Validação dos Dados

**Requisito:**  
Cada registro deverá ser classificado como:

- válido;
- inválido;
- incompleto;
- duplicado.

**Implementação:**

O módulo de validação verifica:

- Campos obrigatórios;
- Identificadores;
- Datas;
- Valores categóricos;
- Intervalo das avaliações;
- Valores numéricos incompatíveis;
- Referências a usuários inexistentes;
- Referências a conteúdos inexistentes;
- Duplicidades.

Os registros rejeitados mantêm o motivo de sua classificação para auditoria.

### RF04 — Tratamento e Padronização

**Requisito:**  
O sistema deverá limpar, padronizar e tratar os registros antes do armazenamento.

**Implementação:**

O processamento realiza:

- Remoção de espaços desnecessários;
- Padronização de letras maiúsculas e minúsculas;
- Padronização de categorias;
- Padronização dos tipos de conteúdo;
- Padronização dos níveis;
- Conversão de datas;
- Conversão de valores numéricos;
- Tratamento de valores ausentes;
- Identificação e remoção de duplicidades.

Os arquivos originais são preservados em `dados/brutos/`.

Os resultados tratados são enviados para:

```text
dados/processados/
```

### RF05 — Resumo da Ingestão

**Requisito:**  
Ao final do processamento deverá ser produzido um resumo em JSON.

**Implementação:**

O arquivo:

```text
dados/processados/resumo_ingestao.json
```

registra informações como:

- Total de registros lidos;
- Registros válidos;
- Registros inválidos;
- Registros incompletos;
- Registros duplicados;
- Registros corrigidos;
- Registros carregados nos bancos;
- Tempo total de processamento.

### RF06 — Persistência no PostgreSQL

**Requisito:**  
Os dados estruturados deverão ser armazenados no PostgreSQL.

**Implementação:**

O modelo relacional possui entidades equivalentes a:

```text
usuario
categoria
conteudo
interacao
recomendacao
```

São utilizadas:

- Chaves primárias;
- Chaves estrangeiras;
- Restrições de integridade;
- Restrições contra duplicidade;
- Transações durante a carga.

Os scripts estão localizados em:

```text
sql/
├── criar_banco.sql
└── consultas.sql
```

### RF07 — Persistência no MongoDB

**Requisito:**  
Comentários, avaliações e outros dados semiestruturados deverão ser armazenados no MongoDB.

**Implementação prevista:**

A coleção deverá permitir:

- Inserir documentos;
- Consultar comentários por conteúdo;
- Pesquisar documentos por tag;
- Filtrar avaliações por nota;
- Agregar comentários ou avaliações por categoria.

As consultas utilizadas serão registradas em:

```text
mongodb/consultas.js
```

### RF08 — Geração e Armazenamento de Embeddings

**Requisito:**  
Cada conteúdo válido deverá possuir uma representação vetorial.

**Implementação prevista:**

O texto utilizado para gerar cada embedding será formado por:

```text
Título + Descrição
```

Os vetores serão:

- Associados ao `conteudo_id`;
- Gerados somente para conteúdos válidos;
- Armazenados no PostgreSQL;
- Persistidos utilizando a extensão `pgvector`;
- Protegidos contra geração duplicada.

O modelo de embeddings utilizado deverá ser registrado na documentação.

### RF09 — Busca por Similaridade Semântica

**Requisito:**  
O sistema deverá receber uma consulta em linguagem natural e recuperar os conteúdos semanticamente mais semelhantes.

**Implementação prevista:**

Cada resultado deverá apresentar:

- Posição;
- Identificador do conteúdo;
- Título;
- Categoria;
- Tipo;
- Similaridade ou distância.

Exemplo:

```text
Quero aprender os fundamentos de banco de dados para inteligência artificial.
```

A equipe deverá demonstrar pelo menos três consultas semânticas diferentes.

### RF10 — Geração de Recomendações

**Requisito:**  
O sistema deverá gerar recomendações considerando o comportamento do usuário.

Serão considerados:

- Conteúdos visualizados;
- Conteúdos curtidos;
- Avaliações positivas;
- Conteúdos já concluídos.

A fórmula definida para o desafio é:

```text
Pontuação = ((Ivis + Icur) / 2) × 100 × Iconc
```

Onde:

- **Ivis (Índice de Visualizações — 0.0 a 1.0):** Calculado por **Similaridade Vetorial Semântica via pgvector / Embeddings Ponderados**, gerando um perfil latente do usuário (`user_embedding`) ponderado pelo tempo consumido e percentual de conclusão, comparado via cosseno contra os vetores indexados no banco vetorial.
- **Icur (Índice de Curtidas e Avaliações — 0.0 a 1.0):** Representa curtidas explícitas ou avaliações positivas com nota igual ou superior a 4.0 na mesma categoria.
- **Iconc (Índice de Remoção de Concluídos):**
  - `0` = conteúdo já concluído (anula a pontuação);
  - `1` = conteúdo ainda não concluído.

**Regras de Classificação Oficial (Tipo de Recomendação):**

- **Positivo (Pontuação >= 70.0):** Forte afinidade;
- **Estável (40.0 < Pontuação < 70.0):** Afinidade moderada / interesse parcial;
- **Negativo (Pontuação <= 40.0 ou Iconc = 0):** Baixo interesse ou já concluído (**descartado da lista de sugestões**).

### RF11 — Persistência das Recomendações

**Requisito:**  
As recomendações geradas deverão ser armazenadas no PostgreSQL.

Cada recomendação possui:

- Identificador do usuário (`usuario_id`);
- Identificador do conteúdo (`conteudo_id`);
- Pontuação final (`pontuacao`);
- Posição no resultado (`posicao`);
- Status da recomendação (`status`: Positivo ou Estável);
- Data e hora da geração (`data_geracao`).

**Persistência Integral:** O pipeline armazena todas as sugestões válidas geradas para cada usuário ordenadas por pontuação decrescente ($1 \dots N$), sem truncamento artificial, persistindo-as na tabela `recomendacoes` do PostgreSQL e em `dados/processados/recomendacoes.json`.

### RF12 — Produção de Métricas e KPIs

**Requisito:**  
O projeto deverá calcular no mínimo:

```text
2 métricas operacionais
2 KPIs orientados à tomada de decisão
```

Possíveis indicadores:

- Total de usuários;
- Total de conteúdos;
- Visualizações por período;
- Avaliação média;
- Taxa de conclusão;
- Engajamento;
- Retenção;
- Conversão das recomendações;
- Tempo médio consumido;
- Total de recomendações geradas.

Para cada KPI deverão ser documentados:

- Nome;
- Objetivo;
- Fórmula;
- Fonte dos dados;
- Periodicidade;
- Interpretação.

### RF13 — Dashboard no Apache Superset

**Requisito:**  
O dashboard deverá utilizar os dados consolidados no PostgreSQL.

Deverá possuir no mínimo:

```text
3 cartões de indicadores
1 gráfico de barras
1 gráfico de linhas
2 filtros interativos
```

O dashboard deverá responder pelo menos duas perguntas de negócio definidas pela equipe.

### RF14 — Registro de Execução

**Requisito:**  
O sistema deverá registrar as principais etapas do processamento.

**Implementação:**

Os logs deverão registrar:

- Início do processamento;
- Término do processamento;
- Arquivos processados;
- Quantidade de registros lidos;
- Registros rejeitados;
- Falhas de conexão;
- Falhas de persistência;
- Falhas relacionadas aos embeddings;
- Tempo de processamento.

Os registros de execução são armazenados em:

```text
logs/
```

---

## Decisões Adotadas para o Tratamento dos Dados

Durante o desenvolvimento foram adotadas as seguintes decisões:

1. **Preservação dos dados originais**  
   Os arquivos presentes em `dados/brutos/` não são sobrescritos durante o pipeline.

2. **Rastreabilidade de registros rejeitados**  
   Registros inválidos, incompletos ou duplicados mantêm a justificativa de sua classificação.

3. **Separação entre dados brutos e processados**  
   Dados tratados são armazenados exclusivamente em `dados/processados/`.

4. **Integridade no PostgreSQL**  
   Chaves primárias, estrangeiras e restrições são utilizadas para impedir registros inconsistentes.

5. **Separação das credenciais**  
   Senhas e dados sensíveis ficam fora do código-fonte através do arquivo `.env`.

6. **Processamento resiliente**  
   Um registro inválido não deverá impedir que os demais registros sejam processados.

---

## Tecnologias Utilizadas

- **Python**
- **Pandas**
- **PostgreSQL**
- **psycopg2**
- **MongoDB**
- **PyMongo**
- **pgvector**
- **Sentence Transformers**
- **PyYAML**
- **python-dotenv**
- **Apache Superset**
- **Pytest**
- **Git / GitHub**

---

##  Estrutura do Projeto

```text
desafio-03-pipeline-recomendacao/
├── config/
│   └── config.yaml
│
├── dados/
│   ├── brutos/
│   │   ├── catalogo.csv
│   │   ├── interacoes.json
│   │   └── comentarios.json
│   │
│   └── processados/
│       ├── catalogo_processado.csv
│       ├── interacoes_processadas.json
│       ├── comentarios_processados.json
│       ├── embeddings.json
│       ├── recomendacoes.json
│       ├── registros_rejeitados.json
│       └── resumo_ingestao.json
│
├── dashboard/
│   ├── dashboard_export.zip
│   ├── sync_database.py
│   ├── README.md
│   └── evidencias/
│       └── README.md
│
├── documentacao/
│   ├── estudante-1.md
│   ├── estudante-2.md
│   ├── estudante-3.md
│   ├── uso_da_ia.md
│   └── README.md
│
├── logs/
│   └── pipeline.log
│
├── mongodb/
│   └── consultas.js
│
├── sql/
│   ├── criar_banco.sql
│   └── consultas.sql
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── logging_utils.py
│   │
│   ├── ingestao/
│   │   ├── __init__.py
│   │   ├── leitura.py
│   │   ├── validacao.py
│   │   ├── tratamento.py
│   │   └── pipeline.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   └── mongo.py
│   │
│   └── recomendacao/
│       ├── __init__.py
│       ├── embeddings.py
│       ├── busca.py
│       ├── motor.py
│       └── persistencia.py
│
├── tests/
│   ├── conftest.py
│   ├── test_dashboard_metricas.py
│   ├── test_embeddings.py
│   ├── test_ingestao.py
│   ├── test_mongo.py
│   ├── test_postgres.py
│   ├── test_recomendacao.py
│   ├── test_regras_negocio.py
│   └── test_validacao.py
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Configuração Dinâmica (`config/config.yaml`)

As configurações do projeto ficam centralizadas no arquivo:

```text
config/config.yaml
```

Exemplo:

```yaml
dados:
  catalogo: dados/brutos/catalogo.csv
  interacoes: dados/brutos/interacoes.json
  comentarios: dados/brutos/comentarios.json
  resumo_ingestao: dados/processados/resumo_ingestao.json

postgres:
  schema: public

mongodb:
  colecao_comentarios: comentarios

recomendacao:
  limite: 10
```

As credenciais de banco de dados são mantidas separadamente no `.env`.

---

## Guia de Instalação e Execução

O projeto é compatível com **Windows**, **Linux** e **macOS**. Siga as instruções do seu sistema operacional abaixo:

---

### 1. Clonar o Repositório e Acessar o Diretório

```bash
git clone https://github.com/seu-usuario/desafio-03-pipeline-recomendacao.git
cd desafio-03-pipeline-recomendacao
```

---

### 2. Criar e Ativar o Ambiente Virtual Python

#### No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Caso ocorra erro de permissão no PowerShell, execute antes: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

#### No Windows (Prompt de Comando - CMD):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

#### No Linux (Bash / Zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### No macOS (Terminal):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Instalar as Dependências

Em qualquer sistema operacional, com o ambiente virtual `.venv` ativado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Configurar as Variáveis de Ambiente (`.env`)

Crie o arquivo local `.env` a partir do modelo pré-configurado `.env.example`:

#### No Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### No Windows (CMD):
```cmd
copy .env.example .env
```

#### No Linux ou  macOS:
```bash
cp .env.example .env
```

> **Nota:** Os valores padrão do arquivo `.env.example` já estão sincronizados com as portas e credenciais do `docker-compose.yml` (`postgres:postgres` e `admin:admin123`).

---

### 5. Inicializar os Bancos de Dados via Docker

Para subir os contêineres do **PostgreSQL** (com extensão nativa `pgvector`) e do **MongoDB**:

```bash
docker compose up -d
```

Para verificar se os contêineres estão em execução:

```bash
docker compose ps
```

---

## Execução da Aplicação — RF01

A aplicação integrada deverá ser executada a partir da raiz do projeto:

```bash
python -m src.main
```

O comando executará o fluxo unificado de ponta a ponta:
1. Ingestão, validação e tratamento das 3 fontes (catálogo, interações e comentários);
2. Persistência dos dados relacionais no PostgreSQL;
3. Carga e enriquecimento semiestruturado no MongoDB com agregação analítica;
4. Geração dos embeddings densos (384d) e armazenamento via pgvector;
5. Demonstração de 3 buscas semânticas em linguagem natural;
6. Cálculo do motor de recomendação personalizada ($Ivis$, $Icur$ e $Iconc$);
7. Persistência das recomendações no PostgreSQL e em arquivo processado JSON;
8. Atualização do resumo geral da ingestão em `dados/processados/resumo_ingestao.json`.

---

## Testes Automatizados — Pytest

A suíte de testes é organizada de forma modular, permitindo a execução completa do sistema ou a validação pontual por componente:

### Execução Completa (53 testes):
```bash
python -m pytest -v
```

### Execução Isolada por Domínio:
```bash
# Ingestão (RF01, RF02, RF04, RF05)
python -m pytest tests/test_ingestao.py -v

# Validação e Qualidade dos Dados (RF03)
python -m pytest tests/test_validacao.py -v

# Banco Relacional PostgreSQL e pgvector (RF06, RF08, RF11)
python -m pytest tests/test_postgres.py -v

# Banco NoSQL MongoDB (RF07)
python -m pytest tests/test_mongo.py -v

# Embeddings e Busca Semântica (RF08, RF09)
python -m pytest tests/test_embeddings.py -v

# Motor de Recomendação (RF10, RF11)
python -m pytest tests/test_recomendacao.py -v
```

> **Status:** 53 testes automatizados cobrindo 100% dos requisitos funcionais implementados (RF01 a RF11), todos aprovados com sucesso.

---

## Controle de Versão e Branches

O projeto utiliza desenvolvimento colaborativo com uma branch principal e três branches de funcionalidades.

### `main`

Branch estável e utilizada para integração do projeto.

### `feature/estudante-1-ingestao-postgresql`

**Responsável:** Diego Assunção Leite

Atividades:

- Ingestão;
- Validação;
- Tratamento;
- PostgreSQL.

### `feature/estudante-2-mongodb-embeddings-recomendacoes`

**Responsável:** Gabriel Moreira Branco  

Atividades:

- MongoDB;
- Embeddings;
- pgvector;
- Busca semântica;
- Motor de recomendação.

### `feature/estudante-3-metricas-superset`

**Responsável:** Gabriel André de Siqueira Nonato

Atividades:

- Métricas;
- KPIs;
- Consultas;
- Views;
- Dashboard no Apache Superset.

---

## Uso Consciente de Ferramentas de Inteligência Artificial

O projeto adota uma política estrita de governança técnica contra práticas de *vibecoding*: toda a concepção arquitetural, modelagem de dados, decisões matemáticas e resolução de regras de negócio foram de autoria exclusiva dos discentes.

As ferramentas **ChatGPT (OpenAI)** e **Google Gemini (Google)** foram utilizadas pontualmente apenas como apoio a tarefas mecânicas, verificação de sintaxe e documentação:

### Finalidades Autorizadas e Aplicadas:

- Consulta de sintaxe pontual (operadores pgvector e sintaxe de agregações `$group` no MongoDB);
- Aceleração de código repetitivo de testes unitários (`pytest`);
- Apoio na padronização e diagramação de tabelas e documentação em Markdown;
- Revisão crítica de cobertura de testes.

### Princípio de Domínio e Responsabilidade:

A equipe revisou, testou e validou cada sugestão. Erros comuns de IA (como truncamento indevido de IDs decimais, má interpretação de valores de corte de borda e tentativas de junções custosas no NoSQL) foram ativamente identificados e corrigidos pelos alunos. 

O detalhamento completo das solicitações, correções humanas e decisões tomadas está registrado no documento oficial:
 [`documentacao/uso_da_ia.md`](documentacao/uso_da_ia.md).

### Participação dos Discentes

As sugestões fornecidas pela ferramenta deverão ser analisadas, testadas e adaptadas pelos integrantes da equipe.

Os estudantes continuam responsáveis por:

- Implementar e revisar o código;
- Executar testes;
- Validar os resultados;
- Corrigir erros;
- Compreender a solução;
- Justificar as decisões adotadas;
- Organizar o repositório;
- Realizar commits e merges;
- Preparar a apresentação final.

---

## Autores

- **Diego Assunção Leite**
- **Gabriel Moreira Branco**
- **Gabriel André de Siqueira Nonato**

**Turma:** Vespertino — FIC_DEV  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Ano:** 2026
