# 📊 Pipeline de Recomendação e Dashboard de Conteúdos Educacionais

Sistema desenvolvido em Python para ingestão, validação, tratamento, armazenamento, busca semântica, recomendação e análise de dados de uma plataforma fictícia de conteúdos educacionais.

O projeto recebe dados provenientes de arquivos CSV e JSON, realiza limpeza e padronização dos registros, armazena dados estruturados no PostgreSQL e dados semiestruturados no MongoDB, gera embeddings armazenados com pgvector, realiza buscas por similaridade semântica, produz recomendações personalizadas e disponibiliza métricas e KPIs em um dashboard no Apache Superset.

---

## 👨‍💻 Identificação

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

## 🎯 Objetivo

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

## 📌 Mapeamento da Implementação dos Requisitos Funcionais

Abaixo está o detalhamento técnico dos **Requisitos Funcionais RF01 a RF14** definidos para o desafio.

### 🔹 RF01 — Inicialização e Configuração

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

### 🔹 RF02 — Leitura das Fontes de Dados

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

### 🔹 RF03 — Validação dos Dados

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

### 🔹 RF04 — Tratamento e Padronização

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

### 🔹 RF05 — Resumo da Ingestão

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

### 🔹 RF06 — Persistência no PostgreSQL

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

### 🔹 RF07 — Persistência no MongoDB

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

### 🔹 RF08 — Geração e Armazenamento de Embeddings

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

### 🔹 RF09 — Busca por Similaridade Semântica

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

### 🔹 RF10 — Geração de Recomendações

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

**Ivis** — Índice de Visualizações  
Representa a afinidade do usuário com os conteúdos visualizados.

**Icur** — Índice de Curtidas e Avaliações  
Representa curtidas ou avaliações positivas com nota igual ou superior a 4.

**Iconc** — Índice de Remoção de Concluídos

```text
0 = conteúdo já concluído
1 = conteúdo ainda não concluído
```

### 🔹 RF11 — Persistência das Recomendações

**Requisito:**  
As recomendações deverão ser armazenadas no PostgreSQL.

Cada recomendação deverá possuir:

- Identificador do usuário;
- Identificador do conteúdo;
- Pontuação;
- Posição;
- Data e hora da geração.

### 🔹 RF12 — Produção de Métricas e KPIs

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

### 🔹 RF13 — Dashboard no Apache Superset

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

### 🔹 RF14 — Registro de Execução

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

## ⚠️ Decisões Adotadas para o Tratamento dos Dados

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

## 🛠️ Tecnologias Utilizadas

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

## 📁 Estrutura do Projeto

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
│
├── dashboard/
│   └── evidencias/
│
├── documentacao/
│   ├── arquitetura.pdf
│   ├── modelo_de_dados.pdf
│   ├── kpis.md
│   └── uso_da_ia.md
│
├── logs/
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
│   │
│   ├── ingestao/
│   │   ├── leitura.py
│   │   ├── validacao.py
│   │   ├── tratamento.py
│   │   └── pipeline.py
│   │
│   ├── database/
│   │   └── postgres.py
│   │
│   ├── embeddings/
│   ├── recomendacao/
│   └── metricas/
│
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuração Dinâmica (`config/config.yaml`)

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

## 🐍 Ambiente Virtual e Instalação

### 1. Criar o ambiente virtual

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

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Criar o arquivo de ambiente

Linux:

```bash
cp .env.example .env
```

Configure no `.env` as credenciais locais do PostgreSQL e MongoDB.

---

## ▶️ Execução da Aplicação — RF01

A aplicação deverá ser executada a partir da raiz do projeto:

```bash
python -m src.main
```

---

## 🧪 Testes Automatizados — Pytest

Os testes automatizados serão utilizados para validar partes importantes do pipeline, como validação, tratamento e regras de negócio.

Para executar:

```bash
python -m pytest
```

> O resultado final dos testes será registrado aqui após a integração completa das três branches.

---

## 🔀 Controle de Versão e Branches

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

## 🤖 Uso de Ferramentas de Inteligência Artificial

Durante o desenvolvimento poderá ser utilizada a ferramenta **ChatGPT** como apoio ao processo de construção e compreensão da solução.

### Finalidades

A ferramenta poderá ser utilizada para:

- Interpretar mensagens de erro;
- Auxiliar na compreensão de Python;
- Revisar código;
- Auxiliar na modelagem do PostgreSQL;
- Sugerir consultas SQL;
- Auxiliar em consultas MongoDB;
- Explicar embeddings e pgvector;
- Auxiliar na criação de testes;
- Sugerir métricas e KPIs;
- Apoiar a documentação;
- Auxiliar na organização do Git e GitHub.

### Exemplos de prompts utilizados

- "Como organizar esse pipeline de dados?"
- "Explique esse erro do PostgreSQL."
- "Como validar esse registro em Python?"
- "Como armazenar embeddings usando pgvector?"
- "Como fazer uma busca por similaridade?"
- "Explique a fórmula de recomendação."
- "Como criar esse KPI no PostgreSQL?"
- "Como conectar o Superset ao PostgreSQL?"
- "Revise esse código."
- "Como organizar as branches da equipe?"

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

## 👨‍💻 Autores

- **Diego Assunção Leite**
- **Gabriel Moreira Branco**
- **Gabriel André de Siqueira Nonato**

**Turma:** Vespertino — FIC_DEV  
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá  
**Ano:** 2026
