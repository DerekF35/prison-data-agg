import pandas as pd
df = pd.read_csv('output/us_correctional_facilities_master.csv')
anomalous_pop = df[(df['population'].notna()) & (df['design_capacity'].notna()) & (pd.to_numeric(df['population'], errors='coerce') > 3 * pd.to_numeric(df['design_capacity'], errors='coerce'))]
print(f"Population > 3x Capacity: {len(anomalous_pop)}")
if not anomalous_pop.empty:
    print(anomalous_pop[['facility_name', 'population', 'design_capacity']])
