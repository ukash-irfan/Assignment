import hashlib
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd

NON_MERCHANDISE_CODES = {"POST", "D", "M", "BANK CHARGES", "PADS", "DOT", "CRUK", "B"}

def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_and_audit_retail(xlsx_path, download_date=None):
    path = Path(xlsx_path)
    sha256 = compute_sha256(path)
    df = pd.read_excel(path, dtype={"InvoiceNo": str, "CustomerID": str, "StockCode": str})
    df["InvoiceNo"] = df["InvoiceNo"].str.strip()
    df["CustomerID"] = df["CustomerID"].str.strip()
    df.loc[df["CustomerID"].isin(["", "nan", "None"]), "CustomerID"] = np.nan
    df["StockCode"] = df["StockCode"].str.strip().str.upper()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["LineValue"] = df["Quantity"] * df["UnitPrice"]
    uk_mask = df["Country"].astype(str).str.strip().eq("United Kingdom")
    uk_df = df.loc[uk_mask].copy()
    is_cancel = uk_df["InvoiceNo"].str.startswith("C", na=False)
    is_missing_cid = uk_df["CustomerID"].isna()
    is_bad_qty_price = uk_df["Quantity"].isna() | uk_df["UnitPrice"].isna() | (uk_df["Quantity"] <= 0) | (uk_df["UnitPrice"] <= 0)
    is_non_merch = uk_df["StockCode"].isin(NON_MERCHANDISE_CODES)
    dup_mask = uk_df.duplicated(keep="first")
    audit_records = [
        {"stage": "0_raw_all_countries", "rows": len(df), "line_value_gbp": float(df["LineValue"].sum(skipna=True))},
        {"stage": "1_uk_only", "rows": len(uk_df), "line_value_gbp": float(uk_df["LineValue"].sum(skipna=True))},
        {"stage": "2_cancellations_C", "rows": int(is_cancel.sum()), "line_value_gbp": float(uk_df.loc[is_cancel, "LineValue"].sum(skipna=True))},
        {"stage": "3_missing_CustomerID", "rows": int(is_missing_cid.sum()), "line_value_gbp": float(uk_df.loc[is_missing_cid, "LineValue"].sum(skipna=True))},
        {"stage": "4_zero_or_negative_qty_or_price", "rows": int(is_bad_qty_price.sum()), "line_value_gbp": float(uk_df.loc[is_bad_qty_price, "LineValue"].sum(skipna=True))},
        {"stage": "5_non_merchandise_stockcode", "rows": int(is_non_merch.sum()), "line_value_gbp": float(uk_df.loc[is_non_merch, "LineValue"].sum(skipna=True))},
        {"stage": "6_exact_duplicates", "rows": int(dup_mask.sum()), "line_value_gbp": float(uk_df.loc[dup_mask, "LineValue"].sum(skipna=True))},
    ]
    valid_mask = (~is_cancel) & (~is_missing_cid) & (~is_bad_qty_price) & (~is_non_merch) & (~dup_mask) & uk_df["InvoiceDate"].notna()
    clean_uk_df = uk_df.loc[valid_mask].sort_values(["InvoiceDate", "InvoiceNo"]).reset_index(drop=True)
    audit_records.append({"stage": "7_valid_positive_uk_txns", "rows": len(clean_uk_df), "line_value_gbp": float(clean_uk_df["LineValue"].sum())})
    audit_df = pd.DataFrame(audit_records)
    audit_df["sha256"] = sha256
    audit_df["download_date"] = download_date or datetime.now().strftime("%Y-%m-%d")
    return clean_uk_df, audit_df, uk_df.loc[is_cancel | (uk_df["Quantity"] < 0)].copy()

def build_rfm_at_cutoff(clean_uk_df, cutoff_ts):
    cutoff = pd.Timestamp(cutoff_ts)
    prior = clean_uk_df.loc[clean_uk_df["InvoiceDate"] < cutoff].copy()
    assert (prior["InvoiceDate"] < cutoff).all()
    assert (prior["Quantity"] > 0).all() and (prior["UnitPrice"] > 0).all()
    assert not prior["InvoiceNo"].str.startswith("C", na=False).any()
    grouped = prior.groupby("CustomerID", as_index=False).agg(
        last_purchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("LineValue", "sum"),
    )
    grouped["Recency"] = (cutoff - grouped["last_purchase"]).dt.days
    rfm = grouped[["CustomerID", "Recency", "Frequency", "Monetary"]].sort_values("CustomerID").reset_index(drop=True)
    assert rfm["CustomerID"].is_unique
    assert np.isfinite(rfm[["Recency", "Frequency", "Monetary"]]).all().all()
    assert (rfm["Recency"] >= 0).all() and (rfm["Frequency"] >= 1).all() and (rfm["Monetary"] > 0).all()
    return rfm

def summarize_later_window(clean_uk_df, start_ts, end_ts, eligible_customer_ids):
    start = pd.Timestamp(start_ts)
    end = pd.Timestamp(end_ts)
    first_ever = clean_uk_df.groupby("CustomerID")["InvoiceDate"].min()
    new_in_window = set(first_ever.loc[(first_ever >= start) & (first_ever < end)].index)
    cohort_ids = set(eligible_customer_ids) - new_in_window
    window_txns = clean_uk_df.loc[(clean_uk_df["InvoiceDate"] >= start) & (clean_uk_df["InvoiceDate"] < end) & (clean_uk_df["CustomerID"].isin(cohort_ids))]
    spend_by_cid = window_txns.groupby("CustomerID")["LineValue"].sum()
    inv_by_cid = window_txns.groupby("CustomerID")["InvoiceNo"].nunique()
    out = pd.DataFrame({"CustomerID": sorted(cohort_ids)})
    out["window_spend_gbp"] = out["CustomerID"].map(spend_by_cid).fillna(0.0)
    out["window_invoices"] = out["CustomerID"].map(inv_by_cid).fillna(0).astype(int)
    out["repeat_purchaser"] = (out["window_invoices"] >= 1).astype(int)
    return out