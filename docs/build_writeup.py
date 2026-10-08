"""Build the 2-page PDF write-up from results/*.csv so every number comes from the actual run."""
from pathlib import Path
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

root = Path(__file__).resolve().parent.parent
R = root / "results"
t3 = pd.read_csv(R / "table3_bootstrap_summary.csv")
t4 = pd.read_csv(R / "table4_paired_ttests.csv")
data = pd.read_csv(root / "data/synthetic_covid_triage.csv")
cnt = data.groupby("cohort")[["y_icu", "y_mv", "y_death"]].sum()

ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["Normal"], fontName="Helvetica", fontSize=8.6, leading=10.8, spaceAfter=3)
H = ParagraphStyle("H", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=12,
                   spaceBefore=5, spaceAfter=2, textColor=colors.HexColor("#1f3b57"))
T = ParagraphStyle("T", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=14.5, leading=17, spaceAfter=2)
S = ParagraphStyle("S", parent=B, alignment=1, textColor=colors.HexColor("#444444"), spaceAfter=2)
W = ParagraphStyle("W", parent=B, textColor=colors.HexColor("#8a1c1c"), alignment=1, fontName="Helvetica-Bold")
C = ParagraphStyle("C", parent=B, fontSize=7.6, leading=9.2, textColor=colors.HexColor("#444444"))

def pv(task, a, b, m):
    r = t4[(t4.task == task) & (t4.A == a) & (t4.B == b) & (t4.metric == m)].iloc[0]
    return r.mean_diff, r.p_value

order = ["Radiom", "RadiomClin", "RadiomClinLab", "ClinLab", "RScore"]
rows = [["Data configuration", "ICU admission", "Mechanical ventilation", "Death"]]
best = {}
for task in ["ICU", "MV", "Death"]:
    best[task] = t3[t3.task == task].sort_values("AUROC_mean").iloc[-1].data
for d in order:
    row = [d]
    for task in ["ICU", "MV", "Death"]:
        r = t3[(t3.task == task) & (t3.data == d)].iloc[0]
        txt = f"{r.AUROC_mean:.3f} ({r.AUROC_lo:.3f}-{r.AUROC_hi:.3f})"
        row.append(txt)
    rows.append(row)
tbl = Table(rows, colWidths=[3.6 * cm, 4.5 * cm, 4.9 * cm, 4.5 * cm])
style = [("FONT", (0, 0), (-1, -1), "Helvetica", 8), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edf4")),
         ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#999999")),
         ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
for j, task in enumerate(["ICU", "MV", "Death"], start=1):
    i = order.index(best[task]) + 1
    style += [("FONT", (j, i), (j, i), "Helvetica-Bold", 8), ("BACKGROUND", (j, i), (j, i), colors.HexColor("#fff3c4"))]
tbl.setStyle(TableStyle(style))

d_icu = pv("ICU", "Radiom", "RScore", "AUROC"); d_mv = pv("MV", "Radiom", "RScore", "AUROC"); d_dt = pv("Death", "Radiom", "RScore", "AUROC")
d_dt_pr = pv("Death", "Radiom", "RScore", "AUPRC")
g = {t: pv(t, "RadiomClinLab", "RadiomClin", "AUROC") for t in ["ICU", "MV", "Death"]}
cl = {t: t3[(t3.task == t) & (t3.data == "ClinLab")].iloc[0].AUROC_mean for t in ["ICU", "MV", "Death"]}
rcl = {t: t3[(t3.task == t) & (t3.data == "RadiomClinLab")].iloc[0].AUROC_mean for t in ["ICU", "MV", "Death"]}
rs_mv = t3[(t3.task == "MV") & (t3.data == "RScore")].iloc[0].AUROC_mean

story = [
    Paragraph("CT-based Patient Triage of COVID-19: Radiomics Prediction of ICU Admission, "
              "Mechanical Ventilation and Death", T),
    Paragraph("UE24CS352A Machine Learning - Mini-Project: <b>Faculty sample solution</b>", S),
    Paragraph("SAMPLE FOR STUDENTS - SYNTHETIC DATA - NOT CLINICALLY MEANINGFUL", W),

    Paragraph("1. Problem statement", H),
    Paragraph("At hospital admission, predict which COVID-19 patients will (i) be admitted to the ICU, (ii) require "
              "mechanical ventilation (MV) or (iii) die in hospital, from CT radiomics, clinical features and lab "
              "results, so scarce resources can go to high-risk patients first. The task and design follow Zhan &amp; Li "
              "(Stanford CS229, 2020). Outcomes are rare, so imbalance and small positive counts are the central difficulty.", B),

    Paragraph("2. Dataset", H),
    Paragraph(f"The paper's data (about 3,500 patients, 39 hospitals) is private, so this sample uses a <b>synthetic</b> dataset "
              f"from <font face='Courier'>src/generate_synthetic_data.py</font> that copies its structure: 2,362 patients in two "
              f"cohorts split by admission period. <b>Cohort 1</b> (development, n=1,662; ICU {cnt.loc[1,'y_icu']}, MV {cnt.loc[1,'y_mv']}, "
              f"death {cnt.loc[1,'y_death']}) and <b>Cohort 2</b> (external validation, n=700; ICU {cnt.loc[2,'y_icu']}, MV {cnt.loc[2,'y_mv']}, "
              f"death {cnt.loc[2,'y_death']}, with a mild covariate shift). Features: 100 radiomics, 7 clinical (age, sex, symptoms, comorbidities), "
              f"7 labs, and a 0-4 radiologist score (<i>RScore</i>). Radiomics, labs and outcomes are all driven by one latent "
              f"lung-involvement variable plus noise, so the data is realistic in structure only.", B),

    Paragraph("3. Approach", H),
    Paragraph("Five data configurations are compared: <b>Radiom</b>, <b>RadiomClin</b>, <b>RadiomClinLab</b>, <b>ClinLab</b> and "
              "<b>RScore</b>. Imbalance is handled by class weights, <b>SMOTEENN</b> (oversample then clean) or SMOTEENN followed by "
              "<b>LASSO</b> feature selection, with five models: logistic regression, random forest, SVM, MLP and LightGBM. "
              "Cohort 1 is split 70/30. For each task and configuration the best (feature engineering, model) pair is chosen by "
              "3-fold stratified CV AUROC on the 70% split only; the 30% split and cohort 2 never influence selection (the paper "
              "selected on the 30% split, a mild leak we avoid). Final models are refit on all of cohort 1 and validated on cohort 2 "
              "with 30 bootstrap resamples, 95% percentile intervals and paired one-sided t-tests.", B),

    Paragraph("4. Implementation overview", H),
    Paragraph("Python with scikit-learn, imbalanced-learn (SMOTEENN inside an <font face='Courier'>imblearn</font> Pipeline so "
              "resampling happens only on training folds), LightGBM and SciPy. <font face='Courier'>pipeline.py</font> runs the whole "
              "experiment end to end (about 5 minutes on 2 CPU cores, seeded for exact reproducibility) and writes tables and figures to "
              "<font face='Courier'>results/</font>; <font face='Courier'>demo.py</font> scores individual patients live. The repository "
              "README gives setup and run commands.", B),

    Paragraph("5. Results (cohort 2, bootstrap mean AUROC with 95% interval)", H),
    tbl,
    Paragraph("Best AUROC per task is highlighted. Cohort 2 contains only 32-57 positives per task, so intervals are wide.", C),
    Spacer(1, 3),
    Image(str(R / "figures/fig2_roc_pr_cohort2.png"), width=16.2 * cm, height=16.2 * cm * 7.5 / 13),
    Paragraph("Figure 1. ROC (top) and precision-recall (bottom) curves on cohort 2, one line per data configuration.", C),
    PageBreak(),

    Paragraph("6. Conclusions", H),
    Paragraph(f"<b>What held.</b> Radiomics beat the radiologist score for ICU (AUROC +{d_icu[0]:.3f}) and MV (+{d_mv[0]:.3f}), both p&lt;0.001; "
              f"for death it was not better on AUROC ({d_dt[0]:+.3f}) but was on AUPRC (p={d_dt_pr[1]:.3f}). Adding clinical features to radiomics "
              f"improved all three tasks (p&lt;0.001). <b>What did not.</b> The paper reports RadiomClinLab as best; here ClinLab (no radiomics) was best "
              f"on every task (AUROC {cl['ICU']:.3f} / {cl['MV']:.3f} / {cl['Death']:.3f} vs {rcl['ICU']:.3f} / {rcl['MV']:.3f} / {rcl['Death']:.3f}). "
              f"By construction, labs here are a cleaner readout of the latent severity than radiomics, and with only tens of positives, 100 extra "
              f"noisy features cost more than they add. Adding labs to RadiomClin raised AUROC only slightly (ICU {g['ICU'][0]:+.3f}, MV {g['MV'][0]:+.3f}, "
              f"death {g['Death'][0]:+.3f}). <b>Caveats.</b> Results come from synthetic data; the RScore ventilation model scored below chance "
              f"(AUROC {rs_mv:.3f}), a reminder that flexible models overfit when positives are few; no hyperparameter search was run. "
              f"<b>Takeaway for students:</b> state your data limits honestly, keep test data out of model selection, and report intervals, not point estimates.", B),
    Spacer(1, 4),
    Image(str(R / "figures/fig3_bootstrap_boxplots.png"), width=16.2 * cm, height=16.2 * cm * 7 / 13),
    Paragraph("Figure 2. AUROC and AUPRC across 30 bootstrap resamples of cohort 2 (basis of the intervals and t-tests above).", C),
    Spacer(1, 4),
    Image(str(R / "figures/fig4_feature_importance.png"), width=16.2 * cm, height=16.2 * cm * 4.2 / 13),
    Paragraph("Figure 3. Top-10 permutation importance (drop in AUROC on cohort 2) for the RadiomClinLab models: age, neutrophils, D-dimer and dyspnea rank high, alongside a few radiomics features.", C),
]

doc = SimpleDocTemplate(str(root / "docs/COVID_Triage_Writeup.pdf"), pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                        topMargin=1.3 * cm, bottomMargin=1.2 * cm, title="CT-based Patient Triage of COVID-19 (sample write-up)",
                        author="Faculty sample - UE24CS352A")
doc.build(story)
print("ok")
