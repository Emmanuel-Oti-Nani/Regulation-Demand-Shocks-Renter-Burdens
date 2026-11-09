# =============================================================================
# Cross-check of the main estimates in R (fixest)
# Regulation, Demand Shocks, and Renter Cost Burdens (2013-2024)
#
# Run from the housing_research_data folder:
#     Rscript check_results.R
# Requires: install.packages(c("data.table", "fixest"))
#
# It re-creates the analysis sample from data/panel_full.csv, re-estimates
# Table 3 (annual panel) and Table 4 (long difference), and prints each
# coefficient next to the value reported in the manuscript.
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(fixest) })

d <- fread("data/panel_full.csv", colClasses = list(character = "cbsa"))
years <- c(2013:2019, 2021:2024)

# --- Sample: metros observed in all 11 years ---------------------------------
d <- d[year %in% years]
keep <- d[, .(ny = uniqueN(year)), by = cbsa][ny == length(years), cbsa]
d <- d[cbsa %in% keep]

# --- Variables, built exactly as in analysis.py ------------------------------
d[, ln_permits := log(pmax(permits_per_1k, 0.1))]
d[, ln_rent    := log(real_rent)]
cs <- d[year == 2019]                                   # one row per metro
d[, wrluri_z := (wrluri - mean(cs$wrluri, na.rm = TRUE)) / sd(cs$wrluri, na.rm = TRUE)]
d[, ln_inc13 := log(real_inc13)]
d[, div_year := paste(division, year, sep = "_")]

outcomes <- c("ln_permits", "burden30", "burden50", "ln_rent",
              "burden_lt35k", "burden_35_75k", "burden_75kp")

# Values reported in the manuscript (Table 3: D x regulation; Table 4: W x regulation)
ref3 <- c(ln_permits = 0.002, burden30 = -0.009, burden50 = -0.017, ln_rent = -0.001,
          burden_lt35k = -0.255, burden_35_75k = -0.021, burden_75kp = -0.041)
ref3_se <- c(ln_permits = 0.009, burden30 = 0.099, burden50 = 0.073, ln_rent = 0.001,
             burden_lt35k = 0.124, burden_35_75k = 0.171, burden_75kp = 0.082)
ref4 <- c(ln_permits = -0.027, burden30 = -0.345, burden50 = -0.078, ln_rent = -0.006,
          burden_lt35k = -0.262, burden_35_75k = -0.879, burden_75kp = -0.326)
ref4_se <- c(ln_permits = 0.024, burden30 = 0.199, burden50 = 0.358, ln_rent = 0.004,
             burden_lt35k = 0.310, burden_35_75k = 0.628, burden_75kp = 0.272)

# --- Table 3: annual panel ---------------------------------------------------
# Y_it = metro FE + division-by-year FE + b1*D + b2*D*R + year x (ln income 2013, BA share 2013)
pA <- d[n_resp >= 3 & !is.na(bartik) & !is.na(wrluri_z) & !is.na(real_inc13) &
        !is.na(ba_share13) & !is.na(division)]
pA[, DxR := bartik * wrluri_z]

cat("\nTABLE 3 CHECK: coefficient on D x regulation\n")
cat(sprintf("%-15s %10s %10s %10s %10s %6s %6s\n", "outcome", "R coef", "paper", "R se", "paper", "N", "metros"))
for (y in outcomes) {
  m <- feols(as.formula(paste0(y, " ~ bartik + DxR + i(year, ln_inc13, ref = 2013) + ",
                               "i(year, ba_share13, ref = 2013) | cbsa + div_year")),
             data = pA, cluster = ~cbsa)
  cat(sprintf("%-15s %10.3f %10.3f %10.3f %10.3f %6d %6d\n", y, coef(m)["DxR"], ref3[y],
              se(m)["DxR"], ref3_se[y], nobs(m), length(unique(pA[!is.na(get(y)), cbsa]))))
}

# --- Table 4: long difference 2019-2024 --------------------------------------
w <- dcast(d, cbsa ~ year, value.var = outcomes)
base <- d[year == 2019, .(cbsa, wfh2019, wrluri_z, ln_inc13, ba_share13, renter_share13, division, n_resp)]

cat("\nTABLE 4 CHECK: coefficient on remote work x regulation\n")
cat(sprintf("%-15s %10s %10s %10s %10s %6s\n", "outcome", "R coef", "paper", "R se", "paper", "N"))
for (y in outcomes) {
  b <- merge(base, w[, .(cbsa, dY = get(paste0(y, "_2024")) - get(paste0(y, "_2019")))], by = "cbsa")
  b <- na.omit(b)[n_resp >= 3]
  b[, W := wfh2019 - mean(wfh2019)]
  b[, WxR := W * wrluri_z]
  m <- feols(dY ~ W + WxR + wrluri_z + ln_inc13 + ba_share13 + renter_share13 | division,
             data = b, vcov = "hetero")
  cat(sprintf("%-15s %10.3f %10.3f %10.3f %10.3f %6d\n", y, coef(m)["WxR"], ref4[y],
              se(m)["WxR"], ref4_se[y], nobs(m)))
}
cat("\nCoefficients should match to the third decimal. Standard errors may differ in the\n",
    "third decimal because of small-sample adjustments; differences larger than that\n",
    "indicate a problem worth investigating.\n")
