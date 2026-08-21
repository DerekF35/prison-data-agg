import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv', dtype=str)

df['cap'] = pd.to_numeric(df['design_capacity'], errors='coerce')
df['pop'] = pd.to_numeric(df['population'], errors='coerce')

overpop = df[(df['pop'] > 3 * df['cap']) & (df['cap'] > 0)]
print(f"Population > 3x capacity: {len(overpop)}")

complete_info = df[df['street_address'].notna() & (df['street_address'] != '') & 
                   df['phone_number'].notna() & (df['phone_number'] != '') & 
                   df['website'].notna() & (df['website'] != '')]
print(f"All 3 populated (street, phone, website): {len(complete_info)}")

