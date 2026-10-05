import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

import db_manager as db

# Page setup
st.set_page_config(
    page_title="RetailIQ — Smart Retail & Sales Intelligence",
    page_icon="🛍️",
    layout="wide"
)

# Initialize database
db.init_db()

# Session State for User Auth
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

# ----------------- AUTHENTICATION VIEWS -----------------
def render_auth_page():
    st.markdown("<h2 style='text-align: center;'>🛍️ RetailIQ Analytics Suite</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Project-Grade Retail & Inventory Intelligence Platform</p>", unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.warning("Please fill in all fields.")
                else:
                    user = db.authenticate_user(username, password)
                    if user:
                        st.session_state.authenticated_user = user
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

    with tab_signup:
        with st.form("signup_form"):
            new_user = st.text_input("New Username").strip().lower()
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            create_btn = st.form_submit_button("Register", use_container_width=True)
            if create_btn:
                if not new_user or not new_pass:
                    st.warning("All fields are required.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = db.create_user(new_user, new_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

# Check authentication
if not st.session_state.authenticated_user:
    render_auth_page()
    st.stop()

# ----------------- MAIN LOGGED-IN APPLICATION -----------------
current_user = st.session_state.authenticated_user

# Sidebar Navigation & Session Control
st.sidebar.title(f"👤 {current_user['username'].capitalize()}")
if st.sidebar.button("Log Out", use_container_width=True):
    st.session_state.authenticated_user = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Upload Retail Data")
uploaded_file = st.sidebar.file_uploader("Upload .csv or .xlsx", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df_uploaded = pd.read_csv(uploaded_file)
        else:
            df_uploaded = pd.read_excel(uploaded_file)
        
        db.save_user_dataset(current_user["id"], uploaded_file.name, df_uploaded)
        st.sidebar.success(f"Saved: {uploaded_file.name}")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# Load active user data from SQLite
current_filename, df = db.load_user_dataset(current_user["id"])

if df is None:
    st.info("👋 Welcome! Please upload a retail dataset (.csv or .xlsx) from the sidebar to activate the dashboard.")
    st.stop()

st.title("📊 RetailIQ Intelligence Dashboard")
st.caption(f"Active Dataset: **{current_filename}** ({len(df):,} rows, {len(df.columns)} columns)")

# Identify key standard columns automatically
cols = df.columns.tolist()

def match_col(keywords):
    for c in cols:
        if any(k.lower() in c.lower() for k in keywords):
            return c
    return None

date_col_guess = match_col(["date", "time", "day"])
sales_col_guess = match_col(["sales", "revenue", "amount", "total", "price"])
qty_col_guess = match_col(["quantity", "qty", "units", "volume"])
product_col_guess = match_col(["product", "item", "sku", "category", "description"])
stock_col_guess = match_col(["stock", "inventory", "available", "on_hand"])

# ----------------- TABS WORKSPACE -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Executive KPIs", 
    "📦 Inventory & Stock", 
    "🔮 Sales Forecasting", 
    "🛠️ Dataset Profiler", 
    "📑 Export Center"
])

# TAB 1: EXECUTIVE KPIs
with tab1:
    st.subheader("Performance Overview")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    with col_c1:
        rev_col = st.selectbox("Revenue / Sales Column:", num_cols, index=num_cols.index(sales_col_guess) if sales_col_guess in num_cols else 0)
    with col_c2:
        prod_col = st.selectbox("Product / Category Column:", cols, index=cols.index(product_col_guess) if product_col_guess in cols else 0)
    with col_c3:
        dt_col = st.selectbox("Date Column (Optional):", [None] + cols, index=(cols.index(date_col_guess) + 1) if date_col_guess in cols else 0)

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    total_rev = df[rev_col].sum() if rev_col else 0
    avg_order = df[rev_col].mean() if rev_col else 0
    total_records = len(df)
    unique_items = df[prod_col].nunique() if prod_col else 0

    m1.metric("Total Revenue", f"${total_rev:,.2f}")
    m2.metric("Average Transaction", f"${avg_order:,.2f}")
    m3.metric("Total Transactions", f"{total_records:,}")
    m4.metric("Unique Products", f"{unique_items:,}")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("**Top Performing Products by Revenue**")
        if prod_col and rev_col:
            top_products = df.groupby(prod_col)[rev_col].sum().reset_index().sort_values(by=rev_col, ascending=False).head(10)
            fig_bar = px.bar(top_products, x=rev_col, y=prod_col, orientation="h", color=rev_col, color_continuous_scale="Viridis")
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=0, r=0, t=20, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)
            
    with col_chart2:
        st.markdown("**Revenue Trend Over Time**")
        if dt_col and rev_col:
            temp_df = df.copy()
            temp_df[dt_col] = pd.to_datetime(temp_df[dt_col], errors="coerce")
            temp_df = temp_df.dropna(subset=[dt_col])
            trend = temp_df.groupby(pd.Grouper(key=dt_col, freq="W"))[rev_col].sum().reset_index()
            fig_trend = px.line(trend, x=dt_col, y=rev_col, markers=True)
            fig_trend.update_layout(margin=dict(l=0, r=0, t=20, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Select a valid Date column above to display temporal trends.")

# TAB 2: INVENTORY & STOCK
with tab2:
    st.subheader("Inventory Distribution & Stock Level Alerts")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        stock_col = st.selectbox("Stock / Units Column:", num_cols, index=num_cols.index(stock_col_guess) if stock_col_guess in num_cols else 0)
    with col_i2:
        threshold = st.number_input("Low Stock Threshold Alert", value=20, min_value=1)

    if stock_col and prod_col:
        low_stock = df[df[stock_col] <= threshold][[prod_col, stock_col]].drop_duplicates()
        
        st.warning(f"⚠️️ Items Below Threshold ({threshold} units): {len(low_stock)}")
        if not low_stock.empty:
            st.dataframe(low_stock.sort_values(by=stock_col), use_container_width=True)
        else:
            st.success("All listed items are above the minimum stock threshold.")

        # Distribution Chart
        fig_stock = px.histogram(df, x=stock_col, nbins=30, title="Inventory Distribution Spread")
        st.plotly_chart(fig_stock, use_container_width=True)

# TAB 3: FORECASTING
with tab3:
    st.subheader("Sales Trend & Moving Average Projection")
    if not dt_col or not rev_col:
        st.warning("Please configure both a Date and Revenue column in the Executive KPIs tab to run forecasting.")
    else:
        fc_df = df.copy()
        fc_df[dt_col] = pd.to_datetime(fc_df[dt_col], errors="coerce")
        fc_df = fc_df.dropna(subset=[dt_col])
        daily_series = fc_df.groupby(pd.Grouper(key=dt_col, freq="D"))[rev_col].sum().reset_index()
        daily_series = daily_series[daily_series[rev_col] > 0]

        if len(daily_series) < 14:
            st.info("At least 14 days of data are recommended for moving average smoothing.")

        window_size = st.slider("Rolling Average Window (Days):", 3, 30, 7)
        daily_series["Rolling_Avg"] = daily_series[rev_col].rolling(window=window_size).mean()

        # Simple linear slope for project-level forecast
        x = np.arange(len(daily_series))
        y = daily_series[rev_col].values
        slope, intercept = np.polyfit(x, y, 1) if len(x) > 1 else (0, 0)
        daily_series["Trend_Line"] = slope * x + intercept

        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(x=daily_series[dt_col], y=daily_series[rev_col], mode="lines+markers", name="Actual Daily Revenue", opacity=0.4))
        fig_forecast.add_trace(go.Scatter(x=daily_series[dt_col], y=daily_series["Rolling_Avg"], mode="lines", name=f"{window_size}-Day Rolling Average", line=dict(color="orange", width=2)))
        fig_forecast.add_trace(go.Scatter(x=daily_series[dt_col], y=daily_series["Trend_Line"], mode="lines", name="Linear Trend Line", line=dict(color="red", dash="dash")))

        st.plotly_chart(fig_forecast, use_container_width=True)

# TAB 4: DATASET PROFILER
with tab4:
    st.subheader("Dataset Summary & Health")
    c_p1, c_p2 = st.columns([1, 2])
    with c_p1:
        st.markdown("**Column Types & Null Checks**")
        summary_df = pd.DataFrame({
            "Type": df.dtypes.astype(str),
            "Null Values": df.isnull().sum()
        })
        st.dataframe(summary_df, use_container_width=True)
    with c_p2:
        st.markdown("**Numeric Descriptive Statistics**")
        st.dataframe(df.describe(), use_container_width=True)

# TAB 5: EXPORT CENTER
with tab5:
    st.subheader("Export Cleaned Analysis & Reports")
    
    # Filter selection
    st.markdown("Download current working data in CSV format:")
    csv_export = df.to_csv(index=False).encode("utf-8")
    
    st.download_button(
        label="📥 Download Cleaned Dataset (CSV)",
        data=csv_export,
        file_name=f"retailiq_export_{current_user['username']}.csv",
        mime="text/csv",
        use_container_width=True
    )
