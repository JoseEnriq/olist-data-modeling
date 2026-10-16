-- One row per seller. Each seller has a single address, so the location is
-- flattened into the dimension instead of pointing to dim_location.

select
    {{ dbt_utils.generate_surrogate_key(['sellers.seller_id']) }} as seller_key,
    sellers.seller_id,
    sellers.seller_zip_code_prefix,
    sellers.seller_city,
    sellers.seller_state,
    zip_codes.latitude,
    zip_codes.longitude

from {{ ref('stg_sellers') }} as sellers
left join {{ ref('int_zip_codes') }} as zip_codes
    on sellers.seller_zip_code_prefix = zip_codes.zip_code_prefix
