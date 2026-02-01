with raw_unioned as (
    {{ union_tables_by_pattern(
        database=source('external_orders', 'orders__shopify').database,
        schema_pattern=source('external_orders', 'orders__shopify').schema, 
        table_pattern='ORDERS__%'
    ) }}
)

select
    order_id,
    order_amount,
    order_date,
    -- Extracts 'AMAZON' from 'RAW.DBT_LEARN_JINJA.ORDERS__AMAZON'
    split_part(_dbt_source_relation, '__', 2) as platform_name
from raw_unioned