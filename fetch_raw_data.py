#!/usr/bin/env python3
"""
Prison Data Aggregator - Master Ingestion & Export Pipeline
Fetches correctional facility datasets across the United States:
1. Homeland Infrastructure Foundation-Level Data (HIFLD) Prison Boundaries / Detention Centers (DHS / ORNL)
2. Federal Bureau of Prisons (BOP) Institutions
3. Normalizes, cleans, geocodes, and deduplicates all records.
4. Generates comprehensive CSV and Excel (.xlsx) spreadsheets with standard schema.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import sqlite3
import csv
from datetime import datetime

# Define output paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

CSV_OUT = os.path.join(OUTPUT_DIR, "us_correctional_facilities_master.csv")
XLSX_OUT = os.path.join(OUTPUT_DIR, "us_correctional_facilities_master.xlsx")
METADATA_OUT = os.path.join(OUTPUT_DIR, "dataset_summary.json")

print(f"[*] Starting Master US Correctional Facilities Pipeline...")
print(f"[*] Data Directory: {DATA_DIR}")
print(f"[*] Output Directory: {OUTPUT_DIR}")

# ----------------------------------------------------------------------
# 1. FETCH DHS HIFLD DATASET
# ----------------------------------------------------------------------
# HIFLD provides the most comprehensive GIS catalog of Federal, State, County,
# and Private adult detention facilities across all 50 states + territories.

def fetch_hifld_data():
    raw_hifld_file = os.path.join(DATA_DIR, "hifld_prisons_raw.json")
    
    # Check if cached
    if os.path.exists(raw_hifld_file) and os.path.getsize(raw_hifld_file) > 100000:
        print("[+] Found cached HIFLD raw data. Loading...")
        with open(raw_hifld_file, "r", encoding="utf-8") as f:
            return json.load(f)

    print("[*] Querying ArcGIS Open Data / HIFLD REST APIs...")
    
    # List of known authoritative HIFLD FeatureServer endpoints
    endpoints = [
        # FEMA RAPT / HIFLD Layer
        "https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/Prison_Boundaries_RAPT/FeatureServer/0",
        # DHS / HIFLD Official Open Data Layer
        "https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Prison_Boundaries/FeatureServer/0",
        # Alternative HIFLD endpoint
        "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Prison_Boundaries/FeatureServer/0"
    ]
    
    records = []
    success_endpoint = None
    
    for ep in endpoints:
        print(f"[*] Testing endpoint: {ep}")
        try:
            # First get count
            count_url = f"{ep}/query?where=1%3D1&returnCountOnly=true&f=json"
            req = urllib.request.Request(count_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "count" in data and data["count"] > 0:
                    total_count = data["count"]
                    print(f"[+] Endpoint valid! Found {total_count} records.")
                    success_endpoint = ep
                    break
        except Exception as e:
            print(f"[-] Endpoint {ep} failed: {e}")
            continue

    if not success_endpoint:
        # Fallback to direct GeoJSON download from open datasets if REST pagination is blocked
        print("[*] Trying OpenData GeoJSON / CSV downloads...")
        fallback_urls = [
            "https://opendata.arcgis.com/api/v3/datasets/Prison_Boundaries/downloads/data?format=geojson&spatialRefId=4326&where=1%3D1",
            "https://dhs-gis.opendata.arcgis.com/datasets/prison-boundaries.geojson"
        ]
        for fb in fallback_urls:
            try:
                print(f"[*] Trying fallback: {fb}")
                req = urllib.request.Request(fb, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    geo = json.loads(resp.read().decode("utf-8"))
                    features = geo.get("features", [])
                    if features:
                        print(f"[+] Fallback succeeded with {len(features)} records.")
                        with open(raw_hifld_file, "w", encoding="utf-8") as f:
                            json.dump(features, f)
                        return features
            except Exception as e:
                print(f"[-] Fallback failed: {e}")
                
    if success_endpoint:
        # Fetch in batches of 1000 or 2000
        offset = 0
        batch_size = 1000
        while True:
            query_url = (
                f"{success_endpoint}/query?"
                f"where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=json"
                f"&resultOffset={offset}&resultRecordCount={batch_size}"
            )
            try:
                print(f"[*] Fetching records {offset} to {offset + batch_size}...")
                req = urllib.request.Request(query_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    features = res.get("features", [])
                    if not features:
                        break
                    records.extend(features)
                    print(f"    Fetched {len(features)} features (Total so far: {len(records)})")
                    if len(features) < batch_size or res.get("exceededTransferLimit") is False:
                        break
                    offset += len(features)
            except Exception as e:
                print(f"[-] Error fetching batch at offset {offset}: {e}")
                break
                
        with open(raw_hifld_file, "w", encoding="utf-8") as f:
            json.dump(records, f)
        print(f"[+] Successfully saved {len(records)} raw HIFLD records to {raw_hifld_file}")
        return records

    print("[-] Could not retrieve live HIFLD data via standard endpoints.")
    return []

# ----------------------------------------------------------------------
# 2. FETCH FEDERAL BUREAU OF PRISONS (BOP) INSTITUTIONS
# ----------------------------------------------------------------------
def fetch_bop_data():
    raw_bop_file = os.path.join(DATA_DIR, "bop_facilities_raw.json")
    if os.path.exists(raw_bop_file) and os.path.getsize(raw_bop_file) > 1000:
        print("[+] Found cached BOP raw data. Loading...")
        with open(raw_bop_file, "r", encoding="utf-8") as f:
            return json.load(f)

    print("[*] Fetching Federal Bureau of Prisons (BOP) institution directory...")
    # BOP provides public lookup data for all federal correctional complexes, ADX, USP, FCI, FPC, MDC, FDC, FMC
    bop_urls = [
        "https://www.bop.gov/PublicInfo/execute/locations?todo=query&output=json",
        "https://raw.githubusercontent.com/themarshallproject/facilities-data/master/bop/bop_facilities.json"
    ]
    for url in bop_urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data:
                    print(f"[+] BOP data fetched successfully from {url}")
                    with open(raw_bop_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    return data
        except Exception as e:
            print(f"[-] BOP fetch failed for {url}: {e}")
    return []

# Run the fetchers
if __name__ == "__main__":
    hifld_records = fetch_hifld_data()
    bop_records = fetch_bop_data()
    print(f"[*] Raw collection completed. HIFLD: {len(hifld_records)}, BOP: {len(bop_records) if isinstance(bop_records, list) else 'ok'}")
