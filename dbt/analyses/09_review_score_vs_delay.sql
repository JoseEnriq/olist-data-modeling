-- Question: how much does a late delivery hurt the review score?
-- Delivered orders with a review, grouped by how many days after the estimated
-- date they arrived. Orders with several reviews count once, with their average.

with order_scores as (

    select order_id, avg(review_score) as score
    from {{ ref('fct_reviews') }}
    group by order_id

),

delivered as (

    select
        orders.order_id,
        case
            when orders.days_late_vs_estimate <= 0  then '1. no prazo ou antes'
            when orders.days_late_vs_estimate <= 3  then '2. 1 a 3 dias de atraso'
            when orders.days_late_vs_estimate <= 7  then '3. 4 a 7 dias de atraso'
            when orders.days_late_vs_estimate <= 14 then '4. 8 a 14 dias de atraso'
            else                                         '5. mais de 14 dias de atraso'
        end as delay_bucket

    from {{ ref('fct_orders') }} as orders
    where orders.is_delivered

)

select
    delivered.delay_bucket,
    count(*)                                                        as orders,
    round(avg(order_scores.score), 2)                               as average_score,
    round(100.0 * count(*) filter (where order_scores.score <= 2) / count(*), 1)
                                                                    as low_score_pct

from delivered
inner join order_scores
    on delivered.order_id = order_scores.order_id
group by delivered.delay_bucket
order by delivered.delay_bucket
