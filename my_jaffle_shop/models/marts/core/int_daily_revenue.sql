with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2018-01-01' as date)",
        end_date="dateadd(day, 1, current_date())"
    ) }}
),

daily_orders as (
    select
        order_date,
        sum(amount) as daily_revenue
    from {{ ref('fct_orders') }}
    group by order_date
)

select
    cast(d.date_day as date) as date_day,
    coalesce(o.daily_revenue, 0) as revenue
from date_spine d
left join daily_orders o on d.date_day = o.order_date