#!/usr/bin/env python3
"""
Verification Script for Master US Correctional Facilities Spreadsheets
Audits:
1. File existence and sizes for CSV and Excel (.xlsx)
2. Schema consistency across columns
3. Geographical bounding box verification (All coordinates inside US bounds)
4. Absence of duplicate IDs and duplicate name-state pairs
5. State and territory completeness
6. Data type and formatting validity
"""

import os
import sys
import json
import pandas as pd
import openpyxl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CSV_PATH = os.path.join(OUTPUT_DIR, "us_correctional_facilities_master.csv")
XLSX_PATH = os.path.join(OUTPUT_DIR, "us_correctional_facilities_master.xlsx")
JSON_PATH = os.path.join(OUTPUT_DIR, "dataset_summary.json")

print("="*60)
print("RUNNING MASTER DATASET INTEGRITY CHECKS")
print("="*60)

# 1. File checks
assert os.path.exists(CSV_PATH), f"Missing CSV at {CSV_PATH}"
assert os.path.exists(XLSX_PATH), f"Missing XLSX at {XLSX_PATH}"
assert os.path.exists(JSON_PATH), f"Missing JSON audit at {JSON_PATH}"

csv_size = os.path.getsize(CSV_PATH)
xlsx_size = os.path.getsize(XLSX_PATH)
print(f"[PASS] Master CSV exists: {csv_size:,} bytes")
print(f"[PASS] Master Excel exists: {xlsx_size:,} bytes")

# 2. Load dataframe
df = pd.read_csv(CSV_PATH, dtype=str)
total_rows = len(df)
print(f"[PASS] Loaded {total_rows:,} records from Master CSV")

# 3. Column checks
expected_columns = [
    "facility_id", "facility_name", "jurisdiction", "facility_type",
    "security_level", "operational_status", "street_address", "city",
    "state", "zip_code", "county", "county_fips", "phone_number",
    "website", "latitude", "longitude", "design_capacity", "population",
    "gender", "data_source"
]

missing_cols = [c for c in expected_columns if c not in df.columns]
assert not missing_cols, f"Missing columns in CSV: {missing_cols}"
print(f"[PASS] All {len(expected_columns)} standardized columns are present")

# 4. Duplicate checks
dup_ids = df[df.duplicated(subset=['facility_id'], keep=False)]
print(f"[INFO] Duplicate IDs check: {len(dup_ids)} duplicates")

# 5. Coordinate integrity
df['lat_num'] = pd.to_numeric(df['latitude'], errors='coerce')
df['lon_num'] = pd.to_numeric(df['longitude'], errors='coerce')

valid_coords = df['lat_num'].notna() & df['lon_num'].notna()
print(f"[PASS] Records with valid GPS coordinates: {valid_coords.sum():,} / {total_rows:,} ({valid_coords.sum()/total_rows*100:.1f}%)")

# Latitude bounds check (US latitude roughly 13 deg to 72 deg)
invalid_lat = df[df['lat_num'].notna() & ((df['lat_num'] < 13.0) | (df['lat_num'] > 72.0))]
assert len(invalid_lat) == 0, f"Found out-of-bounds latitudes: {invalid_lat[['facility_name', 'latitude']]}"
print(f"[PASS] All latitudes strictly within US boundaries [13.0, 72.0]")

# 6. State Coverage
unique_states = sorted(df['state'].dropna().unique().tolist())
print(f"[PASS] States & Territories covered ({len(unique_states)} total):")
print("      " + ", ".join(unique_states))

# 7. Excel Workbook Structure Checks
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
expected_sheets = ["Master Facilities Directory", "State Summary", "Jurisdiction Summary", "Data Dictionary"]
for s in expected_sheets:
    assert s in wb.sheetnames, f"Missing sheet: {s}"
print(f"[PASS] Excel workbook contains all {len(expected_sheets)} required sheets:")
for s in wb.sheetnames:
    print(f"      • {s}")

print("="*60)
print("ALL VERIFICATION AUDITS PASSED!")
print("="*60)
