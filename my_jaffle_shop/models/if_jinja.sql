-- test changing the temperature variable, then press compiled dbt preview
{% set temperature = 12 %}



On a day like this, I especially like 
{% if temperature > 18 %}
    a refreshing lemon sorbet
{% else %}
    a steaming cup of hot chocolate
{% endif %}