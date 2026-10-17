-- Question: how many customers come back to buy again?
-- Customers are people (customer_unique_id), which is why dim_customer exists:
-- counting customer_id would make every order look like a new customer.
-- Only valid orders (not canceled, not unavailable) count as purchases.

with purchases as (

    select customer_key, count(*) as orders
    from {{ ref('fct_orders') }}
    where order_status not in ('canceled', 'unavailable')
    group by customer_key

)

select
    case
        when orders = 1 then '1 pedido'
        when orders = 2 then '2 pedidos'
        else '3 ou mais pedidos'
    end                                                    as customer_group,
    count(*)                                               as customers,
    round(100.0 * count(*) / sum(count(*)) over (), 2)     as customers_pct

from purchases
group by customer_group
order by customer_group
