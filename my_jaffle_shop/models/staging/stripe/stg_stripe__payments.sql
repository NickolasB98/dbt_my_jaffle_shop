with source as (
        select * from {{ source('stripe', 'payments') }}
  ),
  renamed as (
      select
          {{ adapter.quote("ID") }} as payment_id,
        {{ adapter.quote("ORDERID") }} as order_id,
        {{ adapter.quote("PAYMENTMETHOD") }} as payment_method,
        {{ adapter.quote("STATUS") }} as payment_status,
        {{ adapter.quote("AMOUNT") }} as amount,
        {{ adapter.quote("CREATED") }} as created_at,
        {{ adapter.quote("_BATCHED_AT") }} as batched_at

      from source
  )
  select * from renamed
    