# Codebook: `data/panel_full.csv`

Metro-by-year panel: 402 metropolitan areas observed in 11 survey years (4,216 rows). The analysis uses the 367 metros observed in all 11 years; the main sample is the 163 of them with at least three Wharton survey responses.

| Variable | Description | Unit | Source | Non-missing |
|---|---|---|---|---|
| `year` | ACS survey year (2013-2024; 2020 not released as standard 1-year data) |  |  | 4,216 |
| `cbsa` | Core-based statistical area code (OMB delineation of the ACS vintage) |  | OMB | 4,216 |
| `name` | Metropolitan area name |  | ACS | 4,216 |
| `B25106_024E` | Renter-occupied units (tenure by income by costs) | count | ACS B25106 | 4,216 |
| `B25106_025E` | Renters, household income < $20,000 | count | ACS B25106 | 4,216 |
| `B25106_028E` | Renters < $20,000 paying 30%+ of income | count | ACS B25106 | 4,216 |
| `B25106_029E` | Renters, $20,000-$34,999 | count | ACS B25106 | 4,216 |
| `B25106_032E` | Renters $20,000-$34,999 paying 30%+ | count | ACS B25106 | 4,216 |
| `B25106_033E` | Renters, $35,000-$49,999 | count | ACS B25106 | 4,216 |
| `B25106_036E` | Renters $35,000-$49,999 paying 30%+ | count | ACS B25106 | 4,216 |
| `B25106_037E` | Renters, $50,000-$74,999 | count | ACS B25106 | 4,216 |
| `B25106_040E` | Renters $50,000-$74,999 paying 30%+ | count | ACS B25106 | 4,216 |
| `B25106_041E` | Renters, $75,000+ | count | ACS B25106 | 4,216 |
| `B25106_044E` | Renters $75,000+ paying 30%+ | count | ACS B25106 | 4,216 |
| `B25106_045E` | Renters, zero or negative income | count | ACS B25106 | 4,216 |
| `B25106_046E` | Renters, no cash rent | count | ACS B25106 | 4,216 |
| `B25070_001E` | Renter households (gross rent as % of income), total | count | ACS B25070 | 4,214 |
| `B25070_007E` | Gross rent 30.0-34.9% of income | count | ACS B25070 | 4,214 |
| `B25070_008E` | Gross rent 35.0-39.9% of income | count | ACS B25070 | 4,214 |
| `B25070_009E` | Gross rent 40.0-49.9% of income | count | ACS B25070 | 4,214 |
| `B25070_010E` | Gross rent 50%+ of income | count | ACS B25070 | 4,214 |
| `B25070_011E` | Gross rent as % of income not computed | count | ACS B25070 | 4,214 |
| `B08301_001E` | Workers 16+ (means of transportation); not used, suppressed for small metros | count | ACS B08301 | 2,707 |
| `B08301_021E` | Workers 16+ who worked from home; not used | count | ACS B08301 | 2,707 |
| `B15003_001E` | Population 25+ | count | ACS B15003 | 4,208 |
| `B15003_022E` | Bachelor's degree | count | ACS B15003 | 4,208 |
| `B15003_023E` | Master's degree | count | ACS B15003 | 4,208 |
| `B15003_024E` | Professional school degree | count | ACS B15003 | 4,208 |
| `B15003_025E` | Doctorate degree | count | ACS B15003 | 4,208 |
| `B25064_001E` | Median gross rent | nominal $ | ACS B25064 | 4,216 |
| `B25003_001E` | Occupied housing units (households) | count | ACS B25003 | 4,216 |
| `B25003_003E` | Renter-occupied housing units | count | ACS B25003 | 4,216 |
| `B19013_001E` | Median household income | nominal $ | ACS B19013 | 4,216 |
| `B11001_001E` | Households | count | ACS B11001 | 4,216 |
| `B01003_001E` | Total population | count | ACS B01003 | 4,216 |
| `rent_computed` | Renter households with rent burden computed (B25070_001 - B25070_011) | count | derived | 4,214 |
| `burden30` | Share of renter households paying >30% of income for gross rent (main outcome) | % | derived from B25070 | 4,214 |
| `burden50` | Share paying 50%+ of income (severe burden) | % | derived from B25070 | 4,214 |
| `burden_lt35k` | Burden >30% among renters with income < $35,000 | % | derived from B25106 | 4,216 |
| `burden_35_75k` | Burden >30% among renters with income $35,000-$74,999 | % | derived from B25106 | 4,216 |
| `burden_75kp` | Burden >30% among renters with income $75,000+ | % | derived from B25106 | 4,216 |
| `renter_share` | Renter-occupied share of households | % | derived from B25003 | 4,216 |
| `wfh_share` | Workers who worked from home | % | ACS S0801 | 4,025 |
| `ba_share` | Population 25+ with a bachelor's degree or higher | % | derived from B15003 | 4,208 |
| `households` | Households | count | B25003_001 | 4,216 |
| `med_rent` | Median gross rent | nominal $ | B25064 | 4,216 |
| `med_inc` | Median household income | nominal $ | B19013 | 4,216 |
| `pop` | Population | count | B01003 | 4,216 |
| `state` | Principal state of the metro area (first state in the name) |  | derived | 4,216 |
| `real_rent` | Median gross rent in 2024 dollars (CPI-U less shelter) | 2024 $ | derived | 4,216 |
| `real_inc` | Median household income in 2024 dollars (CPI-U less shelter) | 2024 $ | derived | 4,216 |
| `rent_to_inc` | 12 x median gross rent / median household income | % | derived | 4,216 |
| `units` | Housing units authorized by building permits | units | Census BPS | 4,214 |
| `u5` | Units authorized in buildings with 5+ units | units | Census BPS | 4,214 |
| `permits_per_1k` | Permitted units per 1,000 households | rate | derived | 4,214 |
| `mf_share` | Share of permitted units in 5+ unit buildings | % | derived | 4,214 |
| `g` | Actual private employment growth (first-stage check) | % | BLS QCEW | 4,102 |
| `bartik` | Shift-share predicted private employment growth (2012 sector shares x leave-one-out national sector growth) | % | derived from BLS QCEW | 3,785 |
| `bartik_lag` | Shift-share shock lagged one year | % | derived | 3,438 |
| `wrluri` | Wharton Residential Land Use Regulatory Index 2018, weighted metro average (CBSA weights, metro weights where missing) | index | derived from Gyourko et al. (2019, 2021) | 3,329 |
| `n_resp` | Number of Wharton survey jurisdictions in the metro | count | derived | 3,329 |
| `wrluri_unw` | Unweighted metro average of the 2018 Wharton index | index | derived | 3,329 |
| `zri` | NZLUD Zoning Restrictiveness Index, metro average of municipalities linked through Wharton place codes | index | derived from Mleczko & Desmond (2023) | 2,205 |
| `n_zri` | Number of NZLUD municipalities in the metro average | count | derived | 2,205 |
| `wfh2019` | Work-from-home share in 2019 (remote-work exposure) | % | ACS S0801 | 3,935 |
| `real_inc13` | Real median household income in 2013 | 2024 $ | derived | 4,157 |
| `ba_share13` | Bachelor's degree share in 2013 | % | derived | 4,157 |
| `renter_share13` | Renter share in 2013 | % | derived | 4,157 |
| `division` | Census division (1-9) | code | derived from state | 4,216 |

`data/bartik_sector_contrib.csv`: each NAICS sector's contribution to `bartik` (percentage points) by metro and year.

`data/derived/wharton_zri_cbsa.csv`: metro averages of the Wharton index (`wrluri`, `wrluri_unw`, `n_resp`) and the NZLUD index (`zri`, `n_zri`).
