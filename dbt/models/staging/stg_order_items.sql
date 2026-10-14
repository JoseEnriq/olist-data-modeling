-- One row per unit of product in an order: buying 2 units creates 2 rows.
-- There is no quantity column; quantity is a count of rows.

with source as (

    select * from {{ source('olist', 'order_items') }}

),

renamed as (

    select
        order_id,
        cast(order_item_id as integer)          as order_item_id,
        product_id,
        seller_id,
        cast(shipping_limit_date as timestamp)  as shipping_limit_at,
        -- Money as decimal so sums do not pick up floating point noise.
        cast(price as decimal(10, 2))           as price,
        cast(freight_value as decimal(10, 2))   as freight_value

    from source

)

select * from renamed
