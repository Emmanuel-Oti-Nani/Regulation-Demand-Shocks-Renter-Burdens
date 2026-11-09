# =============================================================================
# 01_build_panel.R
# Builds the metro-year analysis panel, 2013-2024 (2020 excluded), from data/raw.
# Output: data/panel_full.csv
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(haven) })

RAW   <- file.path("data", "raw")
YEARS <- c(2013:2019, 2021:2024)
pad   <- function(x, w) formatC(as.integer(x), width = w, flag = "0")

# ---------------- ACS -------------------------------------------------------
a <- fread(file.path(RAW, "acs1_metro_2013_2024.csv"), colClasses = list(character = c("cbsa", "name")))
a[, rent_computed := B25070_001E - B25070_011E]
a[, burden30 := 100 * (B25070_007E + B25070_008E + B25070_009E + B25070_010E) / rent_computed]
a[, burden50 := 100 * B25070_010E / rent_computed]
# Income tiers (nominal brackets in B25106)
a[, burden_lt35k  := 100 * (B25106_028E + B25106_032E) / (B25106_025E + B25106_029E)]
a[, burden_35_75k := 100 * (B25106_036E + B25106_040E) / (B25106_033E + B25106_037E)]
a[, burden_75kp   := 100 * B25106_044E / B25106_041E]
a[, renter_share  := 100 * B25003_003E / B25003_001E]
a[, ba_share      := 100 * (B15003_022E + B15003_023E + B15003_024E + B15003_025E) / B15003_001E]
a[, households := B25003_001E]
a[, med_rent   := B25064_001E]
a[, med_inc    := B19013_001E]
a[, pop        := B01003_001E]
# State of the principal city: first ", XX" in the metro name
m <- regexpr(", [A-Z]{2}", a$name)
a[, state := NA_character_]
a[m > 0, state := substr(name, m[m > 0] + 2, m[m > 0] + 3)]

# Work from home share (subject table S0801; negative values are suppression codes)
wf <- fread(file.path(RAW, "acs1_S0801_wfh_2013_2024.csv"), colClasses = list(character = "cbsa"))
wf[, wfh_share := fifelse(S0801_C01_013E >= 0, as.numeric(S0801_C01_013E), NA_real_)]
a <- merge(a, wf[, .(year, cbsa, wfh_share)], by = c("year", "cbsa"), all.x = TRUE)

# Deflate with CPI-U less shelter (2024 dollars)
cpi <- fread(file.path(RAW, "cpi_less_shelter_CUUR0000SA0L2_annual.csv"))
cpi_v <- setNames(cpi$cpi_u_less_shelter, cpi$year)
a[, real_rent := med_rent * cpi_v["2024"] / cpi_v[as.character(year)]]
a[, real_inc  := med_inc  * cpi_v["2024"] / cpi_v[as.character(year)]]
a[, rent_to_inc := 100 * 12 * med_rent / med_inc]

# ---------------- Delineations: county -> CBSA by vintage -------------------
delin <- function(f) {
  d <- read.csv(file.path(RAW, f), skip = 2, colClasses = "character", check.names = FALSE)
  d <- d[!is.na(d[["FIPS State Code"]]) & d[["FIPS State Code"]] != "" &
         grepl("^[0-9]{5}$", d[["CBSA Code"]]), ]
  data.table(fips = paste0(pad(d[["FIPS State Code"]], 2), pad(d[["FIPS County Code"]], 3)),
             cbsa = d[["CBSA Code"]])
}
D <- list(`2013` = delin("delin2013.csv"), `2018` = delin("delin2018.csv"),
          `2020` = delin("delin2020.csv"), `2023` = delin("delin2023.csv"))
vint <- function(y) if (y <= 2017) "2013" else if (y <= 2019) "2018" else if (y <= 2022) "2020" else "2023"

# ---------------- Building permits -------------------------------------------
b <- fread(file.path(RAW, "bps_county_2012_2024.csv"), colClasses = list(character = c("st", "cty")))
b[, fips := paste0(pad(st, 2), pad(cty, 3))]
b[, units := u1 + u2 + u34 + u5]
perm <- rbindlist(lapply(YEARS, function(y) {
  bb <- merge(b[year == y], D[[vint(y)]], by = "fips")
  bb[, .(units = sum(units), u5 = sum(u5)), by = cbsa][, year := y]
}))
a <- merge(a, perm, by = c("cbsa", "year"), all.x = TRUE)
a[, permits_per_1k := 1000 * units / households]
a[, mf_share := 100 * u5 / units]

# ---------------- Wharton index and NZLUD ZRI -> CBSA (2018 codes) ------------
# The Wharton file has no redistribution license, so the public repository ships only the
# metro-level averages built here (data/derived/wharton_zri_cbsa.csv). If the original file is
# in data/raw (see data/raw/README_WHARTON.md), the averages are rebuilt from it.
WH <- file.path(RAW, "WHARTON_LAND_REGULATION_DATA_01_15_2020.dta")
DER <- file.path("data", "derived", "wharton_zri_cbsa.csv")
if (file.exists(WH)) {
  w <- as.data.table(zap_labels(read_dta(WH)))
  w <- w[!is.na(cbsacode18) & !is.na(WRLURI18)]
  w[, cbsa := pad(cbsacode18, 5)]
  w[, wt := fcoalesce(as.numeric(weight_cbsa), as.numeric(weight_metro), 1)]
  wr <- w[, .(wrluri = weighted.mean(WRLURI18, wt), n_resp = .N, wrluri_unw = mean(WRLURI18)), by = cbsa]
  # NZLUD Zoning Restrictiveness Index, linked to CBSAs through the Wharton place codes
  z <- fread(file.path(RAW, "nzlud_muni.csv"), encoding = "Latin-1")
  z[, geoid7 := pad(GEOID, 7)]
  wp <- w[!is.na(fipsplacecode18) & fipsplacecode18 != ""]
  wp[, geoid7 := paste0(pad(statecode, 2), pad(fipsplacecode18, 5))]
  wp <- unique(wp[, .(geoid7, cbsa)], by = "geoid7")
  zr <- merge(z, wp, by = "geoid7")[, .(zri = mean(zri, na.rm = TRUE), n_zri = .N), by = cbsa]
  dir.create(file.path("data", "derived"), showWarnings = FALSE, recursive = TRUE)
  fwrite(merge(wr, zr, by = "cbsa", all = TRUE)[order(cbsa)], DER)
} else {
  dz <- fread(DER, colClasses = list(character = "cbsa"))
  wr <- dz[!is.na(wrluri), .(cbsa, wrluri, n_resp, wrluri_unw)]
  zr <- dz[!is.na(zri), .(cbsa, zri, n_zri)]
}

# ---------------- Shift-share (Bartik) shock from QCEW ----------------------
q <- fread(file.path(RAW, "qcew_msa_sector_2012_2024.csv"),
           colClasses = list(character = c("area", "ind", "disc")))
sec <- q[own == 5 & agg == 44]                                   # MSA x NAICS sector, private
tot <- q[own == 5 & agg == 41 & ind == "10", .(area, year, priv_tot = emp)]
nat <- q[area == "US000" & own == 5 & agg == 14, .(ind, year, nat = emp)]
sec <- merge(merge(sec, tot, by = c("area", "year")), nat, by = c("ind", "year"))
sec[, emp := as.numeric(emp)]
sec[, supp := disc %in% "N"]
# Fill suppressed cells: allocate residual private employment by national sector size
sec[, disc_sum := sum(emp[!supp]), by = .(area, year)]
sec[, supp_nat := sum(nat[supp]), by = .(area, year)]
sec[supp == TRUE, emp := pmax(priv_tot - disc_sum, 0) * nat / supp_nat]
sec[, cbsa := paste0(substr(area, 2, 5), "0")]

base <- sec[year == 2012, .(cbsa, ind, emp)]
base[, share := emp / sum(emp), by = cbsa]
loo <- merge(sec[, .(cbsa, ind, year, emp)], nat, by = c("ind", "year"))
loo[, nat_loo := nat - emp]
setorder(loo, cbsa, ind, year)
loo[, g := nat_loo / shift(nat_loo) - 1, by = .(cbsa, ind)]
bt <- merge(loo, base[, .(cbsa, ind, share)], by = c("cbsa", "ind"))
bartik <- bt[, .(bartik = if (all(is.na(g))) NA_real_ else 100 * sum(share * g, na.rm = TRUE)), by = .(cbsa, year)]
# Each sector's contribution to the shock (used by the shift-share diagnostics in 04_robustness_extra.R)
fwrite(bt[!is.na(g), .(cbsa, ind, year, contrib = 100 * share * g)][order(cbsa, ind, year)],
       file.path("data", "bartik_sector_contrib.csv"))

# Actual private employment growth (first-stage check)
tg <- copy(tot)[, cbsa := paste0(substr(area, 2, 5), "0")]
setorder(tg, cbsa, year)
tg[, g := 100 * (priv_tot / shift(priv_tot) - 1), by = cbsa]
a <- merge(a, tg[, .(cbsa, year, g)], by = c("cbsa", "year"), all.x = TRUE)
a <- merge(a, bartik, by = c("cbsa", "year"), all.x = TRUE)
a <- merge(a, bartik[, .(cbsa, year = year + 1L, bartik_lag = bartik)], by = c("cbsa", "year"), all.x = TRUE)

# ---------------- Moderators and baseline covariates ------------------------
a <- merge(a, wr, by = "cbsa", all.x = TRUE)
a <- merge(a, zr, by = "cbsa", all.x = TRUE)
a <- merge(a, a[year == 2019, .(cbsa, wfh2019 = wfh_share)], by = "cbsa", all.x = TRUE)
a <- merge(a, a[year == 2013, .(cbsa, real_inc13 = real_inc, ba_share13 = ba_share,
                                renter_share13 = renter_share)], by = "cbsa", all.x = TRUE)
div <- c(CT=1,ME=1,MA=1,NH=1,RI=1,VT=1, NJ=2,NY=2,PA=2, IL=3,IN=3,MI=3,OH=3,WI=3,
         IA=4,KS=4,MN=4,MO=4,NE=4,ND=4,SD=4, DE=5,DC=5,FL=5,GA=5,MD=5,NC=5,SC=5,VA=5,WV=5,
         AL=6,KY=6,MS=6,TN=6, AR=7,LA=7,OK=7,TX=7, AZ=8,CO=8,ID=8,MT=8,NV=8,NM=8,UT=8,WY=8,
         AK=9,CA=9,HI=9,OR=9,WA=9, PR=0)
a[, division := unname(div[state])]
a <- a[is.na(state) | state != "PR"]
setorder(a, cbsa, year)
fwrite(a, file.path("data", "panel_full.csv"))

nbal <- a[, .(n = uniqueN(year)), by = cbsa][n == length(YEARS), .N]
message(sprintf("Panel built: %d metro areas, %d observed in all 11 years.", uniqueN(a$cbsa), nbal))
