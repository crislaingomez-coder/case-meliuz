# Teste cashback - Parceiro B

## Resumo executivo

Parceiro: **Parceiro B**

Periodo analisado: **2011-05-01 a 2011-06-30**

Variante recomendada: **Grupo 1**

Decisao: **Escalar Grupo 1 para 100% do trafego, mantendo monitoramento de margem e cashback pago nos primeiros dias.**

Grupo 1 liderou em lucro liquido total (R$ 286.570,00), com margem sobre GMV de 7,00% e ROI de cashback de 175,00%. A diferenca para o segundo colocado foi de R$ 143.413,00 (100,18%).

## Tabela comparativa

| grupo | dias | compradores | gmv_total | cashback_total | lucro_liquido_total | margem_sobre_gmv | roi_cashback | uplift_lucro_vs_baseline | uplift_gmv_vs_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Grupo 1 | 61 | 7990 | R$ 4.093.818,00 | R$ 163.751,00 | R$ 286.570,00 | 7,00% | 175,00% | 0,00% | 0,00% |
| Grupo 2 | 61 | 5452 | R$ 2.863.019,00 | R$ 171.778,00 | R$ 143.157,00 | 5,00% | 83,34% | -50,04% | -30,06% |
| Grupo 3 | 61 | 5029 | R$ 2.629.963,00 | R$ 236.697,00 | R$ 52.593,00 | 2,00% | 22,22% | -81,65% | -35,76% |

## Leitura de negocio

A recomendacao prioriza lucro liquido absoluto, porque o objetivo do teste de cashback nao e apenas aumentar GMV, mas encontrar a alavanca com melhor retorno economico para escalar. GMV, margem e ROI de cashback entram como criterios de validacao para evitar escolher uma variante que venda mais, mas destrua margem.

## Qualidade dos dados

- Nenhuma perda de linha apos validacao de tipos e nulos.

## Limitacoes

- O dataset nao informa usuarios expostos por grupo. Por isso, a analise nao calcula taxa de conversao real nem significancia sobre conversao.
- A comparacao estatistica usa variacao diaria de lucro/GMV como sinal de estabilidade, mas a decisao final deve ser monitorada apos o rollout.
- Caso novos datasets tragam centavos, o parser de moeda ja trata virgula decimal e separador de milhar.
