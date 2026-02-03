import streamlit as st
import pandas as pd
from datetime import timedelta, datetime

st.set_page_config(
    page_title="Customer 360 Dashboard",
    page_icon=":busts_in_silhouette:",
    layout="wide"
)

st.title(":busts_in_silhouette: Customer 360 Dashboard")
st.caption("Deep dive into customer behavior, segmentation, and lifetime value")

# Connect to Snowflake
conn = st.connection("snowflake")

# --- Load Data ---
@st.cache_data(ttl=timedelta(minutes=10))
def load_data():
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
    
    orders = conn.query("""
        SELECT 
            ORDER_ID,
            CUSTOMER_ID,
            ORDER_DATE::DATE as ORDER_DATE,
            AMOUNT,
            ORDER_STATUS
        FROM PC_DBT_DB.DBT_NBINIARIS.FCT_ORDERS
    """)
    
    return customers, orders

customers_df, orders_df = load_data()

# --- Calculate Customer Metrics ---
# Customer lifetime value (total spend per customer)
customer_ltv = orders_df.groupby("CUSTOMER_ID").agg(
    total_spend=("AMOUNT", "sum"),
    order_count=("ORDER_ID", "count"),
    first_order=("ORDER_DATE", "min"),
    last_order=("ORDER_DATE", "max")
).reset_index()

customer_ltv["avg_order_value"] = customer_ltv["total_spend"] / customer_ltv["order_count"]

# Merge with customer info
customer_full = customers_df.merge(customer_ltv, on="CUSTOMER_ID", how="left")
customer_full["NAME"] = customer_full["FIRST_NAME"] + " " + customer_full["LAST_NAME"]

# --- Sidebar ---
with st.sidebar:
    st.header("Filters")
    
    # Segment filter
    segments = ["All", "High Value", "Medium Value", "Low Value", "Inactive"]
    selected_segment = st.selectbox("Customer Segment", segments)
    
    # Define segments
    high_value_threshold = customer_ltv["total_spend"].quantile(0.75)
    low_value_threshold = customer_ltv["total_spend"].quantile(0.25)

# --- KPI Metrics ---
total_customers = len(customers_df)
customers_with_orders = customers_df["NUMBER_OF_ORDERS"].notna().sum()
inactive_customers = customers_df["NUMBER_OF_ORDERS"].isna().sum()
avg_ltv = customer_ltv["total_spend"].mean()
avg_orders_per_customer = customer_ltv["order_count"].mean()

with st.container(horizontal=True):
    st.metric("Total Customers", f"{total_customers:,}", border=True)
    st.metric("Active Customers", f"{customers_with_orders:,}", border=True)
    st.metric("Inactive Customers", f"{inactive_customers:,}", border=True)
    st.metric("Avg Lifetime Value", f"${avg_ltv:,.2f}", border=True)
    st.metric("Avg Orders/Customer", f"{avg_orders_per_customer:.1f}", border=True)

st.divider()

# --- Customer Segmentation ---
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Customer Segmentation by Value")
        
        # Segment customers
        def segment_customer(row):
            if pd.isna(row["total_spend"]):
                return "Inactive"
            elif row["total_spend"] >= high_value_threshold:
                return "High Value"
            elif row["total_spend"] >= low_value_threshold:
                return "Medium Value"
            else:
                return "Low Value"
        
        customer_full["segment"] = customer_full.apply(segment_customer, axis=1)
        
        segment_summary = customer_full.groupby("segment").agg(
            customers=("CUSTOMER_ID", "count"),
            total_revenue=("total_spend", "sum")
        ).reset_index()
        
        # Order segments logically
        segment_order = ["High Value", "Medium Value", "Low Value", "Inactive"]
        segment_summary["segment"] = pd.Categorical(
            segment_summary["segment"], 
            categories=segment_order, 
            ordered=True
        )
        segment_summary = segment_summary.sort_values("segment")
        
        st.bar_chart(segment_summary, x="segment", y="customers", use_container_width=True)
        
        # Show segment details
        st.dataframe(
            segment_summary,
            hide_index=True,
            use_container_width=True,
            column_config={
                "segment": st.column_config.TextColumn("Segment"),
                "customers": st.column_config.NumberColumn("Customers"),
                "total_revenue": st.column_config.NumberColumn("Total Revenue", format="$%.0f")
            }
        )

with col2:
    with st.container(border=True):
        st.subheader("Order Frequency Distribution")
        
        # Group by number of orders
        customers_with_data = customers_df[customers_df["NUMBER_OF_ORDERS"].notna()].copy()
        customers_with_data["frequency_bucket"] = pd.cut(
            customers_with_data["NUMBER_OF_ORDERS"],
            bins=[0, 1, 2, 3, 5, float("inf")],
            labels=["1 order", "2 orders", "3 orders", "4-5 orders", "6+ orders"]
        )
        
        frequency_dist = customers_with_data["frequency_bucket"].value_counts().reset_index()
        frequency_dist.columns = ["Order Frequency", "Customers"]
        
        # Sort by order
        freq_order = ["1 order", "2 orders", "3 orders", "4-5 orders", "6+ orders"]
        frequency_dist["Order Frequency"] = pd.Categorical(
            frequency_dist["Order Frequency"],
            categories=freq_order,
            ordered=True
        )
        frequency_dist = frequency_dist.sort_values("Order Frequency")
        
        st.bar_chart(frequency_dist, x="Order Frequency", y="Customers", use_container_width=True)

# --- Cohort Analysis ---
with st.container(border=True):
    st.subheader("Customer Cohort Analysis")
    st.caption("Customers grouped by their first order month")
    
    # Create cohorts based on first order month
    cohort_data = customer_full[customer_full["FIRST_ORDER_DATE"].notna()].copy()
    cohort_data["cohort_month"] = pd.to_datetime(cohort_data["FIRST_ORDER_DATE"]).dt.to_period("M").astype(str)
    
    cohort_summary = cohort_data.groupby("cohort_month").agg(
        customers=("CUSTOMER_ID", "count"),
        avg_ltv=("total_spend", "mean"),
        total_revenue=("total_spend", "sum"),
        avg_orders=("order_count", "mean")
    ).reset_index()
    
    # Chart tabs
    tab1, tab2, tab3 = st.tabs(["New Customers", "Avg LTV by Cohort", "Total Revenue"])
    
    with tab1:
        st.bar_chart(cohort_summary, x="cohort_month", y="customers", use_container_width=True)
    
    with tab2:
        st.line_chart(cohort_summary, x="cohort_month", y="avg_ltv", use_container_width=True)
    
    with tab3:
        st.bar_chart(cohort_summary, x="cohort_month", y="total_revenue", use_container_width=True)

# --- Customer Lifetime Value Analysis ---
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("Top 15 Customers by LTV")
        
        top_customers = customer_full[customer_full["total_spend"].notna()].nlargest(15, "total_spend")
        
        st.dataframe(
            top_customers[["NAME", "total_spend", "order_count", "avg_order_value"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "NAME": st.column_config.TextColumn("Customer"),
                "total_spend": st.column_config.NumberColumn("Lifetime Value", format="$%.0f"),
                "order_count": st.column_config.NumberColumn("Orders"),
                "avg_order_value": st.column_config.NumberColumn("Avg Order", format="$%.2f")
            }
        )

with col4:
    with st.container(border=True):
        st.subheader("LTV Distribution")
        
        ltv_data = customer_ltv[["total_spend"]].copy()
        ltv_data["ltv_bucket"] = pd.cut(
            ltv_data["total_spend"],
            bins=[0, 10, 25, 50, 100, float("inf")],
            labels=["$0-10", "$11-25", "$26-50", "$51-100", "$100+"]
        )
        
        ltv_dist = ltv_data["ltv_bucket"].value_counts().reset_index()
        ltv_dist.columns = ["LTV Range", "Customers"]
        
        bucket_order = ["$0-10", "$11-25", "$26-50", "$51-100", "$100+"]
        ltv_dist["LTV Range"] = pd.Categorical(
            ltv_dist["LTV Range"],
            categories=bucket_order,
            ordered=True
        )
        ltv_dist = ltv_dist.sort_values("LTV Range")
        
        st.bar_chart(ltv_dist, x="LTV Range", y="Customers", use_container_width=True)

# --- Inactive Customer Identification ---
with st.container(border=True):
    st.subheader("Inactive Customers (Never Ordered)")
    
    inactive = customers_df[customers_df["NUMBER_OF_ORDERS"].isna()].copy()
    inactive["NAME"] = inactive["FIRST_NAME"] + " " + inactive["LAST_NAME"]
    
    if len(inactive) > 0:
        st.warning(f"Found {len(inactive)} customers who have never placed an order")
        st.dataframe(
            inactive[["CUSTOMER_ID", "NAME"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "CUSTOMER_ID": st.column_config.NumberColumn("ID"),
                "NAME": st.column_config.TextColumn("Customer Name")
            }
        )
    else:
        st.success("All customers have placed at least one order!")

# --- At-Risk Customers (haven't ordered recently) ---
with st.container(border=True):
    st.subheader("At-Risk Customers")
    st.caption("Customers who haven't ordered in the last 30 days but were previously active")
    
    # Get the latest order date in the dataset and ensure datetime types
    latest_date = pd.to_datetime(orders_df["ORDER_DATE"].max())
    cutoff_date = latest_date - timedelta(days=30)
    
    # Convert last_order to datetime for comparison
    customer_full["last_order"] = pd.to_datetime(customer_full["last_order"])
    
    at_risk = customer_full[
        (customer_full["last_order"].notna()) & 
        (customer_full["last_order"] < cutoff_date)
    ].copy()
    
    at_risk["days_since_order"] = (latest_date - at_risk["last_order"]).dt.days
    at_risk = at_risk.sort_values("days_since_order", ascending=False)
    
    if len(at_risk) > 0:
        st.info(f"Found {len(at_risk)} customers who haven't ordered in 30+ days")
        st.dataframe(
            at_risk[["NAME", "total_spend", "order_count", "last_order", "days_since_order"]].head(20),
            hide_index=True,
            use_container_width=True,
            column_config={
                "NAME": st.column_config.TextColumn("Customer"),
                "total_spend": st.column_config.NumberColumn("Total Spend", format="$%.0f"),
                "order_count": st.column_config.NumberColumn("Orders"),
                "last_order": st.column_config.DateColumn("Last Order"),
                "days_since_order": st.column_config.NumberColumn("Days Inactive")
            }
        )
    else:
        st.success("No at-risk customers found!")
