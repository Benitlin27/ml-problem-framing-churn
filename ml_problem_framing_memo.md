# Machine Learning Problem Framing Memo

## 1. Executive Summary & Problem Context
Subscription cancellations (churn) directly erode recurring monthly revenue, customer lifetime value (LTV), and market share. This project assesses whether a Machine Learning (ML) system is justified for proactive churn prevention or if simpler heuristic-driven rules / non-ML baselines suffice.

---

## 2. Decision & Business Action
* **Business Decision:** Whether to trigger a targeted retention intervention (e.g., outreach by a Customer Success specialist, specialized onboarding reboot, or a targeted plan renewal incentive / discount) for a specific account.
* **Eligible Action Set:**
  1. *High Risk / High Value:* Proactive high-touch outreach by customer success manager + 15% annual contract discount offer.
  2. *Moderate Risk:* Automated targeted in-app nudge and onboarding guide offer.
  3. *Low Risk / Stable:* No intervention (avoid spamming engaged users or wasting discount margins).
  4. *Abstention / Uncertain:* Human review queue (CSM reviews ticket history before deciding).
* **Decisions the system MUST NOT make:**
  - Automated service termination, price hikes, or degradation of service tiers.
  - Denying customer support or deprioritizing SLA obligations based on churn probability.

---

## 3. Prediction Target & Unit of Observation
* **Unit of Observation:** A distinct customer subscription account identified by `customer_id` evaluated at month-end / bi-weekly renewal cycles.
* **Prediction Target (\(Y\)):** Binary indicator `churned \in \{0, 1\}`.
  - `churned = 1`: Customer cancels subscription, downgrades to non-paying, or does not renew within the next 30 days.
  - `churned = 0`: Customer maintains an active paying subscription through the next 30-day window.

---

## 4. Action Window & Temporal Dynamics
* **Observation Window (Features):** Historical behavioral and interaction metrics computed strictly *up to the observation cutoff timestamp \(T\)*:
  - Account tenure (months since initial sign-up up to \(T\)).
  - Number of unresolved/recent support tickets filed within the last 30 days prior to \(T\).
  - Monthly subscription spend (INR) active at \(T\).
  - Recency of activity (`last_login_days` = days elapsed since last session prior to \(T\)).
  - Current subscription tier (`plan_type`).
* **Lead Time / Action Window:** 7–14 days between scoring at time \(T\) and renewal anniversary at \(T + 30\) days, providing Customer Success teams adequate runway to intervene.
* **Target Outcome Window:** \([T, T + 30\text{ days}]\).

---

## 5. Justification: Why ML vs. Non-ML Baseline?
| Dimension | Rule-Based / Heuristic Baseline | Machine Learning Model (Logistic Reg / GBDT) |
|---|---|---|
| **Mechanism** | Simple threshold heuristics (e.g., `last_login_days > 14` AND `support_tickets >= 3`) | Calibrated probability \(P(\text{churn}=1 \mid X)\) synthesizing multi-factor non-linear interactions |
| **Operational Overhead** | Near zero compute; easily explained | Requires pipeline, training, monitoring, and validation |
| **Adaptability** | Rigid; fails when user behavior evolves or across multi-tier price points | Continually trainable on recent cohort distributions |
| **When ML is justified** | **Rule-based baseline must be deployed first.** If baseline capture rate (Recall @ acceptable Precision) meets business ROI thresholds with lower maintenance burden, ML is deferred. ML is justified once feature interactions (e.g. high tickets + high spend vs. low tickets + low login) cause heuristic precision to fall below 65%. |

---

## 6. Business Metrics & Cost Matrix (Cost-Benefit Analysis)

Let:
- \(C_{FP}\): Cost of a False Positive (predicting churn when user would have stayed).
  - Cost of unnecessary outreach / unnecessary discount voucher offered (\(\approx ₹250\) in discount margin or staff time).
- \(C_{FN}\): Cost of a False Negative (predicting retention when user churns without intervention).
  - Loss of Customer Lifetime Value (LTV) / Net Monthly Recurring Revenue (e.g. ₹499 – ₹1,499/mo for an expected remaining 12 months \(\approx ₹6,000\) to \(₹15,000\)).
- \(B_{TP}\): Benefit of a True Positive (successfully predicting and saving an at-risk customer with saving probability \(s \approx 0.35\)):
  - Expected net gain: \(s \times \text{LTV} - C_{\text{intervention}} \approx ₹2,500\).
- \(B_{TN}\): Benefit of True Negative (correctly leaving loyal customers alone): ₹0 marginal cost.

$$\text{Asymmetry Ratio: } \frac{C_{FN}}{C_{FP}} \approx \frac{6000}{250} = 24$$

* **Target Business Metric:** Expected Net Saved Revenue (INR) per 100 evaluated customers.
* **Primary Technical Metric:** PR-AUC and Cost-Sensitive F-Beta Score (\(\beta = 2\)) to heavily penalize False Negatives, along with Precision at Recall \(\ge 0.85\).
* **Calibration Metric:** Brier Score and Expected Calibration Error (ECE) because business decisions require reliable posterior probabilities to allocate tier-based retention budgets.

---

## 7. Decision Thresholds & Policy
Given predicted probability \(\hat{p} = P(\text{churn}=1 \mid x)\):
1. \(\hat{p} < 0.30\): **Low Risk** — Automatic no-action.
2. \(0.30 \le \hat{p} < 0.65\): **Uncertain / Abstention Zone** — Escalate to human review (CSM review queue).
3. \(0.65 \le \hat{p} < 0.85\): **High Risk (Standard)** — Automated targeted retention workflow.
4. \(\hat{p} \ge 0.85\): **Critical Risk (High Value)** — Immediate personal outreach by senior account manager.
