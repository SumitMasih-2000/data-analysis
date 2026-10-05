import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from db_manager import get_data

# Ensure session configuration remains clean
st.set_page_config(page_title="RetailIQ Ultimate Analytics", page_icon="📊", layout="wide")

if not st.session_state.get('user'):
    st.error("Please login on the Home page first.")
    st.stop()

csv_string = get_data(st.session_state.user)
if not csv_string:
    st.warning("No data found. Please upload a file on the main page.")
    st.stop()

df = pd.read_csv(io.StringIO(csv_string))

# -------------------------------------------------------------------------
# SMART PRE-PROCESSING
# -------------------------------------------------------------------------
for col in df.columns:
    if 'date' in col.lower() or 'time' in col.lower():
        try:
            df[col] = pd.to_datetime(df[col])
        except Exception:
            pass

# Custom Dark Theme Stylesheet injection
st.markdown("""<style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #000000; color: white; }
    div[data-testid="stMetric"] { background-color: #1e1e1e; padding: 15px; border-radius: 8px; border: 1px solid #2d2d2d; }
    h1, h2, h3, h4 { color: white !important; }
</style>""", unsafe_allow_html=True)

st.title("📊 RetailIQ Ultimate Analytics Engine")

# Dynamic Column Category Discovery
numeric_cols = df.select_dtypes(include='number').columns.tolist()
categorical_cols = df.select_dtypes(include='object').columns.tolist()
date_cols = df.select_dtypes(include='datetime').columns.tolist()

# -------------------------------------------------------------------------
# GLOBAL SIDEBAR CONTROL FILTERS (New Interactive Feature)
# -------------------------------------------------------------------------
st.sidebar.header("🕹️ Global Dashboard Filters")
filtered_df = df.copy()

if categorical_cols:
    st.sidebar.subheader("Filter Attributes")
    for col in categorical_cols[:3]: # Limit to first 3 categorical variables to keep sidebar clean
        unique_vals = ["All"] + df[col].unique().tolist()
        selected_val = st.sidebar.selectbox(f"Select {col}", unique_vals)
        if selected_val != "All":
            filtered_df = filtered_df[filtered_df[col] == selected_val]

if date_cols:
    st.sidebar.subheader("Timeline Filter")
    for col in date_cols:
        min_date, max_date = df[col].min(), df[col].max()
        if pd.notnull(min_date) and pd.notnull(max_date):
            date_range = st.sidebar.date_input(f"Range: {col}", [min_date.date(), max_date.date()])
            if len(date_range) == 2:
                filtered_df = filtered_df[(filtered_df[col].dt.date >= date_range[0]) & (filtered_df[col].dt.date <= date_range[1])]

# Tab Array Declaration
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 KPI Overview", 
    "🔍 Inventory Analysis", 
    "🤖 Infinite Dataset Profiler", 
    "🎨 Dynamic Sandbox Chart Builder"
])

# -------------------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------------------
with tab1:
    if numeric_cols:
        rev = numeric_cols[0]
        cat = next((c for c in filtered_df.columns if 'product' in c.lower()), filtered_df.columns[0])
        loc = next((c for c in filtered_df.columns if 'location' in c.lower()), filtered_df.columns[0])
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Summed Value", f"{filtered_df[rev].sum():,.2f}")
        c2.metric("Mean Average Value", f"{filtered_df[rev].mean():,.2f}")
        
        try:
            c3.metric("Top Segment Driver", str(filtered_df.groupby(cat)[rev].sum().idxmax()))
            c4.metric("Top Location Target", str(filtered_df.groupby(loc)[rev].sum().idxmax()))
        except Exception:
            c3.metric("Top Segment Driver", "N/A")
            c4.metric("Top Location Target", "N/A")
        
        l1, r1 = st.columns(2)
        with l1: 
            st.plotly_chart(px.pie(filtered_df, values=rev, names=cat, title=f"Share Breakdown of {rev} by {cat}", template="plotly_dark", hole=0.4), use_container_width=True)
        with r1: 
            st.plotly_chart(px.bar(filtered_df.groupby(loc)[rev].sum().reset_index(), x=loc, y=rev, title=f"Total Aggregated {rev} grouped by {loc}", template="plotly_dark", color=rev, color_continuous_scale="Viridis"), use_container_width=True)
    else:
        st.error("No numeric metrics detected to build the default overview panel.")

# -------------------------------------------------------------------------
# TAB 2: INVENTORY MATRIX
# -------------------------------------------------------------------------
with tab2:
    st.subheader("Inventory Stock Optimization Matrix")
    
    # Smart Fallback check for inventory tracking
    stock_col = next((c for c in filtered_df.columns if 'stock' in c.lower() or 'qty' in c.lower() or 'quantity' in c.lower()), None)
    
    if stock_col:
        st.write(f"Using **'{stock_col}'** column as the reference metric inventory source.")
        mean_stock = filtered_df[stock_col].mean()
        
        # UI Threshold dynamic adjustment slider
        threshold_percentage = st.slider("Define Critical Alert Buffer Line (% of Average Stock)", 10, 150, 80)
        critical_value = mean_stock * (threshold_percentage / 100)
        
        critical_items = filtered_df[filtered_df[stock_col] <= critical_value]
        
        st.metric("SKUs Flagged For Restocking Alert", len(critical_items), delta=f"-{len(df)-len(critical_items)} safe items")
        st.dataframe(critical_items.sort_values(by=stock_col), use_container_width=True)
    else: 
        st.info("To see immediate stock reorder matrix alerts, ensure your file contains columns named 'Stock', 'Qty' or 'Quantity'.")

# -------------------------------------------------------------------------
# TAB 3: THE "ANALYZE EVERYTHING" INFINITE ENGINE
# -------------------------------------------------------------------------
with tab3:
    st.subheader("🤖 Extended Dataset Profiler Matrix")
    
    # ---- NEW ADVANCED STATISTICAL PROFILE ADDITIONS ----
    if len(numeric_cols) > 1:
        with st.expander("🔗 Deep Statistical Correlation Heatmap Matrix", expanded=True):
            st.write("Displays mutual tracking associations. Values approach $1$ or $-1$ if behaviors change predictably together.")
            corr_matrix = filtered_df[numeric_cols].corr()
            fig_corr = px.imshow(
                corr_matrix, 
                text_auto=".2f", 
                aspect="auto", 
                color_continuous_scale='RdBu_r', 
                template="plotly_dark",
                zmin=-1, zmax=1
            )
            st.plotly_chart(fig_corr, use_container_width=True)

    if len(categorical_cols) >= 2:
        with st.expander("🧩 Categorical Cross-Tabulation Matrix Pivot Tool", expanded=False):
            st.write("Cross-reference distribution frequencies between categories.")
            row_choice = st.selectbox("Select Core Row Category Attribute", categorical_cols, index=0)
            col_choice = st.selectbox("Select Target Columns Intersection", categorical_cols, index=1 if len(categorical_cols)>1 else 0)
            
            crosstab_res = pd.crosstab(filtered_df[row_choice], filtered_df[col_choice])
            st.dataframe(crosstab_res, use_container_width=True)

    # --- SECTION A: CATEGORICAL VARIABLES ---
    if categorical_cols:
        st.write("### 🏷️ Categorical Attribute Data Slices")
        for col in categorical_cols:
            if filtered_df[col].nunique() > 50:
                continue
                
            with st.expander(f"📍 Distribution Breakdown: {col}", expanded=False):
                col_counts = filtered_df[col].value_counts().reset_index()
                col_counts.columns = [col, 'Total Count']
                
                left, right = st.columns([2, 1])
                with left:
                    fig = px.bar(col_counts, x=col, y='Total Count', color='Total Count', template="plotly_dark", color_continuous_scale="Cividis")
                    st.plotly_chart(fig, use_container_width=True)
                with right:
                    st.dataframe(col_counts, hide_index=True)

    # --- SECTION B: NUMERICAL VARIABLES ---
    if numeric_cols:
        st.write("### 🔢 Mathematical Variable Outlier Density Maps")
        for col in numeric_cols:
            with st.expander(f"💰 Outlier Verification: {col}", expanded=False):
                l_graph, r_graph = st.columns(2)
                with l_graph:
                    fig_h = px.histogram(filtered_df, x=col, marginal="rug", title=f"Density Curve of {col}", template="plotly_dark", color_discrete_sequence=['#00CC96'])
                    st.plotly_chart(fig_h, use_container_width=True)
                with r_graph:
                    fig_b = px.box(filtered_df, y=col, points="all", title=f"Spread Analysis of {col}", template="plotly_dark", color_discrete_sequence=['#AB63FA'])
                    st.plotly_chart(fig_b, use_container_width=True)

    # --- SECTION C: TIME TREND TIMELINES ---
    if date_cols and numeric_cols:
        st.write("### 📅 Historical Operational Timelines")
        primary_metric = st.selectbox("Choose Timeline Performance Axis Metric Value", numeric_cols)
        for col in date_cols:
            with st.expander(f"📈 Timeline Path: {col} via {primary_metric}", expanded=False):
                timeline_data = filtered_df.groupby(col)[primary_metric].sum().reset_index()
                fig_t = px.line(timeline_data, x=col, y=primary_metric, title=f"Timeline Acceleration Curve", template="plotly_dark", markers=True)
                st.plotly_chart(fig_t, use_container_width=True)

# -------------------------------------------------------------------------
# NEW TAB 4: MULTI-VARIABLE SANDBOX CHART BUILDER
# -------------------------------------------------------------------------
with tab4:
    st.subheader("🎨 Custom Multi-Variable Sandbox Chart Builder")
    st.write("Create custom cross-variable analysis plots on demand.")
    
    col_x = st.selectbox("Select Primary Horizontal X-Axis Variable Target", df.columns)
    col_y = st.selectbox("Select Vertical Y-Axis Variable Metric Target", numeric_cols)
    
    chart_type = st.radio("Choose Graph Visual Rendering Blueprint Layout Type:", ["Scatter Plot", "Bar Chart Tracking", "Line Performance Plot", "Area Stream Mapping"], horizontal=True)
    
    color_by = st.selectbox("Split/Color Categorization Overlay Layer (Optional)", ["None"] + categorical_cols)
    color_var = None if color_by == "None" else color_by

    with st.container():
        try:
            if chart_type == "Scatter Plot":
                fig_sandbox = px.scatter(filtered_df, x=col_x, y=col_y, color=color_var, trendline="ols" if (col_x in numeric_cols and color_by == "None") else None, template="plotly_dark", title=f"Sandbox Scatter Discovery: {col_y} vs {col_x}")
            elif chart_type == "Bar Chart Tracking":
                fig_sandbox = px.bar(filtered_df, x=col_x, y=col_y, color=color_var, barmode="group", template="plotly_dark", title=f"Sandbox Bar Tracking: {col_y} via {col_x}")
            elif chart_type == "Line Performance Plot":
                fig_sandbox = px.line(filtered_df.sort_values(by=col_x), x=col_x, y=col_y, color=color_var, template="plotly_dark", title=f"Sandbox Line Profile Trends")
            elif chart_type == "Area Stream Mapping":
                fig_sandbox = px.area(filtered_df.sort_values(by=col_x), x=col_x, y=col_y, color=color_var, template="plotly_dark", title=f"Sandbox Area Mapping Accumulation")
                
            st.plotly_chart(fig_sandbox, use_container_width=True)
        except Exception as sandbox_err:
            st.error(f"Could not build this unique matrix chart variation layout combination: {sandbox_err}")
