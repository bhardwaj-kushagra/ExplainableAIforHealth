# Canonical DLNM R script (Milestone 2)
# Reads processed parquet (if arrow installed) else CSV fallback.
# Fits quasi-Poisson model with crossbasis for temperature and humidity (0-21 day lag).
# Saves exposure-response and lag surface plots.

suppressPackageStartupMessages({
  library(dlnm)
  library(mgcv)
  library(data.table)
})

args <- commandArgs(trailingOnly = TRUE)
input <- ifelse(length(args) >= 1, args[[1]], 'data_processed/region_daily.parquet')
out_dir <- 'outputs'
if(!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

# Read data
if(grepl('parquet$', input)) {
  # Attempt arrow
  have_arrow <- requireNamespace('arrow', quietly=TRUE)
  if(have_arrow) {
    df <- as.data.table(arrow::read_parquet(input))
  } else {
    stop('arrow package required to read parquet. Install arrow or provide CSV.')
  }
} else {
  df <- fread(input)
}

# Ensure ordering
setorder(df, date)

# Crossbasis for temperature (natural cubic) and humidity (linear) with lag 0-21
cb.temp <- crossbasis(df$temp_mean, lag=21, argvar=list(fun='ns', df=4), arglag=list(fun='ns', df=4))
cb.hum  <- crossbasis(df$rel_humidity, lag=21, argvar=list(fun='ns', df=3), arglag=list(fun='ns', df=3))

# Fit quasi-Poisson GLM with day of week factor
model <- glm(admissions ~ cb.temp + cb.hum + factor(day_of_week), family=quasipoisson(), data=df)

# Predict exposure-response for temperature at lag 0-21 cumulatively
pred.temp <- crosspred(cb.temp, model, by=1)

png(file.path(out_dir,'dlnm_exposure_response.png'), width=900, height=600)
plot(pred.temp, xlab='Mean Temperature (C)', ylab='RR', main='DLNM Exposure-Response (Temperature)')
dev.off()

# Lag-response surface
png(file.path(out_dir,'dlnm_lag_surface.png'), width=900, height=600)
plot(pred.temp, xlab='Mean Temperature (C)', zlab='RR', main='DLNM Lag-Response Surface')
dev.off()

# Simple effect size summary for +3C increase around reference 20C
ref_temp <- 20
delta <- 3
temp_seq <- c(ref_temp, ref_temp + delta)
rr_ref <- pred.temp$allRRfit[which(pred.temp$x == ref_temp)]
rr_delta <- pred.temp$allRRfit[which(pred.temp$x == ref_temp + delta)]
rr_change <- rr_delta/rr_ref

summary_path <- file.path(out_dir,'dlnm_effect_summary.txt')
writeLines(c(
  paste('Reference temp:', ref_temp),
  paste('Increase (C):', delta),
  paste('Relative Risk Change:', round(rr_change,3))
), con=summary_path)

cat('[dlnm] Wrote plots and summary to outputs/\n')
