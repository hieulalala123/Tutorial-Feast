"""
DEMO: Point-in-time join: Chống Data Leakage

Giải thích cơ chế bằng ví dụ đơn giản như:

VD1. User có 1 transactions tại các timestamp khác nhau
Ta đi query feature tại timestamp T
Feast tự dộng tìm Row có timestamp <= T và Mới nhất

"""

import pandas as pd
from feast import FeatureStore
from pathlib import Path

import pandas as pd
from feast import FeatureStore
from pathlib import Path
 
REPO_PATH = Path("/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/feature_repo")
store = FeatureStore(repo_path=str(REPO_PATH))
 
# Xem raw transactions cua user_id=1
print("=" * 60)
print("RAW DATA: Transactions cua user_id=1")
print("=" * 60)
tx_df = pd.read_parquet(REPO_PATH / "data" / "user_transactions.parquet")
user1_tx = tx_df[tx_df["user_id"] == 1].sort_values("event_timestamp")
print(user1_tx[["event_timestamp", "avg_purchase_7d", "total_orders_30d"]].head(10))
 
# Query feature tai 3 thoi diem khac nhau
print("\n" + "=" * 60)
print("QUERY: Lay feature cua user_id=1 tai 3 thoi diem")
print("=" * 60)
 
query_df = pd.DataFrame({
    "user_id": [1, 1, 1],
    "event_timestamp": pd.to_datetime([
        "2024-02-01",  # Som
        "2024-04-15",  # Giua
        "2024-06-20",  # Muon
    ]),
})
 
result = store.get_historical_features(
    entity_df=query_df,
    features=[
        "user_transaction_stats:avg_purchase_7d",
        "user_transaction_stats:total_orders_30d",
    ],
).to_df()
 
print(result)
 
print("\n" + "=" * 60)
print("KET LUAN")
print("=" * 60)
print("""
Voi moi query timestamp, Feast tu dong:
1. Tim moi row co user_id=1 va timestamp <= query timestamp  
2. Lay row MOI NHAT trong so do (closest in past)
3. Loai bo neu vuot qua TTL (30 ngay voi feature view nay)
 
-> Khong bao gio bi data leakage tu tuong lai!
-> Khong bao gio dung feature qua cu (TTL bao ve)!
""")