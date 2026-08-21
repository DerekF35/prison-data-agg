import pandas as pd

df = pd.read_csv('output/us_correctional_facilities_master.csv')

# Check Los Angeles facilities and their website
la = df[df['facility_name'].str.contains('Los Angeles', case=False, na=False)]
for _, row in la.iterrows():
    if 'bop.gov' in str(row['website']):
        print(f"LA facility with BOP URL: {row['facility_name']} - {row['facility_type']} - {row['jurisdiction']} - {row['website']}")

# Check Beaumont, Atlanta, Miami, Coleman, Florence, Butner intra-federal complexes
print("\nFederal complex checks:")
complexes = ['Beaumont', 'Atlanta', 'Miami', 'Coleman', 'Florence', 'Butner']
for c in complexes:
    c_df = df[(df['facility_name'].str.contains(c, case=False, na=False)) & (df['jurisdiction'] == 'Federal')]
    for _, row in c_df.iterrows():
        print(f"Complex {c}: {row['facility_name']} - {row['website']}")
