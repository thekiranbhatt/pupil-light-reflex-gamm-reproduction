"""Checks 1-3: reproduce three numbers/figures from the paper using the public data.

Paper:  Kanari & Tsutsumi (2026), Scientific Reports 16:17383
Data:   https://doi.org/10.5281/zenodo.18448054  (file: dataset_gamm_long_3s.csv)

What this script does
  1. Participant inclusion    -> the paper keeps 39 of 44 people
  2. Split-half reliability   -> the paper reports r = 0.89
  3. Average pupil waveform   -> the shape behind the paper's Figure 1

What it does NOT do
  - The statistical model (GAMM). That is in ../r/run_m1.R
  - The raw 500 Hz signal processing. The public file is already cleaned,
    averaged over both eyes, and reduced to 100 Hz, so those steps cannot be
    repeated from it.

Usage (from the repository root):
    python python/reproduce_checks.py data/dataset_gamm_long_3s.csv
"""
import os
import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/dataset_gamm_long_3s.csv"
OUT_DIR = "results/python"
os.makedirs(OUT_DIR, exist_ok=True)

MIN_VALID_WHITE_TRIALS = 6   # the paper's rule: at least 6 of 10 White trials
COLOURS = ["White", "Red", "Green", "Blue"]


def spearman_brown(r):
    """Correct a half-vs-half correlation to estimate full-length reliability."""
    return 2 * r / (1 + r)


# ---------------------------------------------------------------------------
# Load the data and build a table with one row per trial
# ---------------------------------------------------------------------------
data = pd.read_csv(DATA_PATH)

# A trial is "valid" in two senses, and the file treats them differently:
#   flag_ok  : the authors' rejection flag says the trial was kept
#   has_data : the trial has at least one usable sample in the 0-3 s window
# 97 trials are flagged as kept but are completely empty, so the two differ.
trials = (data.groupby(["Subject_ID", "Trial_ID"])
              .agg(colour=("CondName", "first"),
                   rejected_flag=("TrialRejected_3s", "first"),
                   n_usable_samples=("SampleValid_3s", "sum"))
              .reset_index())
trials["flag_ok"] = ~trials.rejected_flag
trials["has_data"] = trials.n_usable_samples > 0
trials.to_csv(f"{OUT_DIR}/trial_table.csv", index=False)

# ---------------------------------------------------------------------------
# Check 1: who is included?
# ---------------------------------------------------------------------------
white = trials[trials.colour == "White"]
white_ok_by_flag = white.groupby("Subject_ID").flag_ok.sum()
white_ok_by_data = white.groupby("Subject_ID").has_data.sum()

# The paper's count of 39 follows the flag, so we use it for inclusion.
included = white_ok_by_flag[white_ok_by_flag >= MIN_VALID_WHITE_TRIALS].index
strict = white_ok_by_data[white_ok_by_data >= MIN_VALID_WHITE_TRIALS].index

print("CHECK 1: participant inclusion")
print(f"  people in file:                         {white_ok_by_flag.size}")
print(f"  included (flag rule, as in the paper):  {len(included)}   (paper: 39)")
print(f"  included if only non-empty trials count: {len(strict)}")
print(f"  excluded IDs (flag rule): "
      f"{sorted(white_ok_by_flag[white_ok_by_flag < MIN_VALID_WHITE_TRIALS].index)}")
print(f"  kept by the flag but with < 6 non-empty White trials: "
      f"{sorted(set(included) - set(strict))}")

# From here on, use only the included people and non-empty trials.
data = data.merge(trials[["Subject_ID", "Trial_ID", "has_data"]],
                  on=["Subject_ID", "Trial_ID"])
data = data[data.Subject_ID.isin(included) & data.has_data]

# ---------------------------------------------------------------------------
# Check 2: split-half reliability of the average pupil response (0-3 s)
#
# Idea: if the measurement is stable, a person's average over half of their
# trials should predict their average over the other half. We correlate the
# two halves across people, then apply the Spearman-Brown correction.
#
# The paper says "odd vs even trials" but not exactly how, so we try
# several reasonable readings and report all of them.
# ---------------------------------------------------------------------------
trial_means = (data.groupby(["Subject_ID", "CondName", "Trial_ID"])
                   .Pupil_Combined.mean().dropna().reset_index())

# order of each presentation within its colour, counting every trial of that colour
order_all = (trials.sort_values(["Subject_ID", "Trial_ID"])
                   .assign(order_all=lambda t: t.groupby(["Subject_ID", "colour"]).cumcount())
                   [["Subject_ID", "Trial_ID", "order_all"]])
trial_means = trial_means.merge(order_all, on=["Subject_ID", "Trial_ID"])
# order among the usable trials only
trial_means["order_valid"] = trial_means.groupby(["Subject_ID", "CondName"]).cumcount()


def split_half(df, order_col, group_cols):
    """Average each half per group, correlate across groups, return (n, r, r_corrected)."""
    half = np.where(df[order_col] % 2 == 0, "odd", "even")
    halves = (df.assign(half=half)
                .groupby(group_cols + ["half"]).Pupil_Combined.mean()
                .unstack("half").dropna())
    r = np.corrcoef(halves.odd, halves.even)[0, 1]
    return len(halves), r, spearman_brown(r)


per_person_colour = ["Subject_ID", "CondName"]
rows = []
# Reading A (main): odd/even by order of the 10 presentations of each colour
for colour, g in trial_means.groupby("CondName"):
    n, r, rc = split_half(g, "order_all", ["Subject_ID"])
    rows.append((f"A: {colour} only", n, r, rc))
n, r, rc = split_half(trial_means, "order_all", per_person_colour)
rows.append(("A: all colours pooled", n, r, rc))
# Reading B: odd/even among the usable trials only
n, r, rc = split_half(trial_means, "order_valid", per_person_colour)
rows.append(("B: usable trials only, pooled", n, r, rc))
# Reading C: odd/even by the trial number in the whole session
n, r, rc = split_half(trial_means.assign(order_trial=trial_means.Trial_ID), "order_trial", per_person_colour)
rows.append(("C: session trial number, pooled", n, r, rc))
# Reading D: one value per person (colours averaged together)
n, r, rc = split_half(trial_means.assign(order_trial=trial_means.Trial_ID), "order_trial", ["Subject_ID"])
rows.append(("D: colours merged, per person", n, r, rc))

reliability = pd.DataFrame(rows, columns=["reading", "n", "r_raw", "r_corrected"])

# Reading E: 200 random splits (no odd/even at all)
rng = np.random.default_rng(42)
random_rc = []
for _ in range(200):
    half = rng.integers(0, 2, len(trial_means))
    h = (trial_means.assign(half=half)
         .groupby(per_person_colour + ["half"]).Pupil_Combined.mean()
         .unstack("half").dropna())
    random_rc.append(spearman_brown(np.corrcoef(h[0], h[1])[0, 1]))
reliability.loc[len(reliability)] = ["E: 200 random splits (median)", len(h),
                                     np.nan, float(np.median(random_rc))]

print("\nCHECK 2: split-half reliability of mean pupil change, 0-3 s (paper: 0.89)")
print(reliability.round(3).to_string(index=False))
reliability.to_csv(f"{OUT_DIR}/split_half_reliability.csv", index=False)

# ---------------------------------------------------------------------------
# Check 3: the average pupil waveform for each flash colour
#
# Average within each person first, then across people, so every person
# counts equally. Bands are +/- 1.96 standard errors across people.
# These are RAW averages. The paper's Figure 1 shows MODEL predictions.
# ---------------------------------------------------------------------------
per_person = (data.groupby(["CondName", "Subject_ID", "Time_s"])
                  .Pupil_Combined.mean().reset_index())
waveforms = (per_person.groupby(["CondName", "Time_s"]).Pupil_Combined
                       .agg(["mean", "sem"]).reset_index())
waveforms.to_csv(f"{OUT_DIR}/mean_waveforms.csv", index=False)

palette = {"White": "#52514e", "Red": "#eb6834", "Green": "#2a9d5c", "Blue": "#2a78d6"}
fig, ax = plt.subplots(figsize=(7, 4.2))
for colour in COLOURS:
    g = waveforms[waveforms.CondName == colour]
    ax.plot(g.Time_s, g["mean"], color=palette[colour], lw=2, label=colour)
    ax.fill_between(g.Time_s, g["mean"] - 1.96 * g["sem"], g["mean"] + 1.96 * g["sem"],
                    color=palette[colour], alpha=0.15, lw=0)
ax.axhline(0, color="#e6e5e1", lw=1)
ax.set_xlabel("Time after the 100 ms flash (s)")
ax.set_ylabel("Change in pupil size vs. baseline")
ax.set_title(f"Average pupil response by flash colour (n = {len(included)}, raw averages)")
ax.legend(frameon=False)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/mean_waveforms.png", dpi=160)

landmarks = []
for colour, g in waveforms.groupby("CondName"):
    lowest = g["mean"].idxmin()
    landmarks.append((colour, g.loc[lowest, "Time_s"], g.loc[lowest, "mean"],
                      g[g.Time_s == 3.0]["mean"].iloc[0]))
landmarks = pd.DataFrame(landmarks, columns=["colour", "time_of_lowest_s",
                                             "lowest_value", "value_at_3s"])
print("\nCHECK 3: landmarks of the average waveform")
print(landmarks.round(3).to_string(index=False))
landmarks.to_csv(f"{OUT_DIR}/landmarks.csv", index=False)
