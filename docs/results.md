# Resultados das consultas de negócio

Gerado por `scripts/export_results.py` a partir das consultas em [dbt/analyses/](../dbt/analyses/). Não edite à mão.

Definições usadas em todas as consultas (detalhes em [decisions.md](decisions.md)): **pedido válido** é o que não foi cancelado nem ficou indisponível; **receita** é a soma dos preços dos itens, sem frete; séries mensais vão de janeiro de 2017 a agosto de 2018.

## 1. Receita e pedidos por mês

Consulta: [`01_revenue_by_month.sql`](../dbt/analyses/01_revenue_by_month.sql)

> Question: how did revenue and the number of orders evolve month by month? Revenue = sum of item prices (freight excluded) of valid orders, i.e. not canceled and not unavailable. Months at the edges of the dataset have almost no orders, so the series runs from January 2017 to August 2018.

| year_month | orders | revenue |
|---|---|---|
| 2017-01 | 787 | 120.098,27 |
| 2017-02 | 1.718 | 244.959,35 |
| 2017-03 | 2.617 | 368.341,32 |
| 2017-04 | 2.377 | 353.842,98 |
| 2017-05 | 3.640 | 503.159,19 |
| 2017-06 | 3.205 | 429.916,61 |
| 2017-07 | 3.946 | 492.287,30 |
| 2017-08 | 4.272 | 568.245,79 |
| 2017-09 | 4.227 | 621.415,91 |
| 2017-10 | 4.547 | 660.179,62 |
| 2017-11 | 7.421 | 1.003.862,14 |
| 2017-12 | 5.618 | 742.183,79 |
| 2018-01 | 7.187 | 945.456,29 |
| 2018-02 | 6.624 | 837.895,43 |
| 2018-03 | 7.168 | 981.051,06 |
| 2018-04 | 6.919 | 993.592,98 |
| 2018-05 | 6.833 | 992.871,75 |
| 2018-06 | 6.145 | 863.265,53 |
| 2018-07 | 6.233 | 878.044,27 |
| 2018-08 | 6.421 | 848.860,10 |

## 2. Categorias com maior receita

Consulta: [`02_revenue_by_category.sql`](../dbt/analyses/02_revenue_by_category.sql)

> Question: which product categories bring the most revenue? Same revenue definition as 01 (valid orders, item price only). Categories keep their Portuguese names.

| product_category_name | units_sold | revenue | revenue_share_pct | revenue_rank |
|---|---|---|---|---|
| beleza_saude | 9.634 | 1.255.695,13 | 9,3 | 1 |
| relogios_presentes | 5.970 | 1.198.185,21 | 8,9 | 2 |
| cama_mesa_banho | 11.097 | 1.035.964,06 | 7,7 | 3 |
| esporte_lazer | 8.590 | 979.740,92 | 7,3 | 4 |
| informatica_acessorios | 7.781 | 904.322,02 | 6,7 | 5 |
| moveis_decoracao | 8.298 | 727.465,05 | 5,4 | 6 |
| utilidades_domesticas | 6.915 | 626.825,80 | 4,6 | 7 |
| cool_stuff | 3.779 | 620.770,49 | 4,6 | 8 |
| automotivo | 4.204 | 586.585,73 | 4,3 | 9 |
| ferramentas_jardim | 4.328 | 481.009,94 | 3,6 | 10 |

## 3. Ticket médio por ano

Consulta: [`03_average_ticket.sql`](../dbt/analyses/03_average_ticket.sql)

> Question: how much does a customer pay per order, and did it change by year? Ticket = what was actually paid for the order (payment_total, freight and installment interest included), for valid orders with a payment above zero. Median next to the average: a few very expensive orders pull the average up.

| year | orders | average_ticket | median_ticket | average_items_per_order |
|---|---|---|---|---|
| 2016 | 295 | 175,64 | 111,22 | 1,17 |
| 2017 | 44.379 | 159,82 | 103,55 | 1,14 |
| 2018 | 53.532 | 160,56 | 106,87 | 1,14 |

## 4. Formas de pagamento

Consulta: [`04_payment_methods.sql`](../dbt/analyses/04_payment_methods.sql)

> Question: how do customers pay? One order can use more than one method (e.g. card plus voucher), so shares are computed over payments, not over orders.

| payment_type | payments | payments_share_pct | value | value_share_pct | average_installments |
|---|---|---|---|---|---|
| credit_card | 76.795 | 73,9 | 12.542.084,19 | 78,3 | 3,5 |
| boleto | 19.784 | 19,0 | 2.869.361,27 | 17,9 | 1,0 |
| voucher | 5.775 | 5,6 | 379.436,87 | 2,4 | 1,0 |
| debit_card | 1.529 | 1,5 | 217.989,79 | 1,4 | 1,0 |
| not_defined | 3 | 0,0 | 0,00 | 0,0 | 1,0 |

## 5. Tempo de entrega por estado

Consulta: [`05_delivery_time_by_state.sql`](../dbt/analyses/05_delivery_time_by_state.sql)

> Question: how long does delivery take in each state? Delivered orders only (orders with a delivery date). Days from purchase to delivery; the median is shown because a few very late orders inflate the average.

| state | delivered_orders | average_days | median_days |
|---|---|---|---|
| SP | 40.495 | 8,8 | 7,2 |
| MG | 11.355 | 12,0 | 10,3 |
| PR | 4.923 | 12,0 | 10,4 |
| DF | 2.080 | 13,0 | 11,4 |
| RJ | 12.353 | 15,3 | 12,0 |
| SC | 3.547 | 15,0 | 13,0 |
| RS | 5.344 | 15,3 | 13,2 |
| ES | 1.995 | 15,8 | 13,6 |
| MS | 701 | 15,6 | 13,9 |
| GO | 1.957 | 15,6 | 14,0 |
| PE | 1.593 | 18,4 | 15,7 |
| TO | 274 | 17,7 | 15,9 |
| RN | 474 | 19,3 | 16,1 |
| MT | 886 | 18,1 | 16,1 |
| PI | 476 | 19,5 | 16,3 |
| BA | 3.256 | 19,3 | 16,9 |
| RO | 243 | 19,4 | 17,6 |
| SE | 335 | 21,5 | 18,0 |
| PB | 517 | 20,4 | 18,2 |
| CE | 1.279 | 21,3 | 18,2 |
| AC | 80 | 21,0 | 18,4 |
| MA | 717 | 21,6 | 19,2 |
| PA | 946 | 23,8 | 21,1 |
| AL | 397 | 24,5 | 22,3 |
| AP | 67 | 27,2 | 24,4 |
| RR | 41 | 29,4 | 25,0 |
| AM | 145 | 26,4 | 25,9 |

## 6. Entregas atrasadas por estado

Consulta: [`06_late_deliveries_by_state.sql`](../dbt/analyses/06_late_deliveries_by_state.sql)

> Question: where are deliveries late most often? Late = delivered after the estimated delivery date shown to the customer. States with fewer than 500 delivered orders are left out: their rates swing too much with a handful of orders.

| state | delivered_orders | late_orders | late_pct | average_days_late |
|---|---|---|---|---|
| MA | 717 | 125 | 17,4 | 10,5 |
| CE | 1.279 | 176 | 13,8 | 15,2 |
| BA | 3.256 | 396 | 12,2 | 12,0 |
| RJ | 12.353 | 1.495 | 12,1 | 13,5 |
| PA | 946 | 106 | 11,2 | 12,8 |
| ES | 1.995 | 214 | 10,7 | 11,3 |
| PB | 517 | 54 | 10,4 | 10,3 |
| MS | 701 | 68 | 9,7 | 8,3 |
| PE | 1.593 | 153 | 9,6 | 12,0 |
| SC | 3.547 | 291 | 8,2 | 8,3 |
| GO | 1.957 | 128 | 6,5 | 11,4 |
| RS | 5.344 | 325 | 6,1 | 10,2 |
| MT | 886 | 53 | 6,0 | 10,6 |
| DF | 2.080 | 118 | 5,7 | 7,4 |
| MG | 11.355 | 520 | 4,6 | 8,4 |
| SP | 40.495 | 1.820 | 4,5 | 8,3 |
| PR | 4.923 | 199 | 4,0 | 8,3 |

## 7. Pedidos cancelados ou indisponíveis por trimestre

Consulta: [`07_cancellation_rate.sql`](../dbt/analyses/07_cancellation_rate.sql)

> Question: how many orders are lost to cancellation or unavailability, and how does that change over time? "Lost" = status canceled or unavailable. Quarterly, to smooth the monthly noise, from January 2017 to August 2018 (the edges of the dataset have almost no orders), so 2018 Q3 covers July and August only.

| year | quarter | orders | canceled | unavailable | lost_pct |
|---|---|---|---|---|---|
| 2017 | 1 | 5.262 | 53 | 87 | 2,66 |
| 2017 | 2 | 9.349 | 63 | 64 | 1,36 |
| 2017 | 3 | 12.642 | 75 | 122 | 1,56 |
| 2017 | 4 | 17.848 | 74 | 184 | 1,45 |
| 2018 | 1 | 21.208 | 133 | 95 | 1,08 |
| 2018 | 2 | 19.979 | 57 | 25 | 0,41 |
| 2018 | 3 | 12.804 | 125 | 25 | 1,17 |

## 8. Vendedores com melhor e pior nota

Consulta: [`08_seller_ratings.sql`](../dbt/analyses/08_seller_ratings.sql)

> Question: which sellers have the best and the worst review scores? A review belongs to an order, not to a seller. To attribute it fairly, only orders with a single seller are used (1,278 orders have more than one). Orders with several reviews count once, with their average score. Sellers need at least 50 reviewed orders, so a few orders do not decide the rank.

| ranking | seller_id | seller_state | reviewed_orders | average_score | low_score_pct |
|---|---|---|---|---|---|
| top 10 | d13e50eaa47b4cbe9eb81465865d8cfc | SP | 67 | 4,82 | 3,0 |
| top 10 | d9bd94811c3338dceb4181f3dbc0c73e | SP | 54 | 4,8 | 3,7 |
| top 10 | 116ccb1a1604bc88e4d234a8c23f33de | SP | 59 | 4,69 | 1,7 |
| top 10 | d566c37fa119d5e66c4e9052e83ee4ea | SP | 63 | 4,68 | 3,2 |
| top 10 | 376a891762bbdecbc02b4b6adec3fdda | GO | 57 | 4,67 | 1,8 |
| top 10 | d9a84e1403de8da0c3aa531d6d108ba6 | SP | 52 | 4,65 | 3,8 |
| top 10 | 1bb2bdb95f4841f1bba2c0d2cd83d3c9 | SP | 80 | 4,64 | 3,8 |
| top 10 | 289cdb325fb7e7f891c38608bf9e0962 | SP | 104 | 4,63 | 3,8 |
| top 10 | 516e7738bd8f735ac19a010ee5450d8d | RJ | 74 | 4,62 | 2,7 |
| top 10 | 080199a181c46c657dc5aa235411be3b | SP | 78 | 4,62 | 1,3 |
| bottom 10 | 710e3548e02bc1d2831dfc4f1b5b14d4 | PR | 133 | 3,37 | 32,3 |
| bottom 10 | 5058e8c1e82653974541e83690655b4a | SP | 59 | 3,34 | 27,1 |
| bottom 10 | a7f13822ceb966b076af67121f87b063 | SP | 74 | 3,34 | 29,7 |
| bottom 10 | bbad7e518d7af88a0897397ffdca1979 | SP | 64 | 3,3 | 37,5 |
| bottom 10 | 8444e55c1f13cd5c179851e5ca5ebd00 | MG | 97 | 3,26 | 35,1 |
| bottom 10 | 972d0f9cf61b499a4812cf0bfa3ad3c4 | SC | 73 | 3,08 | 41,1 |
| bottom 10 | a49928bcdf77c55c6d6e05e09a9b4ca5 | SP | 95 | 3,06 | 38,9 |
| bottom 10 | 54965bbe3e4f07ae045b90b0b8541f52 | PR | 73 | 3,03 | 43,8 |
| bottom 10 | 2eb70248d66e0e3ef83659f71b244378 | SP | 196 | 2,68 | 50,5 |
| bottom 10 | 1ca7077d890b907f89be8c954a02686a | SP | 112 | 2,33 | 61,6 |

## 9. Nota da avaliação × atraso na entrega

Consulta: [`09_review_score_vs_delay.sql`](../dbt/analyses/09_review_score_vs_delay.sql)

> Question: how much does a late delivery hurt the review score? Delivered orders with a review, grouped by how many days after the estimated date they arrived. Orders with several reviews count once, with their average.

| delay_bucket | orders | average_score | low_score_pct |
|---|---|---|---|
| 1. no prazo ou antes | 89.448 | 4,29 | 9,2 |
| 2. 1 a 3 dias de atraso | 1.852 | 3,29 | 32,2 |
| 3. 4 a 7 dias de atraso | 1.748 | 2,11 | 67,6 |
| 4. 8 a 14 dias de atraso | 1.447 | 1,67 | 80,0 |
| 5. mais de 14 dias de atraso | 1.335 | 1,73 | 78,2 |

## 10. Clientes que voltam a comprar

Consulta: [`10_repeat_customers.sql`](../dbt/analyses/10_repeat_customers.sql)

> Question: how many customers come back to buy again? Customers are people (customer_unique_id), which is why dim_customer exists: counting customer_id would make every order look like a new customer. Only valid orders (not canceled, not unavailable) count as purchases.

| customer_group | customers | customers_pct |
|---|---|---|
| 1 pedido | 92.102 | 96,96 |
| 2 pedidos | 2.652 | 2,79 |
| 3 ou mais pedidos | 236 | 0,25 |
