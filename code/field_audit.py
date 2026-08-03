"""
Field audit of published explainable-IDS work against our six threat-aware criteria.

Methodology (conservative, to avoid misrepresenting others' work): each paper is scored from its
abstract and method description. A criterion is marked MET only when the paper explicitly reports
the corresponding evidence; otherwise it is marked not-reported. Scores are therefore a LOWER
BOUND on each paper's rigor, and the audit measures reporting practice, not hidden quality.

Criteria:
  C1 fidelity budget          -- reports interpretable-artifact vs deployed-model decision agreement
  C2 method invariance        -- reports agreement across >=2 attribution methods (not just "we use both")
  C3 instance invariance      -- reports explanation stability across retrainings/seeds
  C4 explanation adv. robust  -- states a threat model for the explanation itself
  C5 trust as warrant         -- evaluates vs ground truth, not analyst satisfaction/usefulness
  C6 reliability signalling   -- provides a per-alarm when-not-to-trust signal

Legend: 1 = reported, 0 = not reported, 0.5 = partial (mechanism present but not as the criterion).
Papers are real and web-verified; two (Warnecke, Nadeem) are evaluation/SoK works, the rest applied.
"""
import csv, os

# (key, short label, year, venue-tier, [C1..C6])
AUDIT = [
    ("warnecke2020",  "Warnecke et al. (eval)",     2020, "EuroS&P", [0.5, 1, 0, 0.5, 0.5, 0]),
    ("nadeem2023",    "Nadeem et al. (SoK)",         2023, "EuroS&P", [0.5, 0.5, 0, 0.5, 0.5, 0]),
    ("capuano2022",   "Capuano et al. (survey)",     2022, "Access",  [0, 0, 0, 0, 0, 0]),
    ("action2026",    "Le et al. action-contracts",  2026, "Electron.", [0, 0, 0, 0, 0.5, 0.5]),
    ("robustxai2022", "Robust NID via XAI",          2022, "conf",    [0, 0.5, 0, 0.5, 0, 0]),
    ("xgnid2024",     "XG-NID (GNN+LLM)",            2024, "arXiv",   [0, 0, 0, 0, 0, 0]),
    ("ngshap2025",    "NGSHAP-IDS (NGBoost)",        2025, "journal", [0, 0, 0, 0, 0, 0]),
    ("selfattn2025",  "Self-attention XAI IoT",      2025, "Sci.Rep.", [0, 0.5, 0, 0, 0, 0]),
    ("feat5g2025",    "Feature Attrib. 5G IDS",      2025, "arXiv",   [0, 1, 0, 0, 0, 0]),
    ("fronteval2025", "Evaluating ML-IDS w/ XAI",    2025, "Frontiers", [0, 0.5, 0, 0, 0, 0]),
    ("lxaids2025",    "L-XAIDS (LIME framework)",     2025, "arXiv",   [0, 0, 0, 0, 0, 0]),
    ("insider2026",   "Insider-threat SHAP",         2026, "FGCS",    [0, 0, 0, 0, 0, 0]),
]

CRITS = ["C1 fidelity", "C2 method-inv", "C3 instance-inv", "C4 adv-robust",
         "C5 warrant", "C6 reliability"]

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    n = len(AUDIT)
    with open("results/field_audit.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["key", "label", "year", "venue"] + CRITS)
        for k, lab, yr, ven, sc in AUDIT:
            w.writerow([k, lab, yr, ven] + sc)
    # coverage per criterion (fraction reporting, counting partial as 0.5)
    print(f"audited {n} papers")
    for i, c in enumerate(CRITS):
        cov = sum(sc[i] for _, _, _, _, sc in AUDIT) / n
        full = sum(1 for _, _, _, _, sc in AUDIT if sc[i] == 1)
        print(f"  {c:16s}: coverage={cov:.2f}  (fully reported by {full}/{n})")
    print("wrote results/field_audit.csv")
