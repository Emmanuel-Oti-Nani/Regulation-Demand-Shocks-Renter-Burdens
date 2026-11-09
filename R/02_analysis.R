# =============================================================================
# 02_analysis.R
# All estimates reported in the manuscript.
# Input: data/panel_full.csv   Output: output/results.rds (+ CSV tables in 03)
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(fixest) })
setFixest_notes(FALSE)

YEARS <- c(2013:2019, 2021:2024)
a <- fread(file.path("data", "panel_full.csv"), colClasses = list(character = c("cbsa", "name", "state")))
a <- a[year %in% YEARS]
a <- a[cbsa %in% a[, .(n = uniqueN(year)), by = cbsa][n == length(YEARS), cbsa]]   # balanced: 367 metros
a[, ln_permits := log(pmax(permits_per_1k, 0.1))]
a[, ln_rent    := log(real_rent)]
a[, ln_inc13   := log(real_inc13)]
a[, div_year   := paste(division, year, sep = "_")]

# Standardize moderators on the metro cross-section (one row per metro)
cs <- a[year == 2019]
z  <- function(x, ref) (x - mean(ref, na.rm = TRUE)) / sd(ref, na.rm = TRUE)
a[, wrluri_z     := z(wrluri, cs$wrluri)]
a[, zri_z        := z(zri, cs$zri)]
a[, wrluri_unw_z := z(wrluri_unw, cs$wrluri_unw)]

OUTCOMES <- c(ln_permits = "Log permits per 1,000 households",
              burden30 = "Renters paying >30% of income",
              burden50 = "Renters paying >50% of income",
              ln_rent = "Log real median gross rent",
              burden_lt35k = "Burden, renters under $35,000",
              burden_35_75k = "Burden, renters $35,000-$74,999",
              burden_75kp = "Burden, renters $75,000 or more")

ctab <- function(m, term) data.table(b = unname(coef(m)[term]), se = unname(se(m)[term]),
                                     p = unname(pvalue(m)[term]))

# ---- Specification A: annual panel, shift-share shock x regulation ---------
panel_A <- function(d, y, mod = "wrluri_z", shock = "bartik", min_resp = 3, drop = NULL) {
  d <- copy(d)
  d <- d[!is.na(get(y)) & !is.na(get(shock)) & !is.na(get(mod)) & !is.na(real_inc13) &
         !is.na(ba_share13) & !is.na(division)]
  if (min_resp > 0 && startsWith(mod, "wrluri")) d <- d[n_resp >= min_resp]
  if (!is.null(drop)) d <- d[!drop(d)]
  d[, D := get(shock)][, DxR := D * get(mod)]
  r0 <- min(d$year)   # reference year for the control interactions (2014 when 2013 is dropped)
  feols(as.formula(paste0(y, " ~ D + DxR + i(year, ln_inc13, ref = ", r0, ") + ",
                          "i(year, ba_share13, ref = ", r0, ") | cbsa + div_year")),
        data = d, cluster = ~cbsa)
}

# ---- Specification B: long difference 2019 -> y1, remote work x regulation --
long_diff <- function(d, y, mod = "wrluri_z", y0 = 2019, y1 = 2024, min_resp = 3) {
  dy <- merge(d[year == y0, .(cbsa, v0 = get(y))], d[year == y1, .(cbsa, v1 = get(y))], by = "cbsa")
  b <- merge(d[year == y0, .(cbsa, wfh2019, R = get(mod), real_inc13, ba_share13, renter_share13,
                             division, n_resp)], dy, by = "cbsa")
  b[, dY := v1 - v0]
  b <- na.omit(b, cols = c("wfh2019", "R", "real_inc13", "ba_share13", "renter_share13",
                           "division", "n_resp", "dY"))
  if (min_resp > 0 && startsWith(mod, "wrluri")) b <- b[n_resp >= min_resp]
  b[, W := wfh2019 - mean(wfh2019)][, WxR := W * R][, ln_inc13 := log(real_inc13)]
  feols(dY ~ W + WxR + R + ln_inc13 + ba_share13 + renter_share13 | division, data = b, vcov = "hetero")
}

# ---- Event study: remote work x regulation, by year (2019 = reference) -----
event_study <- function(d, y, mod = "wrluri_z", min_resp = 3) {
  d <- d[!is.na(get(y)) & !is.na(wfh2019) & !is.na(get(mod)) & !is.na(real_inc13) &
         !is.na(ba_share13) & !is.na(division) & n_resp >= min_resp]
  d[, Wc := wfh2019 - mean(wfh2019)][, WR := Wc * get(mod)][, R := get(mod)]
  feols(as.formula(paste0(y, " ~ i(year, Wc, ref = 2019) + i(year, WR, ref = 2019) + ",
                          "i(year, R, ref = 2019) + i(year, ln_inc13, ref = 2013) + ",
                          "i(year, ba_share13, ref = 2013) | cbsa + div_year")),
        data = d, cluster = ~cbsa)
}

res <- list()

# Table 3
res$A_models <- lapply(names(OUTCOMES), function(y) panel_A(a, y)); names(res$A_models) <- names(OUTCOMES)
res$table3 <- rbindlist(lapply(names(OUTCOMES), function(y) {
  m <- res$A_models[[y]]
  data.table(outcome = OUTCOMES[[y]], D_b = coef(m)["D"], D_se = se(m)["D"], D_p = pvalue(m)["D"],
             DxR_b = coef(m)["DxR"], DxR_se = se(m)["DxR"], DxR_p = pvalue(m)["DxR"],
             N = nobs(m), metros = unname(m$fixef_sizes["cbsa"]))
}))

# Table 4
res$B_models <- lapply(names(OUTCOMES), function(y) long_diff(a, y)); names(res$B_models) <- names(OUTCOMES)
res$table4 <- rbindlist(lapply(names(OUTCOMES), function(y) {
  m <- res$B_models[[y]]
  data.table(outcome = OUTCOMES[[y]], W_b = coef(m)["W"], W_se = se(m)["W"], W_p = pvalue(m)["W"],
             WxR_b = coef(m)["WxR"], WxR_se = se(m)["WxR"], WxR_p = pvalue(m)["WxR"],
             R_b = coef(m)["R"], R_se = se(m)["R"], R_p = pvalue(m)["R"],
             N = nobs(m), R2 = r2(m, "r2"))
}))

# Table 5: robustness (annual panel)
specs <- list(
  "Main (WRLURI, >=3 responses)"          = list(),
  "WRLURI, >=1 response"                  = list(min_resp = 1),
  "WRLURI, >=5 responses"                 = list(min_resp = 5),
  "WRLURI, unweighted average"            = list(mod = "wrluri_unw_z"),
  "Zoning Restrictiveness Index"          = list(mod = "zri_z", min_resp = 0),
  "Shock lagged one year"                 = list(shock = "bartik_lag"),
  "Excluding 2013"                        = list(drop = function(d) d$year == 2013),
  "Excluding 2021"                        = list(drop = function(d) d$year == 2021),
  "Excluding California"                  = list(drop = function(d) d$state %in% "CA"),
  "Excluding New England"                 = list(drop = function(d) d$division == 1))
res$table5 <- rbindlist(lapply(names(specs), function(s) {
  row <- data.table(specification = s)
  for (y in c("burden30", "ln_permits", "ln_rent")) {
    m <- do.call(panel_A, c(list(d = a, y = y), specs[[s]]))
    row[, (paste0(y, "_b")) := coef(m)["DxR"]][, (paste0(y, "_se")) := se(m)["DxR"]]
    if (y == "burden30") row[, metros := unname(m$fixef_sizes["cbsa"])]
  }
  row
}))

# Long-difference robustness
specsB <- list("Main" = list(), ">=1 response" = list(min_resp = 1), ">=5 responses" = list(min_resp = 5),
               "Zoning Restrictiveness Index" = list(mod = "zri_z", min_resp = 0), "2019 to 2023" = list(y1 = 2023))
res$robustB <- rbindlist(lapply(names(specsB), function(s) {
  m <- do.call(long_diff, c(list(d = a, y = "burden30"), specsB[[s]]))
  data.table(specification = s, WxR_b = coef(m)["WxR"], WxR_se = se(m)["WxR"], N = nobs(m))
}))

# Event study (Figure 2) and first stage
res$ES <- lapply(c(burden30 = "burden30", ln_rent = "ln_rent", ln_permits = "ln_permits"),
                 function(y) event_study(a, y))
es <- res$ES$burden30
k  <- grep("^year::[0-9]+:WR$", names(coef(es)))
res$event <- rbind(data.table(year = as.integer(sub("year::([0-9]+):WR", "\\1", names(coef(es))[k])),
                              b = coef(es)[k], se = se(es)[k]),
                   data.table(year = 2019L, b = 0, se = 0))[order(year)]
fs <- a[!is.na(g) & abs(g) < 30]
res$first_stage <- panel_A(fs, "g")

# Descriptives (Table 2) and trends by regulation tercile (Figure 1)
main <- a[n_resp >= 3]
dv <- c(burden30 = "Renters paying >30% of income (%)", burden50 = "Renters paying >50% of income (%)",
        burden_lt35k = "Burden, renters under $35,000 (%)", burden_35_75k = "Burden, renters $35,000-$74,999 (%)",
        burden_75kp = "Burden, renters $75,000 or more (%)", real_rent = "Real median gross rent (2024 $)",
        permits_per_1k = "Permits per 1,000 households", bartik = "Predicted employment growth (%)",
        wfh2019 = "Worked from home, 2019 (%)", wrluri = "WRLURI 2018 (unstandardized)",
        real_inc13 = "Real median household income, 2013 (2024 $)", ba_share13 = "Bachelor's degree or higher, 2013 (%)")
res$table2 <- rbindlist(lapply(names(dv), function(v) {
  x <- main[[v]]; data.table(variable = dv[[v]], mean = mean(x, na.rm = TRUE), sd = sd(x, na.rm = TRUE),
                             min = min(x, na.rm = TRUE), max = max(x, na.rm = TRUE))
}))
res$n_main_metros <- uniqueN(main$cbsa)
m19 <- main[year == 2019, .(cbsa, wrluri)]
m19[, tercile := cut(wrluri, quantile(wrluri, c(0, 1/3, 2/3, 1)), include.lowest = TRUE,
                     labels = c("Least restrictive", "Middle", "Most restrictive"))]
res$trends <- merge(main, m19[, .(cbsa, tercile)], by = "cbsa")[
  , .(burden30 = mean(burden30, na.rm = TRUE), real_rent = mean(real_rent, na.rm = TRUE),
      permits_per_1k = mean(permits_per_1k, na.rm = TRUE)), by = .(tercile, year)][order(tercile, year)]

dir.create("output", showWarnings = FALSE)
saveRDS(res, file.path("output", "results.rds"))
message("Analysis complete: ", res$n_main_metros, " metros in the main sample.")
