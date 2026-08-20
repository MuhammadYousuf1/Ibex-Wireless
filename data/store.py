from pathlib import Path

import pandas as pd

from data.sample_data import normalize_rebate_dataframe


# Load the real workbook once and reuse it across every dashboard page.
# `sample_data.xlsx` is preferred when supplied; the existing workbook remains
# a fallback for this project.
DATA_DIR = Path(__file__).parent
WORKBOOK_PATH = next(
    (path for path in (DATA_DIR / 'sample_data.xlsx', DATA_DIR / 'spiff_rebates.xlsx') if path.exists()),
    None,
)
if WORKBOOK_PATH is None:
    raise FileNotFoundError('Add sample_data.xlsx to the data folder.')

# --- Sheet 1: Spiffs-Rebates ---
RAW_DF = pd.read_excel(WORKBOOK_PATH, sheet_name='Spiffs-Rebates')
# The workbook ends with a pre-calculated totals row.  It has no transaction
# date, so leaving it in the dataset causes every numeric KPI to be counted
# twice when the dashboard calculates its own totals.
if 'Date' in RAW_DF.columns:
    RAW_DF = RAW_DF.loc[RAW_DF['Date'].notna()].copy()
SOURCE_COLUMNS = RAW_DF.columns.tolist()
DF = normalize_rebate_dataframe(RAW_DF)

# --- Sheet 2: Accessory ---
ACCESSORY_DF = pd.read_excel(WORKBOOK_PATH, sheet_name='Accessory')

# Drop rows where Qty is 0 or missing (no actual sale)
if 'Qty' in ACCESSORY_DF.columns:
    ACCESSORY_DF = ACCESSORY_DF.loc[pd.to_numeric(ACCESSORY_DF['Qty'], errors='coerce').fillna(0) != 0].copy()
ACCESSORY_DF = ACCESSORY_DF.reset_index(drop=True)
ACCESSORY_COLUMNS = ACCESSORY_DF.columns.tolist()
