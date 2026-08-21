#!/usr/bin/env python3
"""
export_raw_excel.py

Converts raw JSON datasets in the data/ folder directly into Excel (.xlsx) files
in the output/raw/ folder. This process applies NO data cleaning, filtering, or 
deduplication. It simply flattens nested JSON structures (e.g., HIFLD geometries 
and BOP location arrays) so they can be viewed natively in Excel.
"""

import os
import json
import pandas as pd

DATA_DIR = "data"
OUT_DIR = "output/raw"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"[*] Starting Raw JSON to Excel export...")
    
    for filename in sorted(os.listdir(DATA_DIR)):
        if not filename.endswith(".json"):
            continue
            
        in_path = os.path.join(DATA_DIR, filename)
        out_name = filename.replace(".json", ".xlsx")
        out_path = os.path.join(OUT_DIR, out_name)
        
        print(f"[*] Processing {filename}...")
        
        with open(in_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        records = []
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict) and "attributes" in data[0]:
                # HIFLD format: extract 'attributes' and flatten 'geometry'
                for item in data:
                    rec = item.get("attributes", {}).copy()
                    geom = item.get("geometry", {})
                    if geom:
                        rec["geometry_x"] = geom.get("x")
                        rec["geometry_y"] = geom.get("y")
                    records.append(rec)
            else:
                records = data
        elif isinstance(data, dict):
            if "Locations" in data:
                # BOP format
                records = data["Locations"]
            else:
                records = [data]
                
        df = pd.json_normalize(records)
        
        print(f"    - Converting {len(df)} rows to Excel...")
        
        # Convert to string to avoid complex types causing ExcelWriter errors
        try:
            with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
        except Exception as e:
            print(f"    ! Error writing native types: {e}. Falling back to string conversion...")
            df = df.astype(str)
            with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
                
        print(f"    - Saved: {out_path}")

    print("[+] Done! All raw datasets have been exported to output/raw/")

if __name__ == "__main__":
    main()
