# Teste cashback - Parceiro C

## Resumo executivo

Parceiro: **Parceiro C**

Periodo analisado: **2011-07-01 a 2011-08-14**

Variante recomendada: **Grupo 1**

Decisao: **Escalar Grupo 1 para 100% do trafego, mantendo monitoramento de margem e cashback pago nos primeiros dias.**

Grupo 1 liderou em lucro liquido total (R$ 34.769,00), com margem sobre GMV de 2,00% e ROI de cashback de 40,00%. A diferenca para o segundo colocado foi de R$ 34.769,00 (sem base percentual positiva).

## Tabela comparativa

| grupo | dias | compradores | gmv_total | cashback_total | lucro_liquido_total | margem_sobre_gmv | roi_cashback | uplift_lucro_vs_baseline | uplift_gmv_vs_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Grupo 1 | 45 | 4549 | R$ 1.738.460,00 | R$ 86.924,00 | R$ 34.769,00 | 2,00% | 40,00% | 0,00% | 0,00% |
| Grupo 2 | 45 | 4522 | R$ 1.685.235,00 | R$ 117.967,00 | R$ 0,00 | 0,00% | 0,00% | -100,00% | -3,06% |

## Leitura de negocio

A recomendacao prioriza lucro liquido absoluto, porque o objetivo do teste de cashback nao e apenas aumentar GMV, mas encontrar a alavanca com melhor retorno economico para escalar. GMV, margem e ROI de cashback entram como criterios de validacao para evitar escolher uma variante que venda mais, mas destrua margem.

## Qualidade dos dados

- Nenhuma perda de linha apos validacao de tipos e nulos.

## Limitacoes

- O dataset nao informa usuarios expostos por grupo. Por isso, a analise nao calcula taxa de conversao real nem significancia sobre conversao.
- A comparacao estatistica usa variacao diaria de lucro/GMV como sinal de estabilidade, mas a decisao final deve ser monitorada apos o rollout.
- Caso novos datasets tragam centavos, o parser de moeda ja trata virgula decimal e separador de milhar.
