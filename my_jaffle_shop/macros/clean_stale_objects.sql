{#

1. queries the information schema of a database
2. finds objects that are >1 week old (no longer maintained)
3. generated automated drop statements
4. has the ability to execute those drop statements

#}

{% macro clean_stale_objects(database=target.database, schema=target.schema, days=7) %}

    {% set sql_query %} 
        select 
            case when table_type = 'VIEW' then 'VIEW' else 'TABLE' end as object_type,
            'DROP ' || object_type || ' {{ database | upper }}.' || table_schema || '.' || table_name || ';' as drop_command
        from {{ database }}.information_schema.tables 
        where table_schema = upper('{{ schema }}')
        and last_altered < dateadd('day', -1 * {{ days }}, current_timestamp())
    {% endset %}

    {% set results = run_query(sql_query) %}

    {# Execute only if we actually found rows #}
    {% if execute and results %}
        {% for row in results %}
            {{ log("Executing: " ~ row[1], info=True) }}
            {% do run_query(row[1]) %}
        {% endfor %}
    {% else %}
        {{ log("No stale objects found to drop.", info=True) }}
    {% endif %}

{% endmacro %}