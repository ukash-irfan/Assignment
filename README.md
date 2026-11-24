# Assignment No 3: Customer Segmentation and Contact Priorities (UK Online Retail)

This project implements a reproducible customer grouping and contact prioritization prototype using the UCI Online Retail dataset (DOI: 10.24432/C5BW33, CC BY 4.0) for United Kingdom customers.

## Setup
1. Place `Online Retail.xlsx` in `data/Online Retail.xlsx`. Do not commit the raw Excel file to Git.
2. Create and activate a virtual environment, then install dependencies:
   pip install -r requirements.txt

## Cutoffs and Seeds
- Development stage: features from transactions before `2011-08-01 00:00:00`; evaluation window `2011-08-01` to before `2011-09-01`.
- Final assessment stage: features from transactions before `2011-09-01 00:00:00`; evaluation window `2011-09-01` to before `2011-10-01`.
- Candidate clustering sweep: `k` in `{2, 3, 4, 5, 6}`, `n_init >= 10`, explicit `random_state`.
- Seed stability check: seeds `1, 10, 21, 42, 100` compared against `random_state=42` using Adjusted Rand Index (ARI).

## Run Order
1. Restart the kernel and run `notebooks/ccp_workflow.ipynb` from top to bottom.