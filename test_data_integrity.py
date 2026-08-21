import pandas as pd
df = pd.read_csv("output/us_correctional_facilities_master.csv", dtype=str)
print("Empty street addresses:", df['street_address'].isna().sum() + (df['street_address'] == '').sum())
print("All three contact fields:", ((df['street_address'].notna() & (df['street_address'] != '')) & (df['phone_number'].notna() & (df['phone_number'] != '')) & (df['website'].notna() & (df['website'] != ''))).sum())
df['pop'] = pd.to_numeric(df['population'])
df['cap'] = pd.to_numeric(df['design_capacity'])
print("Pop > 3x cap:", (df['pop'] > 3 * df['cap']).sum())
bop = df[df['data_source'] == 'Federal Bureau of Prisons (BOP)']
print("BOP missing coords:", bop['latitude'].isna().sum())
print("ZIP losing leading zeros:", df['zip_code'].str.len().min())
print("FIPS losing leading zeros:", df['county_fips'].str.len().min())
