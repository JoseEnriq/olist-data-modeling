-- One row per customer_id. customer_id is generated per order; the person is
-- customer_unique_id. The address belongs to the order, not to the person.

with source as (

    select * from {{ source('olist', 'customers') }}

),

renamed as (

    select
        customer_id,
        customer_unique_id,
        -- Kept as text: prefixes in the São Paulo area start with 0.
        customer_zip_code_prefix,
        customer_city,
        customer_state

    from source

)

select * from renamed
