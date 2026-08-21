# Adversarial Dataset & Code Audit Prompt

Use this prompt to kick off an independent, adversarial deep review of the US Correctional Facilities Aggregator project. Paste it into any capable AI assistant (Claude Sonnet/Opus, Gemini Pro, GPT-4o, etc.) with access to the project directory.

---

## Prompt

You are an expert adversarial code and data quality auditor. Your job is to rigorously examine the US Correctional Facilities Aggregator project at `/home/derekf35/Development/PROJECTS/prison-data-agg` and find every flaw, weakness, or inconsistency.

Perform the following exhaustive review:

---

### 1. CODE QUALITY REVIEW — `build_master_dataset.py`

- Read the entire file and evaluate: error handling, edge case coverage, code smells, logic bugs, maintainability, comments/documentation, hardcoded values, and reproducibility.
- Are there any cases where facilities could be **silently dropped** with no warning?
- Is the **BOP entity matching algorithm** sound? Can it create false negatives (unmatched BOP prisons) or false positives (county jails mislabeled as Federal)?
- Are the **sentinel value filters** comprehensive? Are there additional sentinel values upstream HIFLD might use that are NOT caught?
- Is `clean_coord()` sound? Could valid coordinates be incorrectly rejected?
- Is `clean_int()` sound? Could real capacity/population values be incorrectly rejected (e.g., values of 9999)?
- Is the FIPS correction hardcoded well? Could there be other upstream FIPS errors beyond the Pickens County AL fix?
- Does `format_title()` correctly handle all edge cases: numbers in names, all-caps inputs, hyphenated names with acronyms, names with parentheses, Irish/Scottish names (O'Brien, McDuffie)?

---

### 2. DATA INTEGRITY REVIEW — `output/us_correctional_facilities_master.csv`

Load and analyze the CSV with Python. Run any checks you need.

- Check for: **duplicate facility names at the same city+state** (even if IDs are unique), empty street addresses, anomalous facility names (pure numbers, single-character names), **suspiciously duplicate coordinates** (two distinct facilities sharing exact lat/lon), and facilities in impossible US geography.
- Sample and spot-check **20 random records from each US region** (Northeast, Midwest, South, West, Territories) to verify data integrity.
- Count exactly how many facilities have **all three** of `street_address`, `phone_number`, AND `website` populated.
- Validate the 8 facilities where `population > 3× design_capacity` — are these real data issues or known upstream HIFLD anomalies?
- Check if any BOP-only records (`data_source = 'Federal Bureau of Prisons (BOP)'`) have no GPS coordinates.
- Verify that no ZIP codes have lost their leading zeroes (e.g., `01234` vs `1234`).
- Confirm all `county_fips` values are exactly 5 digits with leading zeroes preserved.

---

### 3. EXCEL WORKBOOK REVIEW — `output/us_correctional_facilities_master.xlsx`

- Load all 4 sheets and verify the Data Dictionary is accurate and complete.
- **Cross-validate** the State Summary sheet totals against independent `groupby` aggregations on the raw CSV.
- Verify column headers in Sheet 1 match field descriptions in the Data Dictionary tab.
- Check for any cells that lost data type fidelity (e.g., ZIPs stored as integers losing leading zero, FIPS codes stored as numbers).

---

### 4. METHODOLOGY & DOCUMENTATION REVIEW — `README.md`

- Read `README.md` in full and evaluate whether the methodology is **accurately described**, complete, and honest about limitations.
- Are the limitations sections sufficient for a **research or policy audience**?
- Does the README mention:
  - The BOP entity matching collision bug fix?
  - The Pickens County Alabama FIPS upstream correction?
  - The Guam and Virgin Islands FIPS imputation?
  - The deduplication of 4,000 multipart GIS polygon features?

---

### 5. TEST SUITE REVIEW — `test_deep_audit.py` and `verify_dataset.py`

- Evaluate whether the test suite is **genuinely adversarial** or just confirming things the pipeline already guarantees.
- Identify any tests that **should be there but are missing**.
- Are there any tests that could give **false PASS results**?
- Suggested missing tests to consider:
  - Duplicate `(facility_name, city, state)` triplets
  - Duplicate `(latitude, longitude)` coordinate pairs across distinct IDs
  - `population > design_capacity × 5` as a data sanity warning
  - Presence of sentinel strings in `facility_name` (e.g., `NOT AVAILABLE`, `-999`)
  - Phone number format regex conformance
  - BOP-sourced records with missing coordinates
  - Irish/Scottish name patterns (O'Brien, McDuffie, McCreary) for casing issues

---

### 6. FINAL SCORING

Score the project out of **100** across five categories:

| Category | Max Points |
|:---|:---:|
| Data Completeness | 20 |
| Data Accuracy | 20 |
| Code Quality & Robustness | 20 |
| Methodology Documentation | 20 |
| Test Suite Rigor | 20 |
| **Total** | **100** |

---

### Deliverables

Report all findings, even minor ones. Be specific about:
- File paths and function names
- Line numbers where relevant
- Column names and sample values for data issues

Structure your output as:
1. **Executive Summary** (3–5 bullet points on the most critical findings)
2. **Section 1–5 Findings** (detailed per section above)
3. **Final Scorecard** with category breakdowns and justifications
4. **Recommended Fixes** prioritized by severity (Critical / High / Medium / Low)
