{% macro test() %}
    {{ log("--- DEBUG: MACRO IS STARTING ---", info=True) }}
    
    {% set query = "SELECT 1" %}
    {% do run_query(query) %}
    
    {{ log("--- DEBUG: MACRO FINISHED ---", info=True) }}
{% endmacro %}