-- create the test for the stg_stripe__payments model
-- assert that the total amount is positive
-- logic of tests: if there is any order with total amount less than 0, then the test fails

select 
    order_id,
    sum(amount) as total_amount
from {{ ref('stg_stripe__payments') }}
group by order_id
having total_amount < 0

-- run the sql in preview and if no data is returned, then the test passes


