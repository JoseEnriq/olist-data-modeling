-- Delivery address as typed in the order: one row per combination of zip
-- prefix, city and state. A single row per prefix would force us to pick a
-- "right" state, because some prefixes appear with more than one.

with addresses as (

    select distinct
        customer_zip_code_prefix as zip_code_prefix,
        customer_city            as city,
        customer_state           as state

    from {{ ref('stg_customers') }}

)

select
    {{ dbt_utils.generate_surrogate_key(['addresses.zip_code_prefix', 'addresses.city', 'addresses.state']) }}
                                as location_key,
    addresses.zip_code_prefix,
    addresses.city,
    addresses.state,
    zip_codes.latitude,
    zip_codes.longitude

from addresses
left join {{ ref('int_zip_codes') }} as zip_codes
    on addresses.zip_code_prefix = zip_codes.zip_code_prefix
