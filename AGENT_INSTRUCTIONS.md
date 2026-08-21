# Agent Operating Instructions & Repository Guidelines
**Project**: United States Correctional Facilities Master Database  
**Repository**: `prison-data-agg`  
**Target Audience**: Data Auditors, Public Policy Researchers, Legal Teams, and AI Coding Assistants

---

## 🛑 1. Core Rule: Audit Gatekeeping & Review Mandate

> [!IMPORTANT]
> **NO ACTION IS TAKEN ON AUDIT RESULTS WITHOUT EXPLICIT USER REVIEW AND APPROVAL.**
>
> When an adversarial audit (automated subagent or user-provided review) generates findings:
> 1. **Do NOT immediately edit code, modify datasets, or commit changes.**
> 2. Present a clear, categorized summary of the audit findings, their root causes, and a proposed step-by-step remediation plan to the USER.
> 3. Wait for the USER's explicit confirmation or direction before touching any pipeline scripts, datasets, or documentation.

---

## 🛡️ 2. Data Quality & ETL Invariant Rules

### A. Zero-Population Preservation
* **Rule**: `0` is a valid, legitimate population and capacity count in US correctional data (representing temporary intake centers, unoccupied holding annexes, or brand-new facilities; ~625 facilities report 0).
* **Action**: Only scrub sentinel placeholders (negative numbers like `-1`, `-999`, and sentinel overflows like `99999`) to null. **Never filter out or nullify `0`**.

### B. BOP Federal Entity Resolution Guardrails
* **Cross-Jurisdiction Protection**: Never allow non-federal facilities (e.g. County Jails, Municipal Lockups) to match BOP codes or receive `bop.gov` URLs (e.g., *Los Angeles County Sybil Brand Institute* must never match BOP code `LOS`).
* **Administrative Entity Segregation**: Regional Offices (`RO`), Community Corrections offices (`RRM`), Central Office (`CO`), Training Centers (`MSTC`), and Complex Management offices (`FCC`) must be ingested as **dedicated standalone records**, never mapped over physical prisons in the same municipality.
* **Camp-to-Camp Parity**: Non-camp federal institutions (*USP*, *FCI*, *FDC*, *MDC*) must only match non-camp directory records. Satellite camps (*FPC*, *Camp*) must only match camp records, preventing satellite camps from stealing parent institution URLs (e.g. *USP Beaumont* receives `/institutions/bmp/` while *FCI Beaumont Low* receives `/institutions/bml/`).

### C. Geospatial & Coordinate Integrity
* **Coordinate Bounding**:
  * Latitude: Valid US range `[13.0, 72.0]`.
  * Longitude: Lower 48, AK, HI, Caribbean territories `[-180.0, -64.0]` AND Pacific Territories / Aleutian Islands crossing the antimeridian `[+144.0, +180.0]`.
* **Multi-Part Polygon Centroids**: Retain primary centroids when consolidating duplicate polygon geometry nodes sharing identical `FACILITYID`s.

### D. Postal & FIPS Code Formatting
* **Leading Zeroes**: ZIP codes and 5-digit County FIPS codes must **always** preserve leading zeroes (e.g., East Coast states `01862`, Puerto Rico `00921`, Saipan `69110`, Pickens County AL `01107`).
* **Storage Type**: Never store ZIP or FIPS codes as raw numerical floats or integers that drop leading zeroes; use string format.

### E. Typography & Surnames
* **Acronym Preservation**: Always preserve uppercase acronyms (`USP`, `FCI`, `ADX`, `MDC`, `FDC`, `FMC`, `BOP`, `DOC`, `SCI`, `ASPC`, `CCFW`).
* **Cultural Surnames**: Properly format Scottish and Irish prefixes (`McDuffie`, `McCreary`, `McKean`, `O'Brien`, `O'Farrell`, `Chain O'Lakes`).

---

## 📦 3. Deliverables & Packaging Synchronicity

Whenever the ETL pipeline is executed, all deliverables must remain **100% synchronized**:

1. **Master CSV**: `output/us_correctional_facilities_master.csv`
2. **Master Excel**: `output/us_correctional_facilities_master.xlsx` (All 4 sheets: *Master Directory*, *State Summary*, *Jurisdiction Summary*, *Data Dictionary* with 3-column key mapping).
3. **Word Technical Report**: `output/US_Correctional_Facilities_Methodology_Report.docx`
4. **PDF Technical Report**: `output/US_Correctional_Facilities_Methodology_Report.pdf` (built via headless LibreOffice).
5. **JSON Audit Summary**: `output/dataset_summary.json`
6. **All-in-One Deliverables Archive**: `output/prison_data_report.zip` (must automatically bundle all 5 files above).

> [!NOTE]
> Every summary table in `README.md`, the Word document, and the PDF report must match the exact row count and column aggregations of the master CSV.

---

## 🧪 4. Testing & Verification Mandates

1. **Mandatory Test Execution**:
   * Before proposing completion, run:
     ```bash
     python3 test_deep_audit.py && python3 verify_dataset.py
     ```
   * All 17 adversarial assertions must pass with 0 defects.
2. **Non-Tautological Testing**:
   * When creating new regression tests for discovered bugs, do not write narrow assertions that check only a single facility ID. Write assertions that validate the entire class of entities across the dataset.

---

## 📜 5. Audit Logging & Scorecard Standards

1. **Audit Persistence**:
   * All audit reports must be saved directly to the `audit/` directory with the standard filename format:
     `audit/YYYY-MM-DD_HHMM_<model-name>_adversarial-audit.md`
   * Never delete, overwrite, or truncate past audit reports.
2. **Audit Summary Scorecard Maintenance (`audit/README.md`)**:
   * Whenever a new audit report is generated, the agent/subagent MUST append a new row to the **Master Audit Scorecard & Progression Table** in [`audit/README.md`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/audit/README.md), documenting the timestamp, model, category scores, total score, report link, and key findings.
3. **Prior Score Referencing**:
   * When writing a scorecard with a "Prior Score" column, the auditor MUST inspect the immediately preceding row in [`audit/README.md`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/audit/README.md) to extract the true chronological prior score, rather than copying static placeholder numbers.
4. **Clean Commits**:
   * Commit messages must clearly specify the exact changes made, entities affected, and tests verified.
