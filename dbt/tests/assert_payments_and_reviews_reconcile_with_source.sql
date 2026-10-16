-- fct_payments and fct_reviews must keep every source row; payments must keep
-- the same total value.

with checks as (

    select
        'fct_payments rows'  as check_name,
        (select count(*) from {{ source('olist', 'order_payments') }}) as source_value,
        (select count(*) from {{ ref('fct_payments') }})              as fact_value

    union all

    select
        'fct_payments value',
        (select sum(cast(payment_value as decimal(18, 2))) from {{ source('olist', 'order_payments') }}),
        (select sum(payment_value) from {{ ref('fct_payments') }})

    union all

    select
        'fct_reviews rows',
        (select count(*) from {{ source('olist', 'order_reviews') }}),
        (select count(*) from {{ ref('fct_reviews') }})

)

select *
from checks
where source_value <> fact_value
