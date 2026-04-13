"""
No-Show Predictor using XGBoost
Predicts probability that a confirmed booking will be a no-show.
"""
import numpy as np
from datetime import datetime
import joblib, os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "noshow_model.joblib")
_model = None


def _train_and_save():
    from xgboost import XGBClassifier
    np.random.seed(42)
    n = 3000
    days_ahead = np.random.randint(0, 30, n)
    hour = np.random.randint(6, 23, n)
    amount = np.random.uniform(200, 2000, n)
    loyalty_pts = np.random.randint(0, 500, n)
    prior_noshow = np.random.randint(0, 5, n)
    source_chatbot = np.random.randint(0, 2, n)

    # Higher no-show: far ahead, low amount, no loyalty, high prior no-show
    prob = (
        0.05
        + 0.01 * days_ahead
        + 0.1 * prior_noshow
        - 0.00005 * amount
        - 0.0002 * loyalty_pts
        + 0.05 * source_chatbot
    )
    prob = np.clip(prob, 0.01, 0.95)
    labels = np.random.binomial(1, prob)

    X = np.column_stack([days_ahead, hour, amount, loyalty_pts, prior_noshow, source_chatbot])
    model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, use_label_encoder=False)
    model.fit(X, labels)
    joblib.dump(model, MODEL_PATH)
    return model


def _load():
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = joblib.load(MODEL_PATH)
        else:
            _model = _train_and_save()


def predict_noshow(
    days_ahead: int,
    hour: int,
    amount: float,
    loyalty_pts: int,
    prior_noshows: int,
    source: str,
) -> float:
    """Returns probability [0, 1] that user will no-show."""
    _load()
    source_chatbot = 1 if source == "chatbot" else 0
    X = np.array([[days_ahead, hour, amount, loyalty_pts, prior_noshows, source_chatbot]])
    prob = float(_model.predict_proba(X)[0][1])
    return round(prob, 4)
