{% set foods = ['pizzas', 'pasta', 'sushi', 'tacos', 'burgers'] %}


{%- for food in foods -%}

    {%- if food == 'pizzas' or food == 'pasta' -%}

        {%- set food_type = 'Italian' -%}

    {%- elif food == 'sushi' -%}

        {%- set food_type = 'Japanese'-%}

    {%- elif food == 'tacos' -%}

        {%- set food_type = 'Mexican' -%}

    {%- else -%}
        
        {%- set food_type = 'American'-%}
    
    {%- endif -%}

The delicious {{ food }} are of {{ food_type }} origin!

{% endfor %}


