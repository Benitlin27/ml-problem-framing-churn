"""
Baseline and Model Benchmarking Pipeline
Compares a deterministic non-ML heuristic baseline against an ML classifier
on the Customer Churn dataset, computing cost-weighted business metrics.
"""

import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv("customer_churn_data.csv")
print("Dataset Loaded Successfully:")
print(df.to_string(index=False))
print("\n" + "="*60 + "\n")

# 1. Non-ML Heuristic Baseline
# Business heuristic: Flag as at-risk if customer has >= 3 support tickets OR has not logged in for >= 14 days
def heuristic_baseline(row):
    return 1 if (row['support_tickets'] >= 3 or row['last_login_days'] >= 14) else 0

df['pred_baseline'] = df.apply(heuristic_baseline, axis=1)

# 2. Performance Metrics Calculation
def evaluate_predictions(y_true, y_pred, name="Model"):
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    beta = 2.0
    f2 = (1 + beta**2) * (precision * recall) / ((beta**2 * precision) + recall) if ((beta**2 * precision) + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true)
    
    # Financial Cost Model:
    # Cost of False Negative (Missed churn / lost LTV) = ₹6,000 avg
    # Cost of False Positive (Unnecessary retention discount/outreach) = ₹250 avg
    c_fn = 6000
    c_fp = 250
    total_cost = (fn * c_fn) + (fp * c_fp)
    
    print(f"--- Performance Summary: {name} ---")
    print(f"Confusion Matrix: TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"Accuracy : {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall   : {recall:.3f}")
    print(f"F1-Score : {f1:.3f}")
    print(f"F2-Score : {f2:.3f} (Prioritizing Recall)")
    print(f"Cost-Sensitive Loss: INR {total_cost:,} (FN cost: INR {fn * c_fn:,}, FP cost: INR {fp * c_fp:,})")
    print("-" * 60)
    
    return {
        "Name": name, "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "Accuracy": accuracy, "Precision": precision, "Recall": recall,
        "F1": f1, "F2": f2, "Total_Cost_INR": total_cost
    }

metrics_baseline = evaluate_predictions(df['churned'], df['pred_baseline'], "Heuristic Rule-Based Baseline")

# 3. Machine Learning Comparison
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    
    features = ['tenure_months', 'support_tickets', 'monthly_spend_inr', 'last_login_days']
    X = df[features]
    y = df['churned']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # L2 regularized logistic regression with balanced class weighting
    clf = LogisticRegression(class_weight='balanced', random_state=42)
    clf.fit(X_scaled, y)
    
    df['ml_prob'] = clf.predict_proba(X_scaled)[:, 1]
    
    # Standard 0.5 threshold
    df['pred_ml_default'] = (df['ml_prob'] >= 0.5).astype(int)
    metrics_ml_default = evaluate_predictions(df['churned'], df['pred_ml_default'], "Logistic Regression (Threshold = 0.50)")
    
    # Cost-tuned threshold (0.35 threshold to favor Recall over FN cost)
    df['pred_ml_tuned'] = (df['ml_prob'] >= 0.35).astype(int)
    metrics_ml_tuned = evaluate_predictions(df['churned'], df['pred_ml_tuned'], "Logistic Regression (Cost-Tuned Threshold = 0.35)")
    
    # Feature coefficients
    coef_df = pd.DataFrame({'Feature': features, 'Weight': clf.coef_[0]}).sort_values(by='Weight', ascending=False)
    print("\nFeature Coefficients (Impact on Churn Propensity):")
    print(coef_df.to_string(index=False))
    
    # Tri-band Decision Policy Simulation
    def policy_action(prob):
        if prob < 0.30:
            return "No Intervention (Low Risk)"
        elif prob < 0.65:
            return "Human Review Queue (Abstention)"
        else:
            return "Targeted Retention (High Risk)"
            
    df['policy_action'] = df['ml_prob'].apply(policy_action)
    print("\nOperational Action Distribution:")
    print(df[['customer_id', 'plan_type', 'churned', 'ml_prob', 'policy_action']])

except Exception as e:
    print(f"ML evaluation skipped or encountered: {e}")
