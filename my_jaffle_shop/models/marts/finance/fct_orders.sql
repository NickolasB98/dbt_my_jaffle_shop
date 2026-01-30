{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
    ) }}

    -- sync_all_columns will delete the no longer existing columns, and add the new columns
    -- this is useful for when you want to add new columns to your model
    -- without having to manually update the model

    -- append_new_columns will add the new columns to the model
    -- without deleting the existing columns
    -- this is useful for when you want to add new columns to your model
    -- without losing the existing ones (we would keep all, modified and old columns)

with orders as (
    select * from {{ ref('stg_jaffle_shop__orders')}}
),

payments as (
    select * from {{ ref('stg_stripe__payments')}}
),

order_payments as (
    select
        order_id,
        sum(case when payment_status = 'success' then amount else 0 end) as amount
    from {{ ref('stg_stripe__payments')}}
    group by order_id
),

final as (
    select
        o.order_id,
        o.customer_id,
        o.order_date,
        o.order_status,
        coalesce(op.amount, 0) as amount
    from orders o 
    left join order_payments op on o.order_id = op.order_id
)

select * from final

{% if is_incremental() %}
    -- this filter will only be applied on an incremental run
    -- we add 3 days to the max order date to account for any late arriving orders
    where order_date >= (select dateadd(day, -3, max(order_date)) from {{ this }})


    -- trick to backfill the whole table - full refresh
    -- where 1=1
{% endif %}

order by order_date desc
