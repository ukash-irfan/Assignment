from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_version
from src.clustering import RFM_COLS, transform_rfm
from src.policy import select_cluster_policy

def save_workflow_bundle(output_path, scaler, kmeans_model, mode, k, cutoff_str, eligibility_rules, ranking_policy, cluster_weights):
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "feature_names": list(RFM_COLS),
        "feature_definitions": {
            "Recency": "Days from latest valid positive purchase before cutoff to cutoff midnight",
            "Frequency": "Count of distinct valid positive purchase invoices before cutoff",
            "Monetary": "Sum of Quantity * UnitPrice (GBP) across valid positive purchases before cutoff",
        },
        "representation_mode": mode,
        "k": int(k),
        "cutoff": str(cutoff_str),
        "eligibility_rules": eligibility_rules,
        "ranking_policy": ranking_policy,
        "cluster_weights": cluster_weights,
        "scaler": scaler,
        "kmeans": kmeans_model,
        "saved_at_utc": datetime.utcnow().isoformat(),
        "versions": {"python": "3.x", "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn_version, "joblib": joblib.__version__},
    }
    joblib.dump(bundle, p)
    return p

def load_workflow_bundle(bundle_path):
    return joblib.load(Path(bundle_path))

def validate_rfm_input(df, expected_features):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    missing = [c for c in expected_features if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required RFM columns: {missing}")
    sub = df[expected_features].copy()
    if sub.isna().any().any():
        raise ValueError("RFM input contains missing values")
    arr = sub.to_numpy(dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError("RFM input contains non-finite values")
    if (sub["Recency"] < 0).any():
        raise ValueError("Recency must be non-negative")
    if (sub["Frequency"] < 1).any():
        raise ValueError("Frequency must be at least 1")
    if (sub["Monetary"] <= 0).any():
        raise ValueError("Monetary must be positive")
    return sub

def assign_existing_clusters(bundle, rfm_df):
    ordered = validate_rfm_input(rfm_df, bundle["feature_names"])
    X_scaled, _ = transform_rfm(ordered, mode=bundle["representation_mode"], scaler=bundle["scaler"])
    return bundle["kmeans"].predict(X_scaled)

def generate_contact_list_from_bundle(bundle, rfm_df):
    labels = assign_existing_clusters(bundle, rfm_df)
    return select_cluster_policy(rfm_df, labels, cluster_weights=bundle.get("cluster_weights"))