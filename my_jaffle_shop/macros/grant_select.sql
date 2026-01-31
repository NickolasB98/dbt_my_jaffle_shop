{% macro grant_select(schema=target.schema, role=target.role, database=target.database) %}

    {% set sql %}
        -- Explicitly scope the schema with the database to prevent "object not found" errors
        grant usage on schema {{ database }}.{{ schema }} to role {{ role }};
        grant select on all tables in schema {{ database }}.{{ schema }} to role {{ role }};
        grant select on all views in schema {{ database }}.{{ schema }} to role {{ role }};
    {% endset %}

    {# Use the correct {% log ... %} syntax so the messages actually print to the terminal #}
    {% do log("Granting select on schema: " ~ database ~ "." ~ schema ~ " to role: " ~ role, info=true) %}

    {% do run_query(sql) %}

    {% do log("Successfully finished granting select!", info=true) %}

{% endmacro %}

