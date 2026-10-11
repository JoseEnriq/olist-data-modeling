# Exploração dos dados

Antes de modelar qualquer coisa, eu quis entender o que cada tabela realmente representa, quais colunas identificam uma linha e onde os dados não se comportam como os nomes das colunas sugerem. Todos os números abaixo vêm de `scripts/profile_data.py`; a saída completa está em [profile.md](profile.md).

## Fonte

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0): pedidos feitos no marketplace da Olist entre setembro de 2016 e outubro de 2018, divididos em 9 arquivos CSV.

## Tabelas, grão e chaves

| tabela | linhas | uma linha é | chave |
|---|---:|---|---|
| orders | 99.441 | um pedido | `order_id` |
| customers | 99.441 | um cliente *por pedido* | `customer_id` |
| order_items | 112.650 | um item dentro de um pedido | `(order_id, order_item_id)` |
| order_payments | 103.886 | um pagamento de um pedido | `(order_id, payment_sequential)` |
| order_reviews | 99.224 | uma avaliação ligada a um pedido | `(review_id, order_id)` |
| products | 32.951 | um produto | `product_id` |
| sellers | 3.095 | um vendedor | `seller_id` |
| geolocation | 1.000.163 | uma coordenada de um prefixo de CEP | nenhuma |
| product_category_name_translation | 71 | uma categoria em português e inglês | `product_category_name` |

Chaves de uma coluna foram confirmadas verificando que a coluna não tem nulos e tem tantos valores distintos quanto linhas. Chaves compostas foram confirmadas com uma contagem distinta sobre o par.

## Descobertas

**1. `customer_id` não é o cliente.** `orders.customer_id` é único, então cada pedido ganha o seu próprio `customer_id`. A pessoa por trás do pedido é o `customer_unique_id`: 99.441 ids de cliente correspondem a 96.096 clientes únicos, e 2.997 deles têm mais de um `customer_id`. Contar clientes por `customer_id` inflaria a base e esconderia as recompras.

**2. `review_id` não é único.** São 98.410 valores distintos de `review_id` para 99.224 linhas; o par `(review_id, order_id)` é único. A mesma avaliação pode estar ligada a mais de um pedido, e 547 pedidos têm mais de uma avaliação.

**3. A geolocalização não pode ser ligada diretamente.** Ela tem cerca de um milhão de linhas para 19.015 prefixos de CEP, sendo 261.831 duplicatas exatas. Um prefixo tem várias coordenadas, então ligá-lo a clientes ou vendedores multiplicaria as linhas. Também há lacunas: 157 prefixos de clientes e 7 de vendedores não aparecem nela.

**4. Prefixos de CEP são texto.** O DuckDB lê como `VARCHAR` porque alguns começam com zero: 23.995 clientes têm prefixo iniciado por `0` (região de São Paulo). Converter para número quebraria o join com a geolocalização.

**5. Nem todo pedido tem itens, pagamentos ou avaliações.** 775 pedidos não têm itens, a maioria `unavailable` (603) e `canceled` (164). Um pedido não tem pagamento e 768 não têm avaliação. Qualquer modelo que parta de `order_items` perde esses pedidos sem avisar.

**6. As datas dos pedidos têm lacunas e inconsistências.** As etapas opcionais ficam nulas, como esperado, nos pedidos que não chegaram até elas (160 sem aprovação, 2.965 sem entrega ao cliente). Mas 8 pedidos estão `delivered` sem data de entrega, e 1.359 foram entregues à transportadora antes do horário de aprovação do pagamento. Não encontrei pedido entregue antes de ser comprado.

**7. As bordas do período são ralas.** Setembro de 2016 tem 4 pedidos, novembro de 2016 nenhum, dezembro de 2016 tem 1, e setembro e outubro de 2018 têm 16 e 4. Tendências mensais devem ser lidas entre janeiro de 2017 e agosto de 2018.

**8. Total dos itens e pagamentos nem sempre batem.** Em 249 pedidos, `sum(price + freight_value)` difere de `sum(payment_value)` em mais de R$ 1 (juros de parcelamento e vouchers são causas prováveis). Receita dos itens e dinheiro recebido nos pagamentos são medidas diferentes.

**9. Atributos de produto têm lacunas e erros de digitação.** 610 produtos não têm categoria nem nome, descrição e fotos; 2 não têm dimensões. As colunas de origem estão com erro de grafia (`product_name_lenght`, `product_description_lenght`).

**10. Pequenas estranhezas nos pagamentos.** 3 pagamentos têm tipo `not_defined`, 9 têm valor 0 e 2 têm 0 parcelas.

**11. A tabela de tradução é incompleta.** 2 categorias usadas pelos produtos não aparecem nela. Isso não afeta o modelo, porque mantenho os nomes de categoria em português.

## O que isso significa para o modelo

- A entidade cliente precisa ser identificada por `customer_unique_id`, com `customer_id` tratado como atributo do pedido.
- Itens, pagamentos e avaliações têm cada um o seu grão. Colocá-los numa tabela só duplicaria o valor do pagamento para cada item do pedido, então serão modelados separadamente.
- A geolocalização precisa ser reduzida a uma linha por prefixo de CEP antes de ser usada, e prefixos ausentes precisam ser permitidos.
- As etapas do pedido são naturalmente incompletas; o modelo deve manter e expor os nulos, não descartar os pedidos.
- Os nomes de coluna serão corrigidos na camada de staging (`lenght` → `length`), com a mudança documentada.
