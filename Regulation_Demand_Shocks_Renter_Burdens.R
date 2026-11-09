# =============================================================================
# Regulation, Demand Shocks, and Renter Cost Burdens (2013-2024)
# MAIN SCRIPT - runs the whole analysis from the raw data.
#
# In RStudio: open Regulation_Demand_Shocks_Renter_Burdens.Rproj, open this
# file, and click "Source" (or press Ctrl+Shift+S).
#
#   data/raw/          source data (ACS, building permits, QCEW, Wharton, NZLUD, CPI, OMB)
#   R/01_build_panel.R builds data/panel_full.csv
#   R/02_analysis.R    estimates every model in the manuscript
#   R/03_tables_figures.R  writes output/tables/*.csv and output/figures/*.png
#   Regulation_Demand_Shocks_Renter_Burdens_report.Rmd  report with all tables and figures
# =============================================================================

# Work from the project folder
if (!interactive()) {
  args <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", args[grep("^--file=", args)])
  if (length(f)) setwd(dirname(normalizePath(f)))
}

# Install any missing packages
pkgs <- c("data.table", "fixest", "haven", "ggplot2", "knitr", "rmarkdown", "HonestDiD")
lib <- Sys.getenv("R_LIBS_USER")
if (nzchar(lib)) { dir.create(lib, recursive = TRUE, showWarnings = FALSE); .libPaths(c(lib, .libPaths())) }
miss <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
if (length(miss)) install.packages(miss, repos = "https://cloud.r-project.org")
if (!requireNamespace("HonestDiD", quietly = TRUE)) {   # fallback: install from the authors' GitHub
  if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes", repos = "https://cloud.r-project.org")
  remotes::install_github("asheshrambachan/HonestDiD")
}

cat("\n== Step 1: building the panel ==\n");      source(file.path("R", "01_build_panel.R"))
cat("\n== Step 2: estimating the models ==\n");   source(file.path("R", "02_analysis.R"))
cat("\n== Step 3: tables and figures ==\n");      source(file.path("R", "03_tables_figures.R"))
cat("\n== Step 4: additional robustness ==\n");  source(file.path("R", "04_robustness_extra.R"))

# Show the results in the console
res <- readRDS(file.path("output", "results.rds"))
cat("\nTable 3. Annual panel: shift-share shock x regulation\n");     print(t3)
cat("\nTable 4. Long difference 2019-2024: remote work x regulation\n"); print(t4)
cat("\nTable 5. Robustness of the shock x regulation interaction\n");  print(t5)
cat("\nCheck against the manuscript\n");                               print(res$check)
if (interactive()) { print(fig1); print(fig2) }

# Build the HTML report (needs pandoc, which comes with RStudio)
if (rmarkdown::pandoc_available()) {
  rmarkdown::render("Regulation_Demand_Shocks_Renter_Burdens_report.Rmd",
                    output_dir = "output", quiet = TRUE)
  cat("\nReport written to output/Regulation_Demand_Shocks_Renter_Burdens_report.html\n")
} else {
  cat("\nPandoc not found, so the HTML report was skipped. Open the .Rmd in RStudio and click Knit.\n")
}
