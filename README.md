# Regulation, Demand Shocks, and Renter Cost Burdens, 2013–2024

[![Data DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24091426.svg)](https://doi.org/10.5281/zenodo.24091426)
[![Paper](https://img.shields.io/badge/Preprint-10.20944%2Fpreprints202611.1208.v1-blue)](https://doi.org/10.20944/preprints202611.1208.v1)

Data, code and interactive results for the paper:

> Nani, E. O. (2026). *Regulation, Demand Shocks, and Renter Cost Burdens: Did Land-Use Restrictiveness Shape Who Bore the 2013–2024 Housing Squeeze?* Preprints. https://doi.org/10.20944/preprints202611.1208.v1

**Read the paper:** https://doi.org/10.20944/preprints202611.1208.v1

**Interactive maps and charts:** https://emmanuel-oti-nani.github.io/Regulation-Demand-Shocks-Renter-Burdens/

## What the study asks

About half of U.S. renter households spend more than 30 percent of their income on housing. This project tests whether restrictive land-use regulation made local demand shocks hit renters harder. It uses an annual panel of U.S. metropolitan areas (2013–2024, excluding 2020) and two demand shocks:

1. **Shift-share (Bartik) predicted employment growth**, from 2012 industry shares and leave-one-out national industry growth (QCEW).
2. **Pre-pandemic exposure to remote work**, the 2019 work-from-home share, for the 2019–2024 period.

Regulation is measured with the 2018 Wharton Residential Land Use Regulatory Index, with the NZLUD Zoning Restrictiveness Index as an alternative.

## Main findings

- Employment shocks were associated with lower renter cost burdens; remote-work exposure raised rents and burdens, mostly for middle- and higher-income renters.
- Neither effect was significantly stronger in more restrictive metros, and permitting was not less responsive there.
- The nulls are informative: for overall burden, the data rule out amplification larger than about a fifth of the main employment effect, and any amplification of the remote-work effect on burden or rents.

## Repository contents

| Path | Contents |
|---|---|
| `data/panel_full.csv` | Metro-by-year analysis panel (402 metros, 11 years); see `data/codebook.md` |
| `data/bartik_sector_contrib.csv` | Each industry's contribution to the shift-share shock |
| `data/derived/wharton_zri_cbsa.csv` | Metro averages of the Wharton and NZLUD regulation indexes |
| `data/raw/` | Source files: ACS, Building Permits Survey, QCEW, CPI, OMB delineations, NZLUD |
| `R/`, `Regulation_Demand_Shocks_Renter_Burdens.R` | R project (data.table, fixest, HonestDiD) |
| `*.py`, `Regulation_Demand_Shocks_Renter_Burdens.py` | Python version (pandas, numpy, matplotlib) |
| `check/` | Independent checks of the main estimates (R, Stata, Python) |
| `output/`, `output_python/` | Tables (CSV), figures and HTML reports |
| `docs/` | The interactive website |

## How to reproduce

**R (4.3 or later).** Open `Regulation_Demand_Shocks_Renter_Burdens.Rproj` in RStudio and run `Regulation_Demand_Shocks_Renter_Burdens.R`, or double-click `run_analysis.bat` on Windows. Missing packages are installed automatically. Results go to `output/`.

**Python (3.10 or later).** Run `pip install -r requirements.txt`, then `python Regulation_Demand_Shocks_Renter_Burdens.py`, or double-click `run_analysis_python.bat` on Windows. Results go to `output_python/`.

Both versions rebuild the panel from `data/raw/`, estimate every model, and compare the estimates with the values printed in the paper. The Rambachan–Roth sensitivity analysis runs in R only.

## Data sources

| Source | Used for | License |
|---|---|---|
| U.S. Census Bureau, American Community Survey 1-year (B25070, B25106, B25064, B25003, B19013, B15003, B11001, B01003, S0801) | Cost burdens, rents, income, education, remote work | Public domain |
| U.S. Census Bureau, Building Permits Survey (county annual) | Permits | Public domain |
| U.S. Bureau of Labor Statistics, QCEW (MSA by NAICS sector) | Shift-share shock | Public domain |
| U.S. Bureau of Labor Statistics, CPI-U all items less shelter (CUUR0000SA0L2) | Deflator | Public domain |
| Office of Management and Budget, metropolitan delineations (2013, 2018, 2020, 2023) | County-to-metro crosswalks | Public domain |
| Gyourko, Hartley & Krimmel (2019, 2021), Wharton Residential Land Use Regulatory Index 2018 | Regulation | Not redistributed; see `data/raw/README_WHARTON.md` |
| Mleczko & Desmond (2023), National Zoning and Land Use Database | Alternative regulation measure | MIT |

Code is released under the MIT License and derived data under CC BY 4.0; see `LICENSE` and `DATA_LICENSE.md`.

## Citation

If you use these data or code, please cite the archived release (see `CITATION.cff`, or the "Cite this repository" button on GitHub):

> Nani, E. O. (2026). *Regulation, Demand Shocks, and Renter Cost Burdens, 2013–2024: Data and Code* (Version 1.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24091426

## Contact

Emmanuel Oti Nani · ORCID [0009-0009-4175-8962](https://orcid.org/0009-0009-4175-8962) · en289s@missouristate.edu
