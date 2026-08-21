import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')
coord_dups = df[df.duplicated(['latitude', 'longitude'], keep=False) & df['latitude'].notna()]
print(coord_dups[['facility_name', 'city', 'state', 'latitude', 'longitude']])
