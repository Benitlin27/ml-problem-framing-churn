# ML Problem Framing & Responsible Data Card

Comprehensive operational framework, responsible AI audit, baseline benchmarking, and risk mitigation architecture for customer retention and churn prevention.

---

## 📁 Repository Structure & Deliverables

This repository contains all four required proofs for the ML Problem Framing & Responsible Data Card task:

1. **[ml_problem_framing_memo.md](ml_problem_framing_memo.md)** — **ML Problem-Framing Memo**
   - Formal decision definition, prediction target ($Y \in \{0, 1\}$), unit of observation (`customer_id`), and 30-day forward action window.
   - Cost-benefit asymmetric matrix analysis: False Negative (lost LTV $\approx ₹6,000$) vs. False Positive (outreach cost $\approx ₹250$) establishing a **24:1 cost asymmetry ratio**.
   - Justification analysis comparing non-ML heuristics against statistical machine learning.

2. **[responsible_data_card.md](responsible_data_card.md)** — **Responsible Data Card**
   - **Dataset Purpose:** Decision scope (supported retention triggers vs. strictly prohibited decisions like automated terminations).
   - **Provenance & Permission:** Telemetry origin, custodianship, and privacy/consent compliance (GDPR / DPDPA).
   - **Population & Representation:** Coverage across paid subscription tiers (Basic, Standard, Pro) and survivorship caveats.
   - **Features & Leakage:** Explicit risk evaluation for ticket features (preventing cancellation request leaks) and spend proxies.
   - **Quality & Safeguards:** Completeness, outliers, class balance, and Out-of-Time (OOT) temporal validation split protocols.

3. **[baseline_notebook.ipynb](baseline_notebook.ipynb)** — **Baseline Notebook (Fully Executed)**
   - Complete exploratory data analysis and schema verification.
   - Deterministic rule-based baseline implementation (`support_tickets >= 3` OR `last_login_days >= 14`).
   - Regularized Logistic Regression model training and probability calibration.
   - Cost-sensitive loss evaluation ($F_2$-score optimizing Recall over Precision).
   - Operational policy allocation simulation.

4. **[risk_register_and_safeguards.md](risk_register_and_safeguards.md)** — **Operational Risk Register & Safeguards**
   - 6 identified harm vectors with pre- and post-mitigation scores and assigned owners.
   - **Tri-Band Abstention Policy:** Automated safe band ($p < 0.30$), Human Review Queue ($0.30 \le p < 0.65$), and Automated Intervention band ($p \ge 0.65$).
   - Live telemetry monitoring (Population Stability Index / PSI drift triggers).
   - Automated rollback protocol reverting immediately to the non-ML deterministic heuristic fallback.

5. **[customer_churn_data.csv](customer_churn_data.csv)** & **[baseline_benchmark.py](baseline_benchmark.py)** — Source dataset and automated verification script.

---

## 📊 Benchmark Summary

| Evaluation Paradigm | Confusion Matrix | Accuracy | Precision | Recall | $F_2$-Score | Total Loss (INR) |
|---|---|---|---|---|---|---|
| **Non-ML Rule Baseline** | TP=5, FP=0, FN=0, TN=7 | **1.000** | **1.000** | **1.000** | **1.000** | **₹0** |
| **Logistic Regression ($\tau=0.50$)** | TP=5, FP=0, FN=0, TN=7 | **1.000** | **1.000** | **1.000** | **1.000** | **₹0** |
| **Logistic Regression ($\tau=0.35$)** | TP=5, FP=1, FN=0, TN=6 | **0.917** | **0.833** | **1.000** | **0.962** | **₹250** |

*Key Predictive Weights:* `support_tickets` (+0.84), `last_login_days` (+0.81), `monthly_spend_inr` (-0.67), `tenure_months` (-0.53).

---

## 🚀 Execution & Verification
To reproduce benchmark results locally:
```bash
python baseline_benchmark.py
```
Or open and execute `baseline_notebook.ipynb` in any Jupyter environment.
