# Notice and credits

## The paper and the data

Kanari, K. & Tsutsumi, T. (2026). Sensory traits are associated with global differences in
the pupillary light reflex waveform in young adults. *Scientific Reports* 16:17383.
https://doi.org/10.1038/s41598-026-48654-5

Data and analysis code: https://doi.org/10.5281/zenodo.18448054

## Code taken from the authors

`r/run_m1.R` reuses the authors' data preparation and the formula of model M1 from their
script `gamm_pipeline_main.R`. According to the README of their deposit, the code is
released under the **MIT licence** and the data under **CC BY 4.0**.

The MIT licence requires that the original copyright notice stays with the copied code.
**Before publishing this repository:** open the Zenodo record, find the licence text that
belongs to the code, and copy its copyright line into this file. The `LICENSE` file inside
the deposit was the CC0 text, which does not match the README, so do not assume. Check the
record page.

## What is mine

The comments, the trimming to model M1, the prediction and plotting step in `r/run_m1.R`,
and everything in `python/`.

This repository is a learning exercise in following a published analysis. It is not
affiliated with the authors and makes no claim of a new finding.
