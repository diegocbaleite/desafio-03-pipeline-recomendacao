# Registro de Uso Consciente de Inteligência Artificial

## 1. Ferramentas Utilizadas

- **ChatGPT (OpenAI)** — Utilizado para consultas conceituais pontuais e revisão de sintaxe textual.
- **Google Gemini (Google)** — Utilizado para auxílio na estruturação de testes automatizados (`pytest`), conferência de casos de borda e padronização da documentação técnica.

---

## 2. Princípios de Governança no Uso da IA

A equipe estabeleceu quatro premissas fundamentais para o desenvolvimento:
1. **Autoria Arquitetural Humana:** Toda a arquitetura (separação entre dados relacionais, semiestruturados e vetoriais), modelagem relacional (PK/FK/Constraints), escolha do modelo de embeddings multilíngue e formulação matemática ponderada ($Ivis, Icur, Iconc$) foram concebidas e calculadas pelos alunos.
2. **Uso Cirúrgico e Produtivo:** Geração de boilerplate repetitivo (layouts de tabelas Markdown, docstrings, sintaxe repetitiva de dicionários de teste e estruturas de classes).
3. **Revisão Crítica Obrigatória (Human-in-the-Loop):** Nenhuma linha de código ou consulta gerada por IA foi aplicada sem teste unitário correspondente e validação manual.
4. **Resolução Ativa de Alucinações:** A equipe identificou, corrigiu e descartou sugestões equivocadas da IA que violavam regras estritas do desafio.

---

## 3. Exemplos de Solicitações Realizadas (Prompts Objetivos)

Em vez de solicitações genéricas ("faça o desafio"), os prompts foram técnicos, isolados e focados em tarefas mecânicas ou de sintaxe:

- *"Qual a sintaxe correta do operador de produto escalar e distância de cosseno no pgvector com SQLAlchemy/psycopg2?"*
- *"Gere um template de tabela Markdown para documentar 4 KPIs com os campos: Nome, Objetivo, Fórmula, Fonte, Periodicidade e Interpretação."*
- *"Formate um dicionário de teste contendo 3 registros simulados com campos nulos para validação de erros no Pytest."*
- *"Revise a tipagem dessa função Python com Type Hints (`list[dict[str, Any]]`) segundo a PEP 585."*
- *"Identifique possíveis problemas de formatação no logging ao emitir quebras de linha com timestamp."*

---

## 4. Trechos e Decisões Apoiadas pela IA

A IA foi empregada unicamente para acelerar tarefas mecânicas e trabalhosas:
- **Estruturação de Testes Unitários:** Criação repetitiva dos corpos de funções de teste (`test_*.py`), agilizando a expansão da suíte para 60 testes automatizados;
- **Sintaxe de Agregação MongoDB:** Auxílio na sintaxe exata dos operadores de pipeline (`$group`, `$avg`, `$push`, `$in`) para o script `consultas.js`;
- **Refatoração de Regex e Limpeza Textual:** Otimização de expressões regulares para remoção de múltiplos espaços em branco (`strip()` e regex);
- **Formatação e Organização dos Documentos:** Padronização visual dos relatórios em Markdown, tabelas comparativas e esquemas conceituais.

---

## 5. Erros, Inadequações e Alucinações Identificados e Corrigidos pela Equipe

A postura ativa da equipe evitou falhas graves que teriam desclassificado requisitos do desafio se tivessem sido aceitas cegamente:

1. **Truncamento Indevido de IDs Decimais:** A IA inicialmente sugeriu converter `conteudo_id` usando `int(float(x))`, o que transformaria um ID inválido como `5.7` silenciosamente em `5` válido. **Decisão da equipe:** Rejeitamos a sugestão e implementamos validação estrita que rejeita IDs não inteiros (`conteudo_id inválido`).
2. **Tratamento de Números Não Finitos (`NaN` / `Inf`):** A IA considerava strings numéricas sem checar `math.isnan()`, permitindo que valores `NaN` passassem como válidos para o PostgreSQL. **Decisão da equipe:** Implementamos filtros defensivos contra valores não finitos.
3. **Ponto de Corte Errado no RF10:** A IA sugeriu `pontuacao < 40.0` para classificação negativa, ignorando que o documento exige explicitamente `Pontuação <= 40.0` (incluindo o valor 40). **Decisão da equipe:** Ajustamos a lógica de borda para refletir exatamente a regra de negócio do curso.
4. **Tentativa de `$lookup` desnecessário no MongoDB:** A IA propôs uma query complexa de junção em tempo de leitura para buscar a categoria do comentário. **Decisão da equipe:** Desnormalizamos o campo `categoria` durante a ingestão, garantindo agregações nativas de altíssima performance.
5. **Silenciamento de Exceções de Persistência:** A IA sugeriu capturar erros de banco com `except: pass`, o que faria o pipeline reportar sucesso mesmo se o PostgreSQL estivesse fora do ar. **Decisão da equipe:** Removemos o mascaramento, forçando logs detalhados com rastreabilidade real de integridade.

---

## 6. Responsabilidade e Domínio Técnico da Equipe

Todos os integrantes do grupo compreendem a arquitetura, conhecem cada arquivo implementado, dominam os modelos conceituais e lógicos e estão plenamente aptos a defender oralmente cada decisão de código e cada fórmula perante a banca avaliadora.
