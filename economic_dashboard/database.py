"""
database.py - Database connection and query functions
"""

import streamlit as st
import oracledb
import pandas as pd


@st.cache_resource
def get_oracle_connection(username: str, password: str, host: str, port: int = 1522, service_name: str = "BOT6DB"):
    """
    Create Oracle database connection using makedsn approach
    
    Args:
        username: Database username
        password: Database password
        host: Database host (e.g., '172.16.1.219')
        port: Database port (default: 1522)
        service_name: Database service name (default: 'BOT6DB')
    
    Returns:
        Connection object or None if connection fails
    """
    try:
        # Create DSN using makedsn
        dsn = oracledb.makedsn(host, port, service_name=service_name)
        
        # Create connection
        conn = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        
        print(f"✅ Successfully connected to {host}:{port}/{service_name}")
        return conn
        
    except oracledb.Error as e:
        error, = e.args
        print(f"❌ Oracle connection error: {error.message}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return None
    


def execute_query(cursor, query, params=None, wide_format=True):
    """
    Execute SQL query and return results as DataFrame
    
    Args:
        cursor: Active database cursor object
        query: SQL query string
        params: Query parameters dictionary (optional)
        wide_format: If True, pivot to wide format with indicators as columns
    
    Returns:
        DataFrame with query results
    """
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)

        if wide_format and not df.empty:
            required_cols = ['TIME_PERIOD', 'LOCATION_NAME', 'INDICATOR_NAME', 'VALUE']
            if all(col in df.columns for col in required_cols):
                df = df.pivot_table(
                    index=['TIME_PERIOD', 'LOCATION_NAME'],
                    columns='INDICATOR_NAME',
                    values='VALUE',
                    aggfunc='first'
                ).reset_index()

        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()


def get_data(
    connection,
    data_group: str,
    start_year=2020,
    end_year=2030,
    start_month=None,
    end_month=None,
    location='Tanzania',
    indicator_names=None,
    unit_names=None,
    aggregation='monthly',
    wide_format=True
):
    """
    Get data for CPI or BOP with flexible filtering and aggregation
    
    Args:
        connection: Active Oracle connection object
        data_group: 'CPI' or 'BOP'
        start_year: Start year for data
        end_year: End year for data
        start_month: Start month (1-12, optional)
        end_month: End month (1-12, optional)
        location: Location name to filter
        indicator_names: List of indicator names to filter (optional)
        unit_names: List of unit names to filter (optional, e.g., ['USD Million', 'TZS Million'])
        aggregation: 'monthly', 'quarterly', 'annual', or 'fiscal_year'
        wide_format: If True, pivot data to wide format
    
    Returns:
        DataFrame with queried data
    """
    cursor = connection.cursor()

    map_table = {'CPI': 'FACT_CPI', 'BOP': 'FACT_BOP'}
    if data_group not in map_table:
        st.error("Invalid data_group. Use 'CPI' or 'BOP'")
        cursor.close()
        return pd.DataFrame()

    fact_table = map_table[data_group]
    
    # Determine aggregation function based on data type
    # CPI: flows are averaged, BOP: flows are summed
    if data_group == 'BOP':
        flow_agg = 'SUM'  # BOP flows should be summed
    else:
        flow_agg = 'AVG'  # CPI flows should be averaged

    # Build query based on aggregation level
    if aggregation == 'monthly':
        # Monthly: return all data with proper time columns
        query = f"""
            SELECT 
                t.TIME_PERIOD,
                t.YEAR,
                t.MONTH,
                t.QUARTER,
                l.LOCATION_NAME,
                i.INDICATOR_NAME,
                i.INDICATOR_TYPE,
                i.DESCRIPTION,
                f.VALUE,
                u.UNIT
            FROM {fact_table} f
            JOIN DIM_TIME t ON f.TIME_ID = t.TIME_ID
            JOIN DIM_LOCATION l ON f.LOCATION_ID = l.LOCATION_ID
            JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
            LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
            WHERE t.YEAR BETWEEN :start_year AND :end_year
            AND l.LOCATION_NAME = :location
        """
    
    elif aggregation == 'quarterly':
        # Quarterly: aggregate flows (SUM for BOP, AVG for CPI), take end-of-quarter for stocks
        query = f"""
            SELECT 
                t.YEAR || 'Q' || t.QUARTER AS TIME_PERIOD,
                t.YEAR,
                t.QUARTER,
                l.LOCATION_NAME,
                i.INDICATOR_NAME,
                i.INDICATOR_TYPE,
                i.DESCRIPTION,
                CASE 
                    WHEN UPPER(i.INDICATOR_TYPE) = 'FLOW' THEN {flow_agg}(f.VALUE)
                    WHEN UPPER(i.INDICATOR_TYPE) = 'STOCK' THEN MAX(CASE WHEN t.IS_QUARTER_END = 1 THEN f.VALUE END)
                    ELSE {flow_agg}(f.VALUE)
                END AS VALUE,
                u.UNIT
            FROM {fact_table} f
            JOIN DIM_TIME t ON f.TIME_ID = t.TIME_ID
            JOIN DIM_LOCATION l ON f.LOCATION_ID = l.LOCATION_ID
            JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
            LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
            WHERE t.YEAR BETWEEN :start_year AND :end_year
            AND l.LOCATION_NAME = :location
        """
    
    elif aggregation == 'fiscal_year':
        # Fiscal Year (July-June): calculate fiscal year and aggregate
        query = f"""
            SELECT 
                'FY' || CASE 
                    WHEN t.MONTH >= 7 THEN t.YEAR || '/' || (t.YEAR + 1)
                    ELSE (t.YEAR - 1) || '/' || t.YEAR
                END AS TIME_PERIOD,
                CASE 
                    WHEN t.MONTH >= 7 THEN t.YEAR
                    ELSE t.YEAR - 1
                END AS FISCAL_YEAR,
                l.LOCATION_NAME,
                i.INDICATOR_NAME,
                i.INDICATOR_TYPE,
                i.DESCRIPTION,
                CASE 
                    WHEN UPPER(i.INDICATOR_TYPE) = 'FLOW' THEN {flow_agg}(f.VALUE)
                    WHEN UPPER(i.INDICATOR_TYPE) = 'STOCK' THEN MAX(CASE WHEN t.MONTH = 6 THEN f.VALUE END)
                    ELSE {flow_agg}(f.VALUE)
                END AS VALUE,
                u.UNIT
            FROM {fact_table} f
            JOIN DIM_TIME t ON f.TIME_ID = t.TIME_ID
            JOIN DIM_LOCATION l ON f.LOCATION_ID = l.LOCATION_ID
            JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
            LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
            WHERE (
                (t.YEAR = :start_year - 1 AND t.MONTH >= 7) OR
                (t.YEAR BETWEEN :start_year AND :end_year) OR
                (t.YEAR = :end_year + 1 AND t.MONTH <= 6)
            )
            AND l.LOCATION_NAME = :location
        """
    
    else:  # annual
        # Annual: aggregate flows (SUM for BOP, AVG for CPI), take year-end for stocks
        query = f"""
            SELECT 
                t.YEAR AS TIME_PERIOD,
                t.YEAR,
                l.LOCATION_NAME,
                i.INDICATOR_NAME,
                i.INDICATOR_TYPE,
                i.DESCRIPTION,
                CASE 
                    WHEN UPPER(i.INDICATOR_TYPE) = 'FLOW' THEN {flow_agg}(f.VALUE)
                    WHEN UPPER(i.INDICATOR_TYPE) = 'STOCK' THEN MAX(CASE WHEN t.MONTH = 12 THEN f.VALUE END)
                    ELSE {flow_agg}(f.VALUE)
                END AS VALUE,
                u.UNIT
            FROM {fact_table} f
            JOIN DIM_TIME t ON f.TIME_ID = t.TIME_ID
            JOIN DIM_LOCATION l ON f.LOCATION_ID = l.LOCATION_ID
            JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
            LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
            WHERE t.YEAR BETWEEN :start_year AND :end_year
            AND l.LOCATION_NAME = :location
        """
    
    params = {
        'start_year': start_year,
        'end_year': end_year,
        'location': location
    }

    # Add month filter if specified
    if start_month and end_month:
        query += " AND t.MONTH BETWEEN :start_month AND :end_month"
        params['start_month'] = start_month
        params['end_month'] = end_month

    # Add indicator filter if specified
    if indicator_names and len(indicator_names) > 0:
        if isinstance(indicator_names, str):
            indicator_names = [indicator_names]
        placeholders = ','.join([f':ind{i}' for i in range(len(indicator_names))])
        query += f" AND i.INDICATOR_NAME IN ({placeholders})"
        for i, name in enumerate(indicator_names):
            params[f'ind{i}'] = name
    
    # Add unit filter if specified
    if unit_names and len(unit_names) > 0:
        if isinstance(unit_names, str):
            unit_names = [unit_names]
        placeholders = ','.join([f':unit{i}' for i in range(len(unit_names))])
        query += f" AND u.UNIT IN ({placeholders})"
        for i, name in enumerate(unit_names):
            params[f'unit{i}'] = name

    # Add GROUP BY for aggregated queries
    if aggregation == 'quarterly':
        query += """
            GROUP BY t.YEAR, t.QUARTER, l.LOCATION_NAME, 
                     i.INDICATOR_NAME, i.INDICATOR_TYPE, i.DESCRIPTION, u.UNIT
            ORDER BY t.YEAR, t.QUARTER, i.INDICATOR_NAME
        """
    elif aggregation == 'fiscal_year':
        query += """
            GROUP BY 
                CASE 
                    WHEN t.MONTH >= 7 THEN t.YEAR
                    ELSE t.YEAR - 1
                END,
                CASE 
                    WHEN t.MONTH >= 7 THEN t.YEAR || '/' || (t.YEAR + 1)
                    ELSE (t.YEAR - 1) || '/' || t.YEAR
                END,
                l.LOCATION_NAME, 
                i.INDICATOR_NAME, i.INDICATOR_TYPE, i.DESCRIPTION, u.UNIT
            ORDER BY 
                CASE 
                    WHEN t.MONTH >= 7 THEN t.YEAR
                    ELSE t.YEAR - 1
                END, 
                i.INDICATOR_NAME
        """
    elif aggregation == 'annual':
        query += """
            GROUP BY t.YEAR, l.LOCATION_NAME, 
                     i.INDICATOR_NAME, i.INDICATOR_TYPE, i.DESCRIPTION, u.UNIT
            ORDER BY t.YEAR, i.INDICATOR_NAME
        """
    else:
        query += " ORDER BY t.TIME_PERIOD, l.LOCATION_NAME, i.INDICATOR_NAME"

    df = execute_query(cursor, query, params, wide_format=wide_format)
    cursor.close()
    return df


@st.cache_data(ttl=600)
def get_units(_connection):
    """
    Get list of available units from database

    Args:
        _connection: Active Oracle connection object

    Returns:
        List of unit names
    """
    try:
        df = pd.read_sql("SELECT DISTINCT UNIT FROM DIM_UNITS ORDER BY UNIT", _connection)
        return df['UNIT'].tolist()
    except:
        return []


@st.cache_data(ttl=300)
def get_units_for_indicators(_connection, indicator_names: tuple, indicator_type: str):
    """
    Get list of units that are actually used by the specified indicators
    through the fact table join. Cached for 5 minutes.

    Args:
        _connection: Active Oracle connection object
        indicator_names: Tuple of indicator names to filter by (tuple for caching)
        indicator_type: 'CPI' or 'BOP' to determine which fact table to use

    Returns:
        List of unit names relevant to the selected indicators
    """
    if not indicator_names:
        return []

    try:
        fact_table = "FACT_CPI" if indicator_type == "CPI" else "FACT_BOP"

        # Create parameterized query
        placeholders = ','.join([f':ind{i}' for i in range(len(indicator_names))])
        query = f"""
            SELECT DISTINCT u.UNIT
            FROM {fact_table} f
            JOIN DIM_INDICATOR i ON f.INDICATOR_ID = i.INDICATOR_ID
            LEFT JOIN DIM_UNITS u ON f.UNIT_ID = u.UNIT_ID
            WHERE i.INDICATOR_NAME IN ({placeholders})
            AND u.UNIT IS NOT NULL
            ORDER BY u.UNIT
        """
        params = {f'ind{i}': name for i, name in enumerate(indicator_names)}

        cursor = _connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()

        return [row[0] for row in rows if row[0]]
    except:
        return []


@st.cache_data(ttl=600)
def get_locations(_connection):
    """
    Get list of available locations from database
    
    Args:
        _connection: Active Oracle connection object
    
    Returns:
        List of location names
    """
    try:
        df = pd.read_sql("SELECT DISTINCT LOCATION_NAME FROM DIM_LOCATION ORDER BY LOCATION_NAME", _connection)
        return df['LOCATION_NAME'].tolist()
    except:
        return []


@st.cache_data(ttl=600)
def get_indicators(_connection, section=None):
    """
    Get list of available indicators from database
    
    Args:
        _connection: Active Oracle connection object
        section: Filter by section ('CPI', 'BOP', etc.')
    
    Returns:
        DataFrame with indicator information
    """
    try:
        # Try SECTION column first, fallback to INDICATOR_TYPE
        query = """
            SELECT INDICATOR_NAME, DESCRIPTION, 
                   CASE 
                       WHEN EXISTS (SELECT 1 FROM USER_TAB_COLUMNS 
                                    WHERE TABLE_NAME = 'DIM_INDICATOR' 
                                    AND COLUMN_NAME = 'SECTION') 
                       THEN SECTION 
                       ELSE INDICATOR_TYPE 
                   END as SECTION
            FROM DIM_INDICATOR
        """
        if section:
            # Try SECTION first, fallback to INDICATOR_TYPE
            query = """
                SELECT INDICATOR_NAME, DESCRIPTION, SECTION
                FROM DIM_INDICATOR
                WHERE (UPPER(SECTION) = UPPER(:section)
                       OR (SECTION IS NULL AND UPPER(INDICATOR_TYPE) = UPPER(:section)))
                ORDER BY INDICATOR_NAME
            """
            df = pd.read_sql(query, _connection, params={'section': section})
        else:
            query += " ORDER BY INDICATOR_NAME"
            df = pd.read_sql(query, _connection)
        return df
    except Exception as e:
        # Fallback to simpler query
        try:
            query = "SELECT INDICATOR_NAME, DESCRIPTION FROM DIM_INDICATOR"
            if section:
                query += " WHERE UPPER(SECTION) = UPPER(:section)"
                df = pd.read_sql(query + " ORDER BY INDICATOR_NAME", _connection, params={'section': section})
            else:
                df = pd.read_sql(query + " ORDER BY INDICATOR_NAME", _connection)
            return df
        except:
            return pd.DataFrame()


def test_connection(connection):
    """
    Test database connection by querying current timestamp
    
    Args:
        connection: Active Oracle connection object
    
    Returns:
        Tuple of (success: bool, message: str, timestamp: str)
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT SYSDATE FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        return True, "Connection active", str(result[0])
    except Exception as e:
        return False, f"Connection failed: {e}", None