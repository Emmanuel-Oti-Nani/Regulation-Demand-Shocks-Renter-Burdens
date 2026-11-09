# =============================================================================
# 04_robustness_extra.R
# Additional robustness analyses (Table 6 and the pre-trend sensitivity analysis)
# Run after 02_analysis.R (uses a, panel_A, long_diff, event_study and res).
#   1. Precision of the null: 90% confidence intervals and minimum detectable
#      effects (80% power) for every regulation interaction in Tables 3 and 4.
#   2. Standard errors clustered by state.
#   3. Shift-share diagnostics: sector weights that decompose the shock x
#      regulation coefficient (Goldsmith-Pinkham, Sorkin & Swift, 2020) and
#      leave-one-sector-out estimates.
#   4. Pre-trends in the remote-work event study: joint test of the 2013-2018
#      coefficients, a linear-trend-adjusted post-period average, and the
#      Rambachan & Roth (2023) relative-magnitudes sensitivity analysis.
# Output: output/results_extra.rds and output/tables/table6_*.csv
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(fixest); library(HonestDiD) })

Z90 <- qnorm(0.95); Z95 <- qnorm(0.975); ZPOW <- qnorm(0.80)
ex <- list()
ci_row <- function(b, se) data.table(b = b, se = se, ci90_lo = b - Z90 * se, ci90_hi = b + Z90 * se,
                                     ci95_lo = b - Z95 * se, ci95_hi = b + Z95 * se, mde80 = (Z95 + ZPOW) * se)

# ---- 1. Precision of the null ------------------------------------------------
ex$equiv_A <- rbindlist(lapply(names(OUTCOMES), function(y) {
  m <- res$A_models[[y]]
  cbind(outcome = OUTCOMES[[y]], main_D = unname(coef(m)["D"]), ci_row(unname(coef(m)["DxR"]), unname(se(m)["DxR"])))
}))
ex$equiv_B <- rbindlist(lapply(names(OUTCOMES), function(y) {
  m <- res$B_models[[y]]
  cbind(outcome = OUTCOMES[[y]], main_W = unname(coef(m)["W"]), ci_row(unname(coef(m)["WxR"]), unname(se(m)["WxR"])))
}))

# ---- 2. Standard errors clustered by state ----------------------------------
ex$state_cluster <- rbindlist(lapply(c("burden30", "ln_permits", "ln_rent"), function(y) {
  m <- summary(res$A_models[[y]], cluster = ~state)
  data.table(outcome = OUTCOMES[[y]], DxR = unname(coef(m)["DxR"]), se_metro = unname(se(res$A_models[[y]])["DxR"]),
             se_state = unname(se(m)["DxR"]), p_state = unname(pvalue(m)["DxR"]))
}))

# ---- 3. Shift-share diagnostics ----------------------------------------------
SECTORS <- c("11" = "Agriculture", "21" = "Mining", "22" = "Utilities", "23" = "Construction",
             "31-33" = "Manufacturing", "42" = "Wholesale trade", "44-45" = "Retail trade",
             "48-49" = "Transportation and warehousing", "51" = "Information", "52" = "Finance and insurance",
             "53" = "Real estate", "54" = "Professional services", "55" = "Management of companies",
             "56" = "Administrative services", "61" = "Educational services", "62" = "Health care",
             "71" = "Arts and recreation", "72" = "Accommodation and food", "81" = "Other services")
sc <- fread(file.path("data", "bartik_sector_contrib.csv"), colClasses = list(character = c("cbsa", "ind")))
scw <- dcast(sc, cbsa + year ~ ind, value.var = "contrib", fill = 0)
inds <- setdiff(names(scw), c("cbsa", "year"))

sector_diag <- function(y) {
  m <- res$A_models[[y]]
  d <- copy(a)[!is.na(get(y)) & !is.na(bartik) & !is.na(wrluri_z) & !is.na(real_inc13) &
                 !is.na(ba_share13) & !is.na(division) & n_resp >= 3]
  d <- merge(d, scw, by = c("cbsa", "year"), all.x = TRUE)
  for (k in inds) set(d, which(is.na(d[[k]])), k, 0)
  d[, D := bartik][, DxR := bartik * wrluri_z]
  # Frisch-Waugh-Lovell: residualize y, DxR and each sector piece of DxR on all other regressors and fixed effects
  rhs <- paste0("D + i(year, ln_inc13, ref = ", min(d$year), ") + i(year, ba_share13, ref = ", min(d$year), ") | cbsa + div_year")
  zn <- paste0("z_", gsub("-", "_", inds))
  for (j in seq_along(inds)) d[, (zn[j]) := get(inds[j]) * wrluri_z]
  lhs <- c(y, "DxR", zn)
  rr <- feols(as.formula(paste0("c(", paste(lhs, collapse = ","), ") ~ ", rhs)), data = d)
  R <- sapply(seq_along(lhs), function(i) resid(rr[[i]])); colnames(R) <- lhs
  dxr <- R[, "DxR"]; yy <- R[, y]
  w <- t(R[, zn]) %*% dxr / sum(dxr^2)
  bk <- (t(R[, zn]) %*% yy) / (t(R[, zn]) %*% dxr)
  tab <- data.table(naics = inds, sector = SECTORS[inds], weight = as.numeric(w), beta_k = as.numeric(bk))
  # Leave-one-sector-out estimates
  loo <- rbindlist(lapply(inds, function(k) {
    dk <- merge(copy(a), scw[, c("cbsa", "year", k), with = FALSE], by = c("cbsa", "year"), all.x = TRUE)
    dk[, bartik_x := bartik - fifelse(is.na(get(k)), 0, get(k))]
    mk <- panel_A(dk, y, shock = "bartik_x")
    data.table(sector = SECTORS[[k]], DxR = unname(coef(mk)["DxR"]), se = unname(se(mk)["DxR"]))
  }))
  list(weights = tab[order(-abs(weight))], check = c(decomposed = sum(tab$weight * tab$beta_k), estimate = unname(coef(m)["DxR"])),
       loo = loo)
}
ex$sectors <- lapply(c(burden30 = "burden30", ln_permits = "ln_permits", ln_rent = "ln_rent"), sector_diag)

# ---- 4. Pre-trends in the remote-work event study ----------------------------
PRE <- 2013:2018; POST <- 2021:2024
pretrend <- function(es) {
  nm <- paste0("year::", c(PRE, POST), ":WR")
  b <- coef(es)[nm]; V <- vcov(es)[nm, nm]
  kp <- length(PRE)
  bp <- b[1:kp]; Vp <- V[1:kp, 1:kp]
  wald <- as.numeric(t(bp) %*% solve(Vp, bp))
  # Linear trend through the pre-period coefficients and 2019 (= 0), extrapolated to the post period
  yrs <- c(PRE, 2019) - 2019; A <- cbind(1, yrs); L <- solve(t(A) %*% A) %*% t(A)
  w <- c(rep(0, kp), rep(1 / length(POST), length(POST)))
  for (t in POST) w[1:kp] <- w[1:kp] - (L[1, 1:kp] + L[2, 1:kp] * (t - 2019)) / length(POST)
  wp <- c(rep(0, kp), rep(1 / length(POST), length(POST)))
  list(joint_chi2 = wald, df = kp, p = 1 - pchisq(wald, kp),
       avg_post = sum(wp * b), avg_post_se = sqrt(as.numeric(t(wp) %*% V %*% wp)),
       detrended = sum(w * b), detrended_se = sqrt(as.numeric(t(w) %*% V %*% w)), b = b, V = V)
}
ex$pretrend <- lapply(res$ES, pretrend)

# Rambachan & Roth (2023): how large may post-2020 violations of parallel trends be, relative to the
# largest change between consecutive pre-period years, before the average 2021-2024 effect could be positive?
pt <- ex$pretrend$burden30
lvec <- matrix(rep(1 / length(POST), length(POST)), ncol = 1)
orig <- constructOriginalCS(betahat = pt$b, sigma = pt$V, numPrePeriods = length(PRE),
                            numPostPeriods = length(POST), l_vec = lvec)
rm_res <- createSensitivityResults_relativeMagnitudes(betahat = pt$b, sigma = pt$V, numPrePeriods = length(PRE),
                                                      numPostPeriods = length(POST), l_vec = lvec,
                                                      Mbarvec = seq(0, 2, by = 0.25))
orig_df <- as.data.frame(orig); rm_df <- as.data.frame(rm_res)
ex$honestdid <- rbindlist(list(
  data.table(Mbar = NA_real_, lb = as.numeric(orig_df[["lb"]]), ub = as.numeric(orig_df[["ub"]]), method = "Original"),
  data.table(Mbar = as.numeric(rm_df[["Mbar"]]), lb = as.numeric(rm_df[["lb"]]), ub = as.numeric(rm_df[["ub"]]),
             method = "Relative magnitudes")), use.names = TRUE, fill = TRUE)
ex$honestdid_breakdown <- suppressWarnings(min(rm_df$Mbar[rm_df$ub > 0]))   # Inf if the interval never includes positive values

# ---- Save ------------------------------------------------------------------------
dir.create(file.path("output", "tables"), recursive = TRUE, showWarnings = FALSE)
saveRDS(ex, file.path("output", "results_extra.rds"))
fwrite(ex$equiv_A, file.path("output", "tables", "table6a_precision_annual_panel.csv"))
fwrite(ex$equiv_B, file.path("output", "tables", "table6b_precision_long_difference.csv"))
fwrite(ex$state_cluster, file.path("output", "tables", "table6c_state_clustered_se.csv"))
fwrite(rbindlist(lapply(names(ex$sectors), function(y) cbind(outcome = y, ex$sectors[[y]]$weights))),
       file.path("output", "tables", "table6d_sector_weights.csv"))
fwrite(rbindlist(lapply(names(ex$sectors), function(y) cbind(outcome = y, ex$sectors[[y]]$loo))),
       file.path("output", "tables", "table6e_leave_one_sector_out.csv"))
fwrite(rbindlist(lapply(names(ex$pretrend), function(y) with(ex$pretrend[[y]],
       data.table(outcome = y, joint_chi2, df, p, avg_post, avg_post_se, detrended, detrended_se)))),
       file.path("output", "tables", "table6f_pretrend_tests.csv"))
fwrite(ex$honestdid, file.path("output", "tables", "table6g_honestdid_relative_magnitudes.csv"))

cat("\nAdditional robustness (04_robustness_extra.R)\n")
cat("Precision, annual panel:\n"); print(ex$equiv_A[, .(outcome, b = round(b, 3), ci90_lo = round(ci90_lo, 3), ci90_hi = round(ci90_hi, 3), mde80 = round(mde80, 3))])
cat("Precision, long difference:\n"); print(ex$equiv_B[, .(outcome, b = round(b, 3), ci90_lo = round(ci90_lo, 3), ci90_hi = round(ci90_hi, 3), mde80 = round(mde80, 3))])
cat("State-clustered SEs:\n"); print(ex$state_cluster)
for (y in names(ex$sectors)) { cat("Sector weights,", y, "- check:", round(ex$sectors[[y]]$check, 4), "\n"); print(head(ex$sectors[[y]]$weights, 5)) }
cat("Pre-trend tests:\n"); print(fread(file.path("output", "tables", "table6f_pretrend_tests.csv")))
cat("Rambachan-Roth relative magnitudes (average 2021-2024 effect, burden >30%):\n"); print(ex$honestdid)
cat("Breakdown value of Mbar:", ex$honestdid_breakdown, "\n")
