"""
app.py - Modern Economic Indicators Dashboard (CPI & BOP) with Plotly charts
Enhanced version with improved UI/UX and updated connection style
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

try:
    from .database import (
        get_oracle_connection,
        get_data,
        get_locations,
        get_units,
        get_units_for_indicators,
        test_connection,
        get_indicators
    )
except ImportError:
    # Running directly (e.g., streamlit run app.py)
    from database import (
        get_oracle_connection,
        get_data,
        get_locations,
        get_units,
        get_units_for_indicators,
        test_connection,
        get_indicators
    )

# ────────────────────────────────────────────────
#   Page config & global styling
# ────────────────────────────────────────────────
st.set_page_config(page_title="Macroeconomic Database Explorer", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(145deg, #f8fafc, #f1f5f9);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 600 !important;
    }
    
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    section[data-testid="stSidebar"] button {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: white;
        border-radius: 12px;
        padding: 8px 12px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        color: #475569;
        font-weight: 500;
        padding: 0 20px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        padding: 0.7rem 1.4rem;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }

    hr { 
        margin: 1.8rem 0; 
        border: none;
        border-top: 2px solid #e2e8f0;
    }
    
    .stExpander {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ──── Header ────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1.5rem;">
        <h1 style="margin:0; font-size: 2.9rem; color: #1e293b; font-weight: 700;">
            📊 Macroeconomic Database Explorer
        </h1>
        <p style="color: #64748b; font-size: 1.2rem; margin-top: 0.5rem; font-weight: 400;">
            Bank of Tanzania Hub for Macroeconomic and Financial Statistics
        </p>
    </div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#   Session state & login
# ────────────────────────────────────────────────
if 'connected' not in st.session_state:
    st.session_state.connected = False
    st.session_state.conn = None

if not st.session_state.connected:
    st.info("🔐 Please enter your Oracle database credentials to connect.")
    
    with st.form("login"):
        st.markdown("### Database Connection")
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", value="", placeholder="Enter username")
            host = st.text_input("Host", value="172.16.1.219", 
                               help="Database server hostname or IP",
                               placeholder="172.16.1.219")
            port = st.number_input("Port", value=1522, min_value=1, max_value=65535,
                                 help="Database port number")
        with col2:
            password = st.text_input("Password", type="password", placeholder="Enter password")
            service_name = st.text_input("Service Name", value="BOT6DB",
                                       help="Database service name",
                                       placeholder="BOT6DB")
            st.write("")  # Spacing
        
        submitted = st.form_submit_button("🔌 Connect to Database", type="primary", use_container_width=True)
        
        if submitted:
            if username and password and host and service_name:
                with st.spinner("Connecting to database..."):
                    try:
                        conn = get_oracle_connection(username, password, host, int(port), service_name)
                        if conn:
                            st.session_state.connected = True
                            st.session_state.conn = conn
                            st.session_state.connection_info = {
                                'username': username,
                                'host': host,
                                'port': port,
                                'service_name': service_name
                            }
                            st.success("✅ Connected successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Connection failed. Please check your credentials.")
                    except Exception as e:
                        st.error(f"❌ Connection error: {str(e)}")
            else:
                st.error("⚠️ All fields are required.")
    st.stop()

conn = st.session_state.conn

# Load reference data with error handling
try:
    locations = get_locations(conn) or ["Tanzania"]
    units = get_units(conn) or []
except Exception as e:
    st.error(f"Error loading reference data: {e}")
    locations = ["Tanzania"]
    units = []

# ────────────────────────────────────────────────
#   Enhanced render_data_display (Plotly + metrics)
# ────────────────────────────────────────────────
def render_data_display(df: pd.DataFrame, title: str, indicator_type: str):
    """Enhanced data display with better visualizations and metrics"""
    if df.empty:
        st.warning(f"⚠️ No data found for {title}. Try adjusting your filters.")
        return

    st.markdown(f"### {title} Results")
    st.markdown("---")

    # Enhanced metrics cards with better styling
    cols = st.columns(4)
    
    # Total rows
    with cols[0]:
        st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;'>
                <div style='font-size: 0.75rem; color: #64748b; font-weight: 500; margin-bottom: 0.5rem;'>
                    📊 TOTAL RECORDS
                </div>
                <div style='font-size: 2rem; font-weight: 700; color: #1e293b;'>
                    {len(df):,}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Time period
    time_col = next((c for c in ["TIME_PERIOD", "YEAR", "FISCAL_YEAR", "PERIOD"] if c in df.columns), None)
    if time_col:
        time_range = f"{df[time_col].min()} – {df[time_col].max()}"
        with cols[1]:
            st.markdown(f"""
                <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;'>
                    <div style='font-size: 0.75rem; color: #64748b; font-weight: 500; margin-bottom: 0.5rem;'>
                        📅 TIME RANGE
                    </div>
                    <div style='font-size: 1.4rem; font-weight: 700; color: #1e293b;'>
                        {time_range}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # Number of series
    numeric = df.select_dtypes("number").columns.tolist()
    with cols[2]:
        st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;'>
                <div style='font-size: 0.75rem; color: #64748b; font-weight: 500; margin-bottom: 0.5rem;'>
                    📈 DATA SERIES
                </div>
                <div style='font-size: 2rem; font-weight: 700; color: #1e293b;'>
                    {len(numeric)}
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Location
    location_val = df.get("LOCATION_NAME", df.get("LOCATION", pd.Series(["—"]))).iloc[0]
    with cols[3]:
        st.markdown(f"""
            <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); text-align: center;'>
                <div style='font-size: 0.75rem; color: #64748b; font-weight: 500; margin-bottom: 0.5rem;'>
                    🌍 LOCATION
                </div>
                <div style='font-size: 1.6rem; font-weight: 700; color: #1e293b;'>
                    {location_val}
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # Show indicator descriptions if available
    if 'DESCRIPTION' in df.columns:
        indicator_desc = df[['INDICATOR_NAME', 'DESCRIPTION']].drop_duplicates() if 'INDICATOR_NAME' in df.columns else pd.DataFrame()
        
        if not indicator_desc.empty and indicator_desc['DESCRIPTION'].notna().any():
            with st.expander("📋 Indicator Descriptions", expanded=False):
                for _, row in indicator_desc.iterrows():
                    if pd.notna(row['DESCRIPTION']) and row['DESCRIPTION'].strip():
                        st.markdown(f"""
                            <div style='background: #f8fafc; padding: 0.8rem; border-radius: 6px; margin-bottom: 0.8rem; border-left: 3px solid #3b82f6;'>
                                <div style='font-weight: 600; color: #1e293b; margin-bottom: 0.3rem;'>{row['INDICATOR_NAME']}</div>
                                <div style='color: #64748b; font-size: 0.9rem;'>{row['DESCRIPTION']}</div>
                            </div>
                        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Enhanced Plotly chart
    if time_col and len(numeric) > 0:
        id_vars = [time_col]
        if "LOCATION_NAME" in df.columns: 
            id_vars.append("LOCATION_NAME")
        elif "LOCATION" in df.columns:
            id_vars.append("LOCATION")
            
        value_vars = [c for c in df.columns if c not in id_vars + ["UNIT_NAME", "INDICATOR_CODE", "LOCATION_CODE", "DESCRIPTION"]]

        if value_vars:
            df_long = pd.melt(df, id_vars=id_vars, value_vars=value_vars,
                             var_name="Indicator", value_name="Value")
            df_long = df_long.dropna(subset=["Value"])
            df_long = df_long.sort_values(time_col)

            fig = px.line(
                df_long, 
                x=time_col, 
                y="Value", 
                color="Indicator",
                markers=True, 
                title=f"{title} — Time Series Analysis",
                height=600
            )

            fig.update_layout(
                hovermode="x unified",
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.01,
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                    font=dict(size=11)
                ),
                xaxis_title=None,
                yaxis_title="Value",
                margin=dict(l=60, r=200, t=80, b=60),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="white",
                font=dict(family="Inter, sans-serif"),
                title_font_size=18,
                title_font_color="#1e293b",
                title_x=0.02
            )
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)', tickangle=-45)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.05)')

            if df_long["Value"].max() > 1e6:
                fig.update_yaxes(tickformat=",")

            fig.update_traces(
                hovertemplate="<b>%{fullData.name}</b><br>" +
                             time_col + ": %{x}<br>" +
                             "Value: %{y:,.2f}<extra></extra>",
                line=dict(width=2.5)
            )

            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Data table with enhanced display
    with st.expander("📋 View Raw Data & Download", expanded=False):
        display_df = df.copy()
        
        for col in numeric:
            if display_df[col].dtype in ['float64', 'float32']:
                display_df[col] = display_df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else "—")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download CSV",
                csv,
                f"{indicator_type.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        with col_dl2:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            excel_buffer.seek(0)
            
            st.download_button(
                "📊 Download Excel",
                excel_buffer.getvalue(),
                f"{indicator_type.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# ────────────────────────────────────────────────
#   Reusable Filter Component
# ────────────────────────────────────────────────
def render_filters(indicator_type: str, locations: list, units: list, conn):
    """Reusable filter component for both CPI and BOP tabs"""
    
    with st.expander("🔍 Filters & Options", expanded=True):
        col_time_loc, col_ind_units = st.columns([1.4, 1])

        with col_time_loc:
            st.markdown("**⏰ Time & Location**")
            
            use_range = st.checkbox(
                "Use date range instead of years", 
                value=False, 
                key=f"{indicator_type}_use_range",
                help="Select specific months within a date range"
            )

            if use_range:
                c1, c2 = st.columns(2)
                with c1:
                    start_dt = st.date_input(
                        "Start date", 
                        value=pd.to_datetime("2020-01-01"),
                        min_value=pd.to_datetime("1960-01-01"),
                        max_value=pd.to_datetime("2050-12-31"),
                        key=f"{indicator_type}_start_dt"
                    )
                with c2:
                    end_dt = st.date_input(
                        "End date", 
                        value=pd.to_datetime("2023-12-31"),
                        min_value=pd.to_datetime("1960-01-01"),
                        max_value=pd.to_datetime("2050-12-31"),
                        key=f"{indicator_type}_end_dt"
                    )
                start_year = start_dt.year
                end_year = end_dt.year
                start_month = start_dt.month
                end_month = end_dt.month
            else:
                c1, c2 = st.columns(2)
                with c1:
                    start_year = st.number_input(
                        "From year", 
                        min_value=1960, 
                        max_value=2050, 
                        value=2020, 
                        key=f"{indicator_type}_from_year"
                    )
                with c2:
                    end_year = st.number_input(
                        "To year", 
                        min_value=1960, 
                        max_value=2050, 
                        value=2023, 
                        key=f"{indicator_type}_to_year"
                    )
                start_month = end_month = None

            location = st.selectbox(
                "Location", 
                locations,
                index=locations.index("Tanzania") if "Tanzania" in locations else 0,
                key=f"{indicator_type}_location_select"
            )

            aggregation = st.selectbox(
                "Aggregation level",
                ["monthly", "quarterly", "annual", "fiscal_year"],
                key=f"{indicator_type}_agg_select",
                help="Choose how to aggregate the time series data"
            )

        with col_ind_units:
            st.markdown("**📊 Indicators & Units**")
            
            try:
                ind_df = get_indicators(conn, indicator_type)
                ind_options = sorted(ind_df['INDICATOR_NAME'].tolist()) if not ind_df.empty else []
            except Exception as e:
                ind_options = []
                st.caption(f"⚠️ Could not load indicators: {str(e)[:50]}")

            selected_indicators = st.multiselect(
                "Indicators",
                options=ind_options,
                default=[],
                key=f"{indicator_type}_indicators_ms",
                placeholder="All (if empty)",
                help=f"Select specific {indicator_type} indicators to display"
            )

            # Get units relevant to selected indicators (from fact table join)
            if selected_indicators:
                available_units = get_units_for_indicators(conn, selected_indicators, indicator_type)
            else:
                # No indicators selected - show all units for this type
                available_units = units if units else []

            if available_units:
                selected_units = st.multiselect(
                    "Units",
                    options=available_units,
                    default=[],
                    key=f"{indicator_type}_units_ms",
                    placeholder="All (if empty)",
                    help="Units available for the selected indicators"
                )
            else:
                selected_units = []
                if selected_indicators:
                    st.caption("No units found for selected indicators")
    
    if selected_indicators:
        with st.expander("📋 Selected Indicator Descriptions & Metadata", expanded=False):
            try:
                # Determine fact table based on indicator type
                fact_table = "FACT_CPI" if indicator_type == "CPI" else "FACT_BOP"

                placeholders = ','.join([f':ind{i}' for i in range(len(selected_indicators))])
                query = f"""
                    SELECT DISTINCT
                        i.INDICATOR_NAME,
                        i.DESCRIPTION,
                        i.INDICATOR_TYPE,
                        i.SECTION,
                        u.UNIT,
                        l.LOCATION_NAME,
                        s.SOURCE
                    FROM {fact_table} f
                    JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
                    LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
                    JOIN DIM_LOCATION l ON f.LOCATION_ID = l.LOCATION_ID
                    LEFT JOIN DIM_SOURCES s ON f.SOURCE_ID = s.SOURCE_ID
                    WHERE i.INDICATOR_NAME IN ({placeholders})
                    ORDER BY i.INDICATOR_NAME, l.LOCATION_NAME
                """
                params = {f'ind{i}': name for i, name in enumerate(selected_indicators)}

                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                cursor.close()

                if rows:
                    # Create DataFrame for download
                    metadata_df = pd.DataFrame(rows, columns=columns)

                    # Display descriptions with source, units, and location info
                    # Group by indicator to show unique descriptions
                    for indicator_name in metadata_df['INDICATOR_NAME'].unique():
                        indicator_rows = metadata_df[metadata_df['INDICATOR_NAME'] == indicator_name]
                        indicator_data = indicator_rows.iloc[0]
                        description = indicator_data.get('DESCRIPTION', None)

                        # Get all distinct units for this indicator
                        units = indicator_rows['UNIT'].dropna().unique()
                        units_str = ', '.join([str(u) for u in units if u]) or 'N/A'

                        # Get all distinct locations
                        locations = indicator_rows['LOCATION_NAME'].unique()
                        locations_str = ', '.join([str(loc) for loc in locations if loc])

                        # Get source (should be same for all rows of same indicator)
                        source = indicator_data.get('SOURCE', 'N/A') or 'N/A'

                        st.markdown(f"""
                            <div style='background: #f8fafc; padding: 0.8rem; border-radius: 6px; margin-bottom: 0.8rem; border-left: 3px solid #3b82f6;'>
                                <div style='font-weight: 600; color: #1e293b; margin-bottom: 0.3rem; font-size: 0.95rem;'>{indicator_name}</div>
                                <div style='color: #64748b; font-size: 0.85rem; line-height: 1.5;'>{description if description and str(description).strip() else 'No description available'}</div>
                                <div style='color: #475569; font-size: 0.8rem; margin-top: 0.4rem;'><strong>Source:</strong> {source} | <strong>Unit(s):</strong> {units_str} | <strong>Location(s):</strong> {locations_str}</div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Download buttons for metadata
                    st.markdown("---")
                    st.markdown("**📥 Download Indicator Metadata**")
                    col_csv, col_excel = st.columns(2)

                    with col_csv:
                        csv_data = metadata_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📄 Download CSV",
                            csv_data,
                            f"{indicator_type.lower()}_indicator_metadata.csv",
                            "text/csv",
                            use_container_width=True,
                            key=f"{indicator_type}_metadata_csv"
                        )

                    with col_excel:
                        excel_buffer = BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            metadata_df.to_excel(writer, index=False, sheet_name='Indicator Metadata')
                        excel_buffer.seek(0)

                        st.download_button(
                            "📊 Download Excel",
                            excel_buffer.getvalue(),
                            f"{indicator_type.lower()}_indicator_metadata.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"{indicator_type}_metadata_xlsx"
                        )
                else:
                    st.info("No descriptions found for selected indicators.")
            except Exception as e:
                st.warning(f"Could not load descriptions: {str(e)[:100]}")

    return {
        'start_year': start_year,
        'end_year': end_year,
        'start_month': start_month,
        'end_month': end_month,
        'location': location,
        'aggregation': aggregation,
        'selected_indicators': selected_indicators or None,
        'selected_units': selected_units or None
    }

# ──── Tabs ──────────────────────────────────────────────────────────────────
tab_cpi, tab_bop, tab_raw, tab_ref = st.tabs([
    "📈 CPI Analysis", "💰 BOP Analysis", "🔧 Raw SQL", "📚 Reference Data"
])

# ────────────────────────────────────────────────
#   CPI Tab
# ────────────────────────────────────────────────
with tab_cpi:
    st.markdown("### Consumer Price Index (CPI)")
    st.markdown("Track inflation and price changes over time")
    st.markdown("---")

    filters = render_filters("CPI", locations, units, conn)
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    
    if st.button("🔄 Load CPI Data", type="primary", use_container_width=True, key="load_cpi"):
        with st.spinner("📊 Querying CPI data from database..."):
            try:
                df = get_data(
                    conn, "CPI",
                    start_year=filters['start_year'],
                    end_year=filters['end_year'],
                    start_month=filters['start_month'],
                    end_month=filters['end_month'],
                    location=filters['location'],
                    indicator_names=filters['selected_indicators'],
                    unit_names=filters['selected_units'],
                    aggregation=filters['aggregation'],
                    wide_format=True
                )
                render_data_display(df, "Consumer Price Index (CPI)", "CPI")
            except Exception as e:
                st.error(f"❌ Error loading CPI data: {str(e)}")
                st.info("Please check your database connection and filter settings.")

# ────────────────────────────────────────────────
#   BOP Tab
# ────────────────────────────────────────────────
with tab_bop:
    st.markdown("### Balance of Payments (BOP)")
    st.markdown("Analyze international transactions and foreign exchange flows")
    st.markdown("---")

    filters = render_filters("BOP", locations, units, conn)
    
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    
    if st.button("🔄 Load BOP Data", type="primary", use_container_width=True, key="load_bop"):
        with st.spinner("📊 Querying BOP data from database..."):
            try:
                df = get_data(
                    conn, "BOP",
                    start_year=filters['start_year'],
                    end_year=filters['end_year'],
                    start_month=filters['start_month'],
                    end_month=filters['end_month'],
                    location=filters['location'],
                    indicator_names=filters['selected_indicators'],
                    unit_names=filters['selected_units'],
                    aggregation=filters['aggregation'],
                    wide_format=True
                )
                render_data_display(df, "Balance of Payments (BOP)", "BOP")
            except Exception as e:
                st.error(f"❌ Error loading BOP data: {str(e)}")
                st.info("Please check your database connection and filter settings.")

# ────────────────────────────────────────────────
#   Raw SQL Tab
# ────────────────────────────────────────────────
with tab_raw:
    st.markdown("### 🔧 Raw SQL Query Interface")
    st.markdown("Execute custom SQL queries directly on the database")
    st.markdown("---")
    
    st.warning("⚠️ **Advanced users only**. Be careful with write operations.")
    
    sql_query = st.text_area(
        "SQL Query",
        height=200,
        placeholder="SELECT * FROM your_table WHERE...",
        help="Enter your SQL query here. Read-only queries are recommended."
    )
    
    col_exec, col_clear = st.columns([1, 4])
    with col_exec:
        execute_btn = st.button("▶️ Execute", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()
    
    if execute_btn and sql_query.strip():
        try:
            with st.spinner("Executing query..."):
                df_result = pd.read_sql(sql_query, conn)
                
                st.success(f"✅ Query executed successfully! Returned {len(df_result)} rows.")
                
                if not df_result.empty:
                    st.dataframe(df_result, use_container_width=True, hide_index=False)
                    
                    csv = df_result.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download Results as CSV",
                        csv,
                        f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                else:
                    st.info("Query executed but returned no results.")
        except Exception as e:
            st.error(f"❌ Query error: {str(e)}")
    elif execute_btn:
        st.warning("Please enter a SQL query first.")

# ────────────────────────────────────────────────
#   Reference Data Tab
# ────────────────────────────────────────────────
with tab_ref:
    st.markdown("### 📚 Reference Data & Metadata")
    st.markdown("View available locations, indicators, units, and other reference information")
    st.markdown("---")
    
    ref_tabs = st.tabs(["📍 Locations", "📊 CPI Indicators", "💰 BOP Indicators", "📏 Units"])
    
    # Locations
    with ref_tabs[0]:
        st.markdown("#### Available Locations")
        if locations:
            loc_df = pd.DataFrame({"Location": locations})
            st.dataframe(loc_df, use_container_width=True, hide_index=True)
        else:
            st.info("No location data available")
    
    # CPI Indicators
    with ref_tabs[1]:
        st.markdown("#### CPI Indicators")
        try:
            cpi_ind = get_indicators(conn, 'CPI')
            if not cpi_ind.empty:
                st.dataframe(cpi_ind, use_container_width=True, hide_index=True)
                st.caption(f"Total: {len(cpi_ind)} CPI indicators")
            else:
                st.info("No CPI indicators found")
        except Exception as e:
            st.error(f"Error loading CPI indicators: {e}")
    
    # BOP Indicators
    with ref_tabs[2]:
        st.markdown("#### BOP Indicators")
        try:
            bop_ind = get_indicators(conn, 'BOP')
            if not bop_ind.empty:
                st.dataframe(bop_ind, use_container_width=True, hide_index=True)
                st.caption(f"Total: {len(bop_ind)} BOP indicators")
            else:
                st.info("No BOP indicators found")
        except Exception as e:
            st.error(f"Error loading BOP indicators: {e}")
    
    # Units
    with ref_tabs[3]:
        st.markdown("#### Measurement Units")
        if units:
            units_df = pd.DataFrame({"Unit": units})
            st.dataframe(units_df, use_container_width=True, hide_index=True)
        else:
            st.info("No unit data available")

# ────────────────────────────────────────────────
#   Sidebar (Enhanced)
# ────────────────────────────────────────────────
with st.sidebar:
    # Database icon
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C8 2 4 3.5 4 5.5V18.5C4 20.5 8 22 12 22C16 22 20 20.5 20 18.5V5.5C20 3.5 16 2 12 2Z" 
                      fill="url(#grad1)" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M4 12C4 14 8 15.5 12 15.5C16 15.5 20 14 20 12" 
                      stroke="#60a5fa" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M4 8.5C4 10.5 8 12 12 12C16 12 20 10.5 20 8.5" 
                      stroke="#60a5fa" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <ellipse cx="12" cy="5.5" rx="8" ry="3.5" fill="#3b82f6" opacity="0.3"/>
                <defs>
                    <linearGradient id="grad1" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#3b82f6"/>
                        <stop offset="100%" stop-color="#1e40af"/>
                    </linearGradient>
                </defs>
            </svg>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎛️ Database Controls")
    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin: 1rem 0;">', unsafe_allow_html=True)

    # Connection status
    if st.button("🔄 Test Connection", use_container_width=True, key="test_conn_btn"):
        ok, msg, ts = test_connection(conn)
        if ok:
            st.success(f"✅ Active\n\n🕐 {ts}")
        else:
            st.error(f"❌ {msg}")

    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin: 1rem 0;">', unsafe_allow_html=True)
    
    # Database info
    with st.expander("ℹ️ Connection Info", expanded=False):
        try:
            st.markdown(f"""
                <div style='background: rgba(59, 130, 246, 0.15); padding: 1rem; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.4);'>
                    <p style='margin: 0.5rem 0; color: #e2e8f0; font-size: 0.9rem;'><strong>User:</strong> {conn.username if hasattr(conn, 'username') else 'N/A'}</p>
                    <p style='margin: 0.5rem 0; color: #e2e8f0; font-size: 0.9rem;'><strong>DSN:</strong> {conn.dsn if hasattr(conn, 'dsn') else 'N/A'}</p>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
                <div style='background: rgba(239, 68, 68, 0.15); padding: 1rem; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.4);'>
                    <p style='margin: 0; color: #fca5a5; font-size: 0.9rem;'>Connection details unavailable</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin: 1rem 0;">', unsafe_allow_html=True)
    
    # Disconnect button
    if st.button("🔌 Disconnect", type="secondary", use_container_width=True, key="disconnect_btn"):
        try:
            conn.close()
            st.success("Disconnected successfully")
        except Exception as e:
            st.warning(f"Disconnect warning: {e}")
        finally:
            st.session_state.connected = False
            st.session_state.conn = None
            st.rerun()
    
    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin: 1.5rem 0;">', unsafe_allow_html=True)
    
    # Quick Stats
    with st.expander("📊 Quick Stats", expanded=False):
        st.markdown("""
            <div style='background: rgba(16, 185, 129, 0.15); padding: 1rem; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.4);'>
                <p style='margin: 0.5rem 0; color: #e2e8f0; font-size: 0.9rem;'><strong>Tables:</strong> CPI, BOP, + More Coming</p>
                <p style='margin: 0.5rem 0; color: #e2e8f0; font-size: 0.9rem;'><strong>Coverage:</strong> Tanzania Macroeconomic Data</p>
                <p style='margin: 0.5rem 0; color: #e2e8f0; font-size: 0.9rem;'><strong>Status:</strong> Active & Expanding</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<hr style="border-color: rgba(255,255,255,0.2); margin: 1.5rem 0;">', unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0; color: #94a3b8;'>
            <small style='color: #cbd5e1;'>Macroeconomic Database v2.0</small><br>
            <small style='color: #94a3b8;'>© 2026 Tanzania Economic Data</small>
        </div>
    """, unsafe_allow_html=True)