# Registro de Uso de Inteligência Artificial

Este documento registra o uso de IA como apoio ao desenvolvimento do desafio, conforme solicitado no enunciado.

## Ferramenta utilizada

- ChatGPT, da OpenAI.

## Como a IA foi utilizada

Na contribuição do Estudante 1, a IA foi utilizada como apoio para:

- interpretar o enunciado e transformar requisitos em tarefas técnicas;
- revisar a estrutura do pipeline de ingestão;
- adaptar o código ao formato real dos arquivos oficiais;
- revisar normalização e validação de dados;
- revisar o modelo relacional e os scripts PostgreSQL;
- sugerir e revisar testes automatizados;
- interpretar mensagens de erro do Git, PostgreSQL e do ambiente de desenvolvimento;
- apoiar a organização de branches, commits e pull request;
- revisar a documentação e o README.

## Exemplos de solicitações realizadas

Exemplos representativos das solicitações feitas durante o desenvolvimento:

- "Verifique se a minha parte de ingestão, tratamento e PostgreSQL atende ao desafio."
- "Compare o código com os arquivos oficiais que recebi."
- "Explique por que as interações não possuem `interacao_id` no arquivo de entrada."
- "Como validar IDs, datas, percentuais e avaliações?"
- "Revise meu script PostgreSQL com PK, FK e constraints."
- "Crie testes para registros inválidos, incompletos e duplicados."
- "Analise cuidadosamente se existe algum caso de borda no tratamento dos dados."
- "Ajude a resolver conflitos de Git sem enviar alterações para a `main`."

## Decisões e trechos apoiados pela IA

A IA ajudou a revisar ou propor:

- uso de chaves compostas para identificar duplicidade em fontes sem ID próprio;
- geração interna de `interacao_id` e `comentario_id` após a validação;
- normalização dos campos oficiais `tempo_consumido` e `avaliacao_atribuida`;
- validação de referências de `conteudo_id`;
- uso de transação e `ON CONFLICT` no PostgreSQL;
- geração do resumo da ingestão e registro de rejeitados;
- ampliação dos logs com tempos das etapas e contagem de rejeições;
- ampliação dos testes automatizados.

## Erros ou inadequações encontrados durante a revisão

As sugestões iniciais não foram aceitas automaticamente. Durante a revisão foram identificados e corrigidos pontos como:

- conversão de um ID decimal, como `5.7`, para inteiro `5`, o que poderia mascarar um dado inválido;
- aceitação de data sem horário em campo que exige data e hora;
- possibilidade de números não finitos passarem por validações numéricas;
- cálculo do tempo total antes da etapa PostgreSQL;
- tratamento de erro do PostgreSQL que registrava a falha, mas não interrompia a execução;
- cobertura de testes insuficiente para alguns casos obrigatórios do enunciado.

## Alterações realizadas pela equipe

Após a análise, as sugestões foram testadas e adaptadas ao projeto. Entre as alterações aplicadas estão:

- conversão numérica mais segura;
- validação explícita de data e hora;
- rejeição de números não finitos;
- propagação de falhas de persistência;
- medição de tempos das principais etapas;
- registro de quantidades de rejeitados nos logs;
- expansão da suíte de testes para 14 cenários;
- documentação das decisões adotadas.

## Responsabilidade da equipe

A IA foi utilizada somente como ferramenta de apoio. A equipe permanece responsável por executar, testar, compreender, justificar e apresentar o código e as decisões entregues no projeto.
