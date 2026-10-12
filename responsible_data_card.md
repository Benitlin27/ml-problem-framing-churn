# Responsible Data Card: Customer Churn Dataset

## 1. Dataset Purpose
* **Decision Supported:** Proactively identifying subscribers exhibiting behavioral signals of disengagement or dissatisfaction to trigger customer support outreach, onboarding guidance, or account renewal incentives within a 30-day intervention window.
* **Prohibited Decisions:**
  - Automated unilateral service termination or suspension.
  - Price discrimination or punitive rate hikes based on predicted churn propensity.
  - Deprioritizing or denying technical support SLAs to customers flagged with high churn probability.
  - Sharing individual churn propensity scores with third-party advertising brokers or credit bureaus.

---

## 2. Provenance and Permission
* **Data Origin:** Derived from internal product analytics databases, billing telemetry, and customer support ticketing logs (e.g., Zendesk / internal CRM).
* **Custodianship:** Internal Customer Success & Product Analytics Engineering teams.
* **Permitted Usage:** Model development, offline policy evaluation, and internal operational analytics.
* **Consent & Privacy Framework:**
  - Collected under Terms of Service and Privacy Policy for "Service Improvement and Account Management".
  - Data subjects possess rights to access and erasure (GDPR / DPDPA 2023 compliance).
  - Explicit customer consent covers telemetry for billing and support, but forbids external commercialization.
* **Licensing / Classification:** Strictly Internal & Confidential; not open-source; proprietary operational data.

---

## 3. Population and Representation
* **Represented Cohort:** Customers subscribed to paid SaaS tiers (Basic: ₹499/mo, Standard: ₹999/mo, Pro: ₹1,499/mo).
* **Sample Summary (\(N = 12\)):**
  - Churned count: 5 (41.67%)
  - Retained count: 7 (58.33%)
  - Plan distribution: Basic (5, 41.7%), Standard (4, 33.3%), Pro (3, 25.0%)
* **Excluded / Underrepresented Populations:**
  - Free trial / freemium tier users (not present in billing records).
  - Enterprise contract customers (negotiated via bespoke offline SLAs with annual upfront invoicing).
  - Newly acquired accounts under 1 month tenure (excluded due to lack of 30-day behavioral baselines).
* **Known Sampling Biases:**
  - Small sample size (\(N=12\)) represents an illustrative pilot batch; statistical power is limited, and confidence intervals are broad.
  - Survivorship bias: Accounts surviving past 12 months show lower baseline hazard rates.

---

## 4. Features and Target

| Feature Name | Type | Description | Range / Values | Potential Leakage Risk | Sensitive Proxy Risk |
|---|---|---|---|---|---|
| `customer_id` | Identifier | Unique account pseudonym | `C001` - `C012` | High (if used as feature; must be excluded from model training) | None directly, but could track individual identity |
| `tenure_months` | Numerical (Discrete) | Months elapsed since initial account activation | 1 – 30 months | None (strictly historical) | Proxy for account maturity; older accounts may correlate with demographic cohort |
| `support_tickets` | Numerical (Discrete) | Count of support tickets submitted in prior 30 days | 0 – 5 tickets | Potential leakage if tickets include "request cancellation" or "request refund" | Proxy for accessibility or technical literacy barriers |
| `monthly_spend_inr` | Numerical (Continuous) | Current recurring subscription tier billing in INR | ₹499, ₹799, ₹999, ₹1,299, ₹1,499 | None if captured at beginning of evaluation window | Strong proxy for socioeconomic status / business size |
| `last_login_days` | Numerical (Discrete) | Days elapsed between last user session and observation date \(T\) | 1 – 30 days | Must be calculated strictly before observation point \(T\) | Proxy for working hours / digital availability |
| `plan_type` | Categorical | Subscription product tier | `Basic`, `Standard`, `Pro` | Potential redundancy with `monthly_spend_inr` | Proxy for enterprise capability / budget |
| **`churned`** *(Target)* | Binary | Account cancellation status within subsequent 30-day window | `0` (Retained), `1` (Churned) | Target variable | Ground truth outcome |

---

## 5. Quality Checks & Data Health
* **Completeness & Missingness:** 0% missing values across all 12 rows and 7 attributes.
* **Duplicate Records:** 0 duplicate rows detected (`customer_id` is unique primary key).
* **Outliers / Anomalies:**
  - `support_tickets`: Max 5 tickets (within expected operational limits).
  - `last_login_days`: Max 30 days (consistent with monthly cutoff).
  - `monthly_spend_inr`: Correlates with plans (Basic = 499–799, Standard = 799–999, Pro = 1299–1499).
* **Class Imbalance:** Target ratio is 41.7% churned vs. 58.3% retained (mild imbalance; stratified sampling required).
* **Temporal Train/Test Separation Strategy:**
  - **Do NOT use random k-fold cross-validation in production**, as it creates temporal leakage across consecutive billing periods.
  - **Required Protocol:** Out-of-time (OOT) validation splitting training on Cohorts \(T_0 \dots T_{k}\) and testing on subsequent cycle \(T_{k+1}\).

---

## 6. Risks and Safeguards

| Harm Category | Concrete Failure Mode | Mitigation & Safeguard Protocol |
|---|---|---|
| **Socioeconomic Bias** | Over-prioritizing retention incentives to high-spend `Pro` tiers while neglecting `Basic` tier users experiencing software bugs. | Normalize retention scoring by tier; enforce separate support resolution queues so basic users receive bug fixes, not just discount popups. |
| **Proxy Discrimination** | Spend or plan tiers inadvertently penalizing smaller local businesses or non-profits. | Constrain models using monotonic constraints; audit disparate impact ratio across account size categories (\(DI \ge 0.80\)). |
| **Privacy & Tracking** | Exposure of granular customer usage telemetry or identity re-identification. | Hash IDs, anonymize telemetry, enforce role-based access control (RBAC), and purge inactive logs according to retention schedules. |
| **False-Positive Cost** | Annoying loyal customers with unsolicited "Are you unhappy?" surveys or needlessly diluting margin via premature discounts. | Enforce minimum threshold (\(\ge 0.65\)) for financial discounts; use softer, non-intrusive in-app tips for moderate scores. |
| **False-Negative Cost** | Silent churn of a high-value customer with zero intervention, resulting in significant ARR loss. | Incorporate heuristic safety nets (e.g. any account with \(\ge 3\) tickets or \(>14\) days inactivity is flagged regardless of model score). |

---

## 7. Intended Evaluation
* **Non-ML Benchmark:** Simple heuristic decision rule (`support_tickets >= 3` OR `last_login_days >= 14`).
* **Model Families Tested:** Logistic Regression (L2 regularized) and Rule-Based Baseline.
* **Evaluation Metrics:**
  - Precision, Recall, and F2-Score (optimizing recall over precision due to 24:1 cost ratio).
  - Brier Score & Reliability Curves for probability calibration.
  - Confusion Matrix with cost-weighted expected monetary loss in INR.
* **Slice-Based Fairness Evaluation:** Disaggregated evaluation across `plan_type` (`Basic` vs. `Standard` vs. `Pro`) to ensure error parity.
