-- One row per review and order. The same review_id can cover up to 3 orders of
-- the same customer, always with the same content; the split into a review
-- entity happens in the marts.

with source as (

    select * from {{ source('olist', 'order_reviews') }}

),

renamed as (

    select
        review_id,
        order_id,
        cast(review_score as smallint)            as review_score,
        review_comment_title,
        review_comment_message,
        -- Kept as timestamp: 85 reviews have a time part.
        cast(review_creation_date as timestamp)   as created_at,
        cast(review_answer_timestamp as timestamp) as answered_at

    from source

)

select * from renamed
