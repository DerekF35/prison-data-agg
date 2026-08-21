import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')
dups = df[df.duplicated(['facility_name', 'city', 'state'], keep=False)]
print(dups[['facility_id', 'facility_name', 'city', 'state']])
