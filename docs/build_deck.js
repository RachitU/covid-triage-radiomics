// Builds COVID_Triage_Review_Slides.pptx (review-session deck, faculty sample).
// Run: node docs/build_deck.js   (needs pptxgenjs; chart numbers come from deck_data.json)
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");
const path = require("path");
const D = require("./deck_data.json");
const FIG = path.join(__dirname, "..", "results", "figures");

const THEME = {
  name: "Triage Teal",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A34", lt1: "FFFFFF", dk2: "0F3D4C", lt2: "EAF3F4",
    accent1: "0E7C86", accent2: "E07A5F", accent3: "3D5A80", accent4: "81B29A",
    accent5: "F2CC8F", accent6: "6D6875", hlink: "0E7C86", folHlink: "6D6875",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "CT-based Patient Triage of COVID-19 - sample review deck";
pres.author = "Faculty sample - UE24CS352A";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "LIGHT", background: { color: C.background1 },
  objects: [
    { text: { text: "Faculty sample - synthetic data, not for clinical use", options: { x: 0.5, y: 5.2, w: 7, h: 0.25, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.25, fontSize: 10, color: C.accent6 },
  margin: [0.4, 0.5, 0.5, 0.5],
});
pres.defineSlideMaster({
  title: "DARK", background: { color: C.text2 },
});


const LIGHT_TITLE = { x: 0.5, y: 0.3, w: 9, h: 0.8, fontSize: 30, bold: true, color: C.text2, fontFace: THEME.headFontFace, align: "left", valign: "middle", margin: 0, isTextBox: true };
const DARK_TITLE = { x: 0.7, y: 1.3, w: 8.6, h: 1.2, fontSize: 38, bold: true, color: C.background1, fontFace: THEME.headFontFace, align: "left", valign: "top", margin: 0, isTextBox: true };
const title = (s, text, dark = false) => s.addText(text, { ...(dark ? DARK_TITLE : LIGHT_TITLE) });

const bullets = (items, opts = {}) => items.map((t, i) => ({
  text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8, ...opts },
}));
const body = { fontSize: 16, color: C.text1, valign: "top", isTextBox: true, margin: 0 };

// 1 ---------------------------------------------------------------- title
{
  const s = pres.addSlide({ masterName: "DARK" });
  title(s, "CT-based Patient Triage of COVID-19", true);
  s.addText("Radiomics prediction of ICU admission, mechanical ventilation and death", { x: 0.7, y: 2.55, w: 8.4, h: 0.8, fontSize: 20, color: C.background2, margin: 0, isTextBox: true });
  s.addText("UE24CS352A Machine Learning - Mini-Project\nFaculty sample solution for students  |  synthetic data", { x: 0.7, y: 4.0, w: 8.4, h: 0.8, fontSize: 14, color: C.accent5, margin: 0, isTextBox: true });
  s.addNotes("Introduce this as a worked example of a full submission: repo, write-up, slides, live demo. Stress that the data is synthetic and that the point is the method and the standards, not the numbers.");
}

// 2 ---------------------------------------------------------------- problem
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "The problem: who needs intensive care?");
  s.addText(bullets([
    "At admission, predict three outcomes: ICU admission, mechanical ventilation (MV), in-hospital death",
    "Inputs: CT radiomics, clinical features, lab results",
    "Why it matters: allocate limited ICU resources to high-risk patients first",
    "Why it is hard: outcomes are rare (about 2-8% of patients)",
  ]), { x: 0.5, y: 1.4, w: 5.3, h: 3.4, ...body });
  [["3", "outcomes"], ["5", "data configurations"], ["5", "models"]].forEach(([n, l], i) => {
    s.addShape(pres.ShapeType.roundRect, { x: 6.3, y: 1.4 + i * 1.15, w: 3.2, h: 0.95, fill: { color: C.background2 }, rectRadius: 0.1, objectName: `stat-card-${i}` });
    s.addText(n, { x: 6.45, y: 1.4 + i * 1.15, w: 1.0, h: 0.95, fontSize: 40, bold: true, color: C.accent1, fontFace: THEME.headFontFace, valign: "middle", margin: 0, isTextBox: true });
    s.addText(l, { x: 7.4, y: 1.4 + i * 1.15, w: 2.0, h: 0.95, fontSize: 16, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addNotes("Based on Zhan and Li, Stanford CS229 2020. Ask students why rare outcomes make accuracy a misleading metric.");
}

// 3 ---------------------------------------------------------------- dataset
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Data: two cohorts, split by admission period");
  [["1,662", "Cohort 1: development\nICU 93 | MV 47 | death 31"], ["700", "Cohort 2: external validation\nICU 57 | MV 45 | death 32"]].forEach(([n, l], i) => {
    const x = 0.5 + i * 4.6;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.4, w: 4.4, h: 1.9, fill: { color: C.background2 }, rectRadius: 0.1, objectName: `cohort-card-${i}` });
    s.addText(n, { x: x + 0.25, y: 1.5, w: 3.9, h: 0.9, fontSize: 48, bold: true, color: C.accent1, fontFace: THEME.headFontFace, margin: 0, isTextBox: true });
    s.addText(l, { x: x + 0.25, y: 2.4, w: 3.9, h: 0.8, fontSize: 16, color: C.text1, margin: 0, isTextBox: true });
  });
  s.addText(bullets([
    "114 features: 100 radiomics, 7 clinical, 7 labs, plus a 0-4 radiologist score",
    "The paper's hospital data is private, so this sample uses synthetic data with the same structure",
    "Cohort 2 has a mild covariate shift, like a later admission period",
  ]), { x: 0.5, y: 3.55, w: 9, h: 1.5, ...body });
  s.addNotes("The generator lives in src/generate_synthetic_data.py. Be explicit that metrics on synthetic data are not clinically meaningful. A real submission would use a real public dataset and justify the choice.");
}

// 4 ---------------------------------------------------------------- approach
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Approach: select on training data only");
  const steps = [
    ["1", "Split", "Cohort 1: 70% train / 30% test"],
    ["2", "Engineer", "Class weights, SMOTEENN, or SMOTEENN + LASSO"],
    ["3", "Select", "5 models; best by 3-fold CV AUROC on train"],
    ["4", "Validate", "Refit on cohort 1; test on cohort 2"],
  ];
  steps.forEach(([n, h, t], i) => {
    const x = 0.5 + i * 2.28;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.5, w: 2.1, h: 2.3, fill: { color: C.background2 }, rectRadius: 0.1, objectName: `step-card-${i}` });
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.15, y: 1.65, w: 0.5, h: 0.5, fill: { color: C.accent1 }, objectName: `step-badge-${i}` });
    s.addText(n, { x: x + 0.15, y: 1.65, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(h, { x: x + 0.15, y: 2.25, w: 1.8, h: 0.4, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
    s.addText(t, { x: x + 0.15, y: 2.65, w: 1.8, h: 1.1, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Bootstrap: 30 resamples of cohort 2, 95% intervals, paired one-sided t-tests. Deliberate improvement on the paper, which picked models on the 30% test split.",
    { x: 0.5, y: 4.1, w: 9, h: 0.9, fontSize: 16, color: C.text1, margin: 0, isTextBox: true });
  s.addNotes("Why SMOTEENN inside an imblearn Pipeline: resampling must happen only on training folds, otherwise synthetic points leak into validation and inflate scores. Ask students where leakage could creep in.");
}

// 5 ---------------------------------------------------------------- implementation
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Implementation and how to run it");
  s.addText(bullets([
    "Python: scikit-learn, imbalanced-learn, LightGBM, SciPy",
    "pipeline.py runs everything end to end, seeded (about 5 minutes)",
    "demo.py scores individual patients live",
    "README: setup, run commands, layout",
  ]), { x: 0.5, y: 1.4, w: 4.6, h: 3.3, ...body });
  s.addShape(pres.ShapeType.roundRect, { x: 5.4, y: 1.4, w: 4.1, h: 3.3, fill: { color: C.text1 }, rectRadius: 0.1, objectName: "code-card" });
  s.addText("pip install -r requirements.txt\n\npython src/generate_synthetic_data.py\n\npython src/pipeline.py\n\npython demo.py",
    { x: 5.6, y: 1.55, w: 3.7, h: 3.0, fontSize: 14, fontFace: "Courier New", color: C.background2, valign: "top", margin: 0, isTextBox: true });
  s.addNotes("Show the repo on screen. Point out the commit history, a clear README and no data or secrets committed beyond the synthetic CSV. Repository maintenance is graded.");
}

// 6 ---------------------------------------------------------------- results chart
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Results: ClinLab wins on every task");
  const labels = D.order;
  s.addChart(pres.charts.BAR, [
    { name: "ICU admission", labels, values: D.auroc.ICU },
    { name: "Mechanical ventilation", labels, values: D.auroc.MV },
    { name: "Death", labels, values: D.auroc.Death },
  ], {
    x: 0.5, y: 1.25, w: 9, h: 3.2, barDir: "col", barGrouping: "clustered",
    chartColors: [THEME.colors.accent1, THEME.colors.accent2, THEME.colors.accent3],
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: "1B2A34",
    showValue: true, dataLabelFontSize: 10, dataLabelFormatCode: "0.00", dataLabelFontFace: "+mn-lt", dataLabelColor: "1B2A34",
    catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: "1B2A34",
    valAxisLabelFontSize: 12, valAxisLabelFontFace: "+mn-lt", valAxisLabelColor: "1B2A34",
    valAxisMinVal: 0.3, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1,
    valGridLine: { color: "D9E2E4", size: 0.5 }, catGridLine: { style: "none" },
    showValAxisTitle: true, valAxisTitle: "AUROC, cohort 2 (bootstrap mean)", valAxisTitleFontSize: 12, valAxisTitleFontFace: "+mn-lt", valAxisTitleColor: "1B2A34",
  });
  s.addText("The paper's headline (radiomics + clinical + labs best) did not replicate on synthetic data. Honest reporting is the lesson.",
    { x: 0.5, y: 4.55, w: 9, h: 0.55, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });
  s.addNotes("Numbers are bootstrap means from results/table3_bootstrap_summary.csv. In the synthetic generator, labs are a cleaner readout of the latent severity than radiomics, and with few positives, 100 extra noisy features hurt. The RScore ventilation model scored 0.43, below chance: a flexible model overfitting 47 positives.");
}

// 7 ---------------------------------------------------------------- ROC figure
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Discrimination on unseen patients (cohort 2)");
  s.addImage({ path: path.join(FIG, "fig2_roc_pr_cohort2.png"), x: 0.5, y: 1.2, w: 6.2, h: 6.2 * 7.5 / 13, altText: "ROC and precision-recall curves on cohort 2 for each data configuration and outcome" });
  s.addText(bullets([
    "Top: ROC. Bottom: precision-recall",
    "Precision-recall matters with rare outcomes",
    "Wide wobble = few positives (32-57 per task)",
  ]), { x: 7.0, y: 1.4, w: 2.5, h: 3.2, fontSize: 14, color: C.text1, valign: "top", isTextBox: true, margin: 0 });
  s.addNotes("Ask: why is the precision-recall plot more informative than ROC when only 2-8% of patients are positive?");
}

// 8 ---------------------------------------------------------------- significance
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "What the statistics say");
  const f = (a) => (a[0] >= 0 ? "+" : "") + a[0].toFixed(3);
  const rows = [
    [{ text: "Comparison (AUROC)", options: { bold: true, fill: { color: C.background2 } } }, { text: "ICU", options: { bold: true, fill: { color: C.background2 }, align: "center" } }, { text: "MV", options: { bold: true, fill: { color: C.background2 }, align: "center" } }, { text: "Death", options: { bold: true, fill: { color: C.background2 }, align: "center" } }],
    ["Radiomics vs radiologist score", f(D.rad_vs_rscore.ICU), f(D.rad_vs_rscore.MV), f(D.rad_vs_rscore.Death)],
    ["Adding clinical to radiomics", f(D.clin_gain.ICU), f(D.clin_gain.MV), f(D.clin_gain.Death)],
  ].map((r, i) => i === 0 ? r : r.map((c, j) => ({ text: c, options: { align: j ? "center" : "left" } })));
  s.addTable(rows, { x: 0.5, y: 1.3, w: 9, colW: [4.5, 1.5, 1.5, 1.5], fontSize: 14, color: "1B2A34", border: { type: "solid", pt: 0.5, color: "C9D6D8" }, rowH: 0.45, fontFace: THEME.bodyFontFace });
  s.addText(bullets([
    "Paired one-sided t-tests over 30 bootstrap resamples: both comparisons significant (p<0.001) in every task, except radiomics vs radiologist score for death on AUROC",
    "Top features: age, neutrophils, D-dimer, dyspnea, plus a few radiomics features",
    "Caveat: bootstrap p-values on one fixed test cohort understate uncertainty",
  ]), { x: 0.5, y: 2.9, w: 9, h: 2.2, ...body });
  s.addNotes("Final bullet is a genuine limitation worth discussing: the bootstrap resamples the test patients but not the training process, so these p-values are optimistic.");
}

// 9 ---------------------------------------------------------------- conclusions
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  title(s, "Conclusions and takeaways");
  [["What held", ["Radiomics beat the radiologist score for ICU and MV", "Clinical features add real value to radiomics"], C.accent1],
   ["What did not", ["Radiomics + clinical + labs was not best; ClinLab was", "Few positives punish high-dimensional inputs"], C.accent2]].forEach(([h, items, col], i) => {
    const x = 0.5 + i * 4.6;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.35, w: 4.4, h: 2.45, fill: { color: C.background2 }, rectRadius: 0.1, objectName: `concl-card-${i}` });
    s.addText(h, { x: x + 0.25, y: 1.45, w: 3.9, h: 0.5, fontSize: 20, bold: true, color: col, fontFace: THEME.headFontFace, margin: 0, isTextBox: true });
    s.addText(bullets(items), { x: x + 0.25, y: 2.0, w: 3.9, h: 1.7, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("For your own project: state data limits honestly, keep test data out of model selection, report intervals, and be ready to explain every line.",
    { x: 0.5, y: 4.05, w: 9, h: 0.9, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
  s.addNotes("Close by connecting to the grading criteria: individual contribution and Q&A reward understanding, not just working code.");
}

// 10 --------------------------------------------------------------- demo
{
  const s = pres.addSlide({ masterName: "DARK" });
  title(s, "Live demo", true);
  s.addText("python demo.py\nTrains the ICU model on cohort 1, then scores unseen cohort 2 patients and ranks them by predicted risk.",
    { x: 0.7, y: 2.4, w: 8.4, h: 1.4, fontSize: 18, color: C.background2, margin: 0, isTextBox: true });
  s.addText("Questions?", { x: 0.7, y: 4.2, w: 8.4, h: 0.6, fontSize: 22, color: C.accent5, fontFace: THEME.headFontFace, margin: 0, isTextBox: true });
  s.addNotes("Run demo.py live. Expected: eight patients ranked by predicted ICU risk next to the true label. Then take questions.");
}

(async () => {
  const out = path.join(__dirname, "COVID_Triage_Review_Slides.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
