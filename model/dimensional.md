# Modelo dimensional (star schema)

Gerado por `scripts/render_diagrams.py` a partir de [dimensional.dbml](dimensional.dbml). Não edite à mão: altere o `.dbml` e rode o script de novo.

Legenda: `PK` chave primária, `FK` chave estrangeira, `UK` valor único. `||--o{` = um para zero ou muitos; `|o--o{` = a chave estrangeira pode ser nula.

```mermaid
erDiagram
    dim_date {
        int date_key PK
        date date UK
        int year
        int quarter
        int month
        varchar month_name
        varchar year_month
        int day_of_month
        int day_of_week
        varchar day_name
        boolean is_weekend
    }
    dim_customer {
        varchar customer_key PK
        varchar customer_unique_id UK
        timestamp first_purchased_at
        varchar cohort_month
    }
    dim_location {
        varchar location_key PK
        varchar zip_code_prefix
        varchar city
        char state
        double latitude
        double longitude
    }
    dim_product {
        varchar product_key PK
        varchar product_id UK
        varchar product_category_name
        int product_name_length
        int product_description_length
        int product_photos_qty
        int product_weight_g
        int product_length_cm
        int product_height_cm
        int product_width_cm
    }
    dim_seller {
        varchar seller_key PK
        varchar seller_id UK
        varchar seller_zip_code_prefix
        varchar seller_city
        char seller_state
        double latitude
        double longitude
    }
    fct_order_items {
        varchar order_id PK
        int order_item_id PK
        varchar customer_key FK
        varchar delivery_location_key FK
        varchar product_key FK
        varchar seller_key FK
        int purchase_date_key FK
        varchar order_status
        timestamp shipping_limit_at
        decimal price
        decimal freight_value
    }
    fct_orders {
        varchar order_id PK
        varchar customer_key FK
        varchar delivery_location_key FK
        int purchase_date_key FK
        int approved_date_key FK
        int delivered_to_carrier_date_key FK
        int delivered_to_customer_date_key FK
        int estimated_delivery_date_key FK
        varchar order_status
        timestamp purchased_at
        timestamp approved_at
        timestamp delivered_to_carrier_at
        timestamp delivered_to_customer_at
        date estimated_delivery_date
        int items_count
        decimal items_price_total
        decimal freight_total
        decimal payment_total
        decimal hours_to_approve
        decimal days_to_deliver
        decimal days_late_vs_estimate
        boolean is_delivered
        boolean is_late
    }
    fct_payments {
        varchar order_id PK
        int payment_sequential PK
        varchar customer_key FK
        int purchase_date_key FK
        varchar payment_type
        int payment_installments
        decimal payment_value
    }
    fct_reviews {
        varchar review_id PK
        varchar order_id PK
        varchar customer_key FK
        int review_created_date_key FK
        smallint review_score
        boolean has_comment
        decimal hours_to_answer
    }
    dim_customer ||--o{ fct_order_items : "customer_key"
    dim_location ||--o{ fct_order_items : "delivery_location_key"
    dim_product ||--o{ fct_order_items : "product_key"
    dim_seller ||--o{ fct_order_items : "seller_key"
    dim_date ||--o{ fct_order_items : "purchase_date_key"
    dim_customer ||--o{ fct_orders : "customer_key"
    dim_location ||--o{ fct_orders : "delivery_location_key"
    dim_date ||--o{ fct_orders : "purchase_date_key"
    dim_date |o--o{ fct_orders : "approved_date_key"
    dim_date |o--o{ fct_orders : "delivered_to_carrier_date_key"
    dim_date |o--o{ fct_orders : "delivered_to_customer_date_key"
    dim_date ||--o{ fct_orders : "estimated_delivery_date_key"
    dim_customer ||--o{ fct_payments : "customer_key"
    dim_date ||--o{ fct_payments : "purchase_date_key"
    dim_customer ||--o{ fct_reviews : "customer_key"
    dim_date ||--o{ fct_reviews : "review_created_date_key"
```

## Tabelas

| tabela | descrição |
|---|---|
| `dim_date` | Um dia por linha, de 2016-01-01 a 2018-12-31. Usada em vários papéis: compra, aprovação, envio, entrega, entrega prevista, avaliação. |
| `dim_customer` | Uma linha por pessoa. O endereço não fica aqui: ele muda de pedido para pedido (ver dim_location). |
| `dim_location` | Endereço de entrega como foi informado no pedido. Uma linha por combinação de prefixo, cidade e estado, porque o mesmo prefixo aparece com estados diferentes. |
| `dim_product` |  |
| `dim_seller` | O vendedor tem um endereço só, então a localização fica achatada na própria dimensão. |
| `fct_order_items` | Fato transacional. Grão: uma unidade de produto vendida num pedido. |
| `fct_orders` | Accumulating snapshot. Grão: um pedido, com uma coluna de data para cada etapa do ciclo. Datas nulas = etapa ainda não aconteceu. |
| `fct_payments` | Fato transacional. Grão: um pagamento de um pedido. |
| `fct_reviews` | Grão: uma avaliação ligada a um pedido. Uma avaliação que cobre 2 pedidos gera 2 linhas; para contar avaliações, use count(distinct review_id). |
