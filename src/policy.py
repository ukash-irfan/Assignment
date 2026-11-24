import math
import numpy as np
import pandas as pd

CONTACT_COST_GBP = 2.0
MAX_CONTACTS = 200

def compute_contact_budget(n_eligible):
    if n_eligible <= 0:
        return 0
    return min(MAX_CONTACTS, math.floor(0.10 * n_eligible))

def select_baseline_monetary(rfm_df):
    b = compute_contact_budget(len(rfm_df))
    if b == 0:
        return rfm_df.iloc[0:0].copy()
    ordered = rfm_df.sort_values(["Monetary", "CustomerID"], ascending=[False, True]).reset_index(drop=True)
    selected = ordered.iloc[:b].copy()
    selected["rank"] = np.arange(1, len(selected) + 1)
    selected["reason"] = "Top past Monetary baseline; tie-broken by CustomerID"
    return selected

def select_cluster_policy(rfm_df, labels, cluster_weights=None):
    b = compute_contact_budget(len(rfm_df))
    if b == 0:
        return rfm_df.iloc[0:0].copy()
    df = rfm_df.copy()
    df["cluster"] = labels
    clusters = sorted(df["cluster"].unique())
    if cluster_weights is None:
        cluster_weights = {c: 1.0 / len(clusters) for c in clusters}
    raw_quotas = {c: b * float(cluster_weights.get(c, 0.0)) for c in clusters}
    quotas = {c: int(math.floor(raw_quotas[c])) for c in clusters}
    remainder = b - sum(quotas.values())
    frac_order = sorted(clusters, key=lambda c: (-(raw_quotas[c] - quotas[c]), c))
    for c in frac_order:
        if remainder <= 0:
            break
        quotas[c] += 1
        remainder -= 1
    ranked_per_cluster = {}
    for c in clusters:
        sub = df.loc[df["cluster"] == c].copy()
        sub["priority_score"] = sub["Monetary"] / (1.0 + sub["Recency"])
        sub = sub.sort_values(["priority_score", "Frequency", "Monetary", "CustomerID"], ascending=[False, False, False, True]).reset_index(drop=True)
        ranked_per_cluster[c] = sub
    chosen_parts = []
    used_counts = {c: 0 for c in clusters}
    spare_slots = 0
    for c in clusters:
        avail = len(ranked_per_cluster[c])
        take = min(quotas[c], avail)
        spare_slots += (quotas[c] - take)
        used_counts[c] = take
        if take > 0:
            part = ranked_per_cluster[c].iloc[:take].copy()
            part["allocation_type"] = "quota"
            chosen_parts.append(part)
    if spare_slots > 0:
        leftover_pool = []
        for c in clusters:
            rem_rows = ranked_per_cluster[c].iloc[used_counts[c]:].copy()
            if len(rem_rows) > 0:
                leftover_pool.append(rem_rows)
        if leftover_pool:
            pool_df = pd.concat(leftover_pool, ignore_index=True)
            pool_df = pool_df.sort_values(["priority_score", "Frequency", "Monetary", "CustomerID"], ascending=[False, False, False, True]).reset_index(drop=True)
            extra = pool_df.iloc[:spare_slots].copy()
            extra["allocation_type"] = "reallocated_spare"
            chosen_parts.append(extra)
    result = pd.concat(chosen_parts, ignore_index=True) if chosen_parts else df.iloc[0:0].copy()
    result = result.drop_duplicates(subset=["CustomerID"], keep="first").iloc[:b].copy()
    result = result.sort_values(["priority_score", "Frequency", "Monetary", "CustomerID"], ascending=[False, False, False, True]).reset_index(drop=True)
    result["rank"] = np.arange(1, len(result) + 1)
    result["reason"] = result.apply(lambda r: f"Cluster {int(r['cluster'])} ({r['allocation_type']}); score={r['priority_score']:.4f}, M={r['Monetary']:.2f}, R={int(r['Recency'])}", axis=1)
    return result

def evaluate_contact_list(selected_df, later_window_df, total_eligible_n):
    b = len(selected_df)
    cost_gbp = b * CONTACT_COST_GBP
    merged = selected_df[["CustomerID"]].merge(later_window_df, on="CustomerID", how="left")
    merged["window_spend_gbp"] = merged["window_spend_gbp"].fillna(0.0)
    merged["repeat_purchaser"] = merged["repeat_purchaser"].fillna(0).astype(int)
    total_cohort_spend = float(later_window_df["window_spend_gbp"].sum())
    repeat_rate = float(merged["repeat_purchaser"].mean()) if b > 0 else np.nan
    spend_per_selected = float(merged["window_spend_gbp"].mean()) if b > 0 else np.nan
    captured_spend_share = float(merged["window_spend_gbp"].sum() / total_cohort_spend) if total_cohort_spend > 0 else np.nan
    cohort_coverage = float(b / len(later_window_df)) if len(later_window_df) > 0 else np.nan
    eligible_coverage = float(b / total_eligible_n) if total_eligible_n > 0 else np.nan
    return {
        "selected_count": int(b),
        "contact_cost_gbp": float(cost_gbp),
        "repeat_purchase_rate": repeat_rate,
        "spend_per_selected_gbp": spend_per_selected,
        "captured_spend_share": captured_spend_share,
        "cohort_coverage": cohort_coverage,
        "eligible_coverage": eligible_coverage,
    }