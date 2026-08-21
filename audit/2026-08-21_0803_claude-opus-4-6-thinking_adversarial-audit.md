# Adversarial Dataset & Code Quality Audit Report

| Field | Value |
|:---|:---|
| **Date** | 2026-08-21 |
| **Time** | 08:03 EDT |
| **Auditor Model** | Claude Opus 4.6 (Thinking) — Anthropic |
| **Requesting Model** | User Direct Request |
| **Audit Scope** | Full project: pipeline code, raw source data cross-validation, CSV dataset, Excel workbook, Word/PDF reports, ZIP archive, README, test suite, documentation synchronicity |
| **Audit Focus** | Data accuracy, cleaning technique fidelity, source-to-output integrity |
| **Final Score** | **93 / 100** |

---

## Executive Summary

An independent, adversarial audit was conducted on the **US Correctional Facilities Aggregator** at `/home/derekf35/Development/PROJECTS/prison-data-agg`. This audit prioritized **data accuracy** — specifically whether cleaning techniques and script processing faithfully represent the source data without introducing distortions. The audit went beyond the existing 17-test suite by writing and executing a 19-probe independent deep analysis that cross-referenced raw source JSON against output CSV at the record level.

### Top-Level Findings

1. **Strong Data Integrity Foundation**: 6,788 facilities with 100% unique IDs, 100% geocoding, 100% county FIPS coverage, and zero sentinel leakage. All 17 existing tests pass cleanly.
2. **Faithful Source Reproduction**: Coordinate fidelity is exact to raw source within rounding tolerance across all 6,737 HIFLD records. Zero-population preservation (625 records) exactly matches the unique raw facility IDs with `POPULATION=0`. No closed-to-open status flips. No sentinel string or integer leakage.
3. **Gender Value Documentation Mismatch** (Severity: Medium): The Data Dictionary, README, Word report, and PDF all document the `gender` field as accepting `Male, Female, Co-ed, Not Specified`. However, the actual data contains **24 records with `Mixed`** (not `Co-ed`). The BOP API uses `"mixed"` which `.title()` normalizes to `"Mixed"`, but no mapping to the documented `"Co-ed"` value exists. This is the single most material documentation-to-data discrepancy.
4. **Private Jurisdiction Dead Code** (Severity: Low): The pipeline has handling for `"PRIVATE" in raw_type` → `jurisdiction = "Private"`, but the upstream HIFLD dataset contains zero records with `TYPE=PRIVATE`. The 6 valid raw TYPE values are: `COUNTY` (6,029), `STATE` (3,519), `LOCAL` (627), `FEDERAL` (445), `MULTI` (66), `NOT AVAILABLE` (51). The README documents "Private" as a jurisdiction category but no facilities carry this classification. This is accurate (no data corruption) but should be disclosed.
5. **One Blank Raw Record Correctly Dropped**: Raw HIFLD contains 6,738 unique FACILITYIDs, but one is a completely blank upstream artifact (OBJECTID 10738, all fields null, created by a Riverside CA GIS editor). The pipeline correctly drops it via the `if not fac_id: continue` guard, yielding 6,737 HIFLD-sourced output records. This is proper behavior.

---

## Section 1: Code Quality & Robustness (20 Points)

### 1.1 Ingestion & Caching (`build_master_dataset.py:39–77`)
- **ArcGIS Pagination**: `fetch_arcgis_features()` implements offset-based pagination with `batch_size=2000`, explicit `resultRecordCount` parameters, and `exceededTransferLimit` detection. Timeouts are set at 15s (count) and 30s (queries). ✅
- **File Caching**: Raw JSON is cached locally with a 100KB minimum size guard to prevent corrupt cache files. ✅
- **BOP Fetch Resilience**: BOP directory fetch has `try/except` fallback with explicit error logging. ✅

### 1.2 Silent Dropping Analysis
- **FACILITYID Guard** (line 315–317): Records missing `FACILITYID` emit `[WARN]` before being skipped. The only record dropped is OBJECTID 10738 — a completely blank upstream artifact with all null fields. This is correct behavior, not silent data loss. ✅
- **Multi-Part Consolidation** (lines 308–332): Secondary polygon features are consolidated by FACILITYID with logging: 4,001 secondary nodes merged (4,000 unique IDs × 2 features = 4,000 secondaries, plus 1 blank → 4,001 total surplus). The "primary centroid preserved" approach retains whichever record was ingested first. ✅

### 1.3 BOP Entity Resolution Guards
- **`is_fed` Type Guard** (lines 366–369, 391–394): Correctly requires HIFLD records to have `TYPE` in `("FEDERAL", "MULTI")` or contain federal prefixes in the name before BOP matching. This prevents county jails (e.g., Sybil Brand Institute, FACILITYID `10000894`) from receiving BOP URLs. Verified by Test 10. ✅
- **Administrative Segregation** (line 350–351): RRM, RO, CO, FCC, TRN, and STAFF TRAINING ACADEMY types are routed directly to `standalone_bop_records`, preventing administrative offices from overwriting physical prisons. 47 raw admin types → correctly segregated. ✅
- **Camp-to-Camp Parity** (lines 380, 399–403): `b_is_camp != h_is_camp` guard ensures satellite camps match only satellite camp HIFLD records and parent institutions match only parent records. Verified by Test 11 (Beaumont complex). ✅

### 1.4 Sanitization Functions

#### `clean_int()` (lines 239–248)
- Returns `0` for valid `0`/`0.0` inputs — confirmed via independent edge case testing. ✅
- Scrubs sentinels `{-999, -1, 99999}` and all negative values to `None`. ✅
- **Zero-Population Preservation**: 625 output records with `population=0` exactly matches the 625 unique HIFLD FACILITYIDs having `POPULATION=0` in the raw source. ✅ (Cross-validated against raw JSON.)

#### `clean_coord()` (lines 250–264)
- Latitude bounds: `[13.0, 72.0]` — covers CNMI (13.4°N) through northernmost Alaska. ✅
- Longitude bounds: `[-180.0, -64.0]` OR `[144.0, 180.0]` — correctly handles Aleutian Islands, Guam (144.7°E), and CNMI. ✅

#### `format_title()` (lines 266–306)
- Mc/O' prefix handling works correctly: no `Mc[a-z]` or `O'[a-z]` patterns in output names (Test 9). ✅
- Articles (`of`, `and`, `for`, `in`, `at`, `on`, `to`, `the`) are lowercased mid-name. No mid-name capitalized articles found. ✅
- ACRONYMS set covers 60+ patterns. ✅

#### `clean_zip()` (lines 196–209)
- 4-digit ZIPs are zero-padded to 5 digits. 3-digit ZIPs are double zero-padded. ✅
- All New England states have leading-zero ZIPs preserved: CT (24), MA (57), ME (27), NH (21), NJ (80), RI (13), VT (15), PR (40). ✅

#### `clean_fips()` (lines 211–221)
- Pickens County AL FIPS typo corrected: `10107` → `01107`. ✅
- 4-digit FIPS codes are zero-padded to 5 digits. ✅
- All 6,788 output FIPS prefixes are valid US state/territory codes and match their stated state abbreviation. ✅ (Cross-validated with state-to-FIPS mapping.)

### 1.5 Code Quality Deductions

- **Minor**: The `GENDER` field referenced at line 533 (`attrs.get("GENDER")`) does not exist in the HIFLD schema. HIFLD has no `GENDER` attribute at all. The `.get()` safely returns `None` which falls through to the `or "Not Specified"` default, so this is not a functional bug, but it's vestigial/misleading code that suggests HIFLD contains gender data when it doesn't. (-0.5)

**Section Score: 19 / 20**

---

## Section 2: Data Integrity & Parity (20 Points)

### 2.1 Unique Primary Keys
- 0 duplicate `facility_id` values across 6,788 records. ✅

### 2.2 Mandatory Field Completeness
- `facility_name`: 100% populated, 0 empty/null. ✅
- `state`: 100% populated, all 55 valid jurisdictions present. ✅
- `jurisdiction`: 100% populated. ✅
- `operational_status`: 100% populated. ✅

### 2.3 Geospatial & Postal Integrity
- **Coordinates**: 100% valid WGS84 coordinates within US bounds. Zero drift from raw source (checked all 6,737 HIFLD records at ±0.0001° tolerance). ✅
- **ZIP Codes**: 100% match `^\d{5}(-\d{4})?$` regex. Leading zeros preserved. ✅
- **County FIPS**: 100% populated, 100% 5-digit format, 100% valid state prefix matching. ✅

### 2.4 Zero Population Preservation
- Exactly 625 zero-population records in output. ✅
- Cross-validated: 625 unique FACILITYIDs in raw HIFLD have `POPULATION=0`. Exact match. ✅
- 3,108 raw features with sentinel population values (`-999`, `-1`, `99999`) correctly scrubbed to null. ✅

### 2.5 Regional Stratified Sampling
| Region | Facilities | States/Territories |
|:---|:---:|:---:|
| South | 3,085 | 17 |
| Midwest | 1,754 | 12 |
| West | 1,247 | 13 |
| Northeast | 655 | 9 |
| Territories | 47 | 4 |
| **Total** | **6,788** | **55** |

Well-known facility spot checks:
- San Quentin State Prison (CA) — ✅ Found, Open
- Attica Correctional Facility (NY) — ✅ Found, Open
- Sing Sing Correctional Facility (NY) — ✅ Found, Open
- USP Leavenworth (KS) — ✅ Found, Open
- Rikers Island — Not found by name search (likely cataloged under official facility names like "Rose M. Singer Center" rather than the island's colloquial name). This is consistent with HIFLD's naming convention.
- Alcatraz — Not found. Expected: it's a National Historic Landmark, not an active correctional facility, so its absence is correct.

### 2.6 Data Integrity Deductions

- **Gender Value Mismatch**: 24 records contain `gender="Mixed"` from BOP API enrichment. The Data Dictionary in both CSV, Excel Sheet 4, README, and Word/PDF all define this field as accepting `"Male", "Female", "Co-ed", "Not Specified"`. The value `"Mixed"` is not listed as a valid option. The BOP API provides `"mixed"` which the pipeline `.title()`-cases to `"Mixed"` but never maps to the documented `"Co-ed"`. This creates a data-to-documentation discrepancy where 24 records carry a value not present in the schema definition. (-2)

**Section Score: 18 / 20**

---

## Section 3: Excel Spreadsheet Fidelity (20 Points)

### 3.1 Sheet Structure
- 4 active sheets: *Master Facilities Directory*, *State Summary*, *Jurisdiction Summary*, *Data Dictionary*. ✅

### 3.2 CSV-Excel Parity
- Excel Master Directory: 6,788 data rows + 1 header = 6,789 total rows. ✅
- 20 columns in both CSV and Excel. ✅

### 3.3 Cross-Validation of Summary Tabs
- State Summary facility total sum: 6,788 (matches CSV). ✅
- State Summary capacity sum: 2,411,708 (matches CSV). ✅
- State Summary population sum: 2,069,547 (matches CSV). ✅
- Jurisdiction Summary facility total sum: 6,788 (matches CSV). ✅

### 3.4 Data Dictionary
- 3-column schema: `Display Column Header`, `CSV Field Name (snake_case)`, `Description & Definition`. ✅
- 20 data rows + 1 header = 21 rows. ✅
- Gender description says `"Male, Female, Co-ed, or Not Specified"` but the actual data uses `"Mixed"` instead of `"Co-ed"`. (Deducted in Section 2.)

**Section Score: 20 / 20**

---

## Section 4: Methodology & Documentation (20 Points)

### 4.1 Synchronicity
- README total facilities (6,788) matches CSV. ✅
- README bed capacity (2,411,708) matches CSV sum. ✅
- README population (2,069,547) matches CSV sum. ✅
- README jurisdiction breakdown matches CSV `value_counts()`. ✅
- Word/PDF report metrics table matches CSV. ✅
- JSON summary matches CSV for total, capacity, population, and GPS count. ✅

### 4.2 Disclosures
- Multi-part polygon consolidation: Disclosed in README Section 2.1 (4,001 secondary nodes consolidated). ✅
- BOP entity matching rules: Disclosed in README Section 2.2 with type guards, camp parity, and admin segregation. ✅
- FIPS corrections/imputations: Disclosed in README Section 2.5 (Pickens County, territory FIPS). ✅
- Zero-population retention: Disclosed in README Section 2.3 (625 records). ✅

### 4.3 Known Limitations & Upstream Anomalies
- Point-in-time census snapshots: Disclosed. ✅
- 8 upstream population vs capacity outliers (>3×): All 8 documented with specific facility names, locations, and ratios. ✅
- Campus co-location: Disclosed. ✅

### 4.4 Documentation Deductions

- **Gender Schema Discrepancy**: README Data Dictionary (line 116), Excel Data Dictionary (row 19), and Word/PDF report all state `gender` accepts `"Male, Female, Co-ed, or Not Specified"`, but actual data contains `"Mixed"` (24 records). The documented value `"Co-ed"` does not appear in the dataset at all. This is an accuracy issue in documentation. (-1)
- **Private Jurisdiction Documentation**: The README jurisdiction table does not include "Private" as a row (which is correct since no records carry this classification), but the Data Dictionary (line 100) lists `"Private"` as a valid jurisdiction value, and the pipeline code supports it. This is minor — the code handles a theoretical upstream category that doesn't currently exist in the data — but the Data Dictionary should either note it's unused or omit it. (-0.5)

**Section Score: 18.5 / 20** (rounded to **18** for scorecard)

---

## Section 5: Test Suite Rigor (20 Points)

### 5.1 Test Coverage Analysis (`test_deep_audit.py`)
- 17 adversarial tests covering: unique IDs, mandatory fields, state coverage, coordinate bounds, ZIP validation, FIPS completeness, phone regex, integer formatting, title casing, BOP entity guard (Sybil Brand), intra-federal complex matching (Beaumont/Atlanta/Miami), BOP coordinate completeness, duplicate thresholds (≤10), CSV-Excel parity, summary tab sums, data dictionary structure, and ZIP archive integrity. ✅
- All 17 tests pass with zero defects. ✅

### 5.2 Test Quality Assessment
- Tests are non-tautological: they assert specific counts, regex patterns, and cross-referenced values rather than trivial existence checks. ✅
- Threshold assertions use bounded upper limits (≤10) for co-located facilities with soft-warning visibility. ✅
- Archive integrity test verifies all 5 deliverables are present in the ZIP. ✅

### 5.3 Test Suite Gaps

- **No gender value validation test**: The test suite does not verify that `gender` values match the documented schema (`Male, Female, Co-ed, Not Specified`). If such a test existed, it would have caught the `"Mixed"` vs `"Co-ed"` discrepancy. (-1)
- **No raw-to-output record count parity test**: The test suite does not cross-reference the number of unique FACILITYIDs in `data/hifld_primary_raw.json` against the number of HIFLD-sourced records in the output CSV. While the current data is correct (6,737 after dropping 1 blank record), a regression that silently drops records would not be caught. (-0.5)
- **No FIPS-to-state cross-validation test**: The suite checks FIPS format (5 digits) and completeness but does not verify that the FIPS state prefix matches the `state` column. A FIPS assigned to the wrong state would pass all current tests. (-0.5)

**Section Score: 18 / 20**

---

## Final Scorecard

| Category | Max Points | Prior Score | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| Code Quality & Robustness | 20 | 20 | 19 | Vestigial `GENDER` field reference in HIFLD processing (attrs.get("GENDER") when HIFLD has no GENDER field). No functional bug but misleading. |
| Data Accuracy | 20 | 20 | 18 | 24 records carry `gender="Mixed"` which is not listed in any documentation (Data Dictionary, README, Word, PDF all say `"Co-ed"`). The BOP → output pathway lacks a `"mixed" → "Co-ed"` mapping. |
| Excel Spreadsheet Fidelity | 20 | 20 | 20 | Perfect parity. 4-sheet workbook structure matches spec. Summary sums match CSV aggregations exactly. |
| Methodology Documentation | 20 | 20 | 18 | Gender schema discrepancy in Data Dictionary. "Private" listed as valid jurisdiction in docs but zero records carry this classification. |
| Test Suite Rigor | 20 | 20 | 18 | Missing tests for: gender value validation against schema, raw-to-output record count parity, FIPS-to-state prefix cross-validation. |
| **Total** | **100** | **100** | **93** | **High-quality production dataset with strong source fidelity. One material documentation-vs-data discrepancy ("Mixed" vs "Co-ed") affects 24 records and propagates through all documentation layers. No data corruption or accuracy issues beyond this naming inconsistency.** |

---

## Detailed Findings Index

### Critical Issues (0)
None. No data corruption, no silent dropping of legitimate records, no sentinel leakage, no coordinate distortion.

### Medium Issues (1)

| # | Issue | Location | Impact |
|:---|:---|:---|:---|
| M-1 | Gender field contains `"Mixed"` (24 records) but all documentation defines `"Co-ed"` as the valid value | `build_master_dataset.py:533`, `build_master_dataset.py:548`, README line 116, Excel Data Dictionary row 19, Word/PDF Section 6 | Documentation-to-data schema mismatch across all documentation layers. Downstream consumers relying on the Data Dictionary will not expect `"Mixed"` values. |

**Recommended Fix for M-1**: Either (a) add a mapping in the pipeline: `if gender.lower() == "mixed": gender = "Co-ed"` at the BOP enrichment point and the standalone BOP processing point, OR (b) update all documentation to list `"Mixed"` instead of `"Co-ed"`. Option (a) is recommended to align with the existing documented schema.

### Low Issues (3)

| # | Issue | Location | Impact |
|:---|:---|:---|:---|
| L-1 | `attrs.get("GENDER")` references non-existent HIFLD field | `build_master_dataset.py:533` | No functional bug (returns None → "Not Specified") but misleading code |
| L-2 | "Private" listed as valid jurisdiction in Data Dictionary but zero records exist | README line 100, Excel Data Dictionary | Minor documentation overstatement |
| L-3 | No raw-to-output record count parity test in test suite | `test_deep_audit.py` | Regression risk: silent record dropping would not be caught |

### Informational Observations

1. **69 large-capacity facilities (>500 beds) with zero population**: These include well-known closed facilities (e.g., Maricopa County Tent City, Nevada State Prison, McNeil Island) and facilities repurposed or mothballed. These are correctly preserved as upstream HIFLD reports them.
2. **Reeves County CI I & II and CI III**: These Multi-Jurisdiction facilities correctly have `bop.gov` URLs because they are GEO Group private prisons operating under BOP contract. The URLs are directly from the upstream HIFLD `WEBSITE` field, not from the BOP matching pipeline. Accurate.
3. **One blank upstream record**: HIFLD OBJECTID 10738 (created by `BVanderhorst@riversideca.gov_CityOfRiverside`) has all null fields. Correctly dropped by the `if not fac_id: continue` guard with warning logging.
4. **4,000 multi-part polygon deduplication pairs**: All are exactly 2-feature pairs (no facility has >2 raw features). The max duplication factor is 2. This is clean deduplication.
5. **Woodman State Jail (TX)**: Population 6,478 vs capacity 900 (7.2×). This is documented in the Known Limitations section as an upstream HIFLD artifact. Correct.

---

## Methodology Notes

This audit was conducted by directly:
1. Reading all pipeline source code (`build_master_dataset.py`, `generate_documents.py`, `fetch_raw_data.py`)
2. Executing the existing 17-test suite (all passed)
3. Writing and executing an independent 19-probe adversarial analysis script that:
   - Cross-referenced raw `data/hifld_primary_raw.json` (10,738 features) against output CSV at the record level
   - Cross-referenced raw `data/bop_raw.json` (165 locations) for accounting
   - Verified coordinate fidelity to within ±0.0001° across all 6,737 HIFLD records
   - Checked FIPS-to-state prefix consistency for all 6,788 records
   - Scanned for sentinel string and integer leakage across all columns
   - Validated jurisdiction classification against raw TYPE field
   - Tested `clean_int()` edge cases programmatically
   - Performed stratified regional sampling and well-known facility spot checks
   - Cross-validated README, JSON summary, and CSV statistics for exact parity
4. Reviewing all 9 prior audit reports and the Master Audit Scorecard
