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

## Modelo dimensional

Arquivo: [model/dimensional.dbml](../model/dimensional.dbml). O modelo normalizado é bom para registrar dados sem contradição, mas, para responder "quanto vendemos por categoria e por mês", ele obriga a juntar cinco ou seis tabelas. O star schema reorganiza os mesmos dados em torno das perguntas de negócio: fatos (o que se mede) no centro e dimensões (por onde se analisa) em volta.

### Os quatro passos de Kimball

**1. Processos de negócio.** Escolhi os quatro eventos que a empresa mede:

| Processo | Evento | Fato |
|---|---|---|
| Venda | uma unidade de produto é vendida | `fct_order_items` |
| Atendimento do pedido | o pedido avança de etapa (aprovado, enviado, entregue) | `fct_orders` |
| Pagamento | um pagamento é registrado | `fct_payments` |
| Avaliação | o cliente avalia a compra | `fct_reviews` |

**2. Grão.** Declarado antes de qualquer coluna:

| Fato | Uma linha é | Tipo |
|---|---|---|
| `fct_order_items` | uma unidade de produto num pedido | transacional |
| `fct_orders` | um pedido, com uma data por etapa | accumulating snapshot |
| `fct_payments` | um pagamento de um pedido | transacional |
| `fct_reviews` | uma avaliação ligada a um pedido | transacional |

**3. Dimensões.** `dim_date`, `dim_customer`, `dim_location`, `dim_product`, `dim_seller`.

**4. Fatos (medidas).** Preço e frete por item; totais, prazos e atraso por pedido; valor e parcelas por pagamento; nota e tempo de resposta por avaliação.

### Bus matrix

Quais dimensões cada processo usa. As dimensões compartilhadas são o que permite cruzar processos (ex.: vendas e avaliações do mesmo cliente).

| Fato | data | cliente | local de entrega | produto | vendedor |
|---|:---:|:---:|:---:|:---:|:---:|
| `fct_order_items` | compra | ✓ | ✓ | ✓ | ✓ |
| `fct_orders` | compra, aprovação, envio, entrega, prevista | ✓ | ✓ | | |
| `fct_payments` | compra | ✓ | | | |
| `fct_reviews` | criação da avaliação | ✓ | | | |

### 10. Quatro fatos, e não um só
Cada processo tem um grão diferente. Juntá-los numa tabela só repetiria valores: um pedido com 3 itens e um pagamento de R$ 300, juntado por `order_id`, viraria 3 linhas, e a soma dos pagamentos daria R$ 900. Esse erro se chama *fan-out*. Fatos separados, cada um no seu grão, evitam o problema; para cruzar processos, agrega-se cada fato ao mesmo nível (ex.: por pedido) antes de juntar.

### 11. `fct_orders` como accumulating snapshot
O pedido passa por etapas: compra, aprovação, envio e entrega, com uma data prevista. Um accumulating snapshot guarda tudo isso numa linha por pedido, com uma chave de data para cada etapa. Datas de etapas que não aconteceram ficam nulas, porque essa é a informação real ("ainda não foi entregue"). A partir delas o fato já traz prazos calculados (`days_to_deliver`, `days_late_vs_estimate`) e indicadores (`is_late`), que são exatamente o que as análises de logística precisam. `is_late` fica nulo para pedidos não entregues, para não contar um pedido cancelado como "no prazo".

### 12. Totais de itens e pagamentos dentro de `fct_orders`
`fct_orders` traz `items_price_total`, `freight_total` e `payment_total`, já somados por pedido. Isso é seguro porque a soma é feita no mesmo grão do fato (o pedido), e facilita comparar o que foi vendido com o que foi pago (os 249 pedidos em que os valores diferem). Pedidos sem itens ficam com total zero, e não somem.

### 13. Local de entrega como dimensão própria, por endereço informado
Na decisão 4 mantive cidade e estado no pedido. Ao juntar os endereços de clientes e vendedores, encontrei 33 prefixos de CEP com mais de um estado, então uma dimensão com uma linha por prefixo obrigaria a escolher um estado "certo". `dim_location` tem uma linha por combinação de prefixo, cidade e estado, exatamente como foi informada, com as coordenadas do prefixo. Os fatos de itens e de pedidos apontam para ela no papel de **local de entrega**.

### 14. Localização do vendedor achatada em `dim_seller`
Cada vendedor tem um endereço só. Em vez de ligar `dim_seller` a `dim_location` (o que criaria um *snowflake*, uma dimensão pendurada em outra), copiei cidade, estado e coordenadas para dentro da própria `dim_seller`. Repetir alguns textos é o preço de consultas mais simples, que é o objetivo do modelo dimensional.

### 15. `dim_customer` com identidade e coorte, SCD tipo 1
A dimensão de cliente tem uma linha por `customer_unique_id`, com a data da primeira compra e o mês de coorte, base para análises de retenção. Sobre mudanças ao longo do tempo (*slowly changing dimensions*): a origem não traz histórico de atributos do cliente, e o único atributo que muda, o endereço, já está resolvido por pedido em `dim_location`. Por isso uso **SCD tipo 1** (o valor atual sobrescreve o anterior). Um SCD tipo 2, com uma linha por versão e datas de validade, só faria sentido se houvesse atributos com histórico, como segmento ou plano do cliente.

### 16. Chaves substitutas por hash
Cada dimensão tem uma chave própria (`customer_key`, `product_key`...), calculada como hash da chave natural.

- **Alternativa:** um número sequencial (1, 2, 3...). Descartada: depende da ordem de carga, muda se a tabela for reconstruída, e exige guardar o último número usado.
- **Escolha:** hash, que é determinístico (a mesma chave natural sempre gera a mesma chave substituta), não depende da ordem e permite montar dimensões e fatos em paralelo. O custo é ocupar mais espaço que um inteiro, irrelevante neste volume.
- **Exceção:** `dim_date` usa um inteiro legível `AAAAMMDD` (ex.: `20170315`), um padrão de mercado que facilita filtrar por período direto no fato.

Por que ter chave substituta se já existe `product_id`? Ela isola o modelo da origem: se o sistema de origem mudar o formato dos ids ou se no futuro houver histórico (SCD tipo 2), os fatos continuam apontando para a mesma chave.

### 17. Dimensões degeneradas
`order_id`, `order_status` e `payment_type` ficam direto nos fatos. Não têm atributos próprios, então uma tabela para cada um só acrescentaria joins. `order_id` em `fct_order_items` é o exemplo clássico: identifica o pedido sem precisar de uma dimensão de pedido.

### 18. Avaliações no grão avaliação × pedido
`fct_reviews` tem 99.224 linhas para 98.410 avaliações, porque 789 avaliações cobrem mais de um pedido. Escolhi esse grão porque a pergunta mais comum é "qual a nota deste pedido?". A regra para quem consulta: média de nota **por pedido** usa as linhas como estão; contagem de **avaliações** usa `count(distinct review_id)`.

Limitação conhecida: a nota é do pedido, não do vendedor. Em 1.278 pedidos há mais de um vendedor, então atribuir a nota a um vendedor exige uma regra. A decisão fica para a etapa das consultas, junto com a consulta que usa a nota por vendedor.

### 19. `dim_date` de 2016 a 2018
A dimensão cobre os anos completos de 2016 a 2018, o que inclui todas as datas de compra, etapas do pedido e avaliações (a última é de 29/10/2018). A exceção é `shipping_limit_at`: 4 itens têm prazo de postagem em 2020, o que parece erro de cadastro. Por isso essa data fica só como timestamp no fato, sem chave de data.

### 20. Nulos nas dimensões
Em dimensões, nulo atrapalha filtros e gráficos ("(em branco)"). Os 610 produtos sem categoria recebem o rótulo `sem_categoria`. Coordenadas continuam nulas quando o prefixo não está na geolocalização: inventar uma coordenada seria pior.

### O que mudou em relação ao modelo normalizado

| Normalizado | Dimensional | Por quê |
|---|---|---|
| `orders` + endereço no pedido | `fct_orders` + `dim_location` | o pedido vira um processo medido; o endereço vira dimensão para análise por região |
| `order_items` | `fct_order_items` | mesmo grão; ganha chaves de dimensão e data de compra |
| `order_payments` | `fct_payments` | mesmo grão; ganha cliente e data |
| `reviews` + `order_reviews` | `fct_reviews` | a tabela ponte some: o grão do fato já é avaliação × pedido |
| `products` + `product_categories` | `dim_product` | categoria achatada na dimensão |
| `sellers` + `zip_codes` | `dim_seller` | localização achatada |
| `customers` | `dim_customer` | ganha primeira compra e coorte |
| — | `dim_date` | nova: permite analisar por mês, dia da semana etc. sem funções de data em toda consulta |

## O que ficou de fora
- **Tradução das categorias:** os valores ficam em português (decisão 7).
- **Cidade e estado da geolocalização:** grafias inconsistentes (decisão 3).
- **Linhas duplicadas da geolocalização:** absorvidas pela agregação por prefixo.
- **Histórico de atributos (SCD tipo 2):** a origem não tem (decisão 15).
- **Chave de data para o prazo de postagem:** datas suspeitas em 2020 (decisão 19).
