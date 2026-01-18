"""
utils.py - Utility functions for the dashboard
"""

import streamlit as st
import pandas as pd


def get_indicator_options(connection, data_group):
    """
    Get indicator options for a specific data group using multiple fallback strategies
    
    Args:
        connection: Active Oracle connection object
        data_group: 'CPI' or 'BOP'
    
    Returns:
        List of indicator names
    """
    from database import get_indicators
    
    indicator_options = []
    
    # Strategy 1: Try to get indicators by SECTION
    try:
        ind_list = get_indicators(connection, data_group)
        if not ind_list.empty:
            indicator_options = ind_list['INDICATOR_NAME'].tolist()
    except:
        pass
    
    # Strategy 2: If no section-based indicators, get from fact table
    if not indicator_options:
        try:
            fact_table = 'FACT_CPI' if data_group == 'CPI' else 'FACT_BOP'
            query = f"""
                SELECT DISTINCT i.INDICATOR_NAME 
                FROM {fact_table} f
                JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
                ORDER BY i.INDICATOR_NAME
            """
            df_ind = pd.read_sql(query, connection)
            indicator_options = df_ind['INDICATOR_NAME'].tolist()
        except:
            pass
    
    # Strategy 3: Get all indicators
    if not indicator_options:
        try:
            df_all_ind = pd.read_sql(
                "SELECT DISTINCT INDICATOR_NAME FROM DIM_INDICATOR ORDER BY INDICATOR_NAME",
                connection
            )
            indicator_options = df_all_ind['INDICATOR_NAME'].tolist()
        except:
            pass
    
    return indicator_options


def get_indicator_description(connection, indicator_name):
    """
    Get description for a specific indicator
    
    Args:
        connection: Active Oracle connection object
        indicator_name: Name of the indicator
    
    Returns:
        Description string or None
    """
    try:
        desc_query = "SELECT DESCRIPTION FROM DIM_INDICATOR WHERE INDICATOR_NAME = :ind_name"
        cursor = connection.cursor()
        cursor.execute(desc_query, {'ind_name': indicator_name})
        result = cursor.fetchone()
        cursor.close()
        if result and result[0]:
            return result[0]
    except:
        pass
    return None


def display_indicator_descriptions(connection, selected_indicators):
    """
    Display descriptions for selected indicators in an expander
    
    Args:
        connection: Active Oracle connection object
        selected_indicators: List of indicator names
    """
    if selected_indicators:
        with st.expander("📋 Selected Indicator Descriptions"):
            for ind in selected_indicators:
                desc = get_indicator_description(connection, ind)
                if desc:
                    st.write(f"**{ind}:** {desc}")
                else:
                    st.write(f"**{ind}**")


def render_date_filters(key_prefix, default_start="2020-01-01", default_end="2023-12-31"):
    """
    Render date filter widgets (calendar or year/month inputs)
    
    Args:
        key_prefix: Unique prefix for widget keys (e.g., 'cpi' or 'bop')
        default_start: Default start date string
        default_end: Default end date string
    
    Returns:
        Tuple of (start_year, end_year, start_month, end_month, use_date_range)
    """
    use_date_range = st.checkbox(
        "Use date range filter", 
        value=False, 
        key=f"{key_prefix}_use_dates"
    )
    
    if use_date_range:
        start_date = st.date_input(
            "Start date",
            value=pd.to_datetime(default_start),
            min_value=pd.to_datetime("2015-01-01"),
            max_value=pd.to_datetime("2030-12-31"),
            key=f"{key_prefix}_start_date"
        )
        start_year = start_date.year
        start_month = start_date.month
        
        end_date = st.date_input(
            "End date",
            value=pd.to_datetime(default_end),
            min_value=pd.to_datetime("2015-01-01"),
            max_value=pd.to_datetime("2030-12-31"),
            key=f"{key_prefix}_end_date"
        )
        end_year = end_date.year
        end_month = end_date.month
    else:
        # Traditional year inputs
        start_year = st.number_input(
            "Start year", 
            2015, 2030, 2020, 
            key=f"{key_prefix}_start"
        )
        end_year = st.number_input(
            "End year", 
            2015, 2030, 2023, 
            key=f"{key_prefix}_end"
        )
        
        # Optional month range filter
        use_months = st.checkbox(
            "Filter by month range", 
            key=f"{key_prefix}_months"
        )
        if use_months:
            col3, col4 = st.columns(2)
            with col3:
                start_month = st.number_input(
                    "Start month", 
                    1, 12, 1, 
                    key=f"{key_prefix}_start_m"
                )
            with col4:
                end_month = st.number_input(
                    "End month", 
                    1, 12, 12, 
                    key=f"{key_prefix}_end_m"
                )
        else:
            start_month = None
            end_month = None
    
    return start_year, end_year, start_month, end_month, use_date_range


def render_indicator_selector(connection, data_group, key_prefix):
    """
    Render indicator selector with multiple fallback strategies
    
    Args:
        connection: Active Oracle connection object
        data_group: 'CPI' or 'BOP'
        key_prefix: Unique prefix for widget keys
    
    Returns:
        List of selected indicator names or None
    """
    st.write("**Filter by Indicators** (leave empty for all)")
    
    indicator_options = get_indicator_options(connection, data_group)
    
    if indicator_options:
        selected_indicators = st.multiselect(
            f"Select {data_group} indicators:",
            options=indicator_options,
            default=None,
            key=f"{key_prefix}_indicators",
            help="Select one or more indicators, or leave empty to include all"
        )
        
        # Display count of selected indicators
        if selected_indicators:
            st.info(f"✓ {len(selected_indicators)} indicator(s) selected")
            display_indicator_descriptions(connection, selected_indicators)
        
        return selected_indicators
    else:
        st.warning("⚠️ No indicators found. Please check your DIM_INDICATOR table or add indicators manually below.")
        # Allow manual text input as absolute fallback
        manual_indicators = st.text_input(
            "Enter indicator names (comma-separated):",
            key=f"{key_prefix}_manual_indicators",
            help=f"Example: {data_group}_FOOD, {data_group}_TRANSPORT, {data_group}_HOUSING"
        )
        if manual_indicators:
            return [ind.strip() for ind in manual_indicators.split(',')]
        else:
            return None


def get_quick_stats(connection):
    """
    Get quick statistics for the sidebar
    
    Args:
        connection: Active Oracle connection object
    
    Returns:
        Dictionary with stat counts
    """
    stats = {}
    try:
        cursor = connection.cursor()
        
        # Count CPI records
        cursor.execute("SELECT COUNT(*) FROM FACT_CPI")
        stats['cpi_count'] = cursor.fetchone()[0]
        
        # Count BOP records
        cursor.execute("SELECT COUNT(*) FROM FACT_BOP")
        stats['bop_count'] = cursor.fetchone()[0]
        
        cursor.close()
    except:
        stats['cpi_count'] = 0
        stats['bop_count'] = 0
    
    return stats


def render_data_display(df, data_group):
    """
    Render data display with download button
    
    Args:
        df: DataFrame to display
        data_group: 'CPI' or 'BOP'
    """
    if df is not None and not df.empty:
        st.success(f"✅ Retrieved {len(df)} rows")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Download as CSV", 
            csv,
            f"{data_group.lower()}_data.csv",
            "text/csv",
            key=f"{data_group.lower()}_download"
        )
    else:
        st.warning("No data returned. Check your filters.")


def format_connection_info(connection):
    """
    Format connection information for display
    
    Args:
        connection: Active Oracle connection object
    
    Returns:
        Dictionary with connection info
    """
    try:
        return {
            'version': connection.version,
            'username': connection.username
        }
    except:
        return {
            'version': 'Unknown',
            'username': 'Unknown'
        }