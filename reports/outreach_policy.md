# Contact Outreach Policy, Time Evaluation, and Management Recommendation

## 1. Cluster-Based Outreach Policy Specification
- **Budget & Capacity:** At cutoff $C$ with $N$ eligible UK customers, select $B = \min(200, \lfloor 0.10 \times N \rfloor)$ unique customers at £2 per contact (maximum £400). At both August ($N = 2,845$) and September ($N = 2,986$) cutoffs, $B = 200$ and total cost $= £400.00$.
- **Inter-Cluster Quota Allocation:** Divide $B$ equally across the $k = 4$ clusters (`50` slots per cluster at $B = 200$; for general $B$, use $\lfloor B/k \rfloor$ plus largest-remainder slots ordered by fractional part descending, then cluster ID ascending).
- **Small-Group & Spare-Slot Rule:** If any cluster contains fewer eligible customers than its assigned quota, take all available customers from that cluster and pool the remaining unused slots. Reallocate spare slots across remaining unselected customers globally using the same priority score until exact $B$ unique customers are selected.
- **Intra-Cluster Ranking & Tie-Breaking:** Within each cluster, rank customers descending by $\text{PriorityScore} = \frac{\text{Monetary}}{1 + \text{Recency}}$, which rewards high historical spend while penalizing long inactivity. Exact ties are broken deterministically by `Frequency` (descending), `Monetary` (descending), and `CustomerID` (ascending).
- **Zero-Denominator Safeguard:** In evaluation ratios (repeat purchase rate, spend per selected customer, captured spend share, and cohort coverage), if $B = 0$, $N_{\text{cohort}} = 0$, or total cohort positive spend $= £0$, report `NaN` rather than dividing by zero.

## 2. Development Stage Decision Log (August 2011)
- **Initial Policy Tested:** Equal-quota allocation (`50` contacts per cluster across 4 `log1p_scaled` clusters) vs. `baseline_monetary` (top `200` past spenders) on the `< 2011-08-01` cohort ($N = 2,845$), evaluated on August 2011 transactions (`2011-08-01` to `< 2011-09-01`).
- **Development Evidence:**
  - `baseline_monetary`: Repeat purchase rate $= 73.5\%$, spend per selected customer $= £1,132.53$, captured spend share $= 51.76\%$, cohort coverage $= 7.03\%$ ($200 / 2,845$), cost $= £400.00$.
  - `cluster_policy`: Repeat purchase rate $= 41.0\%$, spend per selected customer $= £575.16$, captured spend share $= 26.29\%$, cohort coverage $= 7.03\%$ ($200 / 2,845$), cost $= £400.00$.
- **Decision Kept for Final Assessment:** Kept the equal-quota cluster policy fixed without post-hoc retuning so the final September evaluation directly tests whether guaranteeing multi-segment representation justifies the short-term revenue tradeoff against the top-Monetary baseline.

## 3. Untouched Final Assessment Comparison (September 2011)
Refitting the frozen preprocessing and `k = 4` clustering on transactions before `2011-09-01` ($N = 2,986$) and saving both 200-customer lists prior to inspecting September purchases yielded:

| Policy | Selected ($B$) | Cost (£) | Repeat Purchase Rate | Spend / Selected (£) | Captured Spend Share | Cohort Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| `baseline_monetary` | 200 | £400.00 | 74.0% | £1,688.42 | 51.62% | 6.70% (200 / 2,986) |
| `cluster_policy` | 200 | £400.00 | 45.0% | £1,239.50 | 37.89% | 6.70% (200 / 2,986) |

- **Selected Counts per Cluster (`cluster_policy`):** Cluster 0: `50`, Cluster 1: `50`, Cluster 2: `50`, Cluster 3: `50` (total `200`, zero unused slots).
- **Concrete Selection Tradeoff Example:** In the September cohort, Cluster 1 comprises high-frequency loyalists (`mean Frequency = 11.30`, `mean Monetary = £5,596.02`), whereas Cluster 2 comprises dormant one-time buyers (`mean Recency = 149.58 days`, `median Frequency = 1.0`, `mean Monetary = £262.81`). The baseline allocates almost all `200` slots to Cluster 1 heavy spenders, capturing `51.62%` of September cohort spend (`£1,688.42` per contact). By contrast, the cluster policy reserves `50` slots for dormant Cluster 2 customers and `50` slots for recent low-frequency Cluster 3 customers (`mean Recency = 14.70 days`, `mean Monetary = £669.49`), sacrificing `£448.93` in immediate spend per contact (`£1,239.50` vs. `£1,688.42`) in exchange for broad segment representation across all four customer archetypes.

## 4. Causal Interpretation Limits & Pilot Design
- **Non-Causal Observation Limit:** Higher September repeat purchasing (`74.0%` vs. `45.0%`) reflects natural buying persistence among historical high spenders rather than proof that outreach caused purchases. Because the UCI dataset contains no contact log or control group, causal lift cannot be inferred.
- **Recommended Controlled Pilot:** Before full deployment, run a randomized controlled trial within each cluster—randomly splitting eligible candidates into a **Contact Treatment Group** ($50\%$) and a **No-Contact Holdout Control Group** ($50\%$)—and measure incremental repeat order rate, net margin after returns, and response cost over 30 days.

## 5. Final Recommendation to Management
- **Recommendation: Adopt the Top-Monetary Baseline for immediate revenue capture, and run a limited randomized pilot before deploying cluster-based outreach.**
- Across both August and September evaluations, the simple top-Monetary baseline achieved higher repeat purchase rates (`73.5%` and `74.0%`) and captured over half of total eligible cohort spend (`51.76%` and `51.62%`) within the £400 budget. Equal-quota clustering successfully broadens segment coverage across all four UK customer profiles (`50` per group) and remains stable across seeds ($\text{ARI} \ge 0.9986$), making it valuable for targeted retention experiments once a controlled A/B pilot verifies incremental response lift.