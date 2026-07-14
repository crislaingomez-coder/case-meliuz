# Como acionar esta solucao com IA

Esta solucao foi pensada para ser usada com uma ferramenta de IA como ChatGPT, Claude, Claude Code, Cursor ou Gemini.

## Principio

A IA nao deve inventar calculos. O papel dela e acionar a solucao, ler os resultados estruturados e explicar a recomendacao em linguagem executiva.

O Python faz:

- leitura do CSV;
- validacao e limpeza;
- calculo das metricas;
- decisao recomendada;
- relatorios;
- CSV de acompanhamento;
- painel executivo.

A IA faz:

- acionamento em linguagem natural;
- revisao da recomendacao;
- explicacao executiva;
- identificacao de riscos e limitacoes.

## Exemplo de pedido para uma IA

```text
Analise o arquivo dados/dataset_01_parceiroA.csv usando a solucao deste repositorio.
Depois leia o JSON gerado em relatorios/ e explique qual variante deve ser escalada para 100% do trafego.
Nao invente metricas que nao existam no dataset.
```

## Exemplo para todos os testes

```text
Rode python main.py --todos.
Depois revise o painel, o CSV de acompanhamento e os arquivos *_ai_context.json.
Explique em linguagem executiva se a recomendacao de escalar o Grupo 1 faz sentido.
```

## Regra importante

O dataset nao informa usuarios expostos por grupo. Portanto, a IA nao deve afirmar taxa de conversao real nem significancia estatistica de conversao.

Use as metricas disponiveis:

- compradores;
- GMV;
- comissao;
- cashback;
- lucro liquido;
- margem sobre GMV;
- ROI de cashback.

## Resposta esperada da IA

A resposta deve conter:

- variante recomendada;
- justificativa de negocio;
- riscos ou limitacoes;
- proximos passos de monitoramento.
