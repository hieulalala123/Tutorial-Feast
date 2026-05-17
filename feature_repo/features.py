"""
Feature definitions - With advance features

Bổ sung:
1. On-demand Feature View: Tính feature từ Request Runtime

2. Feature Service: Đóng gói feature cho model version

"""

from datetime import timedelta
import pandas as pd
from feast import FeatureService, FeatureView, Field, FileSource, RequestSource
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import Float32, Float64, Int64, String

from entities import user

#=====================================
# DATA SOURCES
#=====================================

user_demographics_source = FileSource(
    name="user_demographic_source",
    path="/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/feature_repo/data/user_demographics.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created"
)


user_transactions_source = FileSource(
    name="user_transaction_source",
    path="/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/feature_repo/data/user_transactions.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created",
)

#=====================================
# BATCH FEATURE VIEWS 
#=====================================
# fv = feature view
user_demographics_fv = FeatureView(
    name="user_demographics",
    entities=[user],
    ttl=timedelta(days=365),
    schema=[
        Field(name="age", dtype=Int64),
        Field(name="country", dtype=String),
    ],
    source=user_demographics_source,
    online=True,
    tags={"category":"demographic"},
)

user_transaction_stats_fv = FeatureView(
    name="user_transaction_stats",
    entities=[user],
    ttl=timedelta(days=365),
    schema=[
        Field(name="avg_purchase_7d", dtype=Float32),
        Field(name="total_orders_30d", dtype=Int64),
        Field(name="days_since_last_purchase", dtype=Int64),
    ],
    source=user_transactions_source,
    online=True,
    tags={"category":"behavioral"},
)


#====================================
# ON-DEMAND FEATURE VIEW (ADVANCED)
#====================================

# Feature được tính từ REQUEST + feature batch tại thời điểm inference

# Request source: data dựa vào lúc Serve, không Pre-Compute được

transaction_request = RequestSource(
    name="transaction_request",
    schema=[
        Field(name="current_purchase_amount", dtype=Float64),
    ],
)

"""
user_transaction_stats_fv, # Feature từ batch (precomputed):
Nguồn gốc: Dữ liệu này lấy ra từ Online Store (file online_store.db SQLite của bạn).

Đặc điểm: Đây là các chỉ số mang tính chất lịch sử, đã được tính toán sẵn từ trước theo lô (batch) 
và được đẩy vào database thông qua lệnh feast materialize.

Ví dụ thực tế: Các chỉ số như: Tổng số tiền user đã tiêu trong 30 ngày qua, 
Số lần quẹt thẻ thất bại trong tuần trước. Những con số này không đổi sau mỗi giây, 
nên việc lưu sẵn trong DB giúp truy xuất cực nhanh.
-----------------------
transaction_request  #feature từ request runtime -- 

Nguồn gốc: Dữ liệu này không nằm trong database. 
Nó do ứng dụng phía Client (ví dụ: app ngân hàng hoặc app thanh toán của bạn) truyền trực tiếp lên cùng 
với câu lệnh gọi API tại đúng mili-giây xảy ra giao dịch.

Đặc điểm: Đây là dữ liệu mang tính bối cảnh (Contextual data), c
hỉ xuất hiện và có ý nghĩa ngay tại thời điểm đó.

Ví dụ thực tế: Số tiền của giao dịch hiện tại đang thực hiện, 
Kênh thanh toán (Web hay App), Vị trí GPS của thiết bị lúc bấm nút thanh toán.

"""
@on_demand_feature_view(
sources = [
    user_transaction_stats_fv, # Feature từ batch (precomputed)
    transaction_request, #feature từ request runtime -- 
],
schema=[
    Field(name="purchase_to_avg_ratio",dtype=Float32),
    Field(name="is_unusual_purchase", dtype=Int64),
],
)

def transaction_anomaly_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """
    Tính 2 feature anomaly từ runtime:
    - purchase_to_avg_ratio: giao dịch hiện tại gấp mấy lần trung bình trong 7 ngày trước
    - is_unsual_purchase: =1 nếu cao hơn 3 lần trung bình

    Use case: Fraud detection real-time
    """

    df = pd.DataFrame()
    df["purchase_to_avg_ratio"] = (inputs["current_purchase_amount"] / inputs["avg_purchase_7d"]).clip(lower=1).astype("float32")
    df["is_unusual_purchase"] = (df["purchase_to_avg_ratio"] > 3.0).astype("int64")
    return df


# ===============================================
# FEATURE SERVICES - đóng gói cho từng Model
# ===============================================

churn_model_v1 = FeatureService(
    name="churn_model_v1", 
    features=[
        user_demographics_fv,
        user_transaction_stats_fv,
    ],
    tags={"model":"churn", "version":"1.0"},
    description="Features cho Churn model version 1 - Batch only"
)

churn_model_v2 = FeatureService(
    name="churn_model_v2",
    features=[
        user_demographics_fv,
        user_transaction_stats_fv,
        transaction_anomaly_features, # On-demand features
    ],
    tags=  {"model": "churn","version":"2.0"},
    description="Features for churn model v2 - với ANOMALY DETECTION REAL-TIME"
)

