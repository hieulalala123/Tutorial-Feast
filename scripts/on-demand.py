"""
Demo Advanced Features:
1. On-Demand Feature View - tinh feature tu request
2. Feature Service - lay nhom feature theo model version
"""
from pathlib import Path
from feast import FeatureStore

REPO_PATH = Path("/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/feature_repo")
store = FeatureStore(repo_path=str(REPO_PATH))

print("=" * 60)
print("DEMO 1: On-Demand Feature View")
print("=" * 60)
print("""
Scenario: User vua thuc hien giao dich $1500.
Ta muon biet day co phai giao dich bat thuong khong (so voi history).
""")

# Cung cap current_purchase_amount tu request
features = store.get_online_features(
    features=[
        "user_transaction_stats:avg_purchase_7d",
        "transaction_anomaly_features:purchase_to_avg_ratio",
        "transaction_anomaly_features:is_unusual_purchase",
    ],
    entity_rows=[
        {"user_id": 1, "current_purchase_amount": 1500.0},   # Cao bat thuong
        {"user_id": 2, "current_purchase_amount": 50.0},     # Bnh thuong
        {"user_id": 100, "current_purchase_amount": 5000.0}, # Cuc cao
    ],
).to_dict()

print(f"User 1 (current $1500):")
print(f"  avg_7d:  ${features['avg_purchase_7d'][0]:.2f}")
print(f"  ratio:   {features['purchase_to_avg_ratio'][0]:.2f}x")
print(f"  unusual: {features['is_unusual_purchase'][0]}")

print(f"\nUser 2 (current $50):")
print(f"  avg_7d:  ${features['avg_purchase_7d'][1]:.2f}")
print(f"  ratio:   {features['purchase_to_avg_ratio'][1]:.2f}x")
print(f"  unusual: {features['is_unusual_purchase'][1]}")

print(f"\nUser 100 (current $5000):")
print(f"  avg_7d:  ${features['avg_purchase_7d'][2]:.2f}")
print(f"  ratio:   {features['purchase_to_avg_ratio'][2]:.2f}x")
print(f"  unusual: {features['is_unusual_purchase'][2]}")

print("\n" + "=" * 60)
print("DEMO 2: Feature Service - lay theo model version")
print("=" * 60)
print("""
Thay vi liet ke tung feature, dung Feature Service de
get ca bo cho 1 model:
""")

# Model V1: chi batch features
v1_features = store.get_online_features(
    features=store.get_feature_service("churn_model_v1"),
    entity_rows=[{"user_id": 1}],
).to_dict()
print(f"churn_model_v1 features:")
for key in v1_features:
    print(f"  {key}: {v1_features[key]}")

print()

# Model V2: them on-demand
v2_features = store.get_online_features(
    features=store.get_feature_service("churn_model_v2"),
    entity_rows=[{"user_id": 1, "current_purchase_amount": 1500.0}],
).to_dict()
print(f"churn_model_v2 features (co on-demand):")
for key in v2_features:
    print(f"  {key}: {v2_features[key]}")

print("\n" + "=" * 60)
print("KEY TAKEAWAY")
print("=" * 60)
print("""
1. ON-DEMAND FV:
   - Cho phep tinh feature TU REQUEST DATA tai inference
   - Gioi han: chi tinh tu input + batch features co san
   - Use case: ratios, derived features, geo distance, time-based

2. FEATURE SERVICE:
   - Dong goi nhom feature cho tung model version
   - Code don gian hon: 1 call thay vi liet ke tung feature
   - De A/B test: tao Feature Service moi cho model v2,
     khong dung den v1 dang chay production
   - De audit: biet model nao dung feature gi
""")