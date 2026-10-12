# Operational Risk Register & Deployment Safeguards

## 1. Overview
This Risk Register establishes operational boundaries, abstention triggers, human-in-the-loop review queues, live telemetry monitors, and rollback mechanisms for the Customer Churn ML Decision System.

---

## 2. Risk Register Matrix

| Risk ID | Harm / Vulnerability Description | Severity | Likelihood | Pre-Mitigation Score | Mitigation & Safeguard Measure | Post-Mitigation Score | Owner |
|---|---|---|---|---|---|---|---|
| **R-01** | **Label Leakage in Ticket Feature:** Support tickets submitted right before observation date might include direct cancellation notices ("Cancel my account"), distorting model weights. | High | High | **Critical** | Implement NLP entity extraction & ticket category filtering. Exclude all tickets labeled with ticket category `Billing/Cancellation` from `support_tickets` count. | Low | Data Engineering |
| **R-02** | **Disparate Action on Lower-Tier Accounts:** `Basic` tier accounts are disproportionately flagged for automated churn without receiving product issue resolution, creating poor customer experience. | High | Medium | **High** | Separate support engineering remediation SLA from discount marketing. Ensure bug tickets from Basic tier trigger engineering fixes regardless of retention status. | Low | Customer Support Lead |
| **R-03** | **Unnecessary Margin Cannibalization (False Positives):** Retained customers offered proactive discounts unnecessarily when they had no intention of churning. | Medium | High | **High** | Calibrate probability threshold to \(\hat{p} \ge 0.65\) before offering financial discounts. Restrict discounts to 1 per customer per 12-month period. | Low | Growth / Commercial Ops |
| **R-04** | **Uncalibrated Model Output:** Overconfidence in raw probabilities leads to misallocated retention team bandwidth. | High | Medium | **High** | Enforce isotonic regression or Platt scaling calibration check on validation set. Require Expected Calibration Error (ECE) \(< 0.08\). | Low | ML Engineer |
| **R-05** | **Data Pipeline Drift / Missing Telemetry:** Upstream app changes cause `last_login_days` to be reported as null or 0, masking disengaged accounts. | Critical | Medium | **Critical** | Implement Great Expectations / strict schema assertions at ingestion. Trigger automated fallback if null rate \(> 1\%\). | Low | MLOps Engineer |
| **R-06** | **Privacy & Subject Rights Non-Compliance:** Churn prediction scores stored indefinitely, conflicting with user deletion requests (GDPR / DPDPA). | High | Low | **Medium** | Tie model inference tables to customer master deletion webhook. Automated cascade deletion within 72 hours of user request. | Very Low | Legal & Security |

---

## 3. Decision Boundary, Abstention & Human-in-the-Loop Review

The model does not make fully autonomous decisions across all prediction regions. Instead, a tri-band policy is instituted:

```
[0.00 -------------- 0.30)        [0.30 ---------------------- 0.65)        [0.65 --------------------- 1.00]
     AUTOMATED SAFE                         ABSTENTION BAND                          AUTOMATED INTERVENTION
  No retention action taken.            Human Review Queue (CSM).              Targeted retention workflow.
   Standard product journey.        Specialist inspects ticket logs.          Discount / Concierge onboarding.
```

### Abstention Criteria (Model Steps Aside):
The system abstains from automated action and routes the account to the **Human Review Queue** under any of the following conditions:
1. **Uncertainty Interval:** Predicted probability falls in the ambiguous zone: \(0.30 \le \hat{p} < 0.65\).
2. **High Strategic Value:** Enterprise / Pro tier accounts with ARR \(> ₹25,000\) are never processed solely by automated emails; they always require CSM sign-off.
3. **Data Quality Flags:** Any imputed feature value or telemetry freshness \(> 48\text{ hours}\) old.
4. **Recent Contract Renegotiation:** Customer interacted with sales or renegotiated terms within the last 14 days.

---

## 4. Production Monitoring Protocol

| Telemetry Type | Monitored Metric | Target / Healthy Range | Alert Threshold | Cadence |
|---|---|---|---|---|
| **Data Drift (Input)** | Population Stability Index (PSI) on `last_login_days` & `support_tickets` | \(PSI < 0.10\) | \(PSI \ge 0.20\) | Weekly cohort run |
| **Target / Output Drift**| Predicted Churn Rate vs. Historical Baseline Rate (\(\approx 42\%\)) | \(35\% - 50\%\) | \(< 25\%\) or \(> 60\%\) | Daily batch inference |
| **Data Integrity** | Null or missing values across model inputs | 0% | \(> 0.5\%\) of records | Per inference job |
| **System Latency** | Batch scoring execution duration | \(< 5\text{ minutes}\) | \(> 15\text{ minutes}\) | Per run |
| **Human Review SLA** | Turnaround time for CSM abstention queue tickets | \(< 48\text{ hours}\) | \(> 96\text{ hours}\) | Daily |

---

## 5. Rollback & Fail-Safe Fallback Conditions

If anomalous behavior is detected, automated fail-safe triggers immediately revert execution to the **Deterministic Non-ML Heuristic Baseline**.

### Rollback Triggers:
1. **Trigger A (Critical Drift):** Feature or prediction PSI exceeds \(0.25\) on consecutive runs.
2. **Trigger B (Pipeline Corruption):** Ingestion schema mismatch or \(> 1\%\) missing values in core features.
3. **Trigger C (Disparate Impact Anomaly):** Selection rate of one plan type exceeds 3x another without behavioral justification.
4. **Trigger D (High False-Negative Spike):** Realized churn among accounts scored \(\hat{p} < 0.30\) exceeds 15% in a single cohort.

### Fallback Procedure:
```
[Anomaly Detected / Alert Fired]
               │
               ▼
   [Halt ML Model Inference]
               │
               ▼
[Activate Deterministic Heuristic Baseline]
   - Rule: IF (support_tickets >= 3 OR last_login_days >= 14) -> Flag for review
               │
               ▼
   [Route Flagged Accounts to CSM]
               │
               ▼
[Notify On-Call ML Engineer & Incident Channel]
```
- **Fallback Execution:** The deterministic ruleset runs locally inside the primary application with zero external ML dependencies.
- **Post-Rollback Protocol:** Root-cause analysis (RCA) within 48 hours; model retraining and shadow testing required prior to redeployment.
