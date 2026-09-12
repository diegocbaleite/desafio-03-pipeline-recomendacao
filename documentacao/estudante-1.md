# Estudante 1 — Ingestão, Tratamento e PostgreSQL

Responsável: **Diego Assunção Leite**

## Status

Parte concluída e revisada na branch `feature/estudante-1-ingestao-postgresql`.

## Escopo implementado

A implementação cobre configuração, leitura das três fontes, tratamento, validação,
classificação de qualidade, geração do resumo de ingestão, registro de execução e
persistência dos dados estruturados no PostgreSQL.

## Fontes processadas

- `dados/brutos/catalogo.csv`
- `dados/brutos/interacoes.json`
- `dados/brutos/comentarios.json`

Os arquivos oficiais utilizados possuem 1000 registros em cada fonte e são preservados
sem sobrescrita durante o pipeline.

## Compatibilidade com o formato oficial

O arquivo oficial de interações não fornece `interacao_id` e utiliza os campos:

- `tempo_consumido`
- `avaliacao_atribuida`

Durante o tratamento esses campos são convertidos para o modelo interno:

- `tempo_consumido_min`
- `avaliacao`

O arquivo oficial de comentários também não fornece `comentario_id`.

Por isso, `interacao_id` e `comentario_id` não são requisitos da validação de entrada.
Depois da classificação dos registros válidos, o pipeline gera IDs internos sequenciais
e reproduzíveis, iniciando em 1.

## Classificação de qualidade

Cada registro pode ser classificado como:

- `válido`
- `inválido`
- `incompleto`
- `duplicado`

Para o catálogo, a duplicidade é verificada por `conteudo_id`.

Como as fontes oficiais de interações e comentários não possuem identificador próprio,
são utilizadas chaves compostas:

```text
interações:
(usuario_id, conteudo_id, tipo_interacao, data_hora)

comentários:
(usuario_id, conteudo_id, data, comentario)
```

## Regras principais

- espaços extras são removidos;
- tipos, níveis e tipos de interação são normalizados;
- datas são convertidas para ISO quando possível;
- IDs devem ser inteiros positivos;
- valores decimais de ID, como `5.7`, não são truncados silenciosamente;
- números não finitos, como `NaN` e infinito, são rejeitados;
- interações exigem data e hora válidas;
- avaliações devem estar entre 1 e 5;
- percentual de conclusão deve estar entre 0 e 100;
- tempo consumido não pode ser negativo;
- referências a conteúdos inexistentes são rejeitadas;
- tags, quando informadas, devem ser uma lista;
- motivos de rejeição são preservados em `registros_rejeitados.json`.

## Resumo e logs

O pipeline gera `dados/processados/resumo_ingestao.json` com as quantidades de registros
lidos, válidos, inválidos, incompletos, duplicados, corrigidos, registros processados para
persistência e tempo total.

### Detalhamento dos registros classificados como "corrigidos" (RF04):
A classificação de "corrigido" ocorre sempre que o registro tratado difere da sua representação bruta original (`tratado != original`):
- **Catálogo (1.000 corrigidos):** Como o arquivo de entrada é um CSV lido textualmente, os campos `conteudo_id` e `carga_horaria_min` foram tipados de string para inteiros (`int`). Além disso, 495 categorias foram padronizadas em caixa e espaçamento (`strip().title()`).
- **Interações (1.000 corrigidos):** O formato oficial utilizava `tempo_consumido` e `avaliacao_atribuida`, que foram normalizados e renomeados para `tempo_consumido_min` e `avaliacao` (com conversão para valores numéricos decimais `float`).
- **Comentários (837 corrigidos):** As listas de `tags` foram limpas, convertidas para minúsculas, deduplicadas e ordenadas em ordem alfabética. Os 163 comentários restantes já apresentavam tags perfeitamente ordenadas e em minúsculas na origem.

Os logs registram:

- início e término do processamento;
- nomes dos arquivos processados;
- quantidade de registros encontrados;
- quantidade de válidos, inválidos, incompletos, duplicados e rejeitados por fonte;
- tempo de leitura, tratamento/validação, gravação e carga PostgreSQL;
- falhas de ingestão, conexão ou persistência com stack trace.

Falhas de PostgreSQL são registradas e propagadas, evitando que uma execução com erro de
persistência seja apresentada como bem-sucedida.

## PostgreSQL

O script `sql/criar_banco.sql` cria:

- `usuarios`
- `categorias`
- `conteudos`
- `interacoes`
- `recomendacoes`

A carga usa uma transação e `ON CONFLICT`. O campo `embedding vector(384)` já está reservado
em `conteudos` para a etapa de embeddings e busca semântica.

O valor informado como `carregados_banco.postgresql` representa a quantidade de registros
enviados/processados pela rotina de carga na execução, incluindo usuários distintos,
categorias, conteúdos e interações.

## Configuração

As credenciais reais ficam fora do código-fonte. O arquivo `.env` é ignorado pelo Git e o
`.env.example` serve como modelo. O carregador de configuração lê parâmetros do PostgreSQL
e do MongoDB a partir de variáveis de ambiente.

## Execução

```bash
cp .env.example .env
pip install -r requirements.txt
python -m src.main
```

## Evidências com os dados oficiais

Execução da ingestão:

```text
catálogo:     1000 lidos / 1000 válidos
interações:   1000 lidos / 1000 válidos
comentários:  1000 lidos / 1000 válidos
```

Na execução validada localmente com PostgreSQL:

```text
Ingestão concluída | catálogo=1000 | interações=1000 | comentários=1000
Carga PostgreSQL concluída: 2158 registros processados
Término do processamento
```

## Testes automatizados

```bash
python -m pytest -q
```

Após a revisão de robustez, o conjunto possui **14 testes** e foi executado com sucesso:

```text
.............. [100%]
14 passed
```

Os testes cobrem normalização, formato oficial, referências inexistentes, avaliações inválidas,
registros incompletos, duplicidades, IDs decimais, data sem horário, tempo negativo, percentual
acima de 100, domínios inválidos e números não finitos.

## Limites do escopo do Estudante 1

MongoDB, embeddings, busca semântica, motor de recomendação, KPIs e dashboard no Superset
são integrados pelas demais branches da equipe. O Estudante 1 deixa a base de ingestão e
PostgreSQL preparada para essas integrações.
