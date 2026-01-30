{% for j in range(10)%}

    select {{ j }} as number {% if not loop.last %} union all {% endif %}

{% endfor %}

{% set my_string = 'My cool cat' %}
{% set my_second_string = 'My cool capybara' %}
{% set my_fav_number =  12 %}

I have next to me {{ my_string }} and {{ my_second_string }}. I want to write Jinja for {{ my_fav_number }} years!


{# This is a comment it is never shown in compiled SQL #}

{# 

{% … %} is used for statements. 
These perform any function programming 
such as setting a variable or starting a for loop.

{{ … }} is used for expressions. It pulls the jinja to the compiled SQL.
These will print text to the rendered file. 
In most cases in dbt, this will compile your Jinja to pure SQL.

# is used for comments.
This allows us to document our code inline. 
This will not be rendered in the pure SQL that 
you create when you run dbt compile or dbt run.

#}

{% set animals = ['cat', 'dog', 'mouse', 'bunny', 'elephant'] %}



{{ animals[0] }}
{{ animals[1] }}
{{ animals[2] }}
{{ animals[3] }}
{{ animals[4] }} 

{%for animal in animals%}

    my favorite animal is a {{ animal }} 

{% endfor%}
