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

Every row carries the DOI of the version that was read. Five rows used to appear in the paper's
table with no citation at all ("Robust NID via XAI ('22)"), which is indefensible in a paper whose
whole argument is that this field does not check its own claims: an audit nobody can look up is
exactly the artifact we are complaining about. Each was identified back to its published record on
2026-08-10, and three of them turned out to have left preprint status since the audit was coded
(XG-NID -> Expert Systems with Applications 2025; 5G feature attribution -> JISA 2026; NGSHAP ->
Computer Networks 2026). The CODING is unchanged -- it was done against the version cited here.
"""
import csv, os

# (key, short label, year, venue, doi, [C1..C6])
AUDIT = [
    ("warnecke2020",  "Warnecke et al. (eval)",     2020, "EuroS&P",
     "10.1109/EuroSP48549.2020.00018", [0.5, 1, 0, 0.5, 0.5, 0]),
    ("nadeem2023",    "Nadeem et al. (SoK)",        2023, "EuroS&P",
     "10.1109/EuroSP57164.2023.00022", [0.5, 0.5, 0, 0.5, 0.5, 0]),
    ("capuano2022",   "Capuano et al. (survey)",    2022, "IEEE Access",
     "10.1109/ACCESS.2022.3204171", [0, 0, 0, 0, 0, 0]),
    ("action2026",    "Le et al. (TRACE)",          2026, "Electronics",
     "10.3390/electronics15153291", [0, 0, 0, 0, 0.5, 0.5]),
    ("robustxai2022", "Barnard et al. robust XAI",  2022, "IEEE Netw. Lett.",
     "10.1109/LNET.2022.3186589", [0, 0.5, 0, 0.5, 0, 0]),
    ("xgnid2024",     "Farrukh et al. (XG-NID)",    2025, "Expert Syst. Appl.",
     "10.1016/j.eswa.2025.128089", [0, 0, 0, 0, 0, 0]),
    ("ngshap2025",    "Dong et al. (NGSHAP-IDS)",   2026, "Comput. Netw.",
     "10.1016/j.comnet.2025.111937", [0, 0, 0, 0, 0, 0]),
    ("selfattn2025",  "Sharma et al. self-attn.",   2025, "Sci. Rep.",
     "10.1038/s41598-025-23750-0", [0, 0.5, 0, 0, 0, 0]),
    ("feat5g2025",    "Uccello et al. 5G attrib.",  2026, "J. Inf. Secur. Appl.",
     "10.1016/j.jisa.2026.104448", [0, 1, 0, 0, 0, 0]),
    ("fronteval2025", "Mohale et al. evaluation",   2025, "Front. Comput. Sci.",
     "10.3389/fcomp.2025.1520741", [0, 0.5, 0, 0, 0, 0]),
    ("lxaids2025",    "Muhammad et al. (L-XAIDS)",  2025, "Cluster Comput.",
     "10.1007/s10586-025-05326-9", [0, 0, 0, 0, 0, 0]),
    ("insider2026",   "Faqihi et al. insider SHAP", 2026, "FGCS",
     "10.1016/j.future.2026.108543", [0, 0, 0, 0, 0, 0]),
]

CRITS = ["C1 fidelity", "C2 method-inv", "C3 instance-inv", "C4 adv-robust",
         "C5 warrant", "C6 reliability"]

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True)
    n = len(AUDIT)
    assert len({r[4] for r in AUDIT}) == n, "a DOI is repeated: two rows are the same paper"
    assert all(r[4].startswith("10.") for r in AUDIT), "a row has no resolvable DOI"
    with open("results/field_audit.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["key", "label", "year", "venue", "doi"] + CRITS)
        for k, lab, yr, ven, doi, sc in AUDIT:
            w.writerow([k, lab, yr, ven, doi] + sc)
    # coverage per criterion (fraction reporting, counting partial as 0.5)
    print(f"audited {n} papers, {n} distinct DOIs")
    for i, c in enumerate(CRITS):
        cov = sum(r[5][i] for r in AUDIT) / n
        full = sum(1 for r in AUDIT if r[5][i] == 1)
        print(f"  {c:16s}: coverage={cov:.2f}  (fully reported by {full}/{n})")
    print("wrote results/field_audit.csv")
