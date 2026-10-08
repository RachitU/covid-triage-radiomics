"""Quick live demo: train on cohort 1, score a few unseen cohort 2 patients (SYNTHETIC data)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))
from pipeline import feature_sets, make_model  # noqa: E402

df = pd.read_csv(Path(__file__).parent / "data" / "synthetic_covid_triage.csv")
cols = feature_sets(df)["RadiomClinLab"]
c1, c2 = df[df.cohort == 1], df[df.cohort == 2]

print("Training ICU-admission model (SMOTEENN + LASSO + LR) on cohort 1 ...")
model = make_model("smoteenn_lasso", "LR").fit(c1[cols].values, c1["y_icu"].values)

sample = c2.sample(8, random_state=1)
risk = model.predict_proba(sample[cols].values)[:, 1]
out = pd.DataFrame({"patient": sample["patient_id"].values, "age": sample["clin_age"].values,
                    "predicted ICU risk": risk.round(3), "actual ICU": sample["y_icu"].values})
print(out.sort_values("predicted ICU risk", ascending=False).to_string(index=False))
print("\n(Synthetic data - for teaching only, not clinical use.)")
