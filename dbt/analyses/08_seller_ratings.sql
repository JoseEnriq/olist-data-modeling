-- Question: which sellers have the best and the worst review scores?
-- A review belongs to an order, not to a seller. To attribute it fairly, only
-- orders with a single seller are used (1,278 orders have more than one).
-- Orders with several reviews count once, with their average score.
-- Sellers need at least 50 reviewed orders, so a few orders do not decide the rank.

with order_scores as (

    select order_id, avg(review_score) as score
    from {{ ref('fct_reviews') }}
    group by order_id

),

single_seller_orders as (

    select order_id, any_value(seller_key) as seller_key
    from {{ ref('fct_order_items') }}
    group by order_id
    having count(distinct seller_key) = 1

),

seller_scores as (

    select
        orders.seller_key,
        count(*)                                     as reviewed_orders,
        avg(order_scores.score)                      as average_score,
        count(*) filter (where order_scores.score <= 2) * 100.0 / count(*)
                                                     as low_score_pct

    from single_seller_orders as orders
    inner join order_scores
        on orders.order_id = order_scores.order_id
    group by orders.seller_key
    having count(*) >= 50

),

ranked as (

    select
        seller_scores.*,
        row_number() over (order by average_score desc, reviewed_orders desc) as best_rank,
        row_number() over (order by average_score asc, reviewed_orders desc)  as worst_rank

    from seller_scores

)

select
    case when ranked.best_rank <= 10 then 'top 10' else 'bottom 10' end as ranking,
    sellers.seller_id,
    sellers.seller_state,
    ranked.reviewed_orders,
    round(ranked.average_score, 2)  as average_score,
    round(ranked.low_score_pct, 1)  as low_score_pct

from ranked
inner join {{ ref('dim_seller') }} as sellers
    on ranked.seller_key = sellers.seller_key

where ranked.best_rank <= 10 or ranked.worst_rank <= 10
order by ranked.average_score desc
