# Decisões de modelagem

Aqui registro cada decisão de modelagem, as alternativas que considerei e por que escolhi uma delas. Os números vêm de `scripts/profile_data.py` ([profile.md](profile.md)); o contexto está em [exploration.md](exploration.md).

## Convenção de nomes

| Elemento | Regra | Exemplo |
|---|---|---|
| Tabelas e colunas | inglês, `snake_case` | `order_items`, `freight_value` |
| Tabelas do modelo normalizado | substantivo no plural | `orders`, `sellers` |
| Camadas do dbt (próximas etapas) | prefixo `stg_`, `dim_`, `fct_` | `stg_orders`, `dim_customer`, `fct_order_items` |
| Chave natural (vinda da origem) | `<entidade>_id` | `order_id`, `seller_id` |
| Chave substituta (criada no modelo dimensional) | `<entidade>_key` | `customer_key` |
| Data com hora | sufixo `_at` | `purchased_at` |
| Data sem hora | sufixo `_date` | `estimated_delivery_date` |
| Valores de domínio | como vieram, em português | `cama_mesa_banho`, `sao paulo` |

Mantive os nomes da origem sempre que já seguiam a regra. Renomeei só o que estava errado ou inconsistente:

| Origem | Modelo | Motivo |
|---|---|---|
| `order_purchase_timestamp` | `purchased_at` | convenção `_at` |
| `order_approved_at` | `approved_at` | prefixo redundante dentro de `orders` |
| `order_delivered_carrier_date` | `delivered_to_carrier_at` | tem hora, então `_at` |
| `order_delivered_customer_date` | `delivered_to_customer_at` | tem hora, então `_at` |
| `order_estimated_delivery_date` | `estimated_delivery_date` | nenhuma linha tem hora |
| `shipping_limit_date` | `shipping_limit_at` | tem hora |
| `review_creation_date` | `created_at` | 85 avaliações têm hora |
| `review_answer_timestamp` | `answered_at` | convenção `_at` |
| `product_name_lenght` | `product_name_length` | erro de grafia na origem |
| `product_description_lenght` | `product_description_length` | erro de grafia na origem |
| `geolocation_lat`, `geolocation_lng` | `latitude`, `longitude` | nome completo |

## Modelo normalizado

Arquivo: [model/normalized.dbml](../model/normalized.dbml). Ele representa a origem em terceira forma normal (3FN): cada fato fica em um lugar só, e cada tabela tem uma chave que identifica a linha.

### Entidades e chaves

| Tabela | Uma linha é | Chave primária |
|---|---|---|
| `customers` | uma pessoa que compra | `customer_unique_id` |
| `orders` | um pedido | `order_id` |
| `order_items` | uma unidade de produto num pedido | `(order_id, order_item_id)` |
| `order_payments` | um pagamento de um pedido | `(order_id, payment_sequential)` |
| `reviews` | uma avaliação | `review_id` |
| `order_reviews` | a ligação entre um pedido e uma avaliação | `(order_id, review_id)` |
| `products` | um produto | `product_id` |
| `product_categories` | uma categoria | `product_category_name` |
| `sellers` | um vendedor | `seller_id` |
| `zip_codes` | um prefixo de CEP | `zip_code_prefix` |

### Relacionamentos e cardinalidades

| Relacionamento | Cardinalidade | Por quê |
|---|---|---|
| cliente → pedidos | 1:N | 2.997 clientes têm mais de um pedido |
| pedido → itens | 1:0..N | 775 pedidos não têm itens |
| pedido → pagamentos | 1:0..N | um pedido pode ser pago em várias partes; 1 pedido não tem pagamento |
| pedido ↔ avaliação | N:N, via `order_reviews` | até 3 avaliações por pedido e até 3 pedidos por avaliação |
| produto → itens | 1:N | |
| vendedor → itens | 1:N | |
| pedido ↔ vendedor | N:N, via `order_items` | 1.278 pedidos têm mais de um vendedor |
| categoria → produtos | 1:N, opcional do lado do produto | 610 produtos sem categoria |
| prefixo de CEP → pedidos e vendedores | 1:N | |

## Decisões

### 1. O cliente é `customer_unique_id`, e o endereço fica no pedido
Na origem, `customers` tem uma linha por `customer_id`, mas `customer_id` é único em `orders`: é um identificador por pedido, não por pessoa. 96.096 pessoas aparecem com 99.441 ids.

- **Alternativa A:** manter `customers` com chave `customer_id`, como na origem. Descartada: contaria a mesma pessoa várias vezes e esconderia as recompras.
- **Alternativa B:** `customers` com chave `customer_unique_id` e o endereço nela. Descartada: 250 clientes compraram com mais de um CEP, então o endereço não depende só do cliente.
- **Escolha:** `customers` guarda só a identidade; CEP, cidade e estado viram atributos do pedido (endereço de entrega). Como `customer_id` é 1:1 com o pedido, ele também vai para `orders`, como coluna única, só para rastrear a origem.

### 2. Avaliações e pedidos são N:N
`review_id` não é único: 789 avaliações estão ligadas a mais de um pedido. Conferi que, nesses casos, nota, título, comentário e datas são sempre iguais e o cliente é sempre o mesmo. Ou seja, é uma avaliação só, que cobre vários pedidos (provavelmente compras feitas juntas).

- **Alternativa:** manter a tabela da origem com chave `(review_id, order_id)`. Descartada: repetiria o conteúdo da avaliação em cada linha.
- **Escolha:** `reviews` com uma linha por avaliação e `order_reviews` como tabela associativa.

### 3. A geolocalização vira uma tabela de prefixos de CEP
A geolocalização tem cerca de um milhão de pontos para 19.015 prefixos, com 261.831 linhas duplicadas, e 8.556 prefixos aparecem com mais de uma grafia de cidade (ex.: "são paulo" e "sao paulo").

- **Escolha:** `zip_codes` com uma linha por prefixo e a **mediana** de latitude e longitude. A mediana é menos sensível a pontos fora do lugar do que a média.
- O conjunto de prefixos é a união dos que aparecem em clientes, vendedores e geolocalização. Assim, os 157 prefixos de clientes e os 7 de vendedores que faltam na geolocalização continuam existindo, com coordenadas nulas, e nenhuma chave estrangeira fica órfã.
- Não uso cidade e estado da geolocalização: as grafias variam demais.

### 4. Cidade e estado ficam no pedido e no vendedor (dependência aceita)
Em 3FN estrita, estado dependeria do prefixo do CEP, e não do pedido. Mas 39 prefixos aparecem com mais de uma cidade nos próprios cadastros de clientes, e a única fonte "de referência" (a geolocalização) é a mais suja. Preferi manter cidade e estado como foram informados em cada pedido e vendedor. É uma pequena desnormalização consciente: o custo é repetir texto; o ganho é não inventar uma cidade "oficial" por prefixo.

### 5. Cada linha de item é uma unidade
Não existe coluna de quantidade: quem compra 2 unidades do mesmo produto gera 2 linhas, com `order_item_id` 1 e 2. Isso acontece em 7.088 pedidos, e em nenhum deles o preço ou o frete varia entre as linhas. Mantive esse grão; a quantidade, quando precisar, é uma contagem de linhas.

### 6. Tipo de pagamento como atributo, não como tabela
São só 5 valores (`credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`), sem nenhum atributo próprio. Uma tabela de domínio não acrescentaria informação. Os 80 pedidos com saltos em `payment_sequential` não afetam a chave.

### 7. Categorias em português e sem tradução
O dataset é brasileiro, e mantenho os valores como vieram. A tabela `product_category_name_translation` não entra no modelo. Além disso, ela está incompleta: faltam `pc_gamer` e `portateis_cozinha_e_preparadores_de_alimentos`. `product_categories` é montada a partir dos produtos, para que toda categoria usada exista.

### 8. Tipos de dados
- Valores em reais como `decimal(10, 2)`, e não ponto flutuante, para somas não acumularem erro de arredondamento.
- Prefixo de CEP como texto de 5 caracteres: há prefixos começando com zero.
- `estimated_delivery_date` como `date`: nenhuma linha tem hora.

### 9. Pedidos incompletos ficam no modelo
Pedidos sem itens (775), sem pagamento (1) ou sem avaliação (768) são reais: foram cancelados, ficaram indisponíveis ou não foram avaliados. As relações são opcionais, e nenhum pedido é descartado.

## O que ficou de fora
- **Tradução das categorias:** os valores ficam em português (decisão 7).
- **Cidade e estado da geolocalização:** grafias inconsistentes (decisão 3).
- **Linhas duplicadas da geolocalização:** absorvidas pela agregação por prefixo.
