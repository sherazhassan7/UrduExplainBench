"""Reproduce the main results from the files in data/.

Run from the repository root:
    pip install -r requirements.txt
    python3 scripts/reproduce_results.py
"""
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, fisher_exact, binomtest

DIMS = ["conceptual_clarity", "grade_appropriateness", "pedagogical_structure", "terminology", "language_quality"]

r = pd.read_csv("data/ratings.csv").dropna(subset=DIMS)
r[DIMS] = r[DIMS].replace(0, 1)                      # four cells were entered as 0 on the 1-5 scale
r["composite"] = r[DIMS].mean(axis=1)

# one pair = one topic explained by one model in both languages; average over raters where several scored it
pairs = r.groupby(["topic", "model", "language"]).composite.mean().unstack()
gap = pairs["Urdu"] - pairs["English"]

rng = np.random.default_rng(2026)
boot = [rng.choice(gap.values, len(gap)).mean() for _ in range(10_000)]
w = wilcoxon(pairs["English"], pairs["Urdu"])

print("Explanation quality, Urdu vs English (90 topic-model pairs)")
print(f"  English mean {pairs['English'].mean():.2f}, Urdu mean {pairs['Urdu'].mean():.2f}")
print(f"  gap (Urdu minus English) {gap.mean():+.2f}, 95% CI {np.percentile(boot, 2.5):+.2f} to {np.percentile(boot, 97.5):+.2f}")
print(f"  Wilcoxon W = {w.statistic}, p = {w.pvalue:.1e}")
print(f"  Urdu lower in {(gap < 0).sum()}, higher in {(gap > 0).sum()}, tied in {(gap == 0).sum()}")
print("\nGap by model")
for m, g in gap.groupby(level="model"):
    print(f"  {m:15s} {g.mean():+.2f}")

oc = pd.read_csv("data/output_characteristics.csv")
ur = oc[oc.lang == "ur"]
print("\nForeign-script contamination in Urdu outputs, all four runs")
names = {"A": "GPT-4o", "B": "Llama-3.3-70B", "C": "Llama-3.1-8B"}
counts = {}
for code, name in names.items():
    s = ur[ur.model_code == code]
    counts[code] = (int(s.foreign_script.sum()), len(s))
    print(f"  {name:15s} {counts[code][0]}/{counts[code][1]}")
(b, nb), (c, nc) = counts["B"], counts["C"]
print(f"  Llama-3.3-70B vs Llama-3.1-8B: Fisher's exact p = {fisher_exact([[b, nb - b], [c, nc - c]]).pvalue:.1e}")

acc = pd.read_csv("data/accuracy_labels.csv")
print("\nFactual errors (0 = none, 1 = minor, 2 = major)")
for lang, s in acc.groupby("language"):
    print(f"  {lang:8s} {(s.accuracy_label > 0).sum()} errors ({(s.accuracy_label == 2).sum()} major, {(s.accuracy_label == 1).sum()} minor)")
p = acc.pivot_table(index=["topic", "model"], columns="language", values="accuracy_label")
en_only = int(((p.English > 0) & (p.Urdu == 0)).sum()); ur_only = int(((p.English == 0) & (p.Urdu > 0)).sum())
print(f"  McNemar exact p = {binomtest(min(en_only, ur_only), en_only + ur_only, 0.5).pvalue:.2f}")
