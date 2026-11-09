# =============================================================================
# 03_tables_figures.R
# Writes the manuscript tables (CSV) and figures (PNG), and checks the R
# estimates against the values printed in the manuscript.
# Input: output/results.rds   Output: output/tables/, output/figures/
# =============================================================================
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })
res <- readRDS(file.path("output", "results.rds"))
dir.create(file.path("output", "tables"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path("output", "figures"), recursive = TRUE, showWarnings = FALSE)

stars <- function(p) fifelse(p < 0.01, "**", fifelse(p < 0.05, "*", ""))
cell  <- function(b, se, p = 1) sprintf("%.3f (%.3f)%s", b, se, stars(p))

# ---- Tables -----------------------------------------------------------------
t2 <- res$table2[, .(Variable = variable, Mean = round(mean, 2), SD = round(sd, 2),
                     Min = round(min, 2), Max = round(max, 2))]
t3 <- res$table3[, .(Outcome = outcome, `Shock (D)` = cell(D_b, D_se, D_p),
                     `D x regulation` = cell(DxR_b, DxR_se, DxR_p), Observations = N, Metros = metros)]
t4 <- res$table4[, .(Outcome = outcome, `Remote work (W)` = cell(W_b, W_se, W_p),
                     `W x regulation` = cell(WxR_b, WxR_se, WxR_p), Regulation = cell(R_b, R_se, R_p),
                     R2 = round(R2, 2), N = N)]
t5 <- res$table5[, .(Specification = specification, Metros = metros,
                     `Burden >30%` = cell(burden30_b, burden30_se), `Log permits` = cell(ln_permits_b, ln_permits_se),
                     `Log real rent` = cell(ln_rent_b, ln_rent_se))]
fwrite(t2, file.path("output", "tables", "table2_descriptives.csv"))
fwrite(t3, file.path("output", "tables", "table3_annual_panel.csv"))
fwrite(t4, file.path("output", "tables", "table4_long_difference.csv"))
fwrite(t5, file.path("output", "tables", "table5_robustness.csv"))
fwrite(res$robustB, file.path("output", "tables", "robustness_long_difference.csv"))

# ---- Figure 1: trends by regulation tercile -------------------------------
tr <- melt(res$trends, id.vars = c("tercile", "year"), variable.name = "measure")
tr[, measure := factor(measure, c("burden30", "real_rent", "permits_per_1k"),
                       c("A. Renters paying >30% of income (%)", "B. Real median gross rent (2024 $)",
                         "C. Permits per 1,000 households"))]
tr[, period := fifelse(year <= 2019, "pre", "post")]
pal <- c("Least restrictive" = "#86b6ef", "Middle" = "#2a78d6", "Most restrictive" = "#104281")
fig1 <- ggplot(tr, aes(year, value, colour = tercile, shape = tercile,
                       group = interaction(tercile, period))) +
  annotate("rect", xmin = 2019.5, xmax = 2020.5, ymin = -Inf, ymax = Inf, fill = "#e4e3df") +
  geom_line(linewidth = 0.8) + geom_point(size = 1.8) +
  facet_wrap(~measure, scales = "free_y") +
  scale_colour_manual(values = pal, name = NULL) + scale_shape_manual(values = c(16, 15, 17), name = NULL) +
  scale_x_continuous(breaks = c(2013, 2016, 2019, 2022)) +
  labs(x = NULL, y = NULL, caption = paste("Shaded band marks 2020 (no standard ACS 1-year estimates).",
                                            "Metros grouped by tercile of the 2018 WRLURI.")) +
  theme_minimal(base_size = 9, base_family = "serif") +
  theme(legend.position = "bottom", panel.grid.minor = element_blank(), panel.grid.major.x = element_blank(),
        strip.text = element_text(hjust = 0), plot.caption = element_text(hjust = 0, colour = "#52514e"))
ggsave(file.path("output", "figures", "figure1_trends.png"), fig1, width = 7.5, height = 3.4, dpi = 300, bg = "white")

# ---- Figure 2: event study --------------------------------------------------
fig2 <- ggplot(res$event, aes(year, b)) +
  annotate("rect", xmin = 2019.7, xmax = 2020.3, ymin = -Inf, ymax = Inf, fill = "#e4e3df") +
  geom_hline(yintercept = 0, colour = "#52514e", linewidth = 0.4) +
  geom_linerange(aes(ymin = b - 1.96 * se, ymax = b + 1.96 * se), colour = "#86b6ef", linewidth = 1.2) +
  geom_point(colour = "#2a78d6", size = 2.4) +
  scale_x_continuous(breaks = res$event$year) +
  labs(x = NULL, y = "Coefficient on remote work x regulation\n(pp. of renters burdened)",
       caption = "Points are estimates relative to 2019 with 95% confidence intervals; standard errors clustered by metro.") +
  theme_minimal(base_size = 9, base_family = "serif") +
  theme(panel.grid.minor = element_blank(), panel.grid.major.x = element_blank(),
        plot.caption = element_text(hjust = 0, colour = "#52514e"))
ggsave(file.path("output", "figures", "figure2_event_study.png"), fig2, width = 6, height = 3, dpi = 300, bg = "white")

# ---- Check against the manuscript -----------------------------------------
paper <- data.table(
  table = rep(c("Table 3: D x regulation", "Table 4: W x regulation"), each = 7),
  outcome = rep(res$table3$outcome, 2),
  paper_coef = c(0.002, -0.009, -0.017, -0.001, -0.255, -0.021, -0.041,
                 -0.027, -0.345, -0.078, -0.006, -0.262, -0.879, -0.326),
  paper_se   = c(0.009, 0.099, 0.073, 0.001, 0.124, 0.171, 0.082,
                 0.024, 0.199, 0.358, 0.004, 0.310, 0.628, 0.272))
paper[, R_coef := round(c(res$table3$DxR_b, res$table4$WxR_b), 3)]
paper[, R_se   := round(c(res$table3$DxR_se, res$table4$WxR_se), 3)]
paper[, match := fifelse(abs(R_coef - paper_coef) <= 0.0015 & abs(R_se - paper_se) <= 0.0025, "yes", "CHECK")]
fwrite(paper, file.path("output", "tables", "check_against_manuscript.csv"))
res$check <- paper
saveRDS(res, file.path("output", "results.rds"))
message(sprintf("Tables and figures written. Manuscript check: %d of %d estimates match.",
                sum(paper$match == "yes"), nrow(paper)))
