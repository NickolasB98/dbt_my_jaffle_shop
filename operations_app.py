import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(
    page_title="Operations Dashboard",
    page_icon=":package:",
    layout="wide"
)

st.title(":package: Operations Dashboard")
st.caption("Order fulfillment tracking, status funnel, and return analysis")

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
    
    daily_revenue = conn.query("""
        SELECT 
            DATE_DAY::DATE as DATE_DAY,
            REVENUE
        FROM PC_DBT_DB.DBT_NBINIARIS.INT_DAILY_REVENUE
        ORDER BY DATE_DAY
    """)
    
    return orders, daily_revenue

orders_df, daily_revenue_df = load_data()

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

# Apply filters
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_orders = orders_df[
        (orders_df["ORDER_DATE"] >= start_date) &
        (orders_df["ORDER_DATE"] <= end_date)
    ]
else:
    filtered_orders = orders_df

# --- Calculate Metrics ---
total_orders = len(filtered_orders)
completed_orders = len(filtered_orders[filtered_orders["ORDER_STATUS"] == "completed"])
shipped_orders = len(filtered_orders[filtered_orders["ORDER_STATUS"] == "shipped"])
placed_orders = len(filtered_orders[filtered_orders["ORDER_STATUS"] == "placed"])
returned_orders = len(filtered_orders[filtered_orders["ORDER_STATUS"].isin(["returned", "return_pending"])])

fulfillment_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
return_rate = (returned_orders / total_orders * 100) if total_orders > 0 else 0

# --- KPI Metrics ---
with st.container(horizontal=True):
    st.metric("Total Orders", f"{total_orders:,}", border=True)
    st.metric("Completed", f"{completed_orders:,}", border=True)
    st.metric("Shipped", f"{shipped_orders:,}", border=True)
    st.metric("Fulfillment Rate", f"{fulfillment_rate:.1f}%", border=True)
    st.metric("Return Rate", f"{return_rate:.1f}%", border=True)

st.divider()

# --- Order Status Funnel ---
with st.container(border=True):
    st.subheader("Order Status Funnel")
    st.caption("Order progression: Placed → Shipped → Completed (with returns tracked separately)")
    
    # Define the funnel stages
    funnel_data = pd.DataFrame({
        "Stage": ["Placed", "Shipped", "Completed", "Returned/Pending"],
        "Orders": [
            placed_orders + shipped_orders + completed_orders + returned_orders,  # All orders start as placed
            shipped_orders + completed_orders,  # Shipped + completed
            completed_orders,  # Completed
            returned_orders  # Returns
        ],
        "Color": ["#3498db", "#f39c12", "#27ae60", "#e74c3c"]
    })
    
    # Create funnel visualization using columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "All Orders",
            f"{total_orders}",
            help="Total orders received",
            border=True
        )
        st.caption("100%")
    
    with col2:
        shipped_plus = shipped_orders + completed_orders
        pct = (shipped_plus / total_orders * 100) if total_orders > 0 else 0
        st.metric(
            "Shipped+",
            f"{shipped_plus}",
            help="Orders that have been shipped or completed",
            border=True
        )
        st.caption(f"{pct:.1f}%")
    
    with col3:
        pct = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        st.metric(
            "Completed",
            f"{completed_orders}",
            help="Successfully delivered orders",
            border=True
        )
        st.caption(f"{pct:.1f}%")
    
    with col4:
        st.metric(
            "Returns",
            f"{returned_orders}",
            delta=f"-{return_rate:.1f}%",
            delta_color="inverse",
            help="Returned or return pending orders",
            border=True
        )

# --- Status Breakdown ---
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Orders by Status")
        
        status_counts = filtered_orders.groupby("ORDER_STATUS").agg(
            orders=("ORDER_ID", "count"),
            revenue=("AMOUNT", "sum")
        ).reset_index()
        
        # Order statuses logically
        status_order = ["placed", "shipped", "completed", "return_pending", "returned"]
        status_counts["ORDER_STATUS"] = pd.Categorical(
            status_counts["ORDER_STATUS"],
            categories=status_order,
            ordered=True
        )
        status_counts = status_counts.sort_values("ORDER_STATUS")
        
        st.bar_chart(status_counts, x="ORDER_STATUS", y="orders", use_container_width=True)
        
        st.dataframe(
            status_counts,
            hide_index=True,
            use_container_width=True,
            column_config={
                "ORDER_STATUS": st.column_config.TextColumn("Status"),
                "orders": st.column_config.NumberColumn("Orders"),
                "revenue": st.column_config.NumberColumn("Revenue", format="$%.0f")
            }
        )

with col2:
    with st.container(border=True):
        st.subheader("Revenue by Status")
        
        st.bar_chart(status_counts, x="ORDER_STATUS", y="revenue", use_container_width=True)
        
        # Revenue at risk (returns)
        return_revenue = filtered_orders[
            filtered_orders["ORDER_STATUS"].isin(["returned", "return_pending"])
        ]["AMOUNT"].sum()
        
        total_revenue = filtered_orders["AMOUNT"].sum()
        
        st.metric(
            "Revenue at Risk (Returns)",
            f"${return_revenue:,.0f}",
            delta=f"{(return_revenue/total_revenue*100):.1f}% of total" if total_revenue > 0 else "0%",
            delta_color="inverse"
        )

st.divider()

# --- Daily Order Volume Trends ---
with st.container(border=True):
    st.subheader("Daily Order Volume")
    
    daily_orders = filtered_orders.groupby("ORDER_DATE").agg(
        orders=("ORDER_ID", "count"),
        revenue=("AMOUNT", "sum")
    ).reset_index()
    
    tab1, tab2 = st.tabs(["Order Count", "Revenue"])
    
    with tab1:
        st.line_chart(daily_orders, x="ORDER_DATE", y="orders", use_container_width=True)
    
    with tab2:
        st.line_chart(daily_orders, x="ORDER_DATE", y="revenue", use_container_width=True)

# --- Weekly Trends ---
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.subheader("Weekly Order Trends")
        
        weekly_orders = filtered_orders.copy()
        weekly_orders["week"] = pd.to_datetime(weekly_orders["ORDER_DATE"]).dt.to_period("W").astype(str)
        
        weekly_agg = weekly_orders.groupby("week").agg(
            orders=("ORDER_ID", "count"),
            revenue=("AMOUNT", "sum")
        ).reset_index()
        
        st.bar_chart(weekly_agg, x="week", y="orders", use_container_width=True)

with col4:
    with st.container(border=True):
        st.subheader("Monthly Order Trends")
        
        monthly_orders = filtered_orders.copy()
        monthly_orders["month"] = pd.to_datetime(monthly_orders["ORDER_DATE"]).dt.to_period("M").astype(str)
        
        monthly_agg = monthly_orders.groupby("month").agg(
            orders=("ORDER_ID", "count"),
            revenue=("AMOUNT", "sum")
        ).reset_index()
        
        st.bar_chart(monthly_agg, x="month", y="orders", use_container_width=True)

# --- Return Analysis ---
with st.container(border=True):
    st.subheader("Return Analysis")
    
    returns = filtered_orders[filtered_orders["ORDER_STATUS"].isin(["returned", "return_pending"])].copy()
    
    if len(returns) > 0:
        col5, col6 = st.columns(2)
        
        with col5:
            st.markdown("**Returns Over Time**")
            returns["month"] = pd.to_datetime(returns["ORDER_DATE"]).dt.to_period("M").astype(str)
            monthly_returns = returns.groupby("month").agg(
                returns=("ORDER_ID", "count"),
                amount=("AMOUNT", "sum")
            ).reset_index()
            
            st.bar_chart(monthly_returns, x="month", y="returns", use_container_width=True)
        
        with col6:
            st.markdown("**Return Status Breakdown**")
            return_status = returns.groupby("ORDER_STATUS").agg(
                count=("ORDER_ID", "count"),
                amount=("AMOUNT", "sum")
            ).reset_index()
            
            st.dataframe(
                return_status,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ORDER_STATUS": st.column_config.TextColumn("Status"),
                    "count": st.column_config.NumberColumn("Count"),
                    "amount": st.column_config.NumberColumn("Amount", format="$%.0f")
                }
            )
        
        # List returned orders
        st.markdown("**Recent Returns**")
        st.dataframe(
            returns[["ORDER_ID", "CUSTOMER_ID", "ORDER_DATE", "AMOUNT", "ORDER_STATUS"]].sort_values("ORDER_DATE", ascending=False).head(10),
            hide_index=True,
            use_container_width=True,
            column_config={
                "ORDER_ID": st.column_config.NumberColumn("Order ID"),
                "CUSTOMER_ID": st.column_config.NumberColumn("Customer ID"),
                "ORDER_DATE": st.column_config.DateColumn("Date"),
                "AMOUNT": st.column_config.NumberColumn("Amount", format="$%.0f"),
                "ORDER_STATUS": st.column_config.TextColumn("Status")
            }
        )
    else:
        st.success("No returns in the selected period!")

# --- Operational Summary ---
with st.container(border=True):
    st.subheader("Operational Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.markdown("**Fulfillment Metrics**")
        st.write(f"- Orders Awaiting Shipment: **{placed_orders}**")
        st.write(f"- Orders In Transit: **{shipped_orders}**")
        st.write(f"- Successfully Delivered: **{completed_orders}**")
    
    with summary_col2:
        st.markdown("**Return Metrics**")
        st.write(f"- Pending Returns: **{len(filtered_orders[filtered_orders['ORDER_STATUS'] == 'return_pending'])}**")
        st.write(f"- Completed Returns: **{len(filtered_orders[filtered_orders['ORDER_STATUS'] == 'returned'])}**")
        st.write(f"- Return Rate: **{return_rate:.1f}%**")
    
    with summary_col3:
        st.markdown("**Revenue Impact**")
        completed_revenue = filtered_orders[filtered_orders["ORDER_STATUS"] == "completed"]["AMOUNT"].sum()
        pending_revenue = filtered_orders[filtered_orders["ORDER_STATUS"].isin(["placed", "shipped"])]["AMOUNT"].sum()
        st.write(f"- Realized Revenue: **${completed_revenue:,.0f}**")
        st.write(f"- Pending Revenue: **${pending_revenue:,.0f}**")
        st.write(f"- Lost to Returns: **${return_revenue:,.0f}**")
