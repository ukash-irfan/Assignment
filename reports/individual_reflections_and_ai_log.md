# Individual Reflections (Questions A–E), Contribution Statement, and AI Usage Log

## 1. Own-Words Reflections

### Question A
While Sales prioritizes top spenders to maximize immediate order revenue, Account Managers require segment diversity across different buying patterns. A highest-spending customer may already purchase organically without outreach or represent a single bulk outlier, whereas allocating our 200-contact budget across clusters balances retention, reactivation, and multi-segment coverage.

### Question B 
Removing InvoiceNo rows starting with 'C' means Monetary represents gross positive merchandise purchases rather than net revenue after returns. In our UK audit, 7,856 cancellation lines totaled -£815,291.60 compared to £7,244,330.32 in valid positive sales. Stating this distinction prevents stakeholders from mistaking gross sales for net profit.

### Question C 
Although raw_scaled k=2 achieved a 0.8729 silhouette, it isolated just 24 extreme spenders into one cluster and lumped 2,821 customers together, giving Account Managers unusable segments. I chose log1p_scaled k=4 (silhouette 0.3760) because it produced four balanced, seed-stable groups (ARI 0.9986-1.0000) supporting actionable multi-segment quotas.

### Question D 
Higher September repeat purchasing (74.0% for baseline versus 45.0% for cluster policy) reflects natural buying persistence among frequent high spenders, not proof that outreach caused those orders. Because the UCI dataset records no actual contact treatments or randomized holdout control group, causal sales uplift cannot be claimed without an A/B pilot.

### Question E
k-Means assigns clusters using Euclidean distances to stored centroids in the exact scaled feature space learned during training. If StandardScaler parameters shift or RFM definitions change—such as subtracting returns from Monetary or altering Recency units—incoming coordinates misalign with saved centroids, producing inconsistent or incorrect group assignments.

---

## 2. Individual Contribution Statement
- **Submission Mode:** Individual submission (`Ukash Irfan Malik`).
- **Ownership Summary:** I defined the UK eligibility rules, temporal cutoffs (`< 2011-08-01` for development and `< 2011-09-01` for final assessment), and contact budget constraint $B = \min(200, \lfloor 0.10 \times N \rfloor)$ prior to model comparison. I executed the local pipeline on `Online Retail.xlsx` (SHA256 `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`), verified manual customer RFM calculations, committed the frozen selection procedure (`be117a85038275638151e82192c6eee561b37420`) to Git prior to September evaluation, and verified the saved `joblib` bundle and input validation checks.

---

## 3. Statement of AI Use and Verification Log

| Date | AI Tool | Purpose | Prompt Summary | Accepted / Changed & How Verified |
| --- | --- | --- | --- | --- |
| 2026-11-24 | Gemini | Modular code scaffolding (`src/features.py`, `src/clustering.py`, `src/policy.py`, `src/bundle.py`) and workflow structuring | Requested clean modular Python functions without inline comments for UK audit, strict cutoff RFM aggregation, k-Means candidate comparison, quota allocation, and `joblib` persistence based on the Assignment 3 specification. | Accepted modular structure after verifying all date cutoffs (`InvoiceDate < cutoff`), two manual customer RFM checks against `audit.csv` and `rfm_dev.csv`, and running a clean top-to-bottom restart of `ccp_workflow.ipynb`. |
| 2026-11-24 | Gemini | Environment & dependency troubleshooting (`openpyxl`) and Git freeze workflow | Reported `ImportError` when reading `Online Retail.xlsx` and requested exact Git commands to exclude raw `.xlsx` data while committing reproducible artifacts. | Installed `openpyxl` in local Python 3.14 environment; added `data/` and `*.xlsx` to `.gitignore` and verified via `git status` and `git rev-parse HEAD` (`be117a8`) that raw Excel data was excluded while all 29 code/report artifacts were committed. |
| 2026-11-24 | Gemini | Drafting structured documentation (`part_a_requirements.md`, `outreach_policy.md`, and A–E reflection drafts) | Requested concise requirement tables, stakeholder conflict mapping, and 40–60 word answers grounded in our actual CSV outputs. | **Correction / Investigation:** Initial notebook path layout placed the notebook inside a `notebooks/` subfolder, which I changed to the root directory (`Assignment_03/ccp_workflow.ipynb`) to keep imports and paths direct; verified every reported metric directly against generated `reports/*.csv` files and word counts (45–51 words each). |