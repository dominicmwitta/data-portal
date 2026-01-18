"""
app.py - Main Streamlit application for Economic Indicators Dashboard
"""

import streamlit as st
import pandas as pd

from database import (
    get_oracle_connection,
    get_data,
    get_locations,
    get_units,
    test_connection
)
from utils import (
    render_date_filters,
    render_indicator_selector,
    get_quick_stats,
    render_data_display,
    format_connection_info
)


# ────────────────────────────────────────────────
#   Page Configuration
# ────────────────────────────────────────────────
st.set_page_config(page_title="CPI & BOP Explorer", layout="wide")

st.title("📊 Economic Indicators Dashboard")
st.markdown("**CPI & Balance of Payments Data Explorer**")


# ────────────────────────────────────────────────
#   Session State Initialization
# ────────────────────────────────────────────────
if 'connected' not in st.session_state:
    st.session_state.connected = False
    st.session_state.conn = None


# ────────────────────────────────────────────────
#   Login Section
# ────────────────────────────────────────────────
if not st.session_state.connected:
    st.info("👤 Please enter your Oracle database credentials to continue")
    
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input(
                "Username", 
                value="SYSTEM", 
                help="Your Oracle database username"
            )
            dsn = st.text_input(
                "DSN (Host:Port/Service)", 
                value="localhost:1521/XE", 
                help="Format: hostname:port/service_name"
            )
        
        with col2:
            password = st.text_input(
                "Password", 
                type="password", 
                help="Your Oracle database password"
            )
            st.write("")  # spacing
            st.write("")  # spacing
        
        submit = st.form_submit_button(
            "🔐 Connect to Database", 
            type="primary", 
            use_container_width=True
        )
        
        if submit:
            if not username or not password or not dsn:
                st.error("Please fill in all fields")
            else:
                with st.spinner("Connecting to Oracle database..."):
                    conn = get_oracle_connection(username, password, dsn)
                    if conn:
                        st.session_state.connected = True
                        st.session_state.conn = conn
                        st.success("✅ Connected successfully!")
                        st.rerun()
    
    st.stop()


# ────────────────────────────────────────────────
#   Main Application (after login)
# ────────────────────────────────────────────────
conn = st.session_state.conn

# Load reference data
locations = get_locations(conn)
units = get_units(conn)

# Create tabs
tab_cpi, tab_bop, tab_raw, tab_ref = st.tabs([
    "📈 CPI", 
    "💰 BOP", 
    "🔧 Raw SQL", 
    "📚 Reference Data"
])


# ────────────────────────────────────────────────
#   CPI Tab
# ────────────────────────────────────────────────
with tab_cpi:
    st.subheader("Consumer Price Index")

    # Date and location filters
    col1, col2 = st.columns(2)
    with col1:
        use_date_range = st.checkbox("Use date range filter", value=False, key="cpi_use_dates")
        
        if use_date_range:
            start_date_cpi = st.date_input(
                "Start date",
                value=pd.to_datetime("2020-01-01"),
                min_value=pd.to_datetime("2015-01-01"),
                max_value=pd.to_datetime("2030-12-31"),
                key="cpi_start_date"
            )
            start_y_cpi = start_date_cpi.year
            start_m = start_date_cpi.month
        else:
            start_y_cpi = st.number_input("Start year", 2015, 2030, 2020, key="cpi_start")
            start_m = None
        
        if locations:
            loc_cpi = st.selectbox(
                "Location", 
                locations, 
                index=locations.index('Tanzania') if 'Tanzania' in locations else 0, 
                key="cpi_loc"
            )
        else:
            loc_cpi = st.text_input("Location name", "Tanzania", key="cpi_loc_text")
    
    with col2:
        if use_date_range:
            end_date_cpi = st.date_input(
                "End date",
                value=pd.to_datetime("2023-12-31"),
                min_value=pd.to_datetime("2015-01-01"),
                max_value=pd.to_datetime("2030-12-31"),
                key="cpi_end_date"
            )
            end_y_cpi = end_date_cpi.year
            end_m = end_date_cpi.month
        else:
            end_y_cpi = st.number_input("End year", 2015, 2030, 2023, key="cpi_end")
            end_m = None
            
        agg_cpi = st.selectbox(
            "Aggregation", 
            ["monthly", "quarterly", "annual", "fiscal_year"],
            help="Fiscal Year runs from July to June",
            key="cpi_agg"
        )

    # Optional: Month range filter (only shown if not using date range)
    if not use_date_range:
        use_months = st.checkbox("Filter by month range", key="cpi_months")
        if use_months:
            col3, col4 = st.columns(2)
            with col3:
                start_m = st.number_input("Start month", 1, 12, 1, key="cpi_start_m")
            with col4:
                end_m = st.number_input("End month", 1, 12, 12, key="cpi_end_m")
        else:
            start_m = None
            end_m = None

    # Indicator selector
    selected_indicators_cpi = render_indicator_selector(conn, 'CPI', 'cpi')
    
    # Unit selector
    st.write("**Filter by Units** (leave empty for all)")
    selected_units_cpi = st.multiselect(
        "Select units:",
        options=units if units else [],
        default=None,
        key="cpi_units",
        help="Filter data by specific units (e.g., USD Million, TZS Billion)"
    )

    # Load data button
    if st.button("Load CPI Data", type="primary", key="cpi_btn"):
        with st.spinner("Querying Oracle database..."):
            df = get_data(
                conn,
                "CPI",
                start_year=start_y_cpi,
                end_year=end_y_cpi,
                start_month=start_m,
                end_month=end_m,
                location=loc_cpi,
                indicator_names=selected_indicators_cpi if selected_indicators_cpi else None,
                unit_names=selected_units_cpi if selected_units_cpi else None,
                aggregation=agg_cpi,
                wide_format=True
            )
            render_data_display(df, 'CPI')


# ────────────────────────────────────────────────
#   BOP Tab
# ────────────────────────────────────────────────
with tab_bop:
    st.subheader("Balance of Payments")

    # Date and location filters
    col1, col2 = st.columns(2)
    with col1:
        use_date_range_bop = st.checkbox("Use date range filter", value=False, key="bop_use_dates")
        
        if use_date_range_bop:
            start_date_bop = st.date_input(
                "Start date",
                value=pd.to_datetime("2020-01-01"),
                min_value=pd.to_datetime("2015-01-01"),
                max_value=pd.to_datetime("2030-12-31"),
                key="bop_start_date"
            )
            start_y_bop = start_date_bop.year
            start_m_bop = start_date_bop.month
        else:
            start_y_bop = st.number_input("Start year", 2015, 2030, 2020, key="bop_start")
            start_m_bop = None
            
        if locations:
            loc_bop = st.selectbox(
                "Location", 
                locations, 
                index=locations.index('Tanzania') if 'Tanzania' in locations else 0, 
                key="bop_loc"
            )
        else:
            loc_bop = st.text_input("Location name", "Tanzania", key="bop_loc_text")
    
    with col2:
        if use_date_range_bop:
            end_date_bop = st.date_input(
                "End date",
                value=pd.to_datetime("2023-12-31"),
                min_value=pd.to_datetime("2015-01-01"),
                max_value=pd.to_datetime("2030-12-31"),
                key="bop_end_date"
            )
            end_y_bop = end_date_bop.year
            end_m_bop = end_date_bop.month
        else:
            end_y_bop = st.number_input("End year", 2015, 2030, 2023, key="bop_end")
            end_m_bop = None
            
        agg_bop = st.selectbox(
            "Aggregation", 
            ["monthly", "quarterly", "annual", "fiscal_year"],
            help="Fiscal Year runs from July to June",
            key="bop_agg"
        )

    # Optional: Month range filter (only shown if not using date range)
    if not use_date_range_bop:
        use_months_bop = st.checkbox("Filter by month range", key="bop_months")
        if use_months_bop:
            col3, col4 = st.columns(2)
            with col3:
                start_m_bop = st.number_input("Start month", 1, 12, 1, key="bop_start_m")
            with col4:
                end_m_bop = st.number_input("End month", 1, 12, 12, key="bop_end_m")
        else:
            start_m_bop = None
            end_m_bop = None

    # Indicator selector
    selected_indicators_bop = render_indicator_selector(conn, 'BOP', 'bop')
    
    # Unit selector
    st.write("**Filter by Units** (leave empty for all)")
    selected_units_bop = st.multiselect(
        "Select units:",
        options=units if units else [],
        default=None,
        key="bop_units",
        help="Filter data by specific units (e.g., USD Million, TZS Billion)"
    )

    # Load data button
    if st.button("Load BOP Data", type="primary", key="bop_btn"):
        with st.spinner("Querying Oracle database..."):
            df = get_data(
                conn,
                "BOP",
                start_year=start_y_bop,
                end_year=end_y_bop,
                start_month=start_m_bop,
                end_month=end_m_bop,
                location=loc_bop,
                indicator_names=selected_indicators_bop if selected_indicators_bop else None,
                unit_names=selected_units_bop if selected_units_bop else None,
                aggregation=agg_bop,
                wide_format=True
            )
            render_data_display(df, 'BOP')


# ────────────────────────────────────────────────
#   Raw SQL Tab
# ────────────────────────────────────────────────
with tab_raw:
    st.subheader("Ad-hoc SQL Query")
    st.warning("⚠️ Use with caution - direct database access")
    
    sql = st.text_area(
        "Enter your SQL query:", 
        height=200, 
        value="SELECT * FROM DIM_INDICATOR WHERE ROWNUM <= 20"
    )
    
    if st.button("Execute Query", key="raw_btn"):
        try:
            with st.spinner("Executing query..."):
                df = pd.read_sql(sql, conn)
                st.success(f"✅ Query returned {len(df)} rows × {len(df.columns)} columns")
                st.dataframe(df, use_container_width=True)
                
                if not df.empty:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "⬇️ Download Results", 
                        csv,
                        "query_results.csv",
                        "text/csv",
                        key="raw_download"
                    )
        except Exception as e:
            st.error(f"❌ Query failed: {e}")


# ────────────────────────────────────────────────
#   Reference Data Tab
# ────────────────────────────────────────────────
with tab_ref:
    st.subheader("Reference Data")
    
    ref_tab1, ref_tab2, ref_tab3, ref_tab4 = st.tabs([
        "Locations", 
        "Indicators", 
        "Time Periods",
        "Units"
    ])
    
    with ref_tab1:
        st.write("**Available Locations:**")
        try:
            df_loc = pd.read_sql("SELECT * FROM DIM_LOCATION ORDER BY LOCATION_NAME", conn)
            st.dataframe(df_loc, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading locations: {e}")
    
    with ref_tab2:
        st.write("**Available Indicators:**")
        try:
            df_ind = pd.read_sql("SELECT * FROM DIM_INDICATOR ORDER BY INDICATOR_NAME", conn)
            st.dataframe(df_ind, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading indicators: {e}")
    
    with ref_tab3:
        st.write("**Time Periods (sample):**")
        try:
            df_time = pd.read_sql("""
                SELECT TIME_PERIOD, YEAR, MONTH, QUARTER, 
                       IS_MONTH_END, IS_QUARTER_END 
                FROM DIM_TIME 
                WHERE ROWNUM <= 50 
                ORDER BY TIME_PERIOD DESC
            """, conn)
            st.dataframe(df_time, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading time periods: {e}")
    
    with ref_tab4:
        st.write("**Available Units:**")
        try:
            df_units = pd.read_sql("SELECT * FROM DIM_UNITS ORDER BY UNIT", conn)
            st.dataframe(df_units, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading units: {e}")


# ────────────────────────────────────────────────
#   Sidebar
# ────────────────────────────────────────────────
with st.sidebar:
    conn_info = format_connection_info(conn)
    st.info(f"**Oracle DB Version:** {conn_info['version']}")
    st.caption(f"Connected as: **{conn_info['username']}**")
    
    if st.button("🔄 Test Connection"):
        success, message, timestamp = test_connection(conn)
        if success:
            st.success(f"✅ {message}\n\nServer time: {timestamp}")
        else:
            st.error(f"❌ {message}")
    
    # Logout button
    if st.button("🚪 Disconnect", type="secondary"):
        try:
            conn.close()
        except:
            pass
        st.session_state.connected = False
        st.session_state.conn = None
        st.rerun()
    
    st.divider()
    st.subheader("Quick Stats")
    stats = get_quick_stats(conn)
    st.metric("CPI Records", f"{stats['cpi_count']:,}")
    st.metric("BOP Records", f"{stats['bop_count']:,}")