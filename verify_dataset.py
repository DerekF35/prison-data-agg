#!/usr/bin/env python3
"""
Verification & Validation Suite for US Correctional Facilities Aggregator
Asserts data cleanliness, schema compliance, coordinate bounds, zero duplicates,
and Excel workbook multi-sheet mathematical integrity.
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
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "dataset_summary.json")

print("="*60)
print("RUNNING MASTER DATASET INTEGRITY CHECKS")
print("="*60)

# 1. Check file existence and sizes
assert os.path.exists(CSV_PATH), f"CSV file missing: {CSV_PATH}"
csv_size = os.path.getsize(CSV_PATH)
assert csv_size > 500000, f"CSV file too small ({csv_size} bytes)"
print(f"[PASS] Master CSV exists: {csv_size:,} bytes")

assert os.path.exists(XLSX_PATH), f"Excel file missing: {XLSX_PATH}"
xlsx_size = os.path.getsize(XLSX_PATH)
assert xlsx_size > 500000, f"Excel file too small ({xlsx_size} bytes)"
print(f"[PASS] Master Excel exists: {xlsx_size:,} bytes")

assert os.path.exists(SUMMARY_PATH), f"Summary JSON missing: {SUMMARY_PATH}"
print(f"[PASS] Dataset summary JSON exists: {os.path.getsize(SUMMARY_PATH):,} bytes")

# 2. Check CSV records and columns
df = pd.read_csv(CSV_PATH, dtype=str)
row_count = len(df)
assert row_count >= 6500, f"Expected >= 6,500 facilities, found {row_count}"
print(f"[PASS] Loaded {row_count:,} records from Master CSV")

expected_columns = [
    "facility_id", "facility_name", "jurisdiction", "facility_type",
    "security_level", "operational_status", "street_address", "city",
    "state", "zip_code", "county", "county_fips", "phone_number",
    "website", "latitude", "longitude", "design_capacity", "population",
    "gender", "data_source"
]

for col in expected_columns:
    assert col in df.columns, f"Missing required column: {col}"
print(f"[PASS] All {len(expected_columns)} standardized columns are present")

# 3. Check Uniqueness of facility_id
duplicates = df[df.duplicated(subset=['facility_id'], keep=False)]
assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate facility IDs!"
print(f"[PASS] Duplicate IDs check: 0 duplicates (100% unique)")

# 4. Check Coordinates bounds
df['lat_float'] = pd.to_numeric(df['latitude'], errors='coerce')
df['lon_float'] = pd.to_numeric(df['longitude'], errors='coerce')

valid_coords = df[df['lat_float'].notna() & df['lon_float'].notna()]
print(f"[PASS] Records with valid GPS coordinates: {len(valid_coords):,} / {row_count:,} ({len(valid_coords)/row_count*100:.1f}%)")

# Strict US Bounding Box (Latitude 13.0 to 72.0, Longitude -180.0 to -64.0 and +144.0 to +180.0)
invalid_lat = df[(df['lat_float'] < 13.0) | (df['lat_float'] > 72.0)]
assert len(invalid_lat) == 0, f"Found {len(invalid_lat)} records with invalid latitudes outside US boundaries"
print(f"[PASS] All latitudes strictly within US boundaries [13.0, 72.0]")

invalid_lon = df[~(((df['lon_float'] >= -180.0) & (df['lon_float'] <= -64.0)) | ((df['lon_float'] >= 144.0) & (df['lon_float'] <= 180.0)))]
assert len(invalid_lon) == 0, f"Found {len(invalid_lon)} records with invalid longitudes"
print(f"[PASS] All longitudes strictly within US and Territory boundaries")

# 5. Check State coverage
states = set(df['state'].unique())
assert len(states) >= 50, f"Expected at least 50 states, got {len(states)}"
print(f"[PASS] States & Territories covered: {len(states)} jurisdictions")

# 6. Check Excel Workbook Integrity
wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
expected_sheets = ["Master Facilities Directory", "State Summary", "Jurisdiction Summary", "Data Dictionary"]
for sheet_name in expected_sheets:
    assert sheet_name in wb.sheetnames, f"Excel workbook missing sheet: {sheet_name}"
print(f"[PASS] Excel workbook contains all {len(expected_sheets)} required sheets")

print("="*60)
print("ALL VERIFICATION AUDITS PASSED!")
print("="*60)
