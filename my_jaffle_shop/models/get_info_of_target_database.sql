{% set database = target.database %}
{% set schema = target.schema %}

select 
    table_type,
    table_schema,
    table_name,
    last_altered,
    case when table_type = 'VIEW' then 'VIEW' else 'TABLE' end as object_type,
    'DROP ' || object_type || ' {{ database | upper }}.' || table_schema || '.' || table_name || ';' as drop_command
from {{ database }}.information_schema.tables 
where table_schema = upper('{{ schema }}')
and last_altered < dateadd('day', -1, current_timestamp())

-- last_altered < dateadd('day', -1, current_timestamp()) means that the table was last altered more than 1 day ago
-- we use this to find stale objects


-- in dates < means older than, > means newer than


