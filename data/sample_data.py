import pandas as pd
import numpy as np

# ==========================================
# 1. COLUMN NAME DEFINITIONS (YOUR EXACT COLUMNS)
# ==========================================
# Date Columns
COL_RAW_DATE_A = 'Date'
COL_RAW_DATE_B = 'Months (Date)'

# Raw Text & Identification Columns
COL_RAW_STORE = 'Store'
COL_RAW_SUB_TYPE = 'Sub Type'
COL_RAW_SKU = 'SKU'
COL_RAW_IMEI = 'IMEI'
COL_RAW_INVOICE_VERIF = 'Invoice Verification'

# Financial & Comm Columns (including exact whitespace)
COL_RAW_VIDAPAY_SPIFF = 'VidaPaySpiff'
COL_RAW_EXP_COMM = 'Exp Comm'
COL_RAW_COMM_RECEIVED = 'Comm Received'
COL_RAW_DEVICE_REBATE = 'Device Rebate'

# Other Custom Workbook Columns
COL_RAW_ACT_ORDER_NUM = 'Activation Order Number'
COL_RAW_VARIANCE = 'Variance'
COL_RAW_FINAL_VARIANCE = 'Final Variance'
COL_RAW_COMMENTS_A = 'Comments'
COL_RAW_FEES_MARGIN = 'Fees Mrgin'
COL_RAW_DEVICE_MARGIN = 'Device Mrgin'
COL_RAW_COMMENTS_B = 'Comments.1'  # Pandas auto-renames duplicate "Comments" columns

# Normalized Target Columns (Dashboard Standard)
COL_NORM_DATE = 'Date'
COL_NORM_REGION = 'Region'
COL_NORM_PRODUCT = 'Product'
COL_NORM_CATEGORY = 'Category'
COL_NORM_SALES = 'Sales'
COL_NORM_QTY = 'Quantity'
COL_NORM_COMM = 'Comm_Received'
COL_NORM_SATISFACTION = 'Customer_Satisfaction'


# ==========================================
# 2. CONFIGURATION & SCHEMA DEFINITIONS
# ==========================================
COLUMN_MAPPINGS = {
    COL_NORM_REGION: [COL_RAW_STORE],
    COL_NORM_PRODUCT: [COL_RAW_SKU],
    COL_NORM_CATEGORY: [COL_RAW_SUB_TYPE],
    COL_NORM_SALES: [COL_RAW_COMM_RECEIVED, COL_RAW_VIDAPAY_SPIFF, COL_RAW_DEVICE_REBATE, COL_RAW_EXP_COMM]
}

DEFAULT_VALUES = {
    COL_NORM_REGION: 'Unknown',
    COL_NORM_PRODUCT: 'Unknown',
    COL_NORM_CATEGORY: '',
    COL_NORM_SALES: 0.0,
    COL_NORM_COMM: 0.0,
    COL_NORM_QTY: 1,
    COL_NORM_SATISFACTION: 3
}

NORMALIZED_COLUMNS = [
    COL_NORM_DATE, 
    COL_NORM_REGION, 
    COL_NORM_PRODUCT, 
    COL_NORM_CATEGORY, 
    COL_NORM_SALES, 
    COL_NORM_QTY, 
    COL_NORM_COMM, 
    COL_NORM_SATISFACTION
]


# ==========================================
# 3. DISPLAY HELPERS (shared across pages)
# ==========================================

def _is_currency_column(column_name):
    """Return True for columns that should be displayed as currency."""
    if not column_name:
        return False

    currency_columns = {
        COL_RAW_VIDAPAY_SPIFF,
        COL_RAW_EXP_COMM,
        COL_RAW_COMM_RECEIVED,
        COL_RAW_DEVICE_REBATE,
        COL_RAW_VARIANCE,
        COL_RAW_FINAL_VARIANCE,
        COL_RAW_FEES_MARGIN,
        COL_RAW_DEVICE_MARGIN,
    }
    normalized = str(column_name).lower()
    currency_keywords = ('margin', 'rebate', 'comm', 'variance', 'fee', 'amount', 'price', 'cost', 'total', 'sales')
    return column_name in currency_columns or any(keyword in normalized for keyword in currency_keywords)


def _format_table_value(value, column_name=None):
    """Format a single cell value for display in dash tables."""
    if pd.isna(value):
        return ''
    if column_name in (COL_RAW_IMEI, COL_RAW_ACT_ORDER_NUM):
        try:
            return f"{int(float(value))}"
        except (ValueError, TypeError):
            return str(value).split('.')[0]
    if isinstance(value, pd.Timestamp):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, (int, float)):
        if _is_currency_column(column_name):
            return f"${float(value):,.2f}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return f"{value:,.0f}"
    return str(value)


def _format_total_value(series, column_name=None):
    """Return a footer total for a numeric workbook column, or a unique-count for identifier fields."""
    if column_name in {COL_RAW_IMEI, COL_RAW_ACT_ORDER_NUM}:
        cleaned_values = pd.Series(series).dropna().astype(str).str.strip()
        non_empty = cleaned_values[cleaned_values != '']
        if non_empty.empty:
            return ''
        return f"{non_empty.nunique():,}"

    numeric_values = pd.to_numeric(series, errors='coerce')
    if not numeric_values.notna().any():
        return ''
    total = numeric_values.sum()
    if _is_currency_column(column_name):
        return f"${total:,.2f}"
    return f"{total:,.2f}" if (numeric_values % 1 != 0).any() else f"{total:,.0f}"


def _build_display_table(df: pd.DataFrame, columns: list[str], sort_by: str | None = None, include_total_row: bool = True):
    """Create a formatted display table and optionally append a totals row."""
    display_columns = [column for column in columns if column in df.columns]
    display_df = df.loc[:, display_columns].copy()

    if sort_by and sort_by in display_df.columns:
        display_df = display_df.sort_values(by=sort_by, ascending=False)

    for column in display_columns:
        display_df[column] = display_df[column].map(lambda value: _format_table_value(value, column))

    if include_total_row and display_columns:
        total_row = {column: '' for column in display_columns}
        total_row[display_columns[0]] = 'Total'
        for column in display_columns:
            total_value = _format_total_value(df[column], column_name=column)
            if total_value:
                total_row[column] = total_value
        display_df = pd.concat([display_df, pd.DataFrame([total_row])], ignore_index=True)

    return display_columns, display_df


# ==========================================
# 4. HELPER CALCULATION & CLEANING FUNCTIONS
# ==========================================
def _clean_text_series(series: pd.Series, default_val: str = '') -> pd.Series:
    """Cleans text data by handling nulls, stripping spaces, and replacing bad strings."""
    return (
        series.fillna(default_val)
        .astype(str)
        .str.strip()
        .replace({'nan': default_val, 'None': default_val, '': default_val})
    )


def _clean_imei_series(series: pd.Series) -> pd.Series:
    """Specifically handles IMEI numeric-to-string formatting without regex overhead."""
    numeric_series = pd.to_numeric(series, errors='coerce')
    return (
        numeric_series.dropna()
        .astype(np.int64)
        .astype(str)
        .reindex(series.index, fill_value='')
    )


def _calculate_satisfaction_vectorized(series: pd.Series) -> pd.Series:
    """Vectorized calculation of satisfaction score using numpy.select."""
    clean_series = series.astype(str).str.strip().str.lower()
    
    conditions = [
        clean_series.str.contains('verified', na=False),
        clean_series.str.contains('received', na=False),
        clean_series.str.contains('missing|reject', na=False)
    ]
    choices = [5, 4, 2]
    
    return pd.Series(
        np.select(conditions, choices, default=DEFAULT_VALUES[COL_NORM_SATISFACTION]),
        index=series.index
    )


def _find_matching_column(df: pd.DataFrame, fallback_list: list[str]) -> str | None:
    """Finds the first column in the DataFrame that matches the fallback list."""
    return next((col for col in fallback_list if col in df.columns), None)


# ==========================================
# 4. DATAFRAME NORMALIZATION PIPELINE
# ==========================================
def normalize_rebate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Step 1: Date Parsing & Sorting ---
    if COL_RAW_DATE_A in df.columns:
        df[COL_NORM_DATE] = pd.to_datetime(df[COL_RAW_DATE_A], errors='coerce')
    elif COL_RAW_DATE_B in df.columns:
        df[COL_NORM_DATE] = pd.to_datetime(df[COL_RAW_DATE_B], errors='coerce')
    else:
        df[COL_NORM_DATE] = pd.date_range(start='2024-01-01', periods=len(df), freq='W')

    df[COL_NORM_DATE] = df[COL_NORM_DATE].fillna(pd.NaT)
    df = df.sort_values(by=COL_NORM_DATE, ascending=True).reset_index(drop=True)

    # --- Step 2: Clean IMEI ---
    if COL_RAW_IMEI in df.columns:
        df[COL_RAW_IMEI] = _clean_imei_series(df[COL_RAW_IMEI])

    # --- Step 3: Map Dynamic Columns & Calculate Values ---
    region_col = _find_matching_column(df, COLUMN_MAPPINGS[COL_NORM_REGION])
    product_col = _find_matching_column(df, COLUMN_MAPPINGS[COL_NORM_PRODUCT])
    category_col = _find_matching_column(df, COLUMN_MAPPINGS[COL_NORM_CATEGORY])
    sales_col = _find_matching_column(df, COLUMN_MAPPINGS[COL_NORM_SALES])

    df[COL_NORM_REGION] = _clean_text_series(df[region_col], DEFAULT_VALUES[COL_NORM_REGION]) if region_col else DEFAULT_VALUES[COL_NORM_REGION]
    df[COL_NORM_PRODUCT] = _clean_text_series(df[product_col], DEFAULT_VALUES[COL_NORM_PRODUCT]) if product_col else DEFAULT_VALUES[COL_NORM_PRODUCT]
    df[COL_NORM_CATEGORY] = _clean_text_series(df[category_col], DEFAULT_VALUES[COL_NORM_CATEGORY]) if category_col else DEFAULT_VALUES[COL_NORM_CATEGORY]

    # Map Comm Received explicitly if it exists
    if COL_RAW_COMM_RECEIVED in df.columns:
        df[COL_NORM_COMM] = pd.to_numeric(df[COL_RAW_COMM_RECEIVED], errors='coerce').fillna(DEFAULT_VALUES[COL_NORM_COMM])
    else:
        df[COL_NORM_COMM] = DEFAULT_VALUES[COL_NORM_COMM]

    if sales_col:
        df[COL_NORM_SALES] = pd.to_numeric(df[sales_col], errors='coerce').fillna(DEFAULT_VALUES[COL_NORM_SALES])
    else:
        df[COL_NORM_SALES] = DEFAULT_VALUES[COL_NORM_SALES]

    # Quantity isn't explicitly in your source columns; fallback to default
    if COL_NORM_QTY in df.columns:
        df[COL_NORM_QTY] = pd.to_numeric(df[COL_NORM_QTY], errors='coerce').fillna(DEFAULT_VALUES[COL_NORM_QTY])
    else:
        df[COL_NORM_QTY] = DEFAULT_VALUES[COL_NORM_QTY]

    # --- Step 4: Satisfaction Score Logic (Vectorized) ---
    if COL_NORM_SATISFACTION not in df.columns:
        if COL_RAW_INVOICE_VERIF in df.columns:
            df[COL_NORM_SATISFACTION] = _calculate_satisfaction_vectorized(df[COL_RAW_INVOICE_VERIF])
        else:
            df[COL_NORM_SATISFACTION] = DEFAULT_VALUES[COL_NORM_SATISFACTION]

    # --- Step 5: Presentation & Formatting ---
    df[COL_NORM_DATE] = df[COL_NORM_DATE].dt.strftime('%m-%d-%Y').fillna('')

    other_cols = [col for col in df.columns if col not in NORMALIZED_COLUMNS]
    return df[NORMALIZED_COLUMNS + other_cols]


# ==========================================
# 5. KPI METRICS (COLUMN-SPECIFIC TOTALS)
# ==========================================
def calculate_raw_kpis(df: pd.DataFrame) -> dict[str, float]:
    """Isolates raw sum totals and averages."""
    sales_source = df.get(COL_RAW_COMM_RECEIVED, df.get(COL_NORM_SALES))
    return {
        'sales': pd.to_numeric(sales_source, errors='coerce').sum() or 0.0,
        'quantity': pd.to_numeric(df.get(COL_NORM_QTY), errors='coerce').sum() or 0.0,
        'commission': pd.to_numeric(df.get(COL_NORM_COMM), errors='coerce').sum() or 0.0,
        'satisfaction_sum': pd.to_numeric(df.get(COL_NORM_SATISFACTION), errors='coerce').sum() or 0.0,
        'satisfaction_avg': pd.to_numeric(df.get(COL_NORM_SATISFACTION), errors='coerce').mean() or 0.0,
        'orders': len(df)
    }


def get_kpi_metrics(df: pd.DataFrame) -> dict[str, str]:
    """Formats column-specific metrics into clean presentation strings."""
    raw = calculate_raw_kpis(df)

    return {
        'Total Sales': f"${raw['sales']:,.2f}",
        'Avg Order Value': f"${raw['sales'] / raw['orders']:,.2f}" if raw['orders'] else '$0.00',
        'Total Quantity': f"{raw['quantity']:,.0f}",
        'Total Commission': f"${raw['commission']:,.2f}",
        'Total Satisfaction': f"{raw['satisfaction_sum']:,.0f}",
        'Avg Satisfaction': f"{raw['satisfaction_avg']:.1f}/5.0",
        'Total Orders': f"{raw['orders']:,}"
    }


# ==========================================
# 6. MEMORY-ONLY SAMPLE DATA GENERATION
# ==========================================
def generate_sample_data() -> pd.DataFrame:
    """Generates synthetic DataFrame using your exact column layout."""
    np.random.seed(42)
    n_rows = 15
    
    data = {
        # COL_RAW_DATE_A: pd.date_range(start='2024-01-01', periods=n_rows, freq='D'),
        # COL_RAW_DATE_B: [None] * n_rows,
        # COL_RAW_STORE: np.random.choice(['Verizon', 'T-Mobile', 'AT&T'], size=n_rows),
        # COL_RAW_SUB_TYPE: np.random.choice(['Smartphone', 'Tablet', 'Accessory'], size=n_rows),
        # COL_RAW_ACT_ORDER_NUM: [f"ACT-{1000 + i}" for i in range(n_rows)],
        # COL_RAW_SKU: np.random.choice(['iPhone 15 Pro', 'Galaxy S24', 'Pixel 8 Pro'], size=n_rows),
        # COL_RAW_IMEI: np.random.choice([8.61021e+14, 3.58291e+14], size=n_rows),
        # COL_RAW_VIDAPAY_SPIFF: np.random.uniform(5.0, 50.0, size=n_rows),
        # COL_RAW_EXP_COMM: np.random.uniform(20.0, 100.0, size=n_rows),
        # COL_RAW_VARIANCE: np.random.uniform(-10.0, 10.0, size=n_rows),
        # COL_RAW_COMM_RECEIVED: np.random.uniform(15.0, 120.0, size=n_rows),
        # COL_RAW_FINAL_VARIANCE: np.random.uniform(-5.0, 5.0, size=n_rows),
        # COL_RAW_INVOICE_VERIF: np.random.choice(['Verified', 'Received', 'Rejected'], size=n_rows),
        # COL_RAW_COMMENTS_A: ['Processed'] * n_rows,
        # COL_RAW_FEES_MARGIN: np.random.uniform(1.0, 5.0, size=n_rows),
        # COL_RAW_DEVICE_REBATE: np.random.uniform(50.0, 200.0, size=n_rows),
        # COL_RAW_DEVICE_MARGIN: np.random.uniform(10.0, 40.0, size=n_rows)
    }
    
    return normalize_rebate_dataframe(pd.DataFrame(data))


# Quick validation check
if __name__ == "__main__":
    df_clean = generate_sample_data()
    print("Your Normalized Workbook DataFrame (First 3 rows):")
    print(df_clean[NORMALIZED_COLUMNS].head(3))
    print("\nNon-Normalized Custom Fields Preserved (First 3 rows):")
    custom_fields = [COL_RAW_ACT_ORDER_NUM, COL_RAW_VARIANCE, COL_RAW_FINAL_VARIANCE]
    print(df_clean[custom_fields].head(3))
    print("\nCalculated Dashboard KPIs:")
    print(get_kpi_metrics(df_clean))
