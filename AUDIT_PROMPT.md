# Adversarial Dataset & Code Audit Prompt

Use this prompt to kick off an independent, adversarial deep review of the US Correctional Facilities Aggregator project. Paste it into any capable AI assistant (Claude Sonnet/Opus, Gemini Pro, GPT-4o, etc.) with access to the project directory.

---

## Output Instructions

**Every audit MUST produce a report file saved to:**
```
audit/YYYY-MM-DD_HHMM_<model-name>_adversarial-audit.md
```

**Example:**
```
audit/2026-08-20_2143_gemini-pro_adversarial-audit.md
audit/2026-08-20_2200_claude-sonnet-4-adversarial-audit.md
```

The report file must include the following header table:

```markdown
| Field | Value |
|:---|:---|
| **Date** | YYYY-MM-DD |
| **Time** | HH:MM TZ |
| **Auditor Model** | <model name and provider> |
| **Requesting Model** | <model that launched the audit, if known> |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | XX / 100 |
```

After writing the file, commit it to git:
```bash
git add audit/
git commit -m "Add audit report: <date> <model>"
git push origin main
```

---

## Prompt

You are an expert adversarial code and data quality auditor. Your job is to rigorously examine the US Correctional Facilities Aggregator project at `/home/derekf35/Development/PROJECTS/prison-data-agg` and find every flaw, weakness, or inconsistency.

Perform the following exhaustive review:

---

### 1. CODE QUALITY REVIEW — `build_master_dataset.py`

- Read the entire file and evaluate: error handling, edge case coverage, code smells, logic bugs, maintainability, comments/documentation, hardcoded values, and reproducibility.
- Are there any cases where facilities could be **silently dropped** with no warning?
- Is the **BOP entity matching algorithm** sound? Can it create false negatives (unmatched BOP prisons) or false positives (county jails mislabeled as Federal)? **Note from prior audit:** Rule 1 (`h_name.startswith(bop_code)`) has been shown to cause false positives for short 3-letter BOP codes in large cities (e.g., `LOS` matching `Los Angeles County Sybil Brand Institute for Women`). Verify whether this has been fixed.
- Are the **sentinel value filters** comprehensive? Are there additional sentinel values upstream HIFLD might use that are NOT caught?
- Is `clean_coord()` sound? Could valid coordinates be incorrectly rejected? **Note:** Alaskan Aleutian Islands have positive longitudes near +172° which may be excluded by the current longitude range check.
- Is `clean_int()` sound? **Prior audit found** that `f <= 0` incorrectly nullifies valid zero-population counts, and `f == 9999` incorrectly rejects a possibly valid capacity. Verify whether this has been fixed.
- Is the FIPS correction hardcoded well? Could there be other upstream FIPS errors beyond the Pickens County AL fix?
- Does `format_title()` correctly handle all edge cases: numbers in names, all-caps inputs, hyphenated names with acronyms, names with parentheses, Irish/Scottish names (`O'Brien`, `McDuffie`, `McCreary`)? **Prior audit found** `O'Brien` → `O'brien` and `McDuffie` → `Mcduffie`. Verify fix status.
- Does deduplication log a warning when features with valid coordinates are silently overwritten?

---

### 2. DATA INTEGRITY REVIEW — `output/us_correctional_facilities_master.csv`

Load and analyze the CSV with Python. Run any checks you need.

- Check for: **duplicate facility names at the same city+state** (even if IDs are unique), empty street addresses, anomalous facility names (pure numbers, single-character names), **suspiciously duplicate coordinates** (two distinct facilities sharing exact lat/lon), and facilities in impossible US geography.
- Sample and spot-check **20 random records from each US region** (Northeast, Midwest, South, West, Territories) to verify data integrity.
- Count exactly how many facilities have **all three** of `street_address`, `phone_number`, AND `website` populated. **Prior audit found: 5,791.**
- Validate the 8 facilities where `population > 3× design_capacity` — are these real data issues or known upstream HIFLD anomalies? **Prior audit confirmed these are upstream HIFLD anomalies.**
- Check if any BOP-only records (`data_source = 'Federal Bureau of Prisons (BOP)'`) have no GPS coordinates.
- Verify that no ZIP codes have lost their leading zeroes (e.g., `01234` vs `1234`).
- Confirm all `county_fips` values are exactly 5 digits with leading zeroes preserved.
- **New:** Verify `O'` and `Mc` prefix names (e.g., `McCreary`, `O'Brien`) are correctly cased.
- **New:** Verify no valid zero-population or zero-capacity values were nullified by `clean_int()`.

---

### 3. EXCEL WORKBOOK REVIEW — `output/us_correctional_facilities_master.xlsx`

- Load all 4 sheets and verify the Data Dictionary is accurate and complete.
- **Cross-validate** the State Summary sheet totals against independent `groupby` aggregations on the raw CSV.
- Verify column headers in Sheet 1 match field descriptions in the Data Dictionary tab.
- Check for any cells that lost data type fidelity (e.g., ZIPs stored as integers losing leading zero, FIPS codes stored as numbers).
- **New:** Verify whether the Data Dictionary tab now includes a "Field Name (CSV)" column showing the programmatic snake_case key. **Prior audit found a mismatch between display headers and CSV field names.**

---

### 4. METHODOLOGY & DOCUMENTATION REVIEW — `README.md`

- Read `README.md` in full and evaluate whether the methodology is **accurately described**, complete, and honest about limitations.
- Are the limitations sections sufficient for a **research or policy audience**?
- Does the README mention:
  - The BOP entity matching collision bug fix?
  - The Pickens County Alabama FIPS upstream correction?
  - The Guam (`66010`) and Virgin Islands (`78010`) FIPS imputation in `STANDALONE_COUNTY_FIPS_MAP`? **Prior audit found these were NOT documented.**
  - The deduplication of 4,000 multipart GIS polygon features?
  - The `clean_int()` zero-population nullification behavior? **Prior audit found this was NOT disclosed.**
- **Prior audit found:** The README falsely claimed entity matching was "collision-free". Verify this has been corrected.

---

### 5. TEST SUITE REVIEW — `test_deep_audit.py` and `verify_dataset.py`

- Evaluate whether the test suite is **genuinely adversarial** or just confirming things the pipeline already guarantees.
- Identify any tests that **should be there but are missing**.
- Are there any tests that could give **false PASS results**?
- Required tests to verify are now present (all were MISSING in the prior audit):
  - [ ] Duplicate `(facility_name, city, state)` triplets → should warn, not fail
  - [ ] Duplicate `(latitude, longitude)` coordinate pairs across distinct facility IDs
  - [ ] Phone number regex conformance: `^\(\d{3}\) \d{3}-\d{4}$`
  - [ ] BOP-sourced records missing GPS coordinates
  - [ ] `O'` and `Mc` name casing validation
  - [ ] Zero-population facilities not being silently dropped (i.e., valid `population == 0` preserved)
  - [ ] Aleutian Island longitude range validity

---

### 6. FINAL SCORING

Score the project out of **100** across five categories:

| Category | Max Points | Prior Score |
|:---|:---:|:---:|
| Data Completeness | 20 | 19 |
| Data Accuracy | 20 | 14 |
| Code Quality & Robustness | 20 | 14 |
| Methodology Documentation | 20 | 16 |
| Test Suite Rigor | 20 | 15 |
| **Total** | **100** | **78** |

---

### Deliverables

Report all findings, even minor ones. Be specific about:
- File paths and function names
- Line numbers where relevant
- Column names and sample values for data issues

Structure your output as:
1. **Metadata Header** (date, time, model, score)
2. **Executive Summary** (3–5 bullet points on the most critical findings)
3. **Section 1–5 Findings** (detailed per section above)
4. **Final Scorecard** with category breakdowns and justifications
5. **Recommended Fixes** prioritized by severity (Critical / High / Medium / Low)

Save the report to `audit/YYYY-MM-DD_HHMM_<model>_adversarial-audit.md` and commit it to git.
