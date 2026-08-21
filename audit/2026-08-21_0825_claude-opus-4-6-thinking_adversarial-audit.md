# Adversarial Dataset & Code Quality Audit Report

| Field | Value |
|:---|:---|
| **Date** | 2026-08-21 |
| **Time** | 08:25 EDT |
| **Auditor Model** | Claude Opus 4.6 (Thinking) — Anthropic |
| **Requesting Model** | User Direct Request |
| **Audit Scope** | Full adversarial audit: pipeline code, raw source data cross-validation, cleaning function edge cases, output CSV/XLSX integrity, documentation synchronicity, test suite gap analysis |
| **Audit Focus** | Data accuracy, cleaning technique fidelity, script processing fidelity, end-to-end source-to-output integrity |
| **Final Score** | **95 / 100** |

---

## Executive Summary

An independent, adversarial audit was conducted on the **US Correctional Facilities Aggregator** at `/home/derekf35/Development/PROJECTS/prison-data-agg`. This audit is the **11th** in the project's audit history and the **second** by Claude Opus 4.6. It was conducted with maximum adversarial rigor, executing **25 independent probes** (Phase 1) and **9 deep-dive targeted probes** (Phase 2) — a total of **34 independent validation checks** beyond the existing 17-test suite.

### Key Verdict

The pipeline is **production-ready** with strong data integrity fundamentals. All 6,788 records pass structural, geospatial, and referential integrity checks. The prior audit's critical finding (gender schema mismatch) has been **fully remediated** — `normalize_gender()` now correctly maps BOP `"Mixed"` → `"Co-ed"`, bringing all 24 affected records into schema compliance. Several minor documentation drift issues remain.

### Summary of Findings

| Severity | Count | Description |
|:---|:---:|:---|
| **Critical** | 0 | No data corruption, no silent record loss, no schema violations |
| **Medium** | 1 | README address percentage displayed as "100.0%" when actual coverage is 99.96% (6,785/6,788) |
| **Low** | 3 | README embedded test output has stale file sizes (Excel, Word, PDF, ZIP differ by 1–4,240 bytes); README references "9 audits" but 10 exist; `format_title` first-word capitalization override |
| **Informational** | 2 | `clean_int(float('inf'))` raises `OverflowError` rather than returning `None` gracefully; 4 non-admin BOP facilities unmatched to HIFLD but correctly handled as standalone |

---

## Section 1: Data Completeness (20 Points)

### 1.1 Record Count Arithmetic (Probe 1)

| Component | Count | Verified |
|:---|---:|:---:|
| Raw HIFLD features | 10,738 | ✅ |
| Unique HIFLD FACILITYIDs | 6,737 | ✅ |
| Multi-part polygon consolidations | 4,000 | ✅ |
| Standalone BOP records | 51 | ✅ |
| **Total output records** | **6,788** | ✅ |
| Expected: 6,737 + 51 | **6,788** | ✅ |

**Zero HIFLD facility IDs were silently dropped.** The arithmetic `6,737 + 51 = 6,788` is exactly correct. All 6,737 unique HIFLD IDs from raw JSON appear in the output CSV.

### 1.2 Geocoding Completeness (Probes 2, 8, 19, 21)
- **100.0%** geocoding: All 6,788 records have valid latitude and longitude.
- **Stratified regional verification**:
  - Northeast: 655 (100%), Midwest: 1,754 (100%), South: 3,085 (100%), West: 1,247 (100%), Territories: 47 (100%)
- **Territory coverage**: Guam (4 records, lat 13.45–13.47, lon 144.75–144.80), CNMI (1 record), VI (2 records), PR (40 records confirmed).
- **Coordinate preservation**: 50 randomly-sampled HIFLD coordinates cross-referenced against raw JSON — all match within rounding tolerance (6 decimal places). 500-record coordinate preservation check found zero valid coordinates dropped.

### 1.3 FIPS & ZIP Completeness (Probes 6, 16)
- **100.0%** county FIPS: All 6,788 records have valid 5-digit FIPS codes.
- **FIPS-to-State consistency**: All 6,788 FIPS code prefixes match their respective state codes. Zero mismatches.
- **100.0%** ZIP codes: All match `^\d{5}(-\d{4})?$` regex. 279 leading-zero ZIP codes correctly preserved.

### 1.4 Mandatory Field Completeness
- `facility_name`: 100% (0 empty)
- `state`: 100% (0 empty)
- `jurisdiction`: 100% (0 empty)
- `operational_status`: 100% (0 empty)
- `street_address`: 6,785 / 6,788 (3 empty: Bullock County AL, Phillips County AR, Saipan MP)

**Score: 20 / 20** — No data loss detected. All structural integrity invariants hold. The 3 empty addresses are genuine upstream data gaps, not pipeline errors.

---

## Section 2: Data Accuracy (20 Points)

### 2.1 Zero-Population Preservation (Probe 3)
- Raw HIFLD records with `POPULATION=0`: **625**
- CSV records with `population=0`: **625**
- **Perfect 1:1 correspondence.** Every zero-population facility ID in the raw source appears as `population=0` in the output. No zero values were erroneously converted to null or dropped.

### 2.2 Sentinel Scrubbing (Probe 3)
- **1,924** raw records with sentinel population values (`-999`, `-1`, `99999`, negative) were properly scrubbed to null.
- Zero sentinel values leaked into the output. ✅

### 2.3 Gender Schema Compliance (Probe 4)
- **Critical Prior Finding REMEDIATED**: Audit #10 discovered that 24 BOP records carried `"Mixed"` instead of the documented `"Co-ed"`. The `normalize_gender()` function now correctly maps `"mixed"` → `"Co-ed"`.
- Current gender distribution: `Not Specified` (6,655), `Male` (103), `Co-ed` (24), `Female` (6).
- All values conform to documented schema `{Male, Female, Co-ed, Not Specified}`. ✅

### 2.4 BOP Entity Resolution (Probes 5, 12, 20)
- **Type guard verified**: Sybil Brand Institute (FACILITYID `10000894`, county jail in Los Angeles) correctly has NO bop.gov URL. ✅
- **Camp-to-camp parity**: USP Beaumont → `/institutions/bmp/`, FCI Beaumont Low → `/institutions/bml/`, FCI Beaumont Medium → `/institutions/bmm/`, USP Atlanta → `/institutions/atl/`. All URL assignments verified correct. ✅
- **Administrative segregation**: 47 raw admin BOP records (RRM, RO, CO, FCC, TRN) correctly routed to standalone. ✅
- **4 unmatched non-admin BOP**: Lompoc I FCI (`BOP-LOF`), Lompoc II FCI (`BOP-LOM`), Morgantown FPC (`BOP-MRG`), Yazoo City Low II FCI (`BOP-YAM`) — all have complete data (name, coordinates, FIPS, ZIP). These represent legitimate standalone entries for BOP-designated sub-institutions that lack direct HIFLD counterparts.

### 2.5 Typography & Title Casing (Probes 7, C)
- **76** Mc-prefix names correctly capitalized (McDuffie, McCreary, McKean, etc.) ✅
- **3** O'-prefix names correctly capitalized (O'Brien, Chain O'Lakes, O'Farrell) ✅
- All checked acronyms (USP, FCI, ADX, FDC, MDC, FMC, FPC, MCC, DOC, SCI) preserved in uppercase. ✅
- **Minor edge case**: `format_title("of the state")` returns `"Of the State"` — the first-word capitalization override correctly capitalizes leading lowercase words per standard title case rules, but this technically conflicts with the function's own lowercase-word list. This does not affect any actual facility names (no facility names begin with articles/prepositions).

### 2.6 Capacity/Population Outliers (Probe 13)
- **Exactly 8** facilities where population > 3× capacity, matching README's documented list precisely.
- All 8 are verified upstream HIFLD artifacts faithfully preserved.

### 2.7 Float Artifact Check (Probe 14)
- Zero `.0` float suffixes in `design_capacity` or `population` columns in the CSV. `Int64` nullable integer serialization working correctly. ✅

### 2.8 Negative Value Check (Probe 17)
- Zero negative capacity or population values in output. ✅

**Score: 19 / 20** — Near-perfect accuracy. Minor deduction for the README's display of street address coverage as "100.0%" when the actual figure is 99.96% (6,785/6,788 = 99.956%) — a misleading rounded percentage.

---

## Section 3: Code Quality & Robustness (20 Points)

### 3.1 Ingestion & Caching
- ArcGIS pagination with batch size 2,000, timeout handling (15s/30s), and `exceededTransferLimit` detection. ✅
- Local JSON caching with minimum size guard (100KB). ✅
- BOP fetch resilience with try/except fallback. ✅

### 3.2 Sanitization Function Quality (Probes A, B, F, G)

#### `clean_int()` Edge Case Results
| Input | Result | Expected | Status |
|:---|:---|:---|:---:|
| `0` | `0` | `0` | ✅ |
| `100.4` | `100` | `100` | ✅ |
| `100.5` | `100` | `100` | ✅ (Banker's) |
| `-999` | `None` | `None` | ✅ |
| `99999` | `None` | `None` | ✅ |
| `None` | `None` | `None` | ✅ |
| `"abc"` | `None` | `None` | ✅ |
| `float('inf')` | `OverflowError` | — | ⚠️ |
| `float('nan')` | `None` | `None` | ✅ |

**Infinity vulnerability**: `clean_int(float('inf'))` raises `OverflowError` at `int(round(f))` rather than returning `None` gracefully. However, this is **theoretical only** — zero infinity values exist in either raw source (HIFLD or BOP). The uncaught exception would crash the pipeline visibly rather than silently corrupt data, making this a fail-safe rather than fail-silent bug.

**Banker's rounding**: Python's `round()` uses banker's rounding (rounds-half-to-even). This has **zero practical impact** — no fractional population or capacity values exist in the raw source data.

#### `clean_coord()` Edge Case Results
All 14 boundary condition tests passed — latitude bounds [13.0, 72.0], longitude bounds [-180.0, -64.0] ∪ [144.0, 180.0], gap rejection, and boundary-inclusive behavior all verified correct. ✅

#### `normalize_gender()` 
Correctly maps: `"mixed"` → `"Co-ed"`, `"Male"` → `"Male"`, `"Female"` → `"Female"`, `""` → `"Not Specified"`. ✅

### 3.3 Multi-Part Polygon Consolidation
- 4,000 secondary polygon nodes consolidated (10,738 − 6,737 unique IDs − 1 blank = 4,000 consolidations).
- Logging is explicit: `"[+] Multi-part polygon features consolidated: X secondary boundary nodes merged"`. ✅

### 3.4 CSV Serialization
- `Int64` nullable integers used for capacity and population — no `.0` float suffixes in CSV. ✅
- UTF-8 encoding with proper string quoting. ✅

**Score: 20 / 20** — Code is resilient, well-guarded, and handles all realistic edge cases. The `float('inf')` issue is theoretical and fail-safe.

---

## Section 4: Methodology Documentation (20 Points)

### 4.1 Count Synchronicity (Probes 9, 11, 22, 24)

| Metric | README | CSV | JSON Summary | Status |
|:---|:---:|:---:|:---:|:---:|
| Total facilities | 6,788 | 6,788 | 6,788 | ✅ |
| Total capacity | 2,411,708 | 2,411,708 | 2,411,708 | ✅ |
| Total population | 2,069,547 | 2,069,547 | 2,069,547 | ✅ |
| County / Local | 3,960 | 3,960 | — | ✅ |
| State | 2,273 | 2,273 | — | ✅ |
| Federal | 308 | 308 | — | ✅ |
| Municipal / Local | 184 | 184 | — | ✅ |
| Multi-Jurisdiction | 36 | 36 | — | ✅ |
| Not Specified | 27 | 27 | — | ✅ |

**All primary counts are synchronized.** ✅

### 4.2 Documentation Drift Issues

1. **README address percentage** (Line 24): States "Facilities with Street Addresses: 6,785 (100.0%)" — but 6,785/6,788 = **99.96%**, not 100.0%. The `(100.0%)` display is inaccurate, even though the count `6,785` itself is correct.

2. **README embedded test output file sizes** (Lines 130–135): The byte sizes shown in the embedded test output no longer match current deliverable files:
   - Excel: README shows `1,037,802`, actual is `1,037,801` (1 byte drift)
   - Word: README shows `40,845`, actual is `41,358` (513 bytes drift)
   - PDF: README shows `101,230`, actual is `105,470` (4,240 bytes drift)
   - ZIP: README shows `1,549,950`, actual is `1,552,578` (2,628 bytes drift)

3. **README audit count reference** (Line 123): References "all 9 independent adversarial audits" but `audit/README.md` contains 10 audit rows. The README is stale by 1 audit.

### 4.3 Known Limitations Section
- Point-in-time census snapshots: documented. ✅
- 8 upstream population outliers (>3×): documented and verified against CSV. ✅
- Campus co-location: documented. ✅
- Multi-part polygon consolidation: documented. ✅

### 4.4 Data Dictionary
- 20-field, 3-column mapping (Display Header → `snake_case` → Description). ✅
- All 20 CSV columns documented. ✅
- Gender schema now correctly documents `{Male, Female, Co-ed, Not Specified}` — matches actual data. ✅

**Score: 18 / 20** — Primary counts are perfectly synchronized. Deductions for: (1) the address coverage percentage displayed as "100.0%" when 3 records lack addresses (misleading rounding), and (2) multiple stale embedded test output byte sizes in README, plus stale audit count reference. These are cosmetic but affect documentation trustworthiness.

---

## Section 5: Test Suite Rigor (20 Points)

### 5.1 Existing Test Suite Results
All 17 tests in `test_deep_audit.py` pass cleanly:
- Test 1–8: Structural integrity (IDs, mandatory fields, states, coordinates, ZIPs, FIPS, phones, integers) ✅
- Test 9: Scottish/Irish name capitalization ✅
- Test 10: BOP entity matching guard (Sybil Brand) ✅
- Test 11: Intra-federal complex matching (Beaumont, Atlanta, Miami) ✅
- Test 12: BOP standalone GPS completeness ✅
- Test 13: Duplicate name/coordinate threshold (≤10) ✅
- Test 14–16: CSV/Excel parity, summary tab sums, data dictionary ✅
- Test 17: ZIP archive integrity ✅

### 5.2 Test Suite Gap Analysis (Probe 25)

The following categories of validation are NOT covered by the existing test suite:

1. **No FIPS-to-state code cross-validation**: The test suite verifies FIPS format (5-digit) and completeness, but does not verify that the first 2 digits of each FIPS code match the state's assigned FIPS prefix. Our Probe 6 validated this independently — all 6,788 codes are consistent.

2. **No raw source data cross-reference tests**: The test suite validates output properties but never cross-references against `hifld_primary_raw.json` or `bop_raw.json` to verify end-to-end fidelity. Our Probes 1–3 fill this gap.

3. **No unit tests for cleaning functions**: `clean_int`, `clean_coord`, `clean_zip`, `clean_text`, `format_title`, `normalize_gender` are tested only implicitly through output validation. No isolated unit tests with exotic inputs exist. Our Probes A–C fill this gap.

4. **No BOP matching completeness verification**: No test confirms that all 165 raw BOP records are accounted for (matched to HIFLD or standalone). Our Probes 18 and 20 verified the accounting.

5. **No explicit gender schema validation test**: Gender values are not checked against the documented enum. Our Probe 4 verified compliance.

6. **No documentation-to-data synchronicity test**: No test compares README counts or JSON summary counts against the CSV. Our Probes 9, 11, and 22 performed this.

### 5.3 Test Suite Strengths
- Non-tautological assertions that test real data properties. ✅
- Bounded threshold for co-location (≤10) with soft warnings. ✅
- Multi-deliverable integrity (CSV, Excel, Word, PDF, ZIP). ✅
- Specific named-entity spot checks (Sybil Brand, Beaumont complex, Atlanta). ✅

**Score: 18 / 20** — Test suite is comprehensive for output validation but lacks raw-source cross-validation, unit-level cleaning function tests, and documentation synchronicity checks. The 6 identified gaps represent meaningful attack surfaces that could allow future regressions to slip past the test suite undetected.

---

## Final Scorecard

| Category | Max Points | Prior Score | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| Data Completeness | 20 | 19 | 20 | Zero record loss, 100% geocoding, 100% FIPS, 100% ZIP. 6,737 + 51 = 6,788 arithmetic verified. All mandatory fields complete. |
| Data Accuracy | 20 | 18 | 19 | Gender schema now compliant (prior finding remediated). Zero-pop preservation exact (625/625). All sentinels scrubbed. BOP entity resolution correct. Minor: README address "100.0%" display when 3 records lack addresses. |
| Code Quality & Robustness | 20 | 20 | 20 | All cleaning functions pass edge case testing. Pagination, caching, type guards, camp-parity all verified. `float('inf')` is theoretical-only and fail-safe. |
| Methodology Documentation | 20 | 18 | 18 | Primary counts synchronized perfectly. Deductions: stale README embedded file sizes (4 of 5 deliverables differ), stale audit count reference (says 9, actually 10), misleading address "100.0%" display. |
| Test Suite Rigor | 20 | 18 | 18 | 17/17 tests pass. 6 identified coverage gaps: no raw-source cross-validation, no cleaning function unit tests, no FIPS-state consistency check, no gender schema test, no BOP accounting test, no documentation sync test. |
| **Total** | **100** | **93** | **95** | **Production-Ready with minor documentation drift.** Prior critical gender finding remediated. No data corruption or silent data loss detected across 34 independent probes. |

---

## Detailed Findings Register

### Finding F-1: README Address Percentage Rounding (Medium)
- **Location**: `README.md` line 24
- **Issue**: Displays "Facilities with Street Addresses: 6,785 (100.0%)" but 6,785/6,788 = 99.96%, not 100.0%.
- **Impact**: Misleading to researchers who expect exact 100% coverage; 3 facilities (Bullock County AL, Phillips County AR, Saipan MP) lack addresses.
- **Recommendation**: Display as "6,785 (99.96%)" or "6,785 (~100%)".

### Finding F-2: Stale README Embedded Test Output (Low)
- **Location**: `README.md` lines 130–135
- **Issue**: Embedded test output shows file sizes from a previous build. Current sizes differ: Excel (1 byte), Word (513 bytes), PDF (4,240 bytes), ZIP (2,628 bytes).
- **Impact**: Documentation integrity; suggests the embedded output was not regenerated after the latest document build.
- **Recommendation**: Re-run `test_deep_audit.py` and update the embedded output block.

### Finding F-3: Stale README Audit Count (Low)
- **Location**: `README.md` line 123
- **Issue**: References "all 9 independent adversarial audits" but `audit/README.md` contains 10 completed audits.
- **Impact**: Minor documentation staleness.
- **Recommendation**: Update to reflect current audit count.

### Finding F-4: `format_title` First-Word Override (Low)
- **Location**: `build_master_dataset.py` line 312
- **Issue**: `format_title("of the state")` → `"Of the State"` — the first-word capitalization override overrides the lowercase-word list for words like "of", "the", etc. when they appear as the first word.
- **Impact**: **Zero practical impact** — no facility names in the dataset begin with articles or prepositions. This is standard title-casing behavior (capitalize first word regardless of article status).
- **Status**: Acceptable behavior; no action needed.

### Finding F-5: `clean_int(float('inf'))` Exception Path (Informational)
- **Location**: `build_master_dataset.py` line 246
- **Issue**: `int(round(float('inf')))` raises `OverflowError` rather than returning `None` via the try/except which catches `ValueError` and `TypeError` but not `OverflowError`.
- **Impact**: **Zero practical impact** — no infinity values exist in either raw source. The exception would crash the pipeline visibly (fail-safe behavior).
- **Recommendation**: Add `OverflowError` to the except clause for defensive completeness.

### Finding F-6: Four Unmatched Non-Admin BOP Facilities (Informational)
- **Location**: `build_master_dataset.py` BOP matching logic
- **Issue**: 4 non-admin BOP facilities (Lompoc I, Lompoc II, Morgantown, Yazoo City Low II) had no HIFLD match and were correctly added as standalone records with `BOP-{code}` IDs.
- **Impact**: **Correct behavior.** These represent sub-institutions of federal complexes that have distinct BOP codes but no direct HIFLD counterpart. All 4 have complete data (name, coordinates, FIPS, ZIP, county).
- **Status**: Working as designed.

---

## Remediation Tracking from Prior Audit (#10)

| Prior Finding | Status | Evidence |
|:---|:---:|:---|
| Gender schema mismatch (24 "Mixed" records) | ✅ **FIXED** | `normalize_gender()` maps `"mixed"` → `"Co-ed"`. All 24 BOP records now carry `"Co-ed"`. Probe 4 verified zero schema violations. |
| Private jurisdiction dead code | ✅ **Acknowledged** | Zero raw records with `TYPE=PRIVATE`. Dead code path confirmed. No data impact. |
| Blank raw record correctly dropped | ✅ **Verified** | OBJECTID 10738 blank artifact correctly excluded by `if not fac_id: continue` guard. |

---

## Methodology

### Tools & Approach
- **Existing test suite**: Executed `test_deep_audit.py` (17/17 pass) as baseline.
- **Independent probe suite**: Wrote and executed 34 custom probes across 2 phases:
  - Phase 1 (25 probes): Record count arithmetic, coordinate fidelity (50 samples), zero-pop preservation, sentinel scrubbing, gender compliance, BOP segregation, FIPS-state consistency, title casing, territory coordinates, jurisdiction cross-check, documentation synchronicity, BOP URL enrichment, outlier verification, float artifacts, BOP ID format, ZIP leading zeros, negative values, BOP accounting, stratified regional sampling, BOP matching coverage, coordinate preservation (500 samples), README staleness, ZIP edge cases, audit reference consistency, test suite gap analysis.
  - Phase 2 (9 probes): `clean_int` unit tests (16 cases), `clean_coord` unit tests (14 cases), `format_title` unit tests (11 cases), unmatched BOP data quality, README embedded file size verification, infinity vulnerability assessment, banker's rounding impact, optional field completeness, private jurisdiction investigation.
- **Cross-reference sources**: Raw `data/hifld_primary_raw.json` (10,738 features, 9.8 MB) and `data/bop_raw.json` (165 locations, 132 KB) compared against `output/us_correctional_facilities_master.csv` (6,788 rows).

### Independence Guarantee
This audit made **zero modifications** to pipeline code, raw data, or output files. All validation was performed through read-only analysis and standalone probe scripts. Probe scripts were deleted after execution.
