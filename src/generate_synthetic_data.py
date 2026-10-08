"""Generate a SYNTHETIC COVID-19 triage dataset mirroring the structure of
Zhan & Li (CS229, 2020): radiomics + clinical + lab + radiologist score, with three
outcomes (ICU admission, mechanical ventilation, in-hospital death).

The real study used private hospital data. Nothing here is real patient data and the
resulting metrics have NO clinical meaning; the data exists to make the pipeline
runnable and teachable.

Cohort sizes and outcome prevalences follow the paper:
    cohort 1 (development): n=1662, ICU 96, MV 55, death 32
    cohort 2 (validation) : n=700,  ICU 60, MV 39, death 29
Cohort 2 is generated with a mild covariate shift to mimic a later admission period.
"""
import argparse
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

N_RADIOMICS = 100
LAB_NAMES = ["ldh", "wbc", "neutrophil", "lymphocyte", "crp", "d_dimer", "potassium"]
CLIN_NAMES = ["age", "male", "dyspnea", "fever", "cough", "hypertension", "diabetes"]


def _calibrate(logit_core, target_n):
    """Intercept so that the expected number of positives equals target_n."""
    f = lambda b: expit(logit_core + b).sum() - target_n
    return brentq(f, -30, 10)


def make_params(rng):
    """Radiomics loadings are a property of the 'scanner/disease', shared by BOTH cohorts."""
    loadings = np.zeros(N_RADIOMICS)
    loadings[:12] = rng.uniform(0.5, 1.1, 12) * rng.choice([-1, 1], 12)
    block_load = rng.normal(0, 0.6, (8, N_RADIOMICS))
    drift = rng.normal(0, 0.3, N_RADIOMICS)
    return loadings, block_load, drift


def make_cohort(n, targets, rng, params, shift=0.0):
    # latent lung involvement L drives radiomics + radiologist score + outcomes
    age = np.clip(rng.normal(52 + 3 * shift, 15, n), 18, 95)
    male = rng.binomial(1, 0.5, n)
    dyspnea = rng.binomial(1, expit(-2.2 + 0.03 * (age - 50)), n)
    fever = rng.binomial(1, 0.55, n)
    cough = rng.binomial(1, 0.6, n)
    htn = rng.binomial(1, expit(-2.2 + 0.05 * (age - 50)), n)
    dm = rng.binomial(1, expit(-2.6 + 0.04 * (age - 50)), n)

    L = 0.5 * dyspnea + 0.015 * (age - 50) + rng.normal(0, 1, n)  # lung involvement

    # labs (log-scale-ish), partly driven by L
    ldh = 230 + 55 * L + rng.normal(0, 60, n)
    wbc = 6.0 + 0.8 * L + rng.normal(0, 2.0, n)
    neut = 4.0 + 0.9 * L + rng.normal(0, 1.8, n)
    lymph = 1.4 - 0.25 * L + rng.normal(0, 0.45, n)
    crp = np.clip(15 + 14 * L + rng.normal(0, 18, n), 0.1, None)
    ddim = np.clip(0.6 + 0.35 * L + rng.normal(0, 0.5, n), 0.05, None)
    potas = 4.1 + rng.normal(0, 0.45, n)

    # radiomics: factor model; 12 informative features load on L, rest are noise blocks
    loadings, block_load, drift = params
    block = rng.normal(0, 1, (n, 8))                    # correlated nuisance blocks
    rad = L[:, None] * loadings[None, :] + block @ block_load + rng.normal(0, 1, (n, N_RADIOMICS))
    rad += shift * drift[None, :]                       # scanner/period drift (cohort 2 only)

    # radiologist score: 0-4 ordinal, noisy view of L (deliberately weaker than radiomics)
    rscore = np.clip(np.round(1.5 + 0.7 * L + rng.normal(0, 1.1, n)), 0, 4)

    # outcomes
    z = (0.045 * (age - 50) + 0.55 * L + 0.7 * dyspnea + 0.35 * htn + 0.2 * dm
         + 0.012 * (ldh - 230) / 10 + 0.012 * (crp - 15) / 5
         - 0.5 * (lymph - 1.4) + 0.15 * (neut - 4) + 0.25 * (ddim - 0.6))
    z = (z - z.mean()) / z.std()
    out = {}
    for name, (target, scale, age_extra) in {
        "icu": (targets[0], 1.7, 0.0),
        "mv": (targets[1], 1.9, 0.0),
        "death": (targets[2], 1.6, 0.35),
    }.items():
        core = scale * z + age_extra * (age - 50) / 15 + rng.normal(0, 0.6, n)
        b = _calibrate(core, target)
        out[name] = rng.binomial(1, expit(core + b))

    df = pd.DataFrame({
        "age": age.round(0), "male": male, "dyspnea": dyspnea, "fever": fever, "cough": cough,
        "hypertension": htn, "diabetes": dm,
        "ldh": ldh, "wbc": wbc, "neutrophil": neut, "lymphocyte": lymph,
        "crp": crp, "d_dimer": ddim, "potassium": potas,
    })
    df.columns = [f"clin_{c}" if c in CLIN_NAMES else f"lab_{c}" for c in df.columns]
    rad_df = pd.DataFrame(rad, columns=[f"rad_{i:03d}" for i in range(N_RADIOMICS)])
    df = pd.concat([df, rad_df], axis=1)
    df["rscore"] = rscore
    for k, v in out.items():
        df[f"y_{k}"] = v
    return df


def main(out_path="data/synthetic_covid_triage.csv", seed=42):
    rng = np.random.default_rng(seed)
    params = make_params(rng)
    c1 = make_cohort(1662, (96, 55, 32), rng, params, shift=0.0)
    c1["cohort"] = 1
    c2 = make_cohort(700, (60, 39, 29), rng, params, shift=1.0)
    c2["cohort"] = 2
    df = pd.concat([c1, c2], ignore_index=True)
    df.insert(0, "patient_id", [f"SYN{i:05d}" for i in range(len(df))])
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}: {df.shape}")
    print(df.groupby("cohort")[["y_icu", "y_mv", "y_death"]].agg(["sum", "mean"]).round(3))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/synthetic_covid_triage.csv")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.out, a.seed)
