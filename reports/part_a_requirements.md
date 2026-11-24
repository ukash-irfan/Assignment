# Part A: Problem Definition, Requirements, Stakeholders, and Workflow

## 1. One-Page Requirements Brief

### Main Decision Question
For United Kingdom online retail customers with at least one valid positive purchase before a given cutoff date, does segmenting customers via scaled RFM k-Means clustering and allocating outreach slots across clusters improve subsequent-month repeat purchasing and captured positive purchase value enough within a strict budget of $B = \min(200, \lfloor 0.10 \times N \rfloor)$ contacts (£2 per contact, maximum £400) to justify deploying a cluster-based contact policy instead of a simple top-Monetary baseline rule?

### Customer Eligibility Rules
- **Geographic scope:** Only transactions where `Country == "United Kingdom"` are included; all findings apply exclusively to UK customers.
- **Identity requirement:** `CustomerID` must be present (non-null) so purchases can be aggregated at the customer level.
- **Temporal boundary:** Only transactions strictly before the cutoff midnight (`InvoiceDate < cutoff`) are eligible.
- **Valid positive purchase definition:** `Quantity > 0`, `UnitPrice > 0`, `InvoiceNo` not starting with `"C"` (cancellations excluded to a separate audit log), non-merchandise stock codes (`POST`, `D`, `M`, `BANK CHARGES`, `PADS`, `DOT`, `CRUK`, `B`) excluded, and exact duplicate rows deduplicated.
- **Minimum activity:** Each eligible customer must have at least one valid positive purchase invoice before the cutoff ($N = 2,845$ before `2011-08-01`; $N = 2,986$ before `2011-09-01`).

### Measurable Objective and Coverage Definition
- **Primary Priority Objective (Effectiveness):** Maximize the **subsequent-month positive purchase value captured per contacted customer (GBP)** and **repeat purchase rate** among the $B$ contacted customers in the immediate post-cutoff evaluation month (`2011-08` for development; `2011-09` for final assessment), subject to $\text{cost} = 2 \times B \le £400$.
- **Coverage Measure:** Define **segment representation coverage** as the number of distinct behavioral clusters represented in the $B$ selected contacts (and the quota allocation across all $k$ groups), paired with **cohort coverage** $= B / N_{\text{cohort}}$ ($200 / 2,845 = 7.03\%$ at development; $200 / 2,986 = 6.70\%$ at final assessment).
- **Conflict Between Priority and Coverage:** Concentrating all $B$ slots on top spenders maximizes expected short-term GBP per contact but leaves low- and mid-tier behavioral groups unrepresented, whereas spreading slots across clusters increases behavioral coverage at the potential cost of lower immediate repeat spend.

### Acceptance Criteria
1. **Reproducibility:** Running the pipeline from raw `Online Retail.xlsx` (verified via SHA256 `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`) produces identical RFM tables, cluster labels, and ranked contact lists.
2. **Constraint Compliance:** Every contact list selects exactly $B = \min(200, \lfloor 0.10 \times N \rfloor)$ unique eligible customers, breaks ties deterministically via `CustomerID`, provides a per-customer reason, and keeps total cost $\le £400$.
3. **Zero Leakage:** No feature or clustering transformation uses records on or after the cutoff date, and the final selection procedure is frozen in Git prior to viewing September 2011 outcomes.
4. **Software & Validation Integrity:** Saved `joblib` bundle reloads cleanly, assigns new customer RFM rows without retraining, and fails explicitly on invalid inputs (such as missing columns or negative Recency).

### Discovering Groups vs. Predicting a Known Label
- **Discovering Groups (Unsupervised Clustering):** No ground-truth "best customer to contact" or "campaign response" label exists in the dataset. `k-Means` partitions customers into internal structure groups based on geometric proximity in scaled RFM space, requiring domain judgment, profile inspection, and downstream policy testing to verify usefulness.
- **Predicting a Known Label (Supervised Classification/Regression):** A target variable $y$ (such as churn or next-month purchase) is known during training, allowing direct optimization against labeled error metrics. Here, later-month purchases are used strictly as an external proxy to evaluate decision rules, not as training labels for clustering.

---

## 2. Stakeholder Table and Conflict Resolution

| Stakeholder | Core Needs & Priorities | Key Metric / Concern | Conflict With Other Stakeholders | Design Resolution / Visibility Mechanism |
| --- | --- | --- | --- | --- |
| **Sales** | Wants to contact top historical spenders to maximize immediate order value. | High GBP spend per contacted customer and captured revenue share. | Conflicts with **Account Managers** (who want multi-segment diversity rather than whale-only lists) and **Finance** (who caps total contacts at $B \le 200$). | Within each cluster, customers are ranked by `Monetary / (1 + Recency)` so high-value active buyers rise first, and performance is benchmarked directly against a pure top-Monetary baseline. |
| **Account Managers** | Wants outreach distributed across distinct buying behaviors (frequent buyers, recent newcomers, dormant customers) rather than one group. | Segment diversity across all $k$ behavioral clusters. | Conflicts with **Sales** because reserving slots for lower-spending segments reduces average past Monetary of the selected list. | Equal cluster quotas ($\lfloor B/k \rfloor$ with largest-remainder rounding and spare-slot reallocation) guarantee representation across all clusters while keeping segment counts explicit. |
| **Finance** | Wants a hard spending cap, clear unit cost tracking, and proof that clustering beats a simple baseline rule. | Total contact cost $\le £400$ ($B \le 200$ at £2/contact) and comparison vs. Monetary baseline. | Conflicts with **Sales** and **Account Managers** if either requests expanding outreach beyond $10\%$ of $N$ or $200$ contacts. | Hard budget enforcement $B = \min(200, \lfloor 0.10 \times N \rfloor)$ in code, automated assertions on cost/uniqueness, and side-by-side baseline comparison tables. |
| **Customers** | Prefer relevant, non-intrusive communication aligned with their actual shopping cadence rather than unsolicited spam. | Contact frequency, relevance, and data privacy. | Conflicts with aggressive outreach quotas that repeatedly target high-frequency buyers who would already purchase organically. | Limit outreach to a single ranked list per cycle ($B \le 200$), exclude non-merchandise/cancelled noise, and restrict outputs to internal `CustomerID` references. |

---

## 3. Assumptions, Data Scope, and Failure Conditions

### What the Data Can Answer
- Historical UK purchase cadence (`Recency`), invoice count (`Frequency`), and gross positive merchandise spend (`Monetary`) prior to each cutoff.
- Whether customer records form separable, seed-stable clusters under raw vs. `log1p`-transformed scaling.
- How customers selected by a fixed policy actually behaved (repeat purchase incidence and positive GBP spend) in the untouched following calendar month (`2011-08` and `2011-09`).

### What Needs Confirmation From the Business
- **True Net Margin & Return Attribution:** Because `Monetary` measures gross positive purchases excluding `C` cancellations, Finance must confirm product profit margins and whether high-spend accounts also carry high return rates.
- **Contact Channel & Operational Capacity:** Whether the £2 unit cost covers phone calls, personalized emails, or vouchers, and whether account managers need tailored scripts per cluster.
- **Causal Uplift:** Because no historical outreach log or randomized control group exists, a live A/B pilot is required to measure actual incremental lift caused by contacting customers.

### When to Advise Against Using the System in Practice
- If the untouched final evaluation shows the cluster-quota policy consistently underperforms the simple top-Monetary baseline on repeat purchase rate and captured spend without an offsetting strategic retention goal.
- If the active UK customer base drops so low that $B = \lfloor 0.10 \times N \rfloor$ yields too few slots to meaningfully populate $k$ clusters.
- If live data feeds change feature definitions, currency (non-GBP), or return handling without refitting and re-validating the saved pipeline.

---

## 4. End-to-End Workflow, Dependencies, and Information Leakage Risks

```text
[1. Raw File Audit & SHA256 Check]
        |  (Depends on unchanged Online Retail.xlsx)
        v
[2. UK & Valid Positive Transaction Filtering]
        |  (Depends on audit rules: C-invoices, missing IDs, <=0 values, non-merchandise, duplicates)
        v
[3. Cutoff-Strict RFM Aggregation (InvoiceDate < C)]
        |  (Depends on clean chronological transactions; Leakage Gate 1)
        v
[4. Representation Scaling & k-Means Fit (Development < 2011-08-01)]
        |  (Depends on dev RFM only; Leakage Gate 2)
        v
[5. Policy Allocation & August Development Evaluation]
        |  (Depends on dev clusters + August window; Freeze Procedure in Git; Leakage Gate 3)
        v
[6. Refit Fixed Procedure (< 2011-09-01) & Generate Final Lists]
        |  (Depends on frozen rules; lists saved BEFORE viewing September; Leakage Gate 4)
        v
[7. Untouched September Evaluation & Bundle Verification]