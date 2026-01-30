-- This is an intermediate model that pivots the order_items table
-- instead of using a case when for every payment method sum(case when payment_method = 'bank_transfer' then amount else 0 end) as bank_transfer_amount,
-- we can use a jinja loop to create the case when statements
-- use - next to % to remove the whitespace in the compiled SQL

{% set payment_methods = ['bank_transfer', 'credit_card', 'gift_card', 'coupon'] %}


with payments as (
    select * from {{ ref ('stg_stripe__payments')}}
    where payment_status = 'success'
),
pivoted as (
    select 
        order_id,

        {%- for method in payment_methods -%}
            sum(case when payment_methods = '{{ method }}' then amount else 0 end) as {{ method }}_amount
            -- add a comma after every column except the last one
            {%- if not loop.last -%}
                ,
            {% endif %}
        {% endfor%}


    from payments
    group by order_id
)

select * from pivoted;