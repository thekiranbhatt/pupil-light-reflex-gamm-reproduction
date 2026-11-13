# Data

The data are **not** included in this repository (the main file is about 124 MB).
They belong to Kanari & Tsutsumi and are public on Zenodo:

https://doi.org/10.5281/zenodo.18448054

## Get it

1. Open the link above and download the files.
2. Put `dataset_gamm_long_3s.csv` in this `data/` folder.
   (`stimulus_metrics_condition_mean_sd.csv` is optional; it lists the brightness and
   colour measurements of each flash.)

## What is in `dataset_gamm_long_3s.csv`

One row per 10 ms time step, for each trial of each person (44 people, 40 trials each,
0 to 3 seconds after the flash). The columns used here:

| Column | Meaning |
|---|---|
| `Subject_ID`, `Trial_ID` | person and trial number |
| `CondName` | flash colour: White, Red, Green or Blue |
| `Time_s` | seconds after the flash starts |
| `Pupil_Combined` | change in pupil size relative to just before the flash (0 = unchanged, -0.1 = 10% smaller) |
| `TrialRejected_3s`, `SampleValid_3s` | the authors' quality flags |
| `AASP R/K/S/A` | four sensory-profile questionnaire scores |

## Licence note

The Zenodo record lists the licence as CC0 1.0 Universal, and the `LICENSE` file inside the
deposit is the CC0 text. The deposit's README says CC BY 4.0, which does not match. Cite the
paper and the dataset in any case.
