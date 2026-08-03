# xai-ids-trust

Code for the study *"When Is an Explanation Trustworthy? Foundations of Interpretability-Based
Trust in Machine-Learning Intrusion Detection."*

Formalizes three necessary properties of interpretability-based trust in ML-IDS (fidelity,
determinacy, groundedness), measures them on three modern NIDS datasets (UNSW-NB15, CICIDS2017,
5G-NIDD) across five explainers (gradient, input x gradient, integrated gradients, SHAP, LIME),
tests an explanation-manipulation attack (reported honestly as inconclusive on tabular IDS), and
builds a per-alarm reliability gate.

## Experiments (code/)
| Script | Produces |
|---|---|
| `exp_trust.py` | P1 fidelity / P2 determinacy / P3 groundedness |
| `exp_breadth.py` | P2 across 5 explainers incl. SHAP + LIME |
| `exp_multiseed.py` | multi-seed means and std |
| `exp_attack.py` | explanation-evasion attack (inconclusive) |
| `exp_defense.py` | reliability gate (AUC) |
| `exp_defense_ablate.py` | gate signal ablation (not-just-OOD) |
| `plots.py` | figures (house style) |

Datasets are public (UNSW-NB15, CICIDS2017, 5G-NIDD); place under `data/`. Deps: torch, numpy,
scikit-learn, shap, lime, matplotlib.
