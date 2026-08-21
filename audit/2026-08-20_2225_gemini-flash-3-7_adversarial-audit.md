# Adversarial Dataset & Code Audit Report

| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 22:25 EDT |
| **Auditor Model** | Gemini 3.7 Flash (Thinking) — Google DeepMind |
| **Requesting Model** | User Request |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | **88 / 100** |

---

## Executive Summary

An exhaustive, adversarial code and data quality audit was conducted on the US Correctional Facilities Aggregator codebase and data products. Significant architectural and data quality enhancements have been implemented since earlier revisions (such as resolving the county jail `LOS` false-positive matching bug, preserving legitimate zero-population facilities, fixing `Mc`/`O'` title casing, establishing complete county FIPS mapping, and integrating a 16-point adversarial test suite). 

However, deep forensic evaluation identified a subtle and critical **intra-federal entity collision bug** in the BOP matching algorithm, alongside minor documentation and test rigor gaps:

1. **Intra-Federal BOP Entity Collision Bug in Rule 3 (`build_master_dataset.py:345–354`)**: While county jail cross-matching was successfully prevented by the `is_fed` guard, Rule 3 (`b_name_norm in h_name_norm and (b_city_norm == h_city_norm)`) uses broad substring matching. In federal complexes and major cities with multiple federal entities (prisons, FCC administrative offices, and RRM community corrections field offices), multiple distinct BOP entities match the *same* primary HIFLD record in loop order. This causes 18 HIFLD facilities (e.g., `USP Atlanta Camp`, `FCI Miami Camp`, `FCI Beaumont Low`) to have their contact phone numbers and URLs overwritten by administrative RRM field offices or complex search portals, while leaving actual institutions (e.g., `USP Beaumont`, `FDC Miami`) with generic fallback URLs.
2. **Preservation of Zero Counts Confirmed**: Zero-population preservation is fully functioning in `clean_int()`, correctly retaining 625 facilities with `population = 0` (e.g., intake, holding, or newly constructed units).
3. **Typography and Acronym Casing Verified**: All 76 `Mc` names (e.g., `McDuffie`, `McCreary`, `McKean`) and 3 `O'` names (e.g., `O'Brien`, `Chain O'Lakes`) are 100.0% correctly cased.
4. **All-Three Completeness Accurately Re-evaluated at 5,790**: Facilities possessing all three of `street_address`, `phone_number`, AND `website` total exactly **5,790** (the shift from 5,791 is directly traceable to the removal of the false BOP website previously assigned to Sybil Brand Institute).
5. **High Deliverable Fidelity**: The 4-sheet Excel workbook, Word report, PDF report, and `prison_data_report.zip` archive exhibit 1-to-1 parity with the master CSV dataset.

---

## Section 1: Code Quality Review — `build_master_dataset.py`

### 1.1 Intra-Federal BOP Entity Collision Bug (Lines 315–373)
- **Status: Active Algorithmic Flaw.**
- **Mechanism**: The Federal Bureau of Prisons directory (`bop_raw.json`) contains three distinct categories of records:
  1. Individual institutions (e.g., `FCI Beaumont Low` [`BML`], `USP Beaumont` [`BMP`], `FCI Miami` [`MIA`], `FDC Miami` [`MIM`]).
  2. Federal Correctional Complexes (FCCs), representing campus-wide management (e.g., `FCC Beaumont` [`BMX`], `FCC Butner` [`BUX`], `FCC Florence` [`FLX`]).
  3. Residential Reentry Management (RRM) field offices (e.g., `RRM Atlanta` [`CAT`], `RRM Miami` [`CMM`], `RRM Philadelphia` [`CPA`], `RRM Phoenix` [`CPH`], `RRM Montgomery` [`CMY`]).
- When `bop_raw` is processed, Rule 3 matches when `b_name_norm in h_name_norm` and cities match:
  - For `RRM Atlanta` (`CAT`, name=`"ATLANTA"`), Rule 3 matches HIFLD record `10006239` (`USP ATLANTA CAMP`), overwriting its phone number with `(470) 832-5841` and its website with `https://www.bop.gov/locations/ccm/cat` (the RRM field office).
  - For `RRM Miami` (`CMM`, name=`"MIAMI"`), Rule 3 matches HIFLD record `10000550` (`FCI MIAMI CAMP`), overwriting it with RRM Miami's phone `(786) 584-4730` and URL `https://www.bop.gov/locations/ccm/cmm`.
  - For `USP Beaumont` (`BMP`, name=`"BEAUMONT"`), Rule 3 matches HIFLD record `10002860` (`FCI BEAUMONT LOW`) before checking `10001990` (`USP BEAUMONT`), assigning the USP URL to the FCI Low facility and leaving the actual USP Beaumont with the generic fallback URL `https://www.bop.gov/locations/`.
- **Impact**: Exactly 18 HIFLD records matched multiple BOP entities, causing data pollution across contact info and URL mappings.

### 1.2 `clean_int()` Integer Filtering (Lines 219–228)
- **Status: Resolved.**
- The condition `if f in SENTINEL_INTS or f < 0:` properly allows `f == 0`. Discrete integer conversion via pandas `Int64` nullable type prevents floating `.0` suffixes in CSV output while preserving null values.

### 1.3 `clean_coord()` Coordinate Filtering (Lines 230–244)
- **Status: Resolved.**
- Latitude check `13.0 <= f <= 72.0` and longitude check `(-180.0 <= f <= -64.0) or (144.0 <= f <= 180.0)` encompass all contiguous US states, Alaska, Hawaii, Puerto Rico, US Virgin Islands, Guam, CNMI, and the Aleutian Islands up to +180° longitude.

### 1.4 `format_title()` Typography & Acronyms (Lines 246–286)
- **Status: Resolved.**
- Surnames and prefixes starting with `Mc` and `O'` are correctly normalized (e.g., `McDuffie`, `McCreary`, `McKean`, `O'Brien`, `Chain O'Lakes`). Possessives like `Men's` and `Women's` are preserved, and acronyms in `ACRONYMS` remain uppercase.

### 1.5 Deduplication and Attribute Retention (Lines 289–307)
- **Status: Functional with Minor Limitation.**
- HIFLD multipart features are deduplicated on `FACILITYID`. When a duplicate feature is encountered, it only overwrites the existing entry if the existing entry lacked GPS coordinates. If the duplicate feature has updated phone numbers or addresses, they are silently ignored without logging.

---

## Section 2: Data Integrity Review — `us_correctional_facilities_master.csv`

### 2.1 Regional Sampling & Spot-Checks
A stratified random sample of 20 records per US region (Northeast, Midwest, South, West, Territories) was analyzed across all 20 columns:
- **Northeast (653 records)**: Standard 5-digit ZIPs with preserved leading zeroes (e.g., `03833` NH, `07456` NJ, `01949` MA); 100% valid FIPS.
- **Midwest (1,753 records)**: Proper casing for complex facility names (e.g., `Parnall Correctional Facility`, `Monday Community Correctional Institution`); 100% coordinate compliance.
- **South (3,083 records)**: Correct handling of county detention centers, youth academies, and work camps; leading zeroes preserved on AR, TX, and FL FIPS.
- **West (1,242 records)**: Valid geocoding across CA, NV, MT, OR, WY, and HI; correct classification for camp programs (e.g., `McCain Valley Conservation Camp #21`).
- **Territories (47 records)**: Complete geocoding for Puerto Rico (`00xxx` ZIPs, `72xxx` FIPS), Guam (`66010` FIPS), US Virgin Islands (`78010` FIPS), and Saipan / Northern Mariana Islands (`69110` FIPS).

### 2.2 Field Population & Metric Audit
- **All-Three Completeness**: Exactly **5,790** facilities have all three of `street_address`, `phone_number`, and `website` populated.
- **Zero-Population Facilities**: Exactly **625** facilities legitimately record `population = 0`.
- **Overcrowded Facilities (`population > 3× design_capacity`)**: Exactly 8 records exhibit this ratio (e.g., `Woodman State Jail` TX: 6,478 pop / 900 cap). Verified as upstream DHS HIFLD data reporting anomalies.
- **BOP Standalone Coordinates**: All 31 standalone BOP records possess 100.0% valid GPS coordinates.
- **Duplicate Name / Coordinate Triplets**:
  - 3 pairs (6 records) share `(facility_name, city, state)` triplets: `Larned State Hospital` (KS), `Jessup Correctional Institution` (MD), and `Garza County Jail` (TX). Verified as upstream duplicate records with distinct HIFLD IDs.
  - 2 coordinate pairs (4 records) share exact lat/lon: co-located BOP regional offices in Grand Prairie, TX (`BOP-GRA` / `BOP-SCR`) and Annapolis Junction, MD (`BOP-MXR` / `BOP-CBR`).
- **Postal & FIPS Integrity**: Zero invalid ZIP formats (`^\d{5}(-\d{4})?$`); zero invalid FIPS codes (`^\d{5}$`).

---

## Section 3: Excel Workbook Review — `us_correctional_facilities_master.xlsx`

### 3.1 Sheet Structure & Data Fidelity
- **Sheet 1 (`Master Facilities Directory`)**: Contains 6,768 facility rows + 1 header row, with 20 formatted columns matching the CSV field order. ZIP and FIPS columns are formatted as Text (`@`), preserving leading zeroes. Design Capacity and Population are formatted with integer thousands separators (`#,##0`).
- **Sheet 2 (`State Summary`)**: Independent `groupby` re-aggregation confirmed exact parity across all 55 jurisdictions:
  - Total Facilities: **6,768**
  - Total Reported Capacity: **2,411,708**
  - Total Reported Population: **2,069,547**
- **Sheet 3 (`Jurisdiction Summary`)**: Groupings by jurisdiction and facility type match the ground-truth CSV aggregations.
- **Sheet 4 (`Data Dictionary`)**: Implements an explicit 3-column mapping design:
  1. `Display Column Header`
  2. `CSV Field Name (snake_case)`
  3. `Description & Definition`
  All 20 programmatic fields are thoroughly defined.

---

## Section 4: Methodology & Documentation Review — `README.md`

### 4.1 Documentation Strengths
- **Accurate Jurisdiction Distribution**: The table in `README.md` mirrors the exact programmatic counts:
  - County / Local: 3,960 (58.5%)
  - State DOC: 2,273 (33.6%)
  - Federal: 288 (4.3%)
  - Municipal / Local: 184 (2.7%)
  - Multi-Jurisdiction: 36 (0.5%)
  - Not Specified: 27 (0.4%)
  - Total: 6,768 (100.0%)
- **Disclosures Present**:
  - Imputation of territory FIPS codes (`66010`, `78010`, `69110`) and standalone BOP offices is documented.
  - Multi-part GIS polygon deduplication logic reducing 10,738 raw features to 6,737 physical facilities is clearly explained.
  - Preservation of zero counts and scrubbing of negative placeholders is explicitly documented.
  - The previous inaccurate claim of "collision-free" entity matching was replaced with "Type-Guarded BOP Entity Matching".

### 4.2 Documentation Gaps
- The `README.md` test suite summary block displays `ALL 15 ADVERSARIAL FORENSIC AUDIT TESTS PASSED`, whereas `test_deep_audit.py` now executes 16 tests.
- The known limitation regarding intra-federal FCC / RRM matching ambiguity has not yet been documented.

---

## Section 5: Test Suite Review — `test_deep_audit.py` & `verify_dataset.py`

### 5.1 Coverage & Rigor
`test_deep_audit.py` contains 16 automated assertions:
- `Test 1`: Unique Primary IDs (`assert len(dup_ids) == 0`)
- `Test 2`: Mandatory string fields completeness (Name, State, Jurisdiction, Status)
- `Test 3`: Exact 55 valid US jurisdictions verified
- `Test 4`: Bounding box coordinates validation including Aleutian range
- `Test 5`: 5-digit standard ZIP format and leading zero preservation
- `Test 6`: County name and 5-digit FIPS code regex completeness
- `Test 7`: Phone number formatting (`^\(\d{3}\) \d{3}-\d{4}( Ext \d+)?$`) and sentinel absence
- `Test 8`: Discrete integer formatting (absence of `.0` float representations)
- `Test 9`: Title casing and Scottish/Irish prefix formatting (`Mc` and `O'`)
- `Test 10`: Type-guarded BOP matching (Sybil Brand county jail verification)
- `Test 11`: Standalone BOP record GPS completeness (100%)
- `Test 12`: Duplicate name and coordinate accounting
- `Test 13`: Exact 1-to-1 parity between CSV and Excel Master Directory
- `Test 14`: Excel summary mathematical sums cross-validation
- `Test 15`: Excel Data Dictionary 3-column schema compliance
- `Test 16`: Master ZIP archive (`prison_data_report.zip`) file integrity

### 5.2 Test Suite Gaps
- `Test 10` only asserts that Sybil Brand (`10000894`) did not match BOP `LOS` and that MDC Los Angeles (`10000892`) matched. It does not test for intra-federal complex collisions (e.g., verifying that `USP Atlanta Camp` does not receive an RRM phone/URL, or that `FCI Beaumont Low` is not assigned the `USP Beaumont` URL).
- `Test 12` logs duplicate triplets as an informational step rather than checking against an expected threshold.

---

## Final Scorecard

| Category | Max Points | Prior Score (Gemini Pro @ 22:16) | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| **Data Completeness** | 20 | 20 | **19** | 100% geocoded, 100% FIPS, 100% ZIP; only 3 missing street addresses from upstream HIFLD. |
| **Data Accuracy** | 20 | 20 | **16** | County false positives and Mc/O' naming resolved; 18 federal facilities affected by intra-federal BOP matching collisions. |
| **Code Quality & Robustness** | 20 | 20 | **16** | Clean pipeline architecture, robust formatting and typing, but BOP Rule 3 substring logic needs refinement to prevent multi-matching. |
| **Methodology Documentation** | 20 | 20 | **19** | Clear provenance, accurate jurisdiction tables, complete FIPS/cleaning disclosure; minor test count typo in README. |
| **Test Suite Rigor** | 20 | 20 | **18** | 16 strict adversarial tests covering regex, bounds, formatting, and file integrity; missing intra-federal collision assertions. |
| **Total** | **100** | **100** | **88** | **Solid improvement with high integrity, accompanied by actionable recommendations for intra-federal entity matching.** |

---

## Recommended Fixes — Prioritized

### 🔴 High Priority

1. **Refine BOP Entity Matching Rule 3 (`build_master_dataset.py:345–354`)**:
   - Disallow non-prison administrative entities (`type in ['RRM', 'RO', 'CO', 'FCC', 'TRN']`) from matching HIFLD physical prison facilities via substring matching; let them be ingested as standalone records.
   - Track matched HIFLD IDs (`bop_matched_hifld_ids = set()`) and do not allow multiple BOP entities to overwrite the same HIFLD record.
   - For multi-facility complexes (FCCs), enforce strict facility type matching (`FCI` to `FCI`, `USP` to `USP`, `FDC` to `FDC`).

   ```python
   # Proposed fix for build_master_dataset.py
   bop_matched_hifld_ids = set()
   for bop in bop_raw:
       bop_type = clean_text(bop.get("type")).upper()
       # Administrative offices and complex hubs should not overwrite specific prisons
       if bop_type in ("RRM", "RO", "CO", "FCC", "TRN"):
           standalone_bop_records.append(bop)
           continue
       ...
       # In matching loop:
       if fac_id in bop_matched_hifld_ids:
           continue
       ...
   ```

### 🟡 Medium Priority

2. **Expand `test_deep_audit.py` to Validate Intra-Federal Complex URLs**:
   - Add explicit assertions ensuring `USP Beaumont` receives `BMP`'s URL, `FCI Beaumont Low` receives `BML`'s URL, and `USP Atlanta Camp` does not receive `RRM Atlanta`'s URL.
3. **Synchronize Test Count in `README.md`**:
   - Update the audit block in `README.md` to reflect all 16 executed tests.

### 🟢 Low Priority

4. **Enhance Deduplication Logging**:
   - Log an informational notice when a duplicate HIFLD feature with populated attributes is discarded in favor of an existing feature.

---

*Report prepared by Gemini 3.7 Flash (Thinking) — Google DeepMind — 2026-08-20 22:25 EDT*
