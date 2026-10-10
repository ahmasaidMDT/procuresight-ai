"""Automated checks for the reusable compliance predictor."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from procuresight_ai.prediction import CompliancePredictor


@pytest.fixture(scope="module")
def predictor():
    project_root = Path(__file__).resolve().parents[1]
    return CompliancePredictor(project_root / "models")


@pytest.fixture
def orders():
    return pd.DataFrame({
        "Supplier": ["Alpha_Inc", "Beta_Supplies"],
        "Item_Category": ["Electronics", "Electronics"],
        "Quantity": [10, 20],
        "Unit_Price": [100.0, 150.0],
        "Negotiated_Price": [90.0, 140.0],
    }, index=[101, 205])


def test_batch_matches_individual_predictions(predictor, orders):
    """Batch processing must preserve order and individual results."""
    batch = predictor.predict(orders)

    individual = pd.concat([
        predictor.predict(orders.iloc[[position]])
        for position in range(len(orders))
    ])

    pd.testing.assert_frame_equal(batch, individual)
    assert batch.index.equals(orders.index)
    assert batch["Compliance_Risk_Score"].between(0, 1).all()


def test_missing_column_is_rejected(predictor, orders):
    incomplete = orders.drop(columns="Quantity")

    with pytest.raises(ValueError, match="Missing required columns"):
        predictor.predict(incomplete)


@pytest.mark.parametrize(
    "invalid_value",
    [0, -1, np.nan, np.inf, "invalid", True],
)
def test_invalid_quantity_is_rejected(
    predictor, orders, invalid_value
):
    invalid = orders.astype({"Quantity": object})
    invalid.loc[101, "Quantity"] = invalid_value

    with pytest.raises(ValueError, match="Quantity"):
        predictor.predict(invalid)


def test_blank_supplier_is_rejected(predictor, orders):
    invalid = orders.copy()
    invalid.loc[101, "Supplier"] = " "

    with pytest.raises(ValueError, match="Supplier"):
        predictor.predict(invalid)


def test_empty_batch_returns_empty_results(predictor, orders):
    result = predictor.predict(orders.iloc[:0])

    assert result.empty
    assert list(result.columns) == [
        "Compliance_Risk_Score",
        "Review_Flag",
    ]