{% macro union_tables_by_pattern(schema_pattern, table_pattern, database=target.database) %}

    {% set relations = dbt_utils.get_relations_by_pattern(
        schema_pattern=schema_pattern, 
        table_pattern=table_pattern,
        database=database
    ) %}

    {{ dbt_utils.union_relations(
        relations=relations,
        column_override={
            "ORDER_ID": "integer",
            "ORDER_AMOUNT": "float"
        }
    ) }}

{% endmacro %}