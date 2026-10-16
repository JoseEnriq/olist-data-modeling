-- Grain: one review linked to one order. A review that covers 2 orders gives
-- 2 rows, so the average score per order uses the rows as they are, while the
-- number of reviews is count(distinct review_id).

select
    reviews.review_id,
    reviews.order_id,
    orders.customer_key,
    {{ date_key('reviews.created_at') }}                   as review_created_date_key,
    reviews.review_score,
    -- A comment counts only if the title or the message has actual text.
    coalesce(trim(reviews.review_comment_title), '') <> ''
        or coalesce(trim(reviews.review_comment_message), '') <> ''
                                                           as has_comment,
    cast(date_diff('second', reviews.created_at, reviews.answered_at) / 3600
         as decimal(10, 2))                                as hours_to_answer

from {{ ref('stg_order_reviews') }} as reviews
inner join {{ ref('int_orders') }} as orders
    on reviews.order_id = orders.order_id
