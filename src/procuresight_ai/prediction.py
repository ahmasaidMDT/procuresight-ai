"""Load the frozen compliance model and score procurement orders."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier


class CompliancePredictor:
    """Provide review scores using the exported model and threshold."""

    def __init__(self, model_dir: str | Path):
        model_dir = Path(model_dir)

        self.settings = json.loads(
            (model_dir / "compliance_settings.json").read_text(
                encoding="utf-8"
            )
        )

        self.features = self.settings["features"]
        self.threshold = float(self.settings["threshold"])

        if not 0 <= self.threshold <= 1:
            raise ValueError("The threshold must be between 0 and 1.")

        self.model = CatBoostClassifier()
        self.model.load_model(
            str(model_dir / "compliance_catboost.cbm")
        )

        if list(self.model.feature_names_) != self.features:
            raise ValueError("Model features do not match the settings.")

        self.positive_index = list(self.model.classes_).index(
            self.settings["positive_class"]
        )

    def predict(self, orders: pd.DataFrame) -> pd.DataFrame:
        """Validate inputs and return scores and human-review flags."""
        if not orders.columns.is_unique:
            raise ValueError("Input column names must be unique.")

        missing = [
            feature for feature in self.features
            if feature not in orders.columns
        ]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        inputs = orders[self.features].copy()

        for column in self.settings["categorical_features"]:
            valid = inputs[column].map(
                lambda value: (
                    isinstance(value, str) and bool(value.strip())
                )
            )
            if not valid.all():
                raise ValueError(
                    f"{column} must contain non-empty text."
                )

        for column in [
            "Quantity", "Unit_Price", "Negotiated_Price"
        ]:
            if inputs[column].map(
                lambda value: isinstance(value, (bool, np.bool_))
            ).any():
                raise ValueError(f"{column} cannot contain booleans.")

            values = pd.to_numeric(
                inputs[column], errors="coerce"
            ).to_numpy(dtype=float, na_value=np.nan)

            if not np.isfinite(values).all():
                raise ValueError(
                    f"{column} must contain finite numeric values."
                )
            if (values <= 0).any():
                raise ValueError(
                    f"{column} must contain positive values."
                )

            inputs[column] = values

        if inputs.empty:
            return pd.DataFrame({
                "Compliance_Risk_Score": pd.Series(
                    index=orders.index, dtype=float
                ),
                "Review_Flag": pd.Series(
                    index=orders.index, dtype=bool
                ),
            })

        scores = self.model.predict_proba(inputs)[
            :, self.positive_index
        ]

        return pd.DataFrame({
            "Compliance_Risk_Score": scores,
            "Review_Flag": scores >= self.threshold,
        }, index=orders.index)