# Wharton Residential Land Use Regulatory Index (WRLURI 2018)

The original survey file is **not included** in this repository because it is distributed by its authors without a license that permits redistribution. The repository includes only the metro-level averages built from it (`data/derived/wharton_zri_cbsa.csv`), which is all the analysis needs.

To rebuild those averages from the original file:

1. Download `WHARTON LAND REGULATION DATA_1_15_2020` (Stata format) from the authors' land use survey page. The original page is preserved at
   https://web.archive.org/web/20251013095048/https://real-faculty.wharton.upenn.edu/gyourko/land-use-survey/
2. Save it in this folder as `WHARTON_LAND_REGULATION_DATA_01_15_2020.dta`.
3. Run the analysis as usual. The build scripts detect the file and rebuild `data/derived/wharton_zri_cbsa.csv`.

Please cite the data as the authors request:

Gyourko, J., Hartley, J., & Krimmel, J. (2019). *The local residential land use regulatory environment across U.S. housing markets: Evidence from a new Wharton index* (NBER Working Paper No. 26573). https://doi.org/10.3386/w26573
