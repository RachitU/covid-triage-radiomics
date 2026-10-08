"""Radiomics-based COVID-19 triage pipeline (reference implementation).

Follows the design of Zhan & Li (CS229, 2020):
  * 5 data configurations: Radiom, RadiomClin, RadiomClinLab, ClinLab, RScore
  * feature engineering: none (class-weighted), SMOTEENN, SMOTEENN + LASSO selection
  * models: LR, RF, SVM, MLP, LightGBM
  * model selection by stratified CV on 70% of cohort 1
  * hold-out test on the other 30% of cohort 1
  * external validation on cohort 2 with 30 bootstrap resamples + paired one-sided t-tests

Deviation from the paper (deliberate): the paper picked the best model on the 30% test
split; here selection uses CV on the training split only, so the 30% test split and
cohort 2 stay untouched by model selection.

Usage:  python src/pipeline.py --data data/synthetic_covid_triage.csv --out results
"""
import argparse
import json
import warnings
from itertools import product
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from imblearn.combine import SMOTEENN
from imblearn.pipeline import Pipeline
from lightgbm import LGBMClassifier
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, precision_recall_curve,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")
SEED = 42
TASKS = {"ICU": "y_icu", "MV": "y_mv", "Death": "y_death"}
N_BOOT = 30


# ----------------------------------------------------------------------------- data
def feature_sets(df):
    rad = [c for c in df.columns if c.startswith("rad_")]
    clin = [c for c in df.columns if c.startswith("clin_")]
    lab = [c for c in df.columns if c.startswith("lab_")]
    return {
        "Radiom": rad,
        "RadiomClin": rad + clin,
        "RadiomClinLab": rad + clin + lab,
        "ClinLab": clin + lab,
        "RScore": ["rscore"],
    }


# ----------------------------------------------------------------------------- models
def make_model(fe, name):
    clf = {
        "LR": LogisticRegression(max_iter=2000, C=0.5,
                                 class_weight="balanced" if fe == "none" else None),
        "RF": RandomForestClassifier(n_estimators=200, min_samples_leaf=3, n_jobs=1,
                                     random_state=SEED,
                                     class_weight="balanced" if fe == "none" else None),
        "SVM": SVC(C=1.0, probability=True, random_state=SEED,
                   class_weight="balanced" if fe == "none" else None),
        "MLP": MLPClassifier(hidden_layer_sizes=(32,), alpha=1e-2, max_iter=400,
                             random_state=SEED),
        "LightGBM": LGBMClassifier(n_estimators=150, learning_rate=0.05, num_leaves=8,
                                   min_child_samples=10, subsample=0.8, colsample_bytree=0.8,
                                   random_state=SEED, verbose=-1, n_jobs=1,
                                   is_unbalance=(fe == "none")),
    }[name]
    steps = [("scale", StandardScaler())]
    if fe in ("smoteenn", "smoteenn_lasso"):
        steps.append(("resample", SMOTEENN(random_state=SEED)))
    if fe == "smoteenn_lasso":
        steps.append(("lasso", SelectFromModel(
            LogisticRegression(penalty="l1", solver="liblinear", C=0.5, max_iter=2000),
            threshold=1e-6)))
    steps.append(("clf", clf))
    return Pipeline(steps)


FES = ["none", "smoteenn", "smoteenn_lasso"]
MODELS = ["LR", "RF", "SVM", "MLP", "LightGBM"]


def select_best(X, y, data_name):
    """Stratified 3-fold CV AUROC over (feature-engineering, model) grid."""
    cv = StratifiedKFold(3, shuffle=True, random_state=SEED)
    # single-feature radiologist score: no point in LASSO selection
    fes = [f for f in FES if not (data_name == "RScore" and f == "smoteenn_lasso")]
    best, rows = None, []
    for fe, m in product(fes, MODELS):
        try:
            s = cross_val_score(make_model(fe, m), X, y, cv=cv, scoring="roc_auc", n_jobs=2).mean()
        except Exception:
            s = np.nan
        rows.append({"fe": fe, "model": m, "cv_auroc": s})
        if np.isfinite(s) and (best is None or s > best[2]):
            best = (fe, m, s)
    return best, pd.DataFrame(rows)


def metrics(y, p):
    return {"AUROC": roc_auc_score(y, p), "AUPRC": average_precision_score(y, p),
            "ACC": accuracy_score(y, (p >= 0.5).astype(int))}


# ----------------------------------------------------------------------------- main
def main(data, out):
    out = Path(out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(data)
    fsets = feature_sets(df)
    c1, c2 = df[df.cohort == 1].reset_index(drop=True), df[df.cohort == 2].reset_index(drop=True)

    selected, cohort1_rows, cv_rows = {}, [], []
    fitted, p_c2 = {}, {}

    for task, ycol in TASKS.items():
        tr_idx, te_idx = train_test_split(np.arange(len(c1)), test_size=0.3, random_state=SEED,
                                          stratify=c1[ycol])
        for dname, cols in fsets.items():
            Xtr, ytr = c1.loc[tr_idx, cols].values, c1.loc[tr_idx, ycol].values
            Xte, yte = c1.loc[te_idx, cols].values, c1.loc[te_idx, ycol].values
            (fe, m, cv_auc), grid = select_best(Xtr, ytr, dname)
            grid.insert(0, "data", dname); grid.insert(0, "task", task)
            cv_rows.append(grid)
            # refit selected config on the 70% train, score the 30% test
            mdl = make_model(fe, m).fit(Xtr, ytr)
            cohort1_rows.append({"task": task, "data": dname, "fe": fe, "model": m,
                                 "cv_auroc": cv_auc, **metrics(yte, mdl.predict_proba(Xte)[:, 1])})
            # final model: refit on ALL of cohort 1, evaluate on cohort 2
            final = make_model(fe, m).fit(c1[cols].values, c1[ycol].values)
            fitted[(task, dname)] = (final, cols)
            p_c2[(task, dname)] = final.predict_proba(c2[cols].values)[:, 1]
            selected[f"{task}/{dname}"] = {"fe": fe, "model": m, "cv_auroc": round(cv_auc, 4)}
            print(f"[{task:5s}] {dname:14s} -> {fe:15s} {m:9s} cv={cv_auc:.3f}", flush=True)

    pd.concat(cv_rows).to_csv(out / "cv_grid_all.csv", index=False)
    t1 = pd.DataFrame(cohort1_rows)
    t1.to_csv(out / "table1_cohort1_test.csv", index=False)
    json.dump(selected, open(out / "selected_models.json", "w"), indent=2)

    # ------------------------------------------------------ cohort 2 + bootstrap
    rng = np.random.default_rng(SEED)
    boot = {t: [] for t in TASKS}
    rows_c2, boot_rows = [], []
    for task, ycol in TASKS.items():
        y2 = c2[ycol].values
        idx_list = []
        while len(idx_list) < N_BOOT:                    # resamples need both classes
            idx = rng.integers(0, len(y2), len(y2))
            if 0 < y2[idx].sum() < len(idx):
                idx_list.append(idx)
        for dname in fsets:
            p = p_c2[(task, dname)]
            rows_c2.append({"task": task, "data": dname, **metrics(y2, p)})
            for b, idx in enumerate(idx_list):
                boot_rows.append({"task": task, "data": dname, "boot": b,
                                  "AUROC": roc_auc_score(y2[idx], p[idx]),
                                  "AUPRC": average_precision_score(y2[idx], p[idx])})
    t2 = pd.DataFrame(rows_c2); t2.to_csv(out / "table2_cohort2.csv", index=False)
    bt = pd.DataFrame(boot_rows); bt.to_csv(out / "bootstrap_cohort2.csv", index=False)

    summ = (bt.groupby(["task", "data"])
              .agg(AUROC_mean=("AUROC", "mean"), AUROC_lo=("AUROC", lambda s: s.quantile(.025)),
                   AUROC_hi=("AUROC", lambda s: s.quantile(.975)),
                   AUPRC_mean=("AUPRC", "mean")).reset_index())
    summ.to_csv(out / "table3_bootstrap_summary.csv", index=False)

    # paired one-sided t-tests (A better than B), same resamples
    pairs = [("Radiom", "RScore"), ("RadiomClin", "Radiom"),
             ("RadiomClinLab", "ClinLab"), ("RadiomClinLab", "RadiomClin")]
    trows = []
    for task in TASKS:
        for a, b in pairs:
            for met in ("AUROC", "AUPRC"):
                xa = bt[(bt.task == task) & (bt.data == a)].sort_values("boot")[met].values
                xb = bt[(bt.task == task) & (bt.data == b)].sort_values("boot")[met].values
                t, p = stats.ttest_rel(xa, xb, alternative="greater")
                trows.append({"task": task, "A": a, "B": b, "metric": met,
                              "mean_diff": (xa - xb).mean(), "p_value": p})
    pd.DataFrame(trows).to_csv(out / "table4_paired_ttests.csv", index=False)

    # ------------------------------------------------------ figures
    colors = {"Radiom": "#1b9e77", "RadiomClin": "#d95f02", "RadiomClinLab": "#7570b3",
              "ClinLab": "#e7298a", "RScore": "#666666"}
    fig, ax = plt.subplots(2, 3, figsize=(13, 7.5))
    for j, (task, ycol) in enumerate(TASKS.items()):
        y2 = c2[ycol].values
        for dname in fsets:
            p = p_c2[(task, dname)]
            fpr, tpr, _ = roc_curve(y2, p); pr, rc, _ = precision_recall_curve(y2, p)
            ax[0, j].plot(fpr, tpr, color=colors[dname], label=f"{dname} ({roc_auc_score(y2,p):.2f})")
            ax[1, j].plot(rc, pr, color=colors[dname])
        ax[0, j].plot([0, 1], [0, 1], "k:", lw=.8)
        ax[0, j].set_title(f"{task}: ROC (cohort 2)"); ax[0, j].set_xlabel("FPR"); ax[0, j].set_ylabel("TPR")
        ax[0, j].legend(fontsize=7, loc="lower right")
        ax[1, j].set_title(f"{task}: precision-recall"); ax[1, j].set_xlabel("Recall"); ax[1, j].set_ylabel("Precision")
        for r in (0, 1):
            ax[r, j].spines[["top", "right"]].set_visible(False)
    fig.suptitle("SYNTHETIC DATA - illustrative only", color="firebrick", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "figures/fig2_roc_pr_cohort2.png", dpi=170); plt.close(fig)

    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    order = list(fsets)
    for j, task in enumerate(TASKS):
        for i, met in enumerate(("AUROC", "AUPRC")):
            data_ = [bt[(bt.task == task) & (bt.data == d)][met].values for d in order]
            bp = ax[i, j].boxplot(data_, tick_labels=order, patch_artist=True)
            for patch, d in zip(bp["boxes"], order):
                patch.set_facecolor(colors[d]); patch.set_alpha(.6)
            ax[i, j].set_title(f"{task}: {met} ({N_BOOT} bootstraps)")
            ax[i, j].tick_params(axis="x", rotation=30, labelsize=8)
            ax[i, j].spines[["top", "right"]].set_visible(False)
    fig.suptitle("SYNTHETIC DATA - illustrative only", color="firebrick", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "figures/fig3_bootstrap_boxplots.png", dpi=170); plt.close(fig)

    # ------------------------------------------------------ feature importance (RadiomClinLab)
    imp_rows = []
    for task, ycol in TASKS.items():
        mdl, cols = fitted[(task, "RadiomClinLab")]
        r = permutation_importance(mdl, c2[cols].values, c2[ycol].values, scoring="roc_auc",
                                   n_repeats=10, random_state=SEED, n_jobs=2)
        imp = pd.Series(r.importances_mean, index=cols).sort_values(ascending=False).head(10)
        for f, v in imp.items():
            imp_rows.append({"task": task, "feature": f, "perm_importance_auroc": v})
    imp_df = pd.DataFrame(imp_rows); imp_df.to_csv(out / "table5_top_features.csv", index=False)

    fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
    for j, task in enumerate(TASKS):
        s = imp_df[imp_df.task == task].iloc[::-1]
        ax[j].barh(s.feature, s.perm_importance_auroc, color="#7570b3")
        ax[j].set_title(f"{task}: top-10 permutation importance"); ax[j].spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(out / "figures/fig4_feature_importance.png", dpi=170); plt.close(fig)

    print("\nDone. Outputs in", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/synthetic_covid_triage.csv")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    main(a.data, a.out)
