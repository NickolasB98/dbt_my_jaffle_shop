{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge'
    ) }}

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
        coalesce(op.amount, 0) as amount
    from orders o 
    left join order_payments op on o.order_id = op.order_id
)

select * from final
{% if is_incremental() %}
    -- this filter will only be applied on an incremental run
    where order_date >= (select max(order_date) from {{ this }})
{% endif %}

order by order_date desc
