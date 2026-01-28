with source as (
        select * from {{ source('jaffle_shop', 'orders') }}
  ),
  renamed as (
      select
          {{ adapter.quote("ID") }} as order_id,
        {{ adapter.quote("USER_ID") }} as customer_id,
        {{ adapter.quote("ORDER_DATE") }},
        {{ adapter.quote("STATUS") }} as order_status,
        {{ adapter.quote("_ETL_LOADED_AT") }}

      from source
  )
  select * from renamed
    