-- One row per zip code prefix used anywhere in the data, with one coordinate.
-- Points outside Brazil are dropped first: for a few prefixes most points are
-- wrong, and the median alone would still land outside the country. The median
-- of what is left is less sensitive to stray points than the average.
-- Prefixes with no usable point are kept with null coordinates, so no customer
-- or seller address loses its zip code.

with all_prefixes as (

    select zip_code_prefix from {{ ref('stg_geolocation') }}
    union
    select customer_zip_code_prefix from {{ ref('stg_customers') }}
    union
    select seller_zip_code_prefix from {{ ref('stg_sellers') }}

),

coordinates as (

    select
        zip_code_prefix,
        median(latitude)  as latitude,
        median(longitude) as longitude,
        count(*)          as source_points

    from {{ ref('stg_geolocation') }}
    where latitude between {{ var('brazil_min_latitude') }} and {{ var('brazil_max_latitude') }}
      and longitude between {{ var('brazil_min_longitude') }} and {{ var('brazil_max_longitude') }}
    group by zip_code_prefix

)

select
    all_prefixes.zip_code_prefix,
    coordinates.latitude,
    coordinates.longitude,
    coalesce(coordinates.source_points, 0) as source_points

from all_prefixes
left join coordinates using (zip_code_prefix)
