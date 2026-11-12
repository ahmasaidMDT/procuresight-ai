import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from procuresight_ai.prediction import CompliancePredictor

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"

compliance = CompliancePredictor(MODEL_DIR)
anomaly = joblib.load(MODEL_DIR / "anomaly_isolation_forest.joblib")
anomaly_settings = json.loads(
    (MODEL_DIR / "anomaly_settings.json").read_text(encoding="utf-8")
)

app = FastAPI(title="ProcureSight AI")


class PurchaseOrder(BaseModel):
    model_config = ConfigDict(
        strict=True, extra="forbid", str_strip_whitespace=True
    )

    Supplier: str = Field(min_length=1)
    Item_Category: str = Field(min_length=1)
    Quantity: float = Field(gt=0, allow_inf_nan=False)
    Unit_Price: float = Field(gt=0, allow_inf_nan=False)
    Negotiated_Price: float = Field(gt=0, allow_inf_nan=False)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(order: PurchaseOrder):
    raw = order.model_dump()
    negotiated_value = order.Quantity * order.Negotiated_Price
    discount = 100 * (
        (order.Unit_Price - order.Negotiated_Price) / order.Unit_Price
    )

    if not np.isfinite([negotiated_value, discount]).all():
        raise HTTPException(
            status_code=422, detail="Derived order values must be finite."
        )

    anomaly_inputs = pd.DataFrame([{
        **raw,
        "Negotiated_Order_Value": negotiated_value,
        "Discount_Percent": discount,
    }])[anomaly_settings["features"]]

    risk = compliance.predict(pd.DataFrame([raw])).iloc[0]
    anomaly_score = float(-anomaly.score_samples(anomaly_inputs)[0])

    return {
        "compliance": {
            "risk_score": float(risk["Compliance_Risk_Score"]),
            "review_flag": bool(risk["Review_Flag"]),
        },
        "anomaly": {
            "score": anomaly_score,
            "review_flag": anomaly_score >= anomaly_settings["threshold"],
        },
    }