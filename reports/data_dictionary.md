# Data Dictionary — UK Online Retail RFM Prototype

## Source Dataset Fields (`Online Retail.xlsx`, UCI DOI: 10.24432/C5BW33)
| Field | Type | Unit / Format | Treatment in Prototype |
| --- | --- | --- | --- |
| `InvoiceNo` | string | Transaction invoice ID | Kept as string identifier; rows starting with `C` excluded as cancellations into separate audit record; not used as a clustering feature. |
| `StockCode` | string | Product / item code | Used to filter non-merchandise codes (`POST`, `D`, `M`, `BANK CHARGES`, `PADS`, `DOT`, `CRUK`, `B`); not used as a clustering feature. |
| `Description` | string | Product text | Inspected during audit; not used as a clustering feature. |
| `Quantity` | float / int | Units per line | Required `Quantity > 0` for valid positive purchases; zero/negative values investigated and logged in audit. |
| `InvoiceDate` | datetime | Timestamp | Converted to datetime, sorted chronologically, and filtered strictly `InvoiceDate < cutoff` to prevent future leakage. |
| `UnitPrice` | float | GBP (£) per unit | Required `UnitPrice > 0` for valid positive purchases; zero/negative values investigated and logged in audit. |
| `CustomerID` | string | Customer identifier | Preserved as string identifier; rows with missing `CustomerID` counted and reported in audit before exclusion; used only for grouping and final deterministic tie-breaking, never as a clustering feature. |
| `Country` | string | Country name | Filtered strictly to `United Kingdom`; all conclusions apply only to UK customers. |

## Derived Customer-Level RFM Features (at Cutoff `C`)
| Feature | Type | Unit | Definition |
| --- | --- | --- | --- |
| `Recency` | int | Days | Whole days from the customer's latest valid positive purchase before `C` to midnight at `C` (`Recency >= 0`). |
| `Frequency` | int | Distinct invoices | Count of unique valid positive purchase `InvoiceNo` values for the customer before `C` (`Frequency >= 1`). |
| `Monetary` | float | GBP (£) | Total positive purchase value `sum(Quantity * UnitPrice)` across valid positive purchases before `C` (`Monetary > 0`). Does not subtract cancellations or returns. |