# Modelo normalizado

Gerado por `scripts/render_diagrams.py` a partir de [normalized.dbml](normalized.dbml). Não edite à mão: altere o `.dbml` e rode o script de novo.

Legenda: `PK` chave primária, `FK` chave estrangeira, `UK` valor único. `||--o{` = um para zero ou muitos; `|o--o{` = a chave estrangeira pode ser nula.

```mermaid
erDiagram
    customers {
        varchar customer_unique_id PK
    }
    orders {
        varchar order_id PK
        varchar customer_id UK
        varchar customer_unique_id FK
        varchar customer_zip_code_prefix FK
        varchar customer_city
        char customer_state
        varchar order_status
        timestamp purchased_at
        timestamp approved_at
        timestamp delivered_to_carrier_at
        timestamp delivered_to_customer_at
        date estimated_delivery_date
    }
    order_items {
        varchar order_id PK, FK
        int order_item_id PK
        varchar product_id FK
        varchar seller_id FK
        timestamp shipping_limit_at
        decimal price
        decimal freight_value
    }
    order_payments {
        varchar order_id PK, FK
        int payment_sequential PK
        varchar payment_type
        int payment_installments
        decimal payment_value
    }
    reviews {
        varchar review_id PK
        smallint review_score
        varchar review_comment_title
        varchar review_comment_message
        timestamp created_at
        timestamp answered_at
    }
    order_reviews {
        varchar order_id PK, FK
        varchar review_id PK, FK
    }
    products {
        varchar product_id PK
        varchar product_category_name FK
        int product_name_length
        int product_description_length
        int product_photos_qty
        int product_weight_g
        int product_length_cm
        int product_height_cm
        int product_width_cm
    }
    product_categories {
        varchar product_category_name PK
    }
    sellers {
        varchar seller_id PK
        varchar seller_zip_code_prefix FK
        varchar seller_city
        char seller_state
    }
    zip_codes {
        varchar zip_code_prefix PK
        double latitude
        double longitude
    }
    customers ||--o{ orders : "customer_unique_id"
    zip_codes ||--o{ orders : "customer_zip_code_prefix"
    zip_codes ||--o{ sellers : "seller_zip_code_prefix"
    orders ||--o{ order_items : "order_id"
    products ||--o{ order_items : "product_id"
    sellers ||--o{ order_items : "seller_id"
    orders ||--o{ order_payments : "order_id"
    orders ||--o{ order_reviews : "order_id"
    reviews ||--o{ order_reviews : "review_id"
    product_categories |o--o{ products : "product_category_name"
```

## Tabelas

| tabela | descrição |
|---|---|
| `customers` | Só a identidade do cliente. O endereço fica no pedido, porque 250 clientes compraram com mais de um CEP. |
| `orders` |  |
| `order_items` |  |
| `order_payments` |  |
| `reviews` | Uma avaliação pode cobrir mais de um pedido do mesmo cliente (789 casos, sempre com o mesmo conteúdo). |
| `order_reviews` | Tabela associativa: resolve a relação N:N entre pedidos e avaliações. |
| `products` |  |
| `product_categories` | Domínio das categorias, montado a partir dos produtos (inclui 2 categorias que faltam na tabela de tradução). |
| `sellers` |  |
| `zip_codes` | Uma linha por prefixo de CEP usado por clientes, vendedores ou pela geolocalização. Substitui a geolocalização bruta, que tem ~1 milhão de pontos e não pode ser ligada diretamente. |
