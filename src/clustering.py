import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

RFM_COLS = ["Recency", "Frequency", "Monetary"]

def cap_monetary_percentile(rfm_df, percentile=99.0):
    out = rfm_df.copy()
    cap_val = float(np.percentile(out["Monetary"].to_numpy(dtype=float), percentile))
    out["Monetary"] = np.minimum(out["Monetary"].to_numpy(dtype=float), cap_val)
    return out, cap_val

def transform_rfm(rfm_df, mode="raw_scaled", scaler=None):
    X = rfm_df[RFM_COLS].to_numpy(dtype=float)
    if mode == "raw_scaled":
        X_repr = X
    elif mode == "log1p_scaled":
        X_repr = np.log1p(X)
    else:
        raise ValueError("Unsupported representation mode")
    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_repr)
    else:
        X_scaled = scaler.transform(X_repr)
    return X_scaled, scaler

def evaluate_k_grid(rfm_df, mode="raw_scaled", k_values=(2, 3, 4, 5, 6), random_state=42, n_init=20):
    X_scaled, _ = transform_rfm(rfm_df, mode=mode, scaler=None)
    rows = []
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        labels = km.fit_predict(X_scaled)
        sil = float(silhouette_score(X_scaled, labels))
        counts = pd.Series(labels).value_counts().to_dict()
        rows.append({
            "representation": mode,
            "k": k,
            "inertia": float(km.inertia_),
            "silhouette": sil,
            "min_cluster_size": int(min(counts.values())),
            "max_cluster_size": int(max(counts.values())),
            "cluster_sizes": str(dict(sorted(counts.items()))),
        })
    return pd.DataFrame(rows)

def cluster_profiles_original_units(rfm_df, labels):
    df = rfm_df.copy()
    df["cluster"] = labels
    rows = []
    for c, grp in df.groupby("cluster"):
        rows.append({
            "cluster": int(c),
            "count": int(len(grp)),
            "share": float(len(grp) / len(df)),
            "recency_mean": float(grp["Recency"].mean()),
            "recency_median": float(grp["Recency"].median()),
            "frequency_mean": float(grp["Frequency"].mean()),
            "frequency_median": float(grp["Frequency"].median()),
            "monetary_mean": float(grp["Monetary"].mean()),
            "monetary_median": float(grp["Monetary"].median()),
            "monetary_sum": float(grp["Monetary"].sum()),
        })
    return pd.DataFrame(rows).sort_values("cluster").reset_index(drop=True)

def seed_stability_ari(rfm_df, mode="log1p_scaled", k=4, seeds=(1, 10, 21, 42, 100), n_init=20):
    X_scaled, _ = transform_rfm(rfm_df, mode=mode, scaler=None)
    ref_model = KMeans(n_clusters=k, random_state=42, n_init=n_init).fit(X_scaled)
    ref_labels = ref_model.labels_
    out = []
    for s in seeds:
        m = KMeans(n_clusters=k, random_state=s, n_init=n_init).fit(X_scaled)
        out.append({"seed": s, "ari_vs_seed_42": float(adjusted_rand_score(ref_labels, m.labels_))})
    return pd.DataFrame(out)

def fit_pca_2d(X_scaled, labels, random_state=42):
    pca = PCA(n_components=2, random_state=random_state)
    coords = pca.fit_transform(X_scaled)
    df = pd.DataFrame({"pc1": coords[:, 0], "pc2": coords[:, 1], "cluster": labels})
    return df, pca.explained_variance_ratio_