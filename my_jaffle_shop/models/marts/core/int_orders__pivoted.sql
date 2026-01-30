{% set payment_methods = ['bank_transfer', 'credit_card', 'gift_card', 'coupon'] %}


with payments as (
    select * from {{ ref ('stg_stripe__payments')}}
    where payment_status = 'success'
),
pivoted as (
    select 
        order_id,

        {%- for method in payment_methods -%}
            sum(case when payment_method = '{{ method }}' then amount else 0 end) as {{ method }}_amount
            {%- if not loop.last -%}
                ,
            {% endif %}
        {% endfor%}


    from payments
    group by order_id
)

select * from pivoted