select 
    order_id


from {{ ref('stg_stripe__payments')}}