# Teste cashback - Parceiro A

## Resumo executivo

Parceiro: **Parceiro A**

Periodo analisado: **2011-01-01 a 2011-04-02**

Variante recomendada: **Grupo 1**

Decisao: **Escalar Grupo 1 para 100% do trafego, mantendo monitoramento de margem e cashback pago nos primeiros dias.**

Grupo 1 liderou em lucro liquido total (R$ 404.711,00), com margem sobre GMV de 7,22% e ROI de cashback de 173,38%. A diferenca para o segundo colocado foi de R$ 47.192,00 (13,20%).

## Tabela comparativa

| grupo | dias | compradores | gmv_total | cashback_total | lucro_liquido_total | margem_sobre_gmv | roi_cashback | uplift_lucro_vs_baseline | uplift_gmv_vs_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Grupo 1 | 92 | 9633 | R$ 5.605.173,00 | R$ 233.424,00 | R$ 404.711,00 | 7,22% | 173,38% | 0,00% | 0,00% |
| Grupo 2 | 92 | 10814 | R$ 6.423.096,00 | R$ 370.659,00 | R$ 357.519,00 | 5,57% | 96,45% | -11,66% | 14,59% |
| Grupo 3 | 92 | 11410 | R$ 6.785.856,00 | R$ 503.600,00 | R$ 264.287,00 | 3,89% | 52,48% | -34,70% | 21,06% |

## Leitura de negocio

A recomendacao prioriza lucro liquido absoluto, porque o objetivo do teste de cashback nao e apenas aumentar GMV, mas encontrar a alavanca com melhor retorno economico para escalar. GMV, margem e ROI de cashback entram como criterios de validacao para evitar escolher uma variante que venda mais, mas destrua margem.

## Qualidade dos dados

- Nenhuma perda de linha apos validacao de tipos e nulos.

## Limitacoes

- O dataset nao informa usuarios expostos por grupo. Por isso, a analise nao calcula taxa de conversao real nem significancia sobre conversao.
- A comparacao estatistica usa variacao diaria de lucro/GMV como sinal de estabilidade, mas a decisao final deve ser monitorada apos o rollout.
- Caso novos datasets tragam centavos, o parser de moeda ja trata virgula decimal e separador de milhar.
