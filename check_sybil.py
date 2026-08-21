import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')
sybil = df[df['facility_name'].str.contains('Sybil', case=False, na=False)]
for _, row in sybil.iterrows():
    print(row['facility_name'], "-", row['website'])
