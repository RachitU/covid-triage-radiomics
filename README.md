# CT-based Patient Triage of COVID-19 — Sample Mini-Project (UE24CS352A)

> **FACULTY SAMPLE SOLUTION — for illustration only.**
> This repository shows students what a complete mini-project submission looks like
> (code, README, write-up, slides). It uses **synthetic data**. The metrics it reports have
> **no clinical meaning** and must not be quoted as real results. Do not copy this project
> for your own problem statement; use it for structure and standards.

## Problem statement

Predict, at hospital admission, which COVID-19 patients will go on to (1) be admitted to the ICU,
(2) need mechanical ventilation (MV), or (3) die in hospital, using CT radiomics features,
clinical features and lab results. Based on:

* Zhan & Li, *CT-based Patient Triage of COVID-19: Radiomics Prediction of ICU Admission,
  Mechanical Ventilation, and Death of Patients*, Stanford CS229, Spring 2020
  ([report](https://cs229.stanford.edu/proj2020spr/report/Zhan_Li.pdf),
  [poster](https://cs229.stanford.edu/proj2020spr/poster/Zhan_Li.pdf)).

## Dataset

The paper used private hospital data (~3,500 patients, 39 hospitals), which is not public.
This sample uses `src/generate_synthetic_data.py` to create a **synthetic** dataset with the
same structure and similar outcome prevalences (counts are random draws, so they differ slightly from the paper's 96/55/32 and 60/39/29):

| | n | ICU | MV | Death |
|---|---|---|---|---|
| Cohort 1 (development) | 1662 | 93 | 47 | 31 |
| Cohort 2 (external validation) | 700 | 57 | 45 | 32 |

Columns: `clin_*` (demographics, symptoms, comorbidities), `lab_*` (7 blood tests),
`rad_*` (100 radiomics features), `rscore` (0-4 radiologist score), outcomes `y_icu`, `y_mv`,
`y_death`, and `cohort`. Cohort 2 has a mild covariate shift to mimic a later admission period.

## Method

1. Five data configurations: **Radiom**, **RadiomClin**, **RadiomClinLab**, **ClinLab**, **RScore**.
2. Feature engineering: none (class-weighted), **SMOTEENN**, **SMOTEENN + LASSO** selection.
3. Models: Logistic Regression, Random Forest, SVM, MLP, LightGBM.
4. Cohort 1 is split 70/30. The best (feature engineering, model) pair per task and data
   configuration is chosen by 3-fold stratified CV AUROC **on the 70% split only**.
5. Selected models are scored on the 30% test split, refit on all of cohort 1, then validated on
   cohort 2 with 30 bootstrap resamples, 95% intervals and paired one-sided t-tests.

Deliberate difference from the paper: the paper chose models using the 30% test split; here the
test split and cohort 2 never influence model selection.

## Setup and run

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python src/generate_synthetic_data.py                  # creates data/synthetic_covid_triage.csv
python src/pipeline.py --data data/synthetic_covid_triage.csv --out results   # ~5 min on 2 CPU cores
```

Outputs in `results/`: `table1_cohort1_test.csv`, `table2_cohort2.csv`,
`table3_bootstrap_summary.csv`, `table4_paired_ttests.csv`, `table5_top_features.csv`,
`selected_models.json`, `cv_grid_all.csv`, and `figures/` (ROC/PR curves, bootstrap box plots,
feature importance). Everything is seeded (`SEED = 42`), so reruns reproduce the same numbers.

Live demo: `python demo.py` loads the data, fits one model, and prints a risk score for a few patients.

## Repository layout

```
src/generate_synthetic_data.py   synthetic cohort generator
src/pipeline.py                  full experiment (selection, validation, bootstrap, figures)
demo.py                          quick live demo for the review session
results/                         tables and figures produced by pipeline.py
docs/                            2-page write-up (PDF) and review slides
```

## Rebuilding the write-up and slides

```bash
python docs/build_writeup.py       # needs reportlab; reads results/*.csv, writes docs/COVID_Triage_Writeup.pdf
node docs/build_deck.js            # needs pptxgenjs; reads docs/deck_data.json
```

## Limitations

* Synthetic data: results show the method works mechanically, not that it works clinically.
* Cohort 2 has few positive deaths/MV cases, so intervals are wide.
* No hyperparameter search beyond fixed sensible defaults, to keep the demo fast.
