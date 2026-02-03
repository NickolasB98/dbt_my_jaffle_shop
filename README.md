# Jaffle Shop Analytics: End-to-End Data Pipeline with Snowflake, dbt & Streamlit

A complete data engineering and analytics project demonstrating modern data stack best practices. This project implements a full ELT pipeline from raw data ingestion through transformation to interactive dashboards.

## Project Overview

This project simulates a real-world e-commerce analytics platform for "Jaffle Shop", a fictional coffee shop chain. It showcases:

- **Data Warehousing** with Snowflake
- **Data Transformation** with dbt (data build tool)
- **Data Visualization** with Streamlit dashboards

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PROJECT ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   S3 Bucket          Snowflake            dbt                 Streamlit         │
│   (Raw Data)         (Data Warehouse)     (Transformations)   (Dashboards)      │
│                                                                                  │
│   ┌─────────┐        ┌─────────────┐      ┌─────────────┐     ┌─────────────┐   │
│   │CUSTOMERS│───────>│  RAW.       │      │  STAGING    │     │  Analytics  │   │
│   │ORDERS   │        │  JAFFLE_SHOP│─────>│  LAYER      │────>│  Dashboard  │   │
│   │PAYMENTS │───────>│  RAW.STRIPE │      │  (Views)    │     │             │   │
│   └─────────┘        └─────────────┘      └──────┬──────┘     │  Customer   │   │
│                                                  │            │  360        │   │
│                                                  v            │             │   │
│                                           ┌─────────────┐     │  Operations │   │
│                                           │   MARTS     │────>│  Dashboard  │   │
│                                           │   (Tables)  │     └─────────────┘   │
│                                           └─────────────┘                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **Snowflake** | Cloud Data Warehouse | Enterprise |
| **dbt Core** | Data Transformation | 1.9+ |
| **Streamlit** | Interactive Dashboards | 1.53+ |
| **Python** | Dashboard Development | 3.12 |

### dbt Packages Used

| Package | Purpose |
|---------|---------|
| `dbt_utils` | Utility functions (date spine, surrogate keys) |
| `codegen` | Auto-generate staging models and YAML |
| `dbt_artifacts` | Track dbt run metadata |
| `snowflake_spend` | Monitor Snowflake costs |

---

## Data Sources

The project uses three source tables loaded from S3 into Snowflake's RAW database:

| Source | Table | Description | Records |
|--------|-------|-------------|---------|
| `jaffle_shop` | `CUSTOMERS` | Customer master data (ID, name) | 104 |
| `jaffle_shop` | `ORDERS` | Order transactions (date, status) | 106 |
| `stripe` | `PAYMENTS` | Payment details (method, amount) | 127 |

### Data Quality Tests

All source tables include built-in data quality tests:
- **Primary Key Validation**: `unique` and `not_null` tests on all IDs
- **Referential Integrity**: Foreign key relationships validated
- **Accepted Values**: Order status constrained to valid values
- **Freshness Checks**: Alerts if source data is stale (>7 days warning, >14 days error)

---

## Data Transformation Layer (dbt)

### Project Structure

```
my_jaffle_shop/
├── models/
│   ├── staging/                    # Raw data cleaning & standardization
│   │   ├── jaffle_shop/
│   │   │   ├── stg_jaffle_shop__customers.sql
│   │   │   ├── stg_jaffle_shop__orders.sql
│   │   │   └── _src_jaffle_shop.yml
│   │   └── stripe/
│   │       ├── stg_stripe__payments.sql
│   │       └── _src_stripe.yml
│   │
│   └── marts/                      # Business-ready analytics tables
│       ├── core/
│       │   ├── int_customers_daily_summary.sql
│       │   ├── int_daily_revenue.sql
│       │   └── int_orders__pivoted.sql
│       ├── finance/
│       │   └── fct_orders.sql      # Fact table (incremental)
│       └── marketing/
│           └── dim_customers.sql   # Dimension table
│
├── macros/
│   └── cents_to_dollars.sql        # Reusable currency conversion
│
├── tests/                          # Custom data tests
├── seeds/                          # Static reference data
└── dbt_project.yml                 # Project configuration
```

### Layer Architecture

#### 1. Staging Layer (Views)

**Purpose**: Clean and standardize raw data without business logic

| Model | Source | Transformations |
|-------|--------|-----------------|
| `stg_jaffle_shop__customers` | RAW.JAFFLE_SHOP.CUSTOMERS | Column renaming, type casting |
| `stg_jaffle_shop__orders` | RAW.JAFFLE_SHOP.ORDERS | Rename `id` → `order_id`, `user_id` → `customer_id` |
| `stg_stripe__payments` | RAW.STRIPE.PAYMENTS | Currency conversion (cents → dollars), column standardization |

**Materialization**: Views (always up-to-date, cost-efficient for staging)

#### 2. Intermediate Layer (Tables)

**Purpose**: Reusable business logic components

| Model | Description | Key Techniques |
|-------|-------------|----------------|
| `int_customers_daily_summary` | Daily order counts per customer | Surrogate key generation using `dbt_utils.generate_surrogate_key()` |
| `int_daily_revenue` | Complete date spine with revenue | `dbt_utils.date_spine()` for gap-free time series |
| `int_orders__pivoted` | Payment methods pivoted to columns | Jinja for-loops for dynamic SQL generation |

#### 3. Marts Layer (Tables)

**Purpose**: Business-ready fact and dimension tables for analytics

##### FCT_ORDERS (Finance Mart)
```sql
-- Incremental loading strategy with merge
{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
) }}
```

| Column | Description |
|--------|-------------|
| `order_id` | Primary key |
| `customer_id` | Foreign key to dim_customers |
| `order_date` | Transaction date |
| `order_status` | placed / shipped / completed / return_pending / returned |
| `amount` | Total payment amount (dollars) |

**Key Features**:
- **Incremental Loading**: Only processes new/changed records
- **Late-Arriving Data Handling**: 3-day lookback window
- **Schema Evolution**: Automatically syncs column changes

##### DIM_CUSTOMERS (Marketing Mart)
| Column | Description |
|--------|-------------|
| `customer_id` | Primary key |
| `first_name` | Customer first name |
| `last_name` | Customer last name |
| `first_order_date` | Customer acquisition date |
| `most_recent_order_date` | Last activity date |
| `number_of_orders` | Lifetime order count |

### Data Lineage

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LINEAGE                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   SOURCES                    STAGING                      MARTS                  │
│                                                                                  │
│   RAW.JAFFLE_SHOP.          stg_jaffle_shop__            ┌─────────────────┐    │
│   CUSTOMERS ───────────────> customers ─────────────────>│  DIM_CUSTOMERS  │    │
│                                    │                     │  (marketing)    │    │
│                                    │                     └─────────────────┘    │
│   RAW.JAFFLE_SHOP.                 │                            ^               │
│   ORDERS ──────────────────> stg_jaffle_shop__ ─────────────────┘               │
│                              orders ─────────────┐                              │
│                                    │             │       ┌─────────────────┐    │
│                                    │             └──────>│   FCT_ORDERS    │    │
│   RAW.STRIPE.                      │                     │   (finance)     │    │
│   PAYMENTS ────────────────> stg_stripe__ ──────────────>│   [incremental] │    │
│                              payments                    └────────┬────────┘    │
│                                                                   │             │
│                                                                   v             │
│                                                          ┌─────────────────┐    │
│                                                          │INT_DAILY_REVENUE│    │
│                                                          │   (core)        │    │
│                                                          └─────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### dbt Best Practices Demonstrated

| Practice | Implementation |
|----------|----------------|
| **Modular Design** | Separation of staging, intermediate, and marts layers |
| **DRY Principle** | Reusable macros (`cents_to_dollars`) |
| **Incremental Models** | Efficient processing of fact tables |
| **Data Testing** | Comprehensive tests on all models |
| **Documentation** | YAML descriptions for all models and columns |
| **Source Freshness** | Automated staleness monitoring |
| **Materialization Strategy** | Views for staging, tables for marts |

---

## Analytics Dashboards (Streamlit)

Three interactive dashboards built with Streamlit, connecting directly to Snowflake:

### 1. Jaffle Shop Analytics Dashboard
**File**: `streamlit_app.py`

The main executive dashboard providing a high-level business overview.

**Features**:
- **KPI Cards**: Total Revenue, Orders, Customers, Avg Order Value (with sparklines)
- **Revenue Trends**: Monthly revenue line chart
- **Order Status Breakdown**: Revenue by status (completed, shipped, returned, etc.)
- **Customer Order Frequency**: Distribution of repeat vs one-time buyers
- **Top Customers**: Ranked by total spend
- **Recent Orders Table**: Detailed transaction view

**Interactive Filters**:
- Date range picker
- Order status multi-select

---

### 2. Customer 360 Dashboard
**File**: `customer_360_app.py`

Deep dive into customer behavior and lifetime value analysis.

**Features**:
- **Customer Segmentation**: High/Medium/Low value tiers based on spend percentiles
- **Order Frequency Distribution**: 1, 2, 3, 4-5, 6+ orders buckets
- **Cohort Analysis**: Customer acquisition trends by first order month
- **LTV Analysis**: Top customers and lifetime value distribution
- **At-Risk Identification**: Customers inactive for 30+ days
- **Inactive Customers**: Never-ordered customer list

**Business Value**:
- Identify high-value customers for retention programs
- Target at-risk customers before churn
- Understand customer acquisition trends

---

### 3. Operations Dashboard
**File**: `operations_app.py`

Operational metrics focused on order fulfillment and returns.

**Features**:
- **Order Funnel**: Visual progression (Placed → Shipped → Completed)
- **Fulfillment Rate**: Percentage of completed orders
- **Return Rate**: Track return trends and revenue impact
- **Daily/Weekly/Monthly Volume**: Order trend analysis
- **Return Analysis**: Detailed breakdown of returned orders
- **Revenue Impact**: Realized vs pending vs lost revenue

**Business Value**:
- Monitor fulfillment performance
- Track return rates and identify issues
- Forecast operational capacity needs

---

## Database Schema

### Snowflake Architecture

```
SNOWFLAKE ACCOUNT
│
├── RAW (Database) ─────────────────── Source Data
│   ├── JAFFLE_SHOP (Schema)
│   │   ├── CUSTOMERS (Table)
│   │   └── ORDERS (Table)
│   └── STRIPE (Schema)
│       └── PAYMENTS (Table)
│
└── PC_DBT_DB (Database) ─────────────── Transformed Data
    └── DBT_NBINIARIS (Schema)
        ├── stg_jaffle_shop__customers (View)
        ├── stg_jaffle_shop__orders (View)
        ├── stg_stripe__payments (View)
        ├── INT_CUSTOMERS_DAILY_SUMMARY (Table)
        ├── INT_DAILY_REVENUE (Table)
        ├── INT_ORDERS__PIVOTED (Table)
        ├── FCT_ORDERS (Table) [Incremental]
        └── DIM_CUSTOMERS (Table)
```

---

## Key Technical Achievements

### 1. Incremental Data Loading
Implemented efficient incremental loading for the fact table:
```sql
{% if is_incremental() %}
    where order_date >= (select dateadd(day, -3, max(order_date)) from {{ this }})
{% endif %}
```
- Reduces processing time on subsequent runs
- Handles late-arriving data with 3-day lookback
- Uses MERGE strategy for upserts

### 2. Dynamic SQL with Jinja
Payment methods pivoting using Jinja loops:
```sql
{% set payment_methods = ['bank_transfer', 'credit_card', 'gift_card', 'coupon'] %}

{%- for method in payment_methods -%}
    sum(case when payment_method = '{{ method }}' then amount else 0 end) 
    as {{ method }}_amount
{% endfor %}
```

### 3. Date Spine Generation
Gap-free time series using dbt_utils:
```sql
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2018-01-01' as date)",
    end_date="dateadd(day, 1, current_date())"
) }}
```

### 4. Surrogate Key Generation
Composite primary keys for daily summaries:
```sql
{{ dbt_utils.generate_surrogate_key(['customer_id', 'order_date']) }} as pk
```

### 5. Reusable Macros
Currency conversion encapsulated in a macro:
```sql
{% macro cents_to_dollars(column_name) %}
    {{ column_name }} / 100
{% endmacro %}
```

---

## Project Statistics

| Metric | Count |
|--------|-------|
| dbt Models | 14 |
| Data Sources | 5 tables |
| Custom Macros | 6 |
| Data Tests | 15 |
| Streamlit Dashboards | 3 |
| Total Lines of SQL | ~200 |
| Total Lines of Python | ~830 |

---

## How to Run

### Prerequisites
- Snowflake account with appropriate permissions
- Python 3.12+
- dbt Core installed

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/snowflake-dbt-project.git
cd snowflake-dbt-project
```

2. **Install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate
pip install dbt-snowflake streamlit snowflake-snowpark-python
```

3. **Configure dbt profile** (`~/.dbt/profiles.yml`)
```yaml
my_jaffle_shop:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: your_account
      user: your_user
      password: your_password
      warehouse: your_warehouse
      database: PC_DBT_DB
      schema: DBT_YOUR_SCHEMA
```

4. **Run dbt**
```bash
cd my_jaffle_shop
dbt deps        # Install packages
dbt build       # Run models and tests
```

5. **Configure Streamlit** (`.streamlit/secrets.toml`)
```toml
[connections.snowflake]
account = "your_account"
user = "your_user"
authenticator = "externalbrowser"
warehouse = "your_warehouse"
database = "PC_DBT_DB"
schema = "DBT_YOUR_SCHEMA"
```

6. **Launch Dashboards**
```bash
# Main Analytics Dashboard
streamlit run streamlit_app.py

# Customer 360 Dashboard
streamlit run customer_360_app.py

# Operations Dashboard
streamlit run operations_app.py
```

---

## Skills Demonstrated

| Category | Skills |
|----------|--------|
| **Data Engineering** | ELT pipelines, incremental loading, data modeling |
| **SQL** | CTEs, window functions, aggregations, joins |
| **dbt** | Staging/marts pattern, macros, tests, documentation |
| **Snowflake** | Cloud data warehouse, schema design, performance |
| **Python** | Pandas, data manipulation, visualization |
| **Streamlit** | Interactive dashboards, caching, Snowflake integration |
| **Data Modeling** | Star schema, fact/dimension tables, surrogate keys |
| **Best Practices** | Version control, documentation, testing, modularity |

---

## Future Enhancements

- [ ] Add CI/CD pipeline with GitHub Actions
- [ ] Implement data quality monitoring with Elementary
- [ ] Add more complex metrics (customer churn prediction, RFM segmentation)
- [ ] Deploy dashboards to Streamlit Cloud or Snowflake Native App

---

## Author

**Nikolas** - Data Analyst

*This project was built as part of my learning journey with the modern data stack. It demonstrates practical skills in data engineering, transformation, and visualization using industry-standard tools.*

---

## License

This project is for educational and portfolio purposes.
