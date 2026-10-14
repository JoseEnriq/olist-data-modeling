-- One row per payment of an order. An order can be paid in several parts
-- (e.g. card plus voucher); payment_sequential gives their order and can skip numbers.

with source as (

    select * from {{ source('olist', 'order_payments') }}

),

renamed as (

    select
        order_id,
        cast(payment_sequential as integer)   as payment_sequential,
        payment_type,
        cast(payment_installments as integer) as payment_installments,
        cast(payment_value as decimal(10, 2)) as payment_value

    from source

)

select * from renamed
