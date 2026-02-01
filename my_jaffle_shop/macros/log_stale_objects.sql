{% macro log_stale_objects(database=target.database, schema=target.schema, days=1) %}

    {% set sql_query %} 
        select 
            table_type,
            table_name,
            last_altered,
            'DROP ' || table_type || ' {{ database | upper }}.' || table_schema || '.' || table_name || ';' as drop_command
        from {{ database }}.information_schema.tables 
        where table_schema = upper('{{ schema }}')
        and last_altered < dateadd('day', -1 * {{ days }}, current_timestamp())
        order by last_altered asc
    {% endset %}

    {% set results = run_query(sql_query) %}

    {% if execute and results %}
        {{ log("--- AUDIT REPORT: STALE OBJECTS FOUND ---", info=True) }}
        {% for row in results %}
            {{ log("OBJECT: " ~ row[1] ~ " | TYPE: " ~ row[0] ~ " | LAST ALTERED: " ~ row[2], info=True) }}
            {{ log("SUGGESTED COMMAND: " ~ row[3], info=True) }}
            {{ log("-----------------------------------------", info=True) }}
        {% endfor %}
        {{ log("TOTAL OBJECTS IDENTIFIED: " ~ results | length, info=True) }}
    {% else %}
        {{ log("No stale objects found for the last " ~ days ~ " days.", info=True) }}
    {% endif %}

{% endmacro %}