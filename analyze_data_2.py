import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')

print("Duplicate names at same city+state:")
dups = df[df.duplicated(subset=['facility_name', 'city', 'state'], keep=False)]
print(dups[['facility_name', 'city', 'state', 'facility_id']])

print("\nEmpty street addresses:")
empty_addr = df[df['street_address'].isna() | (df['street_address'] == '')]
print(empty_addr[['facility_name', 'city', 'state', 'street_address']])

print("\nDuplicate coordinates count:")
dup_coords = df[df.duplicated(subset=['latitude', 'longitude'], keep=False)]
print(dup_coords[['facility_name', 'latitude', 'longitude']])
