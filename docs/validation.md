# Validação dos marts

Gerado por `scripts/validate_marts.py` depois do `dbt build`. Não edite à mão.

Os testes do dbt (`dbt/tests/` e os `.yml`) já fazem o build falhar se algo abaixo quebrar. Este relatório registra os números por trás desses testes.

## Origem × marts

Cada linha e cada real da origem precisa chegar aos marts, sem perda nem duplicação.

| verificação | origem (CSV) | marts | ok |
|---|---:|---:|:---:|
| Pedidos | 99.441 | 99.441 | ✅ |
| Itens | 112.650 | 112.650 | ✅ |
| Pagamentos | 103.886 | 103.886 | ✅ |
| Linhas de avaliação (avaliação × pedido) | 99.224 | 99.224 | ✅ |
| Avaliações distintas | 98.410 | 98.410 | ✅ |
| Clientes (customer_unique_id) | 96.096 | 96.096 | ✅ |
| Produtos | 32.951 | 32.951 | ✅ |
| Vendedores | 3.095 | 3.095 | ✅ |
| Soma de preço dos itens (R$) | 13.591.643,70 | 13.591.643,70 | ✅ |
| Soma de frete dos itens (R$) | 2.251.909,54 | 2.251.909,54 | ✅ |
| Soma dos pagamentos (R$) | 16.008.872,12 | 16.008.872,12 | ✅ |
| Soma dos pagamentos via fct_orders (R$) | 16.008.872,12 | 16.008.872,12 | ✅ |

## Chaves

Nenhuma chave duplicada nas dimensões e nenhuma chave órfã nos fatos (fato apontando para algo que não existe na dimensão).

| verificação | encontrados | ok |
|---|---:|:---:|
| Chaves duplicadas em dim_customer | 0 | ✅ |
| Chaves duplicadas em dim_product | 0 | ✅ |
| Chaves duplicadas em dim_seller | 0 | ✅ |
| Chaves duplicadas em dim_location | 0 | ✅ |
| Pedidos duplicados em fct_orders | 0 | ✅ |
| Itens sem cliente na dimensão | 0 | ✅ |
| Itens sem produto na dimensão | 0 | ✅ |
| Itens sem vendedor na dimensão | 0 | ✅ |
| Itens sem local de entrega na dimensão | 0 | ✅ |
| Pedidos sem data de compra na dimensão | 0 | ✅ |
| Pagamentos sem cliente na dimensão | 0 | ✅ |
| Avaliações sem cliente na dimensão | 0 | ✅ |

## Pontos de atenção

Problemas conhecidos dos dados, mantidos no modelo de propósito. As decisões estão em [decisions.md](decisions.md).

| ponto | quantidade |
|---|---:|
| Pedidos sem itens (ficam em fct_orders com total zero) | 775 |
| Pedidos sem nenhum pagamento registrado | 1 |
| Pedidos com pagamentos que somam zero | 3 |
| Pedidos sem avaliação | 768 |
| Pedidos com status delivered sem data de entrega | 8 |
| Pedidos com data de entrega e outro status | 6 |
| Avaliações que cobrem mais de um pedido | 789 |
| Produtos sem categoria (rótulo sem_categoria) | 610 |
| Pontos de geolocalização fora do Brasil (descartados antes da mediana) | 42 |
| Endereços de entrega sem coordenada | 158 |
| Vendedores sem coordenada | 7 |
