# Auditoria do case

## Diagnostico

O enunciado nao pede apenas uma analise pontual de dados. O foco principal e criar uma solucao reutilizavel, parametrizada e robusta para que uma pessoa do time consiga analisar novos testes A/B com pouca friccao.

Por isso, a entrega foi estruturada como uma pequena ferramenta:

- recebe qualquer CSV no mesmo schema;
- valida e limpa os dados;
- calcula indicadores por grupo;
- gera recomendacao de negocio;
- produz relatorio executivo;
- cria um contexto estruturado para revisao com IA;
- atualiza um CSV consolidado no formato de planilha de acompanhamento.

## Ponto critico de metodologia

Os datasets nao trazem a quantidade de usuarios expostos por variante. Sem esse denominador, nao e correto afirmar taxa de conversao real nem significancia estatistica de conversao.

A analise usa as metricas disponiveis:

- compradores;
- GMV;
- comissao;
- cashback;
- lucro liquido;
- margem;
- ROI de cashback.

Essa limitacao foi registrada nos relatorios para evitar conclusoes artificiais.

## Criterio de decisao

A regra prioriza lucro liquido total e usa GMV, margem e ROI como criterios de validacao. Essa escolha conversa com o problema de negocio: aumentar cashback so vale a pena se o crescimento de vendas compensar o custo adicional.

## Resultado dos tres testes

Nos tres datasets, o Grupo 1 foi a melhor opcao economica:

- Parceiro A: Grupo 1 teve menor GMV que grupos com cashback maior, mas melhor lucro liquido e ROI.
- Parceiro B: Grupo 1 venceu em GMV, lucro e ROI.
- Parceiro C: Grupo 2 praticamente zerou lucro liquido, enquanto Grupo 1 manteve margem positiva.

## Recomendacao de entrega

Publicar o diretorio `case-meliuz/` em um repositorio publico no GitHub, com os relatorios ja gerados, o painel visual e o CSV de acompanhamento preenchido.
