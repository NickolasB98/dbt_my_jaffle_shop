with customers as (
    select * from {{ ref('stg_jaffle_shop__customers')}}
),

orders as (
    select * from {{ ref('stg_jaffle_shop__orders')}}
),

customer_orders as (
    select
        o.customer_id,
        min(o.order_date) as first_order_date,
        max(o.order_date) as most_recent_order_date,
        count(o.order_id) as number_of_orders
    from orders o
    group by o.customer_id
),

final as (
    select
        c.customer_id,
        c.first_name,
        c.last_name,
        co.first_order_date,
        co.most_recent_order_date,
        co.number_of_orders
    from customers c 
    left join customer_orders co on c.customer_id = co.customer_id
)

select * from final 



