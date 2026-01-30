select
    customer_id,
    order_date,
    {{ dbt_utils.generate_surrogate_key(['customer_id', 'order_date']) }} as pk,
    count(*) as order_count
from {{ ref('stg_jaffle_shop__orders') }}
group by customer_id, order_date

-- use dbt_utils.generate_surrogate_key to create a surrogate key for the daily summary

-- why do we need a surrogate key?
-- because the natural key (customer_id, order_date) is not unique



