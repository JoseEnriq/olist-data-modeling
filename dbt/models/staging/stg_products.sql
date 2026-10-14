-- One row per product. Category values stay in Portuguese; 610 products have
-- no category and no name/description/photo attributes, kept as null here.

with source as (

    select * from {{ source('olist', 'products') }}

),

renamed as (

    select
        product_id,
        product_category_name,
        -- The source columns are misspelled ("lenght").
        cast(product_name_lenght as integer)        as product_name_length,
        cast(product_description_lenght as integer) as product_description_length,
        cast(product_photos_qty as integer)         as product_photos_qty,
        cast(product_weight_g as integer)           as product_weight_g,
        cast(product_length_cm as integer)          as product_length_cm,
        cast(product_height_cm as integer)          as product_height_cm,
        cast(product_width_cm as integer)           as product_width_cm

    from source

)

select * from renamed
