# Economic Indicators Dashboard

A dashboard for exploring macroeconomic data — CPI, Balance of Payments, Monetary & Financial Statistics, Fiscal Statistics, and Interest Rates — from an Oracle database.

---

## Installation

Pick whichever method works for you.

**From GitHub:**
```bash
pip install git+https://github.com/dominicmwitta/data-portal.git@main
```

**From source (development mode):**
```bash
git clone https://github.com/dominicmwitta/data-portal.git
cd macro_database
pip install -e .
```

**From a wheel file:**
```bash
pip install economic_indicators_dashboard-1.0.0-py3-none-any.whl
```

After installation, a desktop shortcut called **Economic Dashboard** is created automatically the first time you run the dashboard.

---

## Launch the Dashboard

Open a terminal and run:

```bash
get-data
```

This opens the dashboard in your browser at `http://localhost:8501`. Press `Ctrl+C` in the terminal to stop it.

---

## First Run — Database Connection

When you open the dashboard for the first time, enter your Oracle database credentials:

- **Username** — your Oracle username
- **Password** — your Oracle password
- **DSN** — connection string in the format `hostname:port/service_name`

Your credentials are used only for the current session and are never stored.

---

## What You Can Do

The dashboard has five tabs:

| Tab | Data |
|-----|------|
| CPI & Inflation | Consumer price indices and inflation rates |
| Balance of Payments | BOP summary and component data |
| Monetary & Financial Statistics | Money supply, credit, and financial indicators |
| Fiscal Statistics | Government revenue, expenditure, and fiscal balances |
| Interest Rates | Lending, deposit, and policy interest rates |

**Filtering options on every tab:**
- Choose a date range (year and month)
- Select a location
- Pick specific indicators
- Filter by unit of measurement
- Choose an aggregation level: monthly, quarterly, annual, or fiscal year (July–June)

**Aggregation behaviour:**
- CPI and Interest Rate indicators are always aggregated as an **average**
- Flow indicators (e.g. BOP flows) are summed
- Stock indicators use the end-of-period value

**Exports:**
- Download data as CSV or Excel
- The Excel export includes a **Metadata sheet** with indicator descriptions, definitions, units, source, and location

---

## Database Schema

Your Oracle database must have the following tables:

| Table | Contents |
|-------|----------|
| `FACT_CPI` | CPI and inflation fact data |
| `FACT_BOP` | Balance of Payments fact data |
| `FACT_MONETARY` | Monetary and financial statistics fact data |
| `FACT_FISC` | Fiscal statistics fact data |
| `FACT_INTEREST` | Interest rates fact data |
| `DIM_TIME` | Time dimension |
| `DIM_LOCATION` | Location dimension |
| `DIM_INDICATOR` | Indicator dimension (includes `DESCRIPTION` and `DEFINITION` columns) |
| `DIM_UNITS` | Units dimension |
| `DIM_SOURCES` | Sources dimension |

---

## Uninstall

```bash
pip uninstall economic-indicators-dashboard
```

Then delete the desktop shortcut manually:
- **Windows:** Delete `Economic Dashboard.lnk` from your Desktop
- **Linux:** Delete `~/.local/share/applications/economic-dashboard.desktop`

---

## Requirements

- Python 3.8+
- Oracle database access
- Dependencies installed automatically: `streamlit`, `oracledb`, `pandas`, `plotly`, `openpyxl`, `python-dotenv`

---

## Support

Report issues at: https://github.com/dominicmwitta/data-portal/issues
