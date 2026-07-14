# Case tecnico - Estagio em Operacoes Integradas | Meliuz

Solucao reutilizavel para analisar testes A/B de cashback por parceiro, gerar relatorio executivo e registrar o resultado em uma planilha consolidada em CSV.

## Objetivo

Responder a pergunta central do case:

> Dado esse teste A/B, qual variante de cashback devemos escalar para 100% do trafego?

A solucao foi desenhada para receber qualquer CSV no mesmo schema dos datasets fornecidos, limpar dados de moeda, calcular indicadores de negocio, comparar variantes e gerar uma recomendacao acionavel.

## Arquitetura

```text
CSV do teste
  -> validacao e limpeza
  -> metricas por grupo
  -> regra de decisao
  -> relatorio executivo
  -> contexto para IA
  -> CSV de acompanhamento
```

## Como rodar

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Analise um dataset especifico:

```bash
python main.py dados/dataset_01_parceiroA.csv
```

Analise todos os datasets:

```bash
python main.py --todos
```

## Como testar a entrega

Depois de executar `python main.py --todos`, confira se estes arquivos foram gerados/atualizados:

- `relatorios/dataset_01_parceiroa.md`
- `relatorios/dataset_02_parceirob.md`
- `relatorios/dataset_03_parceiroc.md`
- `resumo/acompanhamento_testes.csv`
- `saidas/painel_meliuz.xlsx`

O arquivo `saidas/painel_meliuz.xlsx` contem a visao visual da analise, com abas por parceiro, KPIs e graficos.

Sempre que o comando e executado, os arquivos de saida sao recriados. Portanto, se os CSVs da pasta `dados/` forem substituidos por novos testes no mesmo schema, o resumo, os relatorios e o painel visual passam a refletir os novos dados.

## Planilha publica

Pasta publica com os arquivos de acompanhamento da entrega:

https://drive.google.com/drive/folders/1xsJaRszwJicuEFyQYcgmJOQOlDo_gLVq?usp=sharing

## Saidas geradas

- `relatorios/*.md`: relatorios executivos por parceiro.
- `relatorios/*_ai_context.json`: contexto estruturado para revisar a analise com uma IA.
- `resumo/acompanhamento_testes.csv`: arquivo no formato da planilha de acompanhamento.
- `saidas/painel_meliuz.xlsx`: painel visual com KPIs e graficos por parceiro.

## Metricas calculadas

- compradores;
- GMV;
- comissao;
- cashback;
- lucro liquido;
- margem sobre GMV;
- ROI de cashback;
- ticket medio;
- cashback por comprador;
- uplift de lucro e GMV versus grupo base.

## Criterio de decisao

A recomendacao prioriza lucro liquido absoluto, validando margem e ROI de cashback. Isso evita escolher uma variante apenas por vender mais, mas que pode destruir rentabilidade.

Como o dataset nao informa usuarios expostos por variante, a solucao nao calcula taxa de conversao real. Essa limitacao aparece nos relatorios para evitar conclusoes estatisticas indevidas.

## Uso com IA

O arquivo `instrucoes_ia/prompt_analista_ia.md` pode ser usado em ChatGPT, Claude, Gemini, Cursor ou Claude Code junto com o JSON gerado em `relatorios/*_ai_context.json`.

Exemplo de comando em linguagem natural:

> Analise o contexto JSON deste teste A/B e revise a recomendacao executiva seguindo o prompt do projeto.

## Dashboard visual

O arquivo `saidas/painel_meliuz.xlsx` foi criado para apoiar a leitura gerencial do case. Ele contem:

- aba de resumo executivo;
- uma aba por parceiro;
- KPIs consolidados;
- graficos de lucro liquido e ROI;
- dados diarios para auditoria.

Esse arquivo pode ser importado no Google Sheets caso a entrega precise ficar em uma planilha compartilhavel.

## Estrutura

```text
case-meliuz/
  dados/
  codigo/
  instrucoes_ia/
  main.py
  relatorios/
  requirements.txt
  resumo/
  saidas/
```
