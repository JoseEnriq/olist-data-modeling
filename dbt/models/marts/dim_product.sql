-- One row per product. The category is flattened into the dimension (star, not
-- snowflake) and stays in Portuguese. Products without a category get the label
-- "sem_categoria": in a dimension, a blank value breaks filters and charts.

select
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
    product_id,
    coalesce(product_category_name, 'sem_categoria')      as product_category_name,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm

from {{ ref('stg_products') }}
