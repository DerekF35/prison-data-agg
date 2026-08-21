# Adversarial Dataset & Code Quality Audit Prompt
**Target**: United States Correctional Facilities Master Database  
**Repository**: `/home/derekf35/Development/PROJECTS/prison-data-agg`  
**Purpose**: Rigorous independent code, data, documentation, and test suite audit.

---

## Instructions for the Auditor

You are an **independent, adversarial code and data quality auditor**. Your mandate is to rigorously evaluate the repository, identify weaknesses, verify invariants, and test edge cases.

### Audit Output Requirements
1. **Write findings to the `audit/` directory** using the standardized filename:  
   `audit/YYYY-MM-DD_HHMM_<model-name>_adversarial-audit.md`
2. **Include complete metadata** (Timestamp, Model Name, Requesting Model/User, Final Score).
3. **Prior Score Reference**: If including a "Prior Score" column in your scorecard, **inspect the most recent row in `audit/README.md`** to extract the true chronological prior score. **DO NOT copy hardcoded placeholder numbers from prompt templates.**
4. **Update `audit/README.md`**: Append a new row to the **Master Audit Scorecard & Progression Table** in `audit/README.md` with your audit's scores and summary.
5. **Follow Agent Policy**: In accordance with `AGENT_INSTRUCTIONS.md`, do **not** modify pipeline code or datasets; only write the audit report, update `audit/README.md`, commit to `git`, and present findings.

---

## Audit Evaluation Rubric (100 Points Total)

### 1. CODE QUALITY & ROBUSTNESS (20 Points) — `build_master_dataset.py` & `generate_documents.py`
* **Error Handling & Resilience**: Are API calls paginated and cached? Are timeouts and exceptions handled safely?
* **Silent Dropping**: Are any records or coordinates silently discarded without explicit logging?
* **BOP Federal Entity Resolution Guardrails**:
  * Are non-federal facilities (e.g. County Jails like *Sybil Brand Institute*) strictly protected by `is_fed` guards?
  * Are administrative command offices (`RRM`, `RO`, `CO`, `FCC`, `MSTC`) segregated into dedicated standalone records?
  * Is **camp-to-camp matching parity** enforced so satellite camps (*FPC*, *Camp*) do not hijack parent institution (*USP*, *FCI*) URLs?
* **Sanitization Functions**:
  * Does `clean_int()` preserve valid `0` counts (unoccupied/holding facilities) while scrubbing negative sentinels (`-999`, `-1`, `99999`)?
  * Does `clean_coord()` allow longitudes up to `+180.0` for Pacific territories and Aleutian Islands?
  * Does `format_title()` preserve uppercase acronyms and Scottish/Irish prefixes (`McDuffie`, `McCreary`, `McKean`, `O'Brien`, `O'Farrell`, `Chain O'Lakes`)?

---

### 2. DATA INTEGRITY & PARITY (20 Points) — `output/us_correctional_facilities_master.csv`
* **Unique Primary Keys**: 100% unique `facility_id` with zero duplicates.
* **Mandatory Field Completeness**: 100% complete `facility_name`, `state`, `jurisdiction`, and `operational_status`.
* **Geospatial & Postal Integrity**: 100% valid WGS84 coordinates; 100% 5-digit ZIP codes and County FIPS codes with preserved leading zeroes.
* **Zero Population Preservation**: Exactly 625 legitimate zero-population records preserved as discrete integers.
* **Regional Sampling**: Stratified random sample check across Northeast, Midwest, South, West, and Territories.

---

### 3. EXCEL SPREADSHEET FIDELITY (20 Points) — `output/us_correctional_facilities_master.xlsx`
* **Sheet Structure**: 4 active sheets (*Master Facilities Directory*, *State Summary*, *Jurisdiction Summary*, *Data Dictionary*).
* **Parity**: Exact row count and column structure matching the CSV.
* **Cross-Validation**: Summary tab counts and capacity/population sums match raw CSV aggregations.
* **Data Dictionary**: Clean 3-column schema mapping: `Display Column Header`, `CSV Field Name (snake_case)`, and `Description & Definition`.

---

### 4. METHODOLOGY & DOCUMENTATION (20 Points) — `README.md`, PDF, & Word Reports
* **Synchronicity**: Counts, figures, and breakdowns across `README.md`, the Word document, and PDF report match the CSV ground truth.
* **Disclosures**: Transparent disclosure of multi-part polygon consolidation, BOP entity matching rules, FIPS corrections/imputations, and zero-population retention.
* **Known Limitations & Upstream Anomalies**: Clear documentation of point-in-time census snapshots, the 8 upstream population vs capacity outliers ($>3\times$), and municipal campus co-location.

---

### 5. TEST SUITE RIGOR (20 Points) — `test_deep_audit.py` & `verify_dataset.py`
* **Adversarial Non-Tautological Checks**: Test entire classes of entities, regex formats, coordinate bounds, and archive integrity.
* **Threshold Assertions**: Upper-bound assertions on co-located facilities ($\le 10$) with soft-warning visibility.
* **Archive Integrity**: Test 17 confirms `prison_data_report.zip` contains all 5 primary deliverables.

---

### 6. FINAL SCORING TEMPLATE

Score the project out of **100** across the five categories. Extract the "Prior Score" from the most recent file in `audit/`:

```markdown
| Category | Max Points | Prior Score | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| Data Completeness | 20 | [Prior] | [Current] | [Detailed rationale] |
| Data Accuracy | 20 | [Prior] | [Current] | [Detailed rationale] |
| Code Quality & Robustness | 20 | [Prior] | [Current] | [Detailed rationale] |
| Methodology Documentation | 20 | [Prior] | [Current] | [Detailed rationale] |
| Test Suite Rigor | 20 | [Prior] | [Current] | [Detailed rationale] |
| **Total** | **100** | **[Prior Total]** | **[Current Total]** | **[Final Grade]** |
```
