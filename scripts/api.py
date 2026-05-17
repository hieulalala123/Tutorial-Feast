# Tạo FastAPI Service

"""
FastAPI inference service tich hop voi Feast Online Store.

Production-ready features:
- Stateless: khong luu trang thai trong RAM
- Health check endpoint
- Async support
- Proper error handling
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from feast import FeatureStore
from pydantic import BaseModel

# ============================================================
# CONFIG
# ============================================================
REPO_PATH =  Path("/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/feature_repo")
MODEL_PATH = Path("/home/trunghieu/projects/my-feast-project/Customer-Churn-Prediction/scripts/model.pkl")

# Globals duoc load 1 lan luc startup - stateless cho moi request
state = {}


# ============================================================
# LIFESPAN: Load model + feast store khi startup
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Loading Feast store...")
    state["store"] = FeatureStore(repo_path=str(REPO_PATH))
    
    print("[STARTUP] Loading model...")
    model_data = joblib.load(MODEL_PATH)
    state["model"] = model_data["model"]
    state["feature_cols"] = model_data["feature_cols"]
    
    print("[STARTUP] Ready!")
    yield
    print("[SHUTDOWN] Cleaning up...")
    state.clear()


app = FastAPI(
    title="Churn Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================
class PredictRequest(BaseModel):
    user_ids: List[int]


class PredictResponse(BaseModel):
    user_id: int
    churn_probability: float
    risk_level: str
    features_used: dict


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/health")
async def health():
    """Health check - K8s dung de biet pod san sang."""
    return {
        "status": "ok",
        "model_loaded": "model" in state,
        "store_loaded": "store" in state,
    }


@app.post("/predict", response_model=List[PredictResponse])
async def predict(request: PredictRequest):
    """
    Predict churn probability cho danh sach user.
    
    Workflow:
    1. Get online features tu Feast
    2. Preprocess
    3. Model predict
    4. Return
    """
    try:
        store: FeatureStore = state["store"]
        model = state["model"]
        feature_cols = state["feature_cols"]
        
        # Step 1: Fetch features tu online store
        entity_rows = [{"user_id": uid} for uid in request.user_ids]
        features = store.get_online_features(
            features=[
                "user_demographics:age",
                "user_demographics:country",
                "user_transaction_stats:avg_purchase_7d",
                "user_transaction_stats:total_orders_30d",
                "user_transaction_stats:days_since_last_purchase",
            ],
            entity_rows=entity_rows,
        ).to_dict()
        
        # Step 2: Preprocess
        df = pd.DataFrame(features)
        
        # Validate: kiem tra co user nao bi missing feature khong
        if df.isnull().any().any():
            missing_users = df[df.isnull().any(axis=1)]["user_id"].tolist()
            raise HTTPException(
                status_code=404,
                detail=f"Features missing for users: {missing_users}",
            )
        
        # One-hot encode country
        df_features = pd.get_dummies(df, columns=["country"], prefix="country")
        for col in feature_cols:
            if col not in df_features.columns:
                df_features[col] = 0
        X = df_features[feature_cols]
        
        # Step 3: Predict
        probabilities = model.predict_proba(X)[:, 1]
        
        # Step 4: Build response
        results = []
        for i, uid in enumerate(request.user_ids):
            prob = float(probabilities[i])
            results.append(PredictResponse(
                user_id=uid,
                churn_probability=round(prob, 4),
                risk_level="HIGH" if prob > 0.5 else "LOW",
                features_used={
                    "age": int(features["age"][i]),
                    "country": features["country"][i],
                    "avg_purchase_7d": round(float(features["avg_purchase_7d"][i]), 2),
                    "total_orders_30d": int(features["total_orders_30d"][i]),
                },
            ))
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feature-views")
async def list_feature_views():
    """List all feature views in registry - debug endpoint."""
    store = state["store"]
    fvs = store.list_feature_views()
    return [
        {
            "name": fv.name,
            "entities": [e for e in fv.entities],
            "features": [f.name for f in fv.features],
            "ttl_days": fv.ttl.days if fv.ttl else None,
        }
        for fv in fvs
    ]