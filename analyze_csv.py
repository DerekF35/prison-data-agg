import pandas as pd

df = pd.read_csv('output/us_correctional_facilities_master.csv')

# 1. Check for duplicate facility names at the same city+state
dups = df[df.duplicated(['facility_name', 'city', 'state'], keep=False)]
print(f"Duplicates (name, city, state): {len(dups)}")

# 2. Check for empty street addresses
print(f"Empty street addresses: {df['street_address'].isna().sum()}")

# 3. Anomalous facility names (pure numbers, single-character)
anomalies = df[df['facility_name'].str.len() <= 1 | df['facility_name'].str.isnumeric()]
print(f"Anomalous names: {len(anomalies)}")

# 4. Suspiciously duplicate coordinates (two distinct facilities sharing exact lat/lon)
coord_dups = df[df.duplicated(['latitude', 'longitude'], keep=False) & df['latitude'].notna()]
print(f"Duplicate coordinates (distinct facilities): {len(coord_dups)}")

# 5. Exactly how many facilities have all three populated
all_three = df[df['street_address'].notna() & df['phone_number'].notna() & df['website'].notna()]
print(f"All three populated: {len(all_three)}")

# 6. BOP-only missing GPS
bop_only = df[df['data_source'] == 'Federal Bureau of Prisons (BOP)']
bop_missing_gps = bop_only[bop_only['latitude'].isna()]
print(f"BOP missing GPS: {len(bop_missing_gps)}")

# 7. Zero-population records
zero_pop = df[df['population'] == 0]
print(f"Zero population: {len(zero_pop)}")

