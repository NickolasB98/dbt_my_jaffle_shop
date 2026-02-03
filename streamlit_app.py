import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(
    page_title="Jaffle Shop Analytics",
    page_icon=":coffee:",
    layout="wide"
)

st.title(":coffee: Jaffle Shop Analytics")

# Connect to Snowflake
conn = st.connection("snowflake")

# --- Load Data ---
@st.cache_data(ttl=timedelta(minutes=10))
def load_data():
    orders = conn.query("""
        SELECT 
            ORDER_ID,
            CUSTOMER_ID,
            ORDER_DATE::DATE as ORDER_DATE,
            AMOUNT,
            ORDER_STATUS
        FROM PC_DBT_DB.DBT_NBINIARIS.FCT_ORDERS
    """)
    
    customers = conn.query("""
        SELECT 
            CUSTOMER_ID,
            FIRST_NAME,
            LAST_NAME,
            FIRST_ORDER_DATE::DATE as FIRST_ORDER_DATE,
            MOST_RECENT_ORDER_DATE::DATE as MOST_RECENT_ORDER_DATE,
            NUMBER_OF_ORDERS
        FROM PC_DBT_DB.DBT_NBINIARIS.DIM_CUSTOMERS
    """)
    
    daily_revenue = conn.query("""
        SELECT 
            DATE_DAY::DATE as DATE_DAY,
            REVENUE
        FROM PC_DBT_DB.DBT_NBINIARIS.INT_DAILY_REVENUE
        ORDER BY DATE_DAY
    """)
    
    return orders, customers, daily_revenue

orders_df, customers_df, daily_revenue_df = load_data()

# --- Sidebar Filters ---
with st.sidebar:
    st.header("Filters")
    
    # Date range filter
    min_date = orders_df["ORDER_DATE"].min()
    max_date = orders_df["ORDER_DATE"].max()
    
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Order status filter
    all_statuses = orders_df["ORDER_STATUS"].unique().tolist()
    selected_statuses = st.multiselect(
        "Order Status",
        options=all_statuses,
        default=all_statuses
    )

# Apply filters
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_orders = orders_df[
        (orders_df["ORDER_DATE"] >= start_date) &
        (orders_df["ORDER_DATE"] <= end_date) &
        (orders_df["ORDER_STATUS"].isin(selected_statuses))
    ]
else:
    filtered_orders = orders_df[orders_df["ORDER_STATUS"].isin(selected_statuses)]

# --- KPI Metrics ---
total_revenue = filtered_orders["AMOUNT"].sum()
total_orders = len(filtered_orders)
total_customers = filtered_orders["CUSTOMER_ID"].nunique()
avg_order_value = filtered_orders["AMOUNT"].mean() if total_orders > 0 else 0

# Calculate sparkline data (last 7 data points of daily revenue)
revenue_trend = daily_revenue_df["REVENUE"].tail(14).tolist()
order_trend = filtered_orders.groupby("ORDER_DATE").size().tail(14).tolist()

with st.container(horizontal=True):
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.0f}",
        border=True,
        chart_data=revenue_trend,
        chart_type="line"
    )
    st.metric(
        "Total Orders",
        f"{total_orders:,}",
        border=True,
        chart_data=order_trend if order_trend else None,
        chart_type="bar"
    )
    st.metric(
        "Unique Customers",
        f"{total_customers:,}",
        border=True
    )
    st.metric(
        "Avg Order Value",
        f"${avg_order_value:,.2f}",
        border=True
    )

st.divider()

# --- Charts Row ---
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Revenue Over Time")
        
        # Group by month for cleaner visualization
        monthly_revenue = filtered_orders.copy()
        monthly_revenue["MONTH"] = pd.to_datetime(monthly_revenue["ORDER_DATE"]).dt.to_period("M").astype(str)
        monthly_agg = monthly_revenue.groupby("MONTH")["AMOUNT"].sum().reset_index()
        
        st.line_chart(monthly_agg, x="MONTH", y="AMOUNT", use_container_width=True)

with col2:
    with st.container(border=True):
        st.subheader("Orders by Status")
        
        status_counts = filtered_orders.groupby("ORDER_STATUS").agg(
            count=("ORDER_ID", "count"),
            revenue=("AMOUNT", "sum")
        ).reset_index()
        
        st.bar_chart(status_counts, x="ORDER_STATUS", y="revenue", use_container_width=True)

# --- Second Row ---
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("Customer Order Frequency")
        
        customers_with_orders = customers_df[customers_df["NUMBER_OF_ORDERS"].notna()].copy()
        customers_with_orders["ORDER_BUCKET"] = pd.cut(
            customers_with_orders["NUMBER_OF_ORDERS"],
            bins=[0, 1, 2, 3, float("inf")],
            labels=["1 order", "2 orders", "3 orders", "4+ orders"]
        )
        
        bucket_counts = customers_with_orders["ORDER_BUCKET"].value_counts().reset_index()
        bucket_counts.columns = ["Order Frequency", "Customers"]
        
        st.bar_chart(bucket_counts, x="Order Frequency", y="Customers", use_container_width=True)

with col4:
    with st.container(border=True):
        st.subheader("Top 10 Customers by Revenue")
        
        top_customers = filtered_orders.groupby("CUSTOMER_ID")["AMOUNT"].sum().reset_index()
        top_customers = top_customers.nlargest(10, "AMOUNT")
        top_customers = top_customers.merge(
            customers_df[["CUSTOMER_ID", "FIRST_NAME", "LAST_NAME"]],
            on="CUSTOMER_ID",
            how="left"
        )
        top_customers["NAME"] = top_customers["FIRST_NAME"] + " " + top_customers["LAST_NAME"]
        
        st.bar_chart(top_customers, x="NAME", y="AMOUNT", horizontal=True, use_container_width=True)

# --- Data Table ---
with st.container(border=True):
    st.subheader("Recent Orders")
    
    recent_orders = filtered_orders.merge(
        customers_df[["CUSTOMER_ID", "FIRST_NAME", "LAST_NAME"]],
        on="CUSTOMER_ID",
        how="left"
    )
    recent_orders["CUSTOMER_NAME"] = recent_orders["FIRST_NAME"] + " " + recent_orders["LAST_NAME"]
    
    display_cols = ["ORDER_ID", "CUSTOMER_NAME", "ORDER_DATE", "AMOUNT", "ORDER_STATUS"]
    recent_orders = recent_orders[display_cols].sort_values("ORDER_DATE", ascending=False).head(20)
    
    st.dataframe(
        recent_orders,
        hide_index=True,
        use_container_width=True,
        column_config={
            "ORDER_ID": st.column_config.NumberColumn("Order ID"),
            "CUSTOMER_NAME": st.column_config.TextColumn("Customer"),
            "ORDER_DATE": st.column_config.DateColumn("Date"),
            "AMOUNT": st.column_config.NumberColumn("Amount", format="$%.0f"),
            "ORDER_STATUS": st.column_config.TextColumn("Status")
        }
    )
