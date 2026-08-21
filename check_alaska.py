import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')
pos_lon = df[df['longitude'] > 0]
print(f"Positive longitudes: {len(pos_lon)}")
if not pos_lon.empty:
    print(pos_lon[['facility_name', 'longitude']])
