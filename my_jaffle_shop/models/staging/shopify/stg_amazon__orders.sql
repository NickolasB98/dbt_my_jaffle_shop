with source as (
        select * from {{ source('external_orders', 'orders__amazon') }}
  ),
  renamed as (
      select
          {{ adapter.quote("ORDER_ID") }},
        {{ adapter.quote("ORDER_AMOUNT") }},
        {{ adapter.quote("ORDER_DATE") }}

      from source
  )
  select * from renamed
    