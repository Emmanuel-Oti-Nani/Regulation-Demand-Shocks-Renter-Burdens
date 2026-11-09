* =============================================================================
* Cross-check of the main estimates in Stata (reghdfe)
* Regulation, Demand Shocks, and Renter Cost Burdens (2013-2024)
*
* Run from the housing_research_data folder:   do check_results.do
* Requires: ssc install reghdfe, replace   and   ssc install ftools, replace
*
* Re-creates the analysis sample from data/panel_full.csv, re-estimates the
* D x regulation coefficient (Table 3) and the remote work x regulation
* coefficient (Table 4), and lists them next to the manuscript values.
* =============================================================================
clear all
set more off
import delimited using "data/panel_full.csv", stringcols(_all) clear
foreach v of varlist year division n_resp permits_per_1k real_rent burden* bartik wrluri ///
        real_inc13 ba_share13 renter_share13 wfh2019 {
    destring `v', replace force
}

* --- Sample: metros observed in all 11 years ---------------------------------
keep if inlist(year,2013,2014,2015,2016,2017,2018,2019,2021,2022,2023,2024)
bysort cbsa: gen ny = _N
keep if ny == 11

* --- Variables, built exactly as in analysis.py ------------------------------
gen ln_permits = ln(max(permits_per_1k, 0.1))
gen ln_rent    = ln(real_rent)
summarize wrluri if year == 2019
gen wrluri_z   = (wrluri - r(mean)) / r(sd)
gen ln_inc13   = ln(real_inc13)
egen div_year  = group(division year)
encode cbsa, gen(metro)

local outcomes ln_permits burden30 burden50 ln_rent burden_lt35k burden_35_75k burden_75kp
local ref3  0.002 -0.009 -0.017 -0.001 -0.255 -0.021 -0.041
local ref4 -0.027 -0.345 -0.078 -0.006 -0.262 -0.879 -0.326

* --- Table 3: annual panel ---------------------------------------------------
preserve
keep if n_resp >= 3 & !missing(bartik, wrluri_z, real_inc13, ba_share13, division)
gen DxR = bartik * wrluri_z
di _n "TABLE 3 CHECK: coefficient on D x regulation (paper value in brackets)"
local i = 1
foreach y of local outcomes {
    quietly reghdfe `y' bartik DxR ib2013.year#c.ln_inc13 ib2013.year#c.ba_share13, ///
        absorb(metro div_year) vce(cluster metro)
    local r : word `i' of `ref3'
    di %-15s "`y'" "  coef = " %7.3f _b[DxR] "  [" %7.3f `r' "]   se = " %6.3f _se[DxR] "   N = " e(N)
    local ++i
}
restore

* --- Table 4: long difference 2019-2024 --------------------------------------
di _n "TABLE 4 CHECK: coefficient on remote work x regulation (paper value in brackets)"
local i = 1
foreach y of local outcomes {
    preserve
    keep if inlist(year, 2019, 2024)
    keep cbsa year `y' wfh2019 wrluri_z ln_inc13 ba_share13 renter_share13 division n_resp
    bysort cbsa (year): gen dY = `y'[2] - `y'[1] if _N == 2
    keep if year == 2019
    drop if missing(dY, wfh2019, wrluri_z, ln_inc13, ba_share13, renter_share13, division, n_resp)
    keep if n_resp >= 3
    summarize wfh2019
    gen W = wfh2019 - r(mean)
    gen WxR = W * wrluri_z
    quietly regress dY W WxR wrluri_z ln_inc13 ba_share13 renter_share13 i.division, vce(robust)
    local r : word `i' of `ref4'
    di %-15s "`y'" "  coef = " %7.3f _b[WxR] "  [" %7.3f `r' "]   se = " %6.3f _se[WxR] "   N = " e(N)
    restore
    local ++i
}
di _n "Coefficients should match to the third decimal; standard errors may differ slightly."
