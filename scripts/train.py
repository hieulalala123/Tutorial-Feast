"""
Training script - su dung get_historical_features.

Day la TRAI TIM cua Feast: point-in-time join.
Voi moi (user_id, event_timestamp) trong entity_df,
Feast tu dong tim feature value tai dung thoi diem do.
"""
import pandas as pd
from feast import FeatureStore
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from pathlib import Path

# Khoi tao Feature Store - tro ve thu muc feature_repo
REPO_PATH = Path(__file__).parent.parent / "feature_repo"
store = FeatureStore(repo_path=str(REPO_PATH))

print("=" * 60)
print("STEP 1: Load entity dataframe (labels + timestamps)")
print("=" * 60)

# Entity DF = danh sach can lay feature
# Cot bat buoc: join_key cua entity + event_timestamp
entity_df = pd.read_parquet(REPO_PATH / "data" / "labels.parquet")
print(f"Entity DF shape: {entity_df.shape}")
print(entity_df.head())
print(f"\nLabel distribution:\n{entity_df['churned'].value_counts()}")

print("\n" + "=" * 60)
print("STEP 2: Get historical features - POINT-IN-TIME JOIN")
print("=" * 60)

# Day la API quan trong nhat
# Feast se:
# 1. Voi moi row (user_id, event_timestamp) trong entity_df
# 2. Tim trong source cua moi feature view: row co cung user_id 
#    va event_timestamp <= query timestamp, lay row MOI NHAT
# 3. Loai bo neu vuot qua TTL
# 4. Tra ve dataframe ket hop
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        # Format: "feature_view_name:feature_name"
        "user_demographics:age",
        "user_demographics:country",
        "user_transaction_stats:avg_purchase_7d",
        "user_transaction_stats:total_orders_30d",
        "user_transaction_stats:days_since_last_purchase",
    ],
).to_df()

print(f"Training DF shape: {training_df.shape}")
print(f"Columns: {list(training_df.columns)}")
print(training_df.head())

print("\n" + "=" * 60)
print("STEP 3: Train model")
print("=" * 60)

# One-hot encode country
training_df = pd.get_dummies(training_df, columns=["country"], prefix="country")

# Drop rows co NaN (TTL het han, khong co feature)
before = len(training_df)
training_df = training_df.dropna()
print(f"Dropped {before - len(training_df)} rows with NaN (TTL expired)")

# Features va label
feature_cols = [c for c in training_df.columns 
                if c not in ["user_id", "event_timestamp", "churned"]]
X = training_df[feature_cols]
y = training_df["churned"]

print(f"Final training shape: X={X.shape}, y={y.shape}")
print(f"Feature columns: {feature_cols}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print(f"\nAUC: {roc_auc_score(y_test, y_proba):.3f}")
print(f"\nClassification report:\n{classification_report(y_test, y_pred)}")

# Save model
import joblib
MODEL_PATH = Path(__file__).parent / "model.pkl"
joblib.dump({"model": model, "feature_cols": feature_cols}, MODEL_PATH)
print(f"\n[OK] Model saved to {MODEL_PATH}")
