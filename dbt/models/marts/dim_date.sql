-- One row per day. Facts point here through integer keys (YYYYMMDD), once per
-- role: purchase, approval, hand-over to the carrier, delivery, estimate, review.
-- Month and day names are in Portuguese, like the rest of the domain values.

with days as (

    select cast(unnest(generate_series(
        date '{{ var("dim_date_start") }}',
        date '{{ var("dim_date_end") }}',
        interval 1 day
    )) as date) as date

)

select
    {{ date_key('date') }}             as date_key,
    date,
    year(date)                         as year,
    quarter(date)                      as quarter,
    month(date)                        as month,
    [
        'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ][month(date)]                     as month_name,
    strftime(date, '%Y-%m')            as year_month,
    day(date)                          as day_of_month,
    -- ISO numbering: 1 = Monday ... 7 = Sunday.
    isodow(date)                       as day_of_week,
    [
        'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo'
    ][isodow(date)]                    as day_name,
    isodow(date) in (6, 7)             as is_weekend

from days
