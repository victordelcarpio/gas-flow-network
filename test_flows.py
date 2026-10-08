import pandas as pd

pipe = pd.read_csv('report_pipeflow.csv')
lng = pd.read_csv('report_lngflow.csv')

# look at available ITEM categories for sanity
print('pipe ITEMs:', pipe['ITEM'].unique() if 'ITEM' in pipe.columns else 'no ITEM')
print('lng ITEMs:', lng['ITEM'].unique() if 'ITEM' in lng.columns else 'no ITEM')

# drop any rows that aren't the correct flow variable
if 'ITEM' in pipe.columns:
    pipe = pipe[
        pipe['ITEM'].astype(str).str.contains('flow', case=False, na=False)
        & ~pipe['ITEM'].astype(str).str.contains('gross', case=False, na=False)
    ]

if 'ITEM' in lng.columns:
    lng = lng[
        lng['ITEM'].astype(str).str.contains('flow', case=False, na=False)
        & lng['ITEM'].astype(str).str.contains('gross', case=False, na=False)
    ]

us_regions = {
    'New England', 'Mid-Atlantic', 'South Atlantic', 'East North Central',
    'East South Central', 'West South Central', 'West North Central', 'Mountain', 'Pacific', 'Texas'
}

def standardize_country_name(name):
    if name in us_regions:
        return 'US'
    if '(' in name and ')' in name:
        name = name.split('(')[0].strip()
    return name

# Apply standardization
pipe['COUNTRY_FROM'] = pipe['COUNTRY_FROM'].apply(standardize_country_name)
pipe['COUNTRY_TO'] = pipe['COUNTRY_TO'].apply(standardize_country_name)
lng['COUNTRY_FROM'] = lng['COUNTRY_FROM'].apply(standardize_country_name)
lng['COUNTRY_TO'] = lng['COUNTRY_TO'].apply(standardize_country_name)

# Get 2030 flows
flows_year = pd.concat([
    pipe[pipe.YEAR == 2030],
    lng[lng.YEAR == 2030]
])

# Aggregate by country pair
flows_year = flows_year.groupby(['COUNTRY_FROM','COUNTRY_TO'], as_index=False)['VALUE'].sum()

# Find US-Mexico flows
us_mx = flows_year[
    ((flows_year['COUNTRY_FROM']=='US') & (flows_year['COUNTRY_TO']=='Mexico')) |
    ((flows_year['COUNTRY_FROM']=='Mexico') & (flows_year['COUNTRY_TO']=='US'))
]

print("US-Mexico flows (2030):")
print(us_mx)
print(f"\nUS -> Mexico: {us_mx[(us_mx['COUNTRY_FROM']=='US') & (us_mx['COUNTRY_TO']=='Mexico')]['VALUE'].sum():.2f} bcm")
print(f"Mexico -> US: {us_mx[(us_mx['COUNTRY_FROM']=='Mexico') & (us_mx['COUNTRY_TO']=='US')]['VALUE'].sum():.2f} bcm")
