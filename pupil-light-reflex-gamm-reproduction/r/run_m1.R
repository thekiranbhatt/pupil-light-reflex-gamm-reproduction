# =============================================================================
# Re-run of model M1 from Kanari & Tsutsumi (2026), Scientific Reports 16:17383
#
# WHAT THIS SCRIPT DOES
#   Fits the paper's main statistical model ("M1") to the authors' public data
#   and draws the model's predicted pupil response for each flash colour,
#   which is the counterpart of the paper's Figure 1.
#
# WHAT IT DOES NOT DO
#   The authors' full script also fits models M2, M3 and four "quadrant" models
#   and draws Figures 2-4. Those are not run here (see the README).
#
# WHERE THE CODE COMES FROM
#   The data preparation (steps 2-4) and the model formula (step 5) come from
#   the authors' script gamm_pipeline_main.R, released under the MIT licence:
#   https://doi.org/10.5281/zenodo.18448054
#   The trimming, the comments, and step 7 (predictions and plot) are mine.
#   See NOTICE.md for the licence details.
#
# HOW TO RUN (from the repository root)
#   Rscript r/run_m1.R
# or in Colab with the R runtime:  source("r/run_m1.R")
#
# STATUS
#   An earlier version of this script, with the same model code but different
#   variable names and comments, ran to completion in Colab (R runtime, mgcv 1.9-4).
#   This commented version has not been re-run.
#   The two model fits are slow (the data has about 410,000 rows).
# =============================================================================


# ---- 1. Settings ------------------------------------------------------------
DATA_FILE <- "data/dataset_gamm_long_3s.csv"   # download it from Zenodo (see data/README.md)
OUT_DIR   <- "results/r"

COLOURS         <- c("White", "Red", "Green", "Blue")
BIN_SECONDS     <- 0.01   # the data is binned into 10 ms steps
WINDOW_START    <- 0      # we analyse the first 3 seconds after the flash
WINDOW_END      <- 3
MIN_VALID_WHITE <- 6      # the paper keeps people with at least 6 of 10 good White trials

# "k" sets how wiggly each smooth curve is allowed to be (the authors' values for M1).
K_TIME         <- 60   # the overall average waveform
K_TIME_COLOUR  <- 20   # extra shape for each flash colour
K_TIME_FOR_TI  <- 60   # time part of the "trait x time" terms
K_TRAIT_FOR_TI <- 5    # trait part of the "trait x time" terms
K_PERSON       <- 10   # each person's own waveform shape

packages <- c("dplyr", "readr", "mgcv", "itsadug", "ggplot2")
missing  <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
if (length(missing) > 0) install.packages(missing)
invisible(lapply(packages, library, character.only = TRUE))

dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)


# ---- 2. Load the data and choose who is included ----------------------------
raw <- readr::read_csv(DATA_FILE, show_col_types = FALSE) %>%
  dplyr::filter(CondName %in% COLOURS) %>%
  dplyr::mutate(CondName = factor(CondName, levels = COLOURS))

# A person is included if at least 6 of their 10 White-flash trials were kept.
trials <- raw %>%
  dplyr::distinct(Subject_ID, Trial_ID, CondName, TrialRejected_3s)

included_ids <- trials %>%
  dplyr::filter(CondName == "White") %>%
  dplyr::group_by(Subject_ID) %>%
  dplyr::summarise(good_white_trials = sum(!TrialRejected_3s), .groups = "drop") %>%
  dplyr::filter(good_white_trials >= MIN_VALID_WHITE) %>%
  dplyr::pull(Subject_ID)
cat("People included:", length(included_ids), "(the paper reports 39)\n")

# Keep only usable measurements inside the 0-3 s window.
dat <- raw %>%
  dplyr::filter(Subject_ID %in% included_ids,
                Time_s >= WINDOW_START, Time_s <= WINDOW_END,
                SampleValid_3s == TRUE,
                !is.na(Pupil_Combined))


# ---- 3. Turn the questionnaire scores into two trait scores -----------------
# The sensory questionnaire (AASP) gives four scores per person. The paper
# combines them into two "axes" from Dunn's model of sensory processing:
#   LowTh  : how low a person's threshold for noticing sensations is
#   Active : how actively they respond to or manage sensations
standardise <- function(x) as.numeric(scale(x))   # mean 0, standard deviation 1

people <- dat %>%
  dplyr::distinct(Subject_ID, Sex_bin, age,
                  `AASP R`, `AASP K`, `AASP S`, `AASP A`) %>%
  dplyr::mutate(
    LowReg_z    = standardise(`AASP R`),   # Low Registration
    SensSeek_z  = standardise(`AASP K`),   # Sensation Seeking
    SensSens_z  = standardise(`AASP S`),   # Sensory Sensitivity
    SensAvoid_z = standardise(`AASP A`),   # Sensation Avoiding
    LowTh   = (SensSens_z + SensAvoid_z - LowReg_z - SensSeek_z) / 2,
    Active  = (SensSeek_z + SensAvoid_z - LowReg_z - SensSens_z) / 2,
    LowTh_z  = standardise(LowTh),
    Active_z = standardise(Active),
    age_z    = standardise(age)
  )

dat <- dat %>%
  dplyr::select(-Sex_bin, -age, -`AASP R`, -`AASP K`, -`AASP S`, -`AASP A`) %>%
  dplyr::left_join(people, by = "Subject_ID")


# ---- 4. Mark where each trial starts ---------------------------------------
# Neighbouring time points inside one trial are very similar. The model corrects
# for this ("AR(1)" errors) and needs to know where every trial begins.
dat <- dat %>%
  dplyr::arrange(Subject_ID, Trial_ID, Time_s) %>%
  dplyr::group_by(Subject_ID, Trial_ID) %>%
  dplyr::mutate(gap = Time_s - dplyr::lag(Time_s),
                AR.start = dplyr::row_number() == 1 | is.na(gap) | gap > (BIN_SECONDS * 1.1)) %>%
  dplyr::ungroup() %>%
  dplyr::mutate(Subject_ID = factor(Subject_ID),
                CondName   = factor(CondName, levels = COLOURS))


# ---- 5. Fit the model without the autocorrelation correction (M0) -----------
# Reading the formula, term by term:
#   CondName                    each flash colour can shift the whole curve up or down
#   s(Time_s)                   the average pupil response over time
#   s(Time_s, by = CondName)    how each colour's response shape differs
#   LowTh_z + Active_z          does a trait change the AVERAGE pupil size?
#   ti(Time_s, LowTh_z), ti(Time_s, Active_z)
#                               does a trait change the SHAPE of the response over time?
#                               (these are the paper's key terms)
#   age_z + Sex_bin             age and sex, as controls
#   s(Subject_ID, bs = "re")    every person gets their own baseline offset
#   s(Time_s, Subject_ID, bs = "fs")
#                               every person gets their own response shape
message("Fitting M0 (without autocorrelation correction). This is slow.")
m0 <- mgcv::bam(
  Pupil_Combined ~
    CondName +
    s(Time_s, k = K_TIME, bs = "cr") +
    s(Time_s, by = CondName, k = K_TIME_COLOUR, bs = "cr") +
    LowTh_z + Active_z +
    ti(Time_s, LowTh_z,  bs = c("cr", "tp"), k = c(K_TIME_FOR_TI, K_TRAIT_FOR_TI)) +
    ti(Time_s, Active_z, bs = c("cr", "tp"), k = c(K_TIME_FOR_TI, K_TRAIT_FOR_TI)) +
    age_z + Sex_bin +
    s(Subject_ID, bs = "re") +
    s(Time_s, Subject_ID, bs = "fs", k = K_PERSON),
  data = dat, method = "fREML", discrete = TRUE
)
saveRDS(m0, file.path(OUT_DIR, "m0.rds"))


# ---- 6. Estimate the autocorrelation, then refit as M1 ----------------------
# rho says how strongly each 10 ms measurement resembles the previous one.
# It is close to 1 here because the pupil changes smoothly.
rho <- itsadug::start_value_rho(m0)
cat(sprintf("rho = %.4f\n", rho))

message("Fitting M1 (with the autocorrelation correction). This is slow.")
m1 <- update(m0, rho = rho, AR.start = dat$AR.start)
saveRDS(m1, file.path(OUT_DIR, "m1.rds"))

capture.output(summary(m1),   file = file.path(OUT_DIR, "summary_M1.txt"))
capture.output(gam.check(m1), file = file.path(OUT_DIR, "gamcheck_M1.txt"))
print(summary(m1))
# Where to look in the summary:
#   "Parametric coefficients": colour shifts and the two trait main effects
#   "ti(LowTh_z,Time_s)" and "ti(Active_z,Time_s)": the trait-by-time shape effects


# ---- 7. Predicted waveform for each colour (my addition) --------------------
# We predict for an "average" person: trait scores, age and sex all set to zero,
# and the person-specific terms left out, so the curve describes the group.
time_grid  <- seq(WINDOW_START, WINDOW_END, by = BIN_SECONDS)
left_out   <- c("s(Subject_ID)", "s(Time_s,Subject_ID)")

predict_colour <- function(colour) {
  new_data <- data.frame(Time_s = time_grid,
                         CondName = factor(colour, levels = COLOURS),
                         LowTh_z = 0, Active_z = 0, age_z = 0, Sex_bin = 0,
                         Subject_ID = dat$Subject_ID[1])
  p <- predict(m1, newdata = new_data, exclude = left_out, se.fit = TRUE)
  data.frame(Time_s = time_grid, Condition = colour,
             fit   = as.numeric(p$fit),
             lower = as.numeric(p$fit) - 1.96 * as.numeric(p$se.fit),   # 95% band
             upper = as.numeric(p$fit) + 1.96 * as.numeric(p$se.fit))
}
predicted <- dplyr::bind_rows(lapply(COLOURS, predict_colour))
readr::write_csv(predicted, file.path(OUT_DIR, "m1_predicted_waveforms.csv"))

line_colours <- c(White = "#52514e", Red = "#eb6834", Green = "#2a9d5c", Blue = "#2a78d6")
plot_m1 <- ggplot2::ggplot(predicted, ggplot2::aes(Time_s, fit, colour = Condition, fill = Condition)) +
  ggplot2::geom_ribbon(ggplot2::aes(ymin = lower, ymax = upper), alpha = 0.15, colour = NA) +
  ggplot2::geom_line(linewidth = 1) +
  ggplot2::scale_colour_manual(values = line_colours) +
  ggplot2::scale_fill_manual(values = line_colours) +
  ggplot2::labs(x = "Time after the 100 ms flash (s)",
                y = "Predicted change in pupil size",
                title = "Model M1: predicted pupil response by flash colour") +
  ggplot2::theme_minimal()
ggplot2::ggsave(file.path(OUT_DIR, "m1_predicted_waveforms.png"), plot_m1,
                width = 7, height = 4.2, dpi = 160)

# Quick check: the lowest point of each curve. In the raw averages (Python
# scripts) White's lowest point is about -0.37 at about 0.87 s.
print(predicted %>%
        dplyr::group_by(Condition) %>%
        dplyr::slice_min(fit, n = 1) %>%
        dplyr::select(Condition, Time_s, fit))
