-- Question: how do customers pay?
-- One order can use more than one method (e.g. card plus voucher), so shares are
-- computed over payments, not over orders.

select
    payment_type,
    count(*)                                              as payments,
    round(100 * count(*) / sum(count(*)) over (), 1)      as payments_share_pct,
    sum(payment_value)                                    as value,
    round(100 * sum(payment_value) / sum(sum(payment_value)) over (), 1)
                                                          as value_share_pct,
    round(avg(payment_installments), 1)                   as average_installments

from {{ ref('fct_payments') }}
group by payment_type
order by payments desc
