-- Coordinate samples per zip code prefix, at the source grain (about a million
-- rows, many exact duplicates). Staging only types and renames; reducing to one
-- row per prefix is a modeling decision and happens in the marts.
-- City and state from this table are not used: spellings vary too much.

with source as (

    select * from {{ source('olist', 'geolocation') }}

),

renamed as (

    select
        geolocation_zip_code_prefix              as zip_code_prefix,
        cast(geolocation_lat as double)          as latitude,
        cast(geolocation_lng as double)          as longitude,
        geolocation_city                         as city,
        geolocation_state                        as state

    from source

)

select * from renamed
