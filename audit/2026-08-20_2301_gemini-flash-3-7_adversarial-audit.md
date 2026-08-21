# Adversarial Dataset & Code Audit Report

| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 23:01 EDT |
| **Auditor Model** | Gemini 3.7 Flash (Thinking) — Google DeepMind |
| **Requesting Model** | User / Parent Subagent Dispatch |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, Word/PDF reports, ZIP archive, README, test suite |
| **Final Score** | **100 / 100** |

---

## Executive Summary

An exhaustive, forensic code and data quality audit was conducted on the **US Correctional Facilities Aggregator** repository at `/home/derekf35/Development/PROJECTS/prison-data-agg`. The audit evaluated all pipeline scripts (`build_master_dataset.py`, `generate_documents.py`), test suites (`test_deep_audit.py`, `verify_dataset.py`), documentation (`README.md`, Word, and PDF technical reports), and data deliverables (`output/us_correctional_facilities_master.csv`, `output/us_correctional_facilities_master.xlsx`, `output/prison_data_report.zip`).

### Key Audit Findings:
1. **Flawless Intra-Federal Entity Resolution & Protection**: The BOP entity resolution algorithm demonstrates remarkable precision. Federal type-guards prevent non-federal municipal and county facilities (e.g., *Sybil Brand Institute* in LA) from matching BOP codes (`LOS`). Administrative command offices (`RRM`, `RO`, `CO`, `FCC`, `MSTC`) are segregated as 51 standalone records, preventing them from overwriting physical prisons. Camp-to-camp matching parity ensures satellite camps never hijack parent institution URLs (e.g., *USP Beaumont* receives `/institutions/bmp/`, *FCI Beaumont Low* receives `/institutions/bml/`, and *USP Beaumont Camp* receives fallback `/locations/`).
2. **100.0% Geospatial, Postal, and Administrative FIPS Integrity**: All 6,788 records possess valid WGS84 coordinates strictly bounded within the US geographic domain (including Aleutian Islands and Pacific territories $+144^\circ$ to $+180^\circ$). All ZIP codes and County FIPS codes are 100.0% populated with 5-digit strings preserving leading zeroes.
3. **Discrete Integer Serialization & Zero-Population Preservation**: Legitimate zero counts representing unoccupied holding annexes or new facilities (exactly 625 records) are preserved, while negative placeholder sentinels (`-999`, `-1`, `99999`) are scrubbed to null. Capacities and populations are serialized as clean nullable integers without floating `.0` suffixes.
4. **Complete Deliverable Parity & Packaging Synchronicity**: Exact 1-to-1 parity is verified across the Master CSV, the 4-sheet Excel workbook, the Word report, the PDF report, and `output/prison_data_report.zip`. Summary tables across documentation match row-for-row and sum-for-sum against programmatic CSV aggregations.
5. **Comprehensive 17-Point Adversarial Test Suite**: All 17 adversarial assertions in `test_deep_audit.py` and all checks in `verify_dataset.py` execute cleanly with zero defects.

---

## Section 1: Code Quality Review — `build_master_dataset.py`

### 1.1 Ingestion & Pipeline Robustness (`build_master_dataset.py:39–105`)
- **Caching & Pagination**: `fetch_arcgis_features()` safely uses file caching (>100KB) and robust pagination (`batch_size=2000`) with network timeouts (15s on count, 30s on queries). Live BOP fetch handles REST JSON decoding gracefully.
- **Silent Dropping Prevention**: Only records missing `FACILITYID` are skipped, with an explicit `[WARN]` logged (`build_master_dataset.py:316`).

### 1.2 Entity Matching & Resolution Architecture (`build_master_dataset.py:337–433`)
- **Administrative Office Segregation**: Lines 350–352 explicitly isolate `RRM`, `RO`, `CO`, `FCC`, `TRN`, and `STAFF TRAINING ACADEMY` entities into `standalone_bop_records`, eliminating previous collision vectors where administrative field offices overwrote physical prisons in the same city.
- **Federal Type-Guard (`is_fed`)**: Lines 366–369 and 391–394 enforce strict type-guarding, ensuring county jails and state prisons never match BOP codes or URLs.
- **Camp-to-Camp Parity Matching**: Lines 380 and 402 enforce `b_is_camp == h_is_camp`, guaranteeing satellite camps and parent institutions map to their respective designated URLs.
- **Priority Cascade**: Priority 1 matches exact names or exact BOP codes, while Priority 2 matches stripped core names with camp parity.

### 1.3 Data Sanitization Functions
- **`clean_int()` (`build_master_dataset.py:239–248`)**:
  ```python
  def clean_int(val):
      if val is None or pd.isna(val):
          return None
      try:
          f = float(val)
          if f in SENTINEL_INTS or f < 0:
              return None
          return int(round(f))
      except (ValueError, TypeError):
          return None
  ```
  Correctly preserves valid `0` counts while scrubbing `SENTINEL_INTS` (`{-999, -1, 99999}`) and negative values.
- **`clean_coord()` (`build_master_dataset.py:250–264`)**: Correctly admits latitudes `[13.0, 72.0]` and longitudes `[-180.0, -64.0]` as well as Pacific Territories / Aleutian Islands crossing the antimeridian `[144.0, 180.0]`.
- **`clean_zip()` & `clean_fips()` (`build_master_dataset.py:196–221`)**: Preserves leading zeroes for East Coast states and territories, and corrects known upstream typos (e.g., Pickens County AL `10107` $\rightarrow$ `01107`).
- **`format_title()` (`build_master_dataset.py:266–306`)**: Handles acronyms (`USP`, `FCI`, `ADX`, `CCFW`, etc.), conjunctions (`and`, `of`, `for`), possessives (`Men's`, `Women's`), and Scottish/Irish prefixes (`McDuffie`, `McCreary`, `McKean`, `O'Brien`, `Chain O'Lakes`, `O'Farrell`).

### 1.4 Polygon Deduplication & Centroid Consolidation (`build_master_dataset.py:308–336`)
- Consolidates 4,000 multi-part GIS polygon features sharing identical `FACILITYID`s into primary centroid representations while ensuring valid GPS coordinates are preserved.

---

## Section 2: Data Integrity Review — `output/us_correctional_facilities_master.csv`

### 2.1 Regional Sampling & Spot-Checks
A stratified random sample of 20 records per US geographic region was inspected across all 20 standardized attributes:
- **Northeast (655 facilities)**: 100% 5-digit ZIPs with leading zeroes (e.g., `03833` NH, `07456` NJ, `01949` MA); 100% valid county FIPS.
- **Midwest (1,754 facilities)**: Clean title casing (e.g., *Monday Community Correctional Institution*, *Lebanon Correctional Institution Camp*); 100% coordinate compliance.
- **South (3,085 facilities)**: Complete classification across state prisons, county jails, and youth development campuses; leading zero preservation on AL, AR, and FL FIPS.
- **West (1,247 facilities)**: Accurate geocoding across CA, NV, MT, OR, WY, AK, and HI; correct classification for conservation camps.
- **Territories (47 facilities)**: 100% complete geocoding and FIPS imputation for Puerto Rico (`009xx` ZIPs, `72xxx` FIPS), Guam (`66010` FIPS), US Virgin Islands (`78010` FIPS), and Northern Mariana Islands / Saipan (`69110` FIPS).

### 2.2 Forensic Field Population Audit
| Attribute | Populated Count | Completeness % | Audit Assessment |
|:---|:---:|:---:|:---|
| `facility_id` | 6,788 | 100.0% | Unique alphanumeric keys; 0 duplicates |
| `facility_name` | 6,788 | 100.0% | Standardized title case with preserved acronyms |
| `jurisdiction` | 6,788 | 100.0% | Standardized 6-tier authority classification |
| `facility_type` | 6,788 | 100.0% | Standardized operational classification |
| `security_level` | 6,788 | 100.0% | 8 standardized security ratings |
| `operational_status` | 6,788 | 100.0% | Standardized (`Open`, `Closed`, `Not Available`) |
| `street_address` | 6,785 | 99.96% | 3 missing are confirmed upstream empty values |
| `city` | 6,788 | 100.0% | Complete physical municipality data |
| `state` | 6,788 | 100.0% | 55 valid US jurisdictions (50 states + DC + 4 territories) |
| `zip_code` | 6,788 | 100.0% | 100% standard 5-digit strings (279 with leading 0) |
| `county` | 6,788 | 100.0% | 100% county / parish / borough names populated |
| `county_fips` | 6,788 | 100.0% | 100% 5-digit FIPS strings (972 with leading 0) |
| `phone_number` | 6,244 | 91.99% | Clean canonical format `(XXX) XXX-XXXX`; 0 sentinels |
| `website` | 6,016 | 88.63% | Valid HTTP/HTTPS URLs; verified BOP institution links |
| `latitude` | 6,788 | 100.0% | WGS84 Decimal Degrees in range [13.448201, 71.291828] |
| `longitude` | 6,788 | 100.0% | WGS84 Decimal Degrees in range [-166.541934, 145.707344] |
| `design_capacity` | 5,071 | 74.71% | Nullable Int64; total 2,411,708 rated beds |
| `population` | 4,813 | 70.90% | Nullable Int64; exactly 625 zero-population preserved |
| `gender` | 6,788 | 100.0% | Standardized (`Male`, `Female`, `Co-ed`, `Not Specified`) |
| `data_source` | 6,788 | 100.0% | Provenance origin agency (HIFLD vs BOP) |

- **Tri-Populated Completeness**: Exactly **5,806** facilities have all three of `street_address`, `phone_number`, AND `website` populated.
- **Upstream Overcrowded Outliers ($>3\times$)**: Exactly 8 records exhibit population exceeding $3\times$ capacity (e.g., *Woodman State Jail* TX, *Burke County Jail* NC, *Fulton County Jail* IN). Confirmed as authentic upstream DHS HIFLD data artifacts.
- **Duplicate Name / Coordinate Triplets**:
  - Exactly 3 pairs (6 records) share `(facility_name, city, state)`: *Garza County Jail* (TX), *Jessup Correctional Institution* (MD), and *Larned State Hospital* (KS). Verified upstream distinct facility IDs.
  - Exactly 3 pairs (6 records) share exact `(latitude, longitude)`: co-located BOP offices in Grand Prairie, TX (`BOP-GRA` / `BOP-SCR`), Annapolis Junction, MD (`BOP-MXR` / `BOP-CBR`), and Yazoo City, MS (`BOP-YAX` / `BOP-YAM`).

---

## Section 3: Excel Workbook Review — `output/us_correctional_facilities_master.xlsx`

### 3.1 Sheet Architecture & Layout
1. **Sheet 1 (`Master Facilities Directory`)**:
   - Contains 6,788 data rows + 1 header row across 20 standardized columns.
   - Text formatting (`@`) applied to ID, Address, City, State, ZIP, County, County FIPS, Phone, Website, and Status.
   - Number formatting (`#,##0`) applied to Design Capacity and Population; coordinate formatting (`0.000000`) applied to Latitude and Longitude.
   - Professional styling with dark navy headers (`#1F4E78`), white bold text, alternating zebra fills (`#F2F5F9`), and frozen header pane (`A2`).
2. **Sheet 2 (`State Summary`)**:
   - Aggregates all 55 jurisdictions sorted by facility count.
   - Cross-validated against independent pandas groupby aggregations:
     - Total Facilities: **6,788**
     - Total Reported Capacity: **2,411,708**
     - Total Reported Population: **2,069,547**
3. **Sheet 3 (`Jurisdiction Summary`)**:
   - Cross-tabulates jurisdiction tiers by facility classifications with total capacities, populations, and geocoded counts.
4. **Sheet 4 (`Data Dictionary`)**:
   - Implements full 3-column schema: `Display Column Header`, `CSV Field Name (snake_case)`, and `Description & Definition`.
   - 100% aligned with Sheet 1 headers and CSV snake_case keys.

---

## Section 4: Methodology & Documentation Review

### 4.1 Synchronicity & Content Completeness
- **Synchronicity**: `README.md`, `US_Correctional_Facilities_Methodology_Report.docx`, `US_Correctional_Facilities_Methodology_Report.pdf`, and `dataset_summary.json` reflect identical statistics (6,788 facilities, 2,411,708 capacity, 2,069,547 population, 55 jurisdictions).
- **Dedicated Limitations Disclosures**: The dedicated section "Known Data Limitations & Upstream Anomalies" across README, Word, and PDF reports explicitly details:
  - Point-in-time census snapshot nature of population figures.
  - The 8 upstream population vs. capacity outliers ($>3\times$).
  - Campus co-location of distinct agencies sharing coordinates/addresses.
- **Methodology Disclosures**:
  - Consolidation of 4,000 multi-part polygon features.
  - Type-guarded and camp-parity BOP entity resolution.
  - Zero-population retention (625 records) and sentinel scrubbing.
  - Complete FIPS imputation for territories and standalone BOP facilities.

---

## Section 5: Test Suite Review — `test_deep_audit.py` & `verify_dataset.py`

### 5.1 Adversarial Test Rigor
`test_deep_audit.py` executes 17 comprehensive, adversarial assertions:
- **Test 1**: 100.0% Unique Primary IDs (`facility_id`).
- **Test 2**: Mandatory string fields (Name, State, Jurisdiction, Status) 100% complete.
- **Test 3**: Exact 55 valid US jurisdictions verified (All 50 states, DC, PR, GU, VI, MP).
- **Test 4**: 100.0% Valid WGS84 Coordinates strictly within geographic bounds (including Aleutian range $+144^\circ$ to $+180^\circ$).
- **Test 5**: 100.0% Standard 5-digit ZIP codes with preserved leading zeroes.
- **Test 6**: 100.0% County & 5-digit FIPS code completeness across all 6,788 records.
- **Test 7**: Canonical phone number regex conformance (`^\(\d{3}\) \d{3}-\d{4}( Ext \d+)?$`) with zero sentinels.
- **Test 8**: Discrete integer formatting; exactly 625 zero-population records preserved.
- **Test 9**: Scottish/Irish name patterns (`McDuffie`, `McCreary`, `McKean`, `O'Brien`, `Chain O'Lakes`) correctly capitalized.
- **Test 10**: BOP entity matching protected against county jail false positives (e.g., *Sybil Brand* in LA).
- **Test 11**: Intra-federal complex accuracy (*Beaumont*, *Atlanta*, *Miami*, *Coleman*, *Florence*, *Yazoo*) and RRM offices strictly mapped with zero cross-overwriting.
- **Test 12**: 100.0% of standalone BOP records possess valid GPS coordinates.
- **Test 13**: Legitimate campus co-located facility names and coordinates validated within strict upper bounds ($\le 10$).
- **Test 14**: Exact 1-to-1 parity between CSV and Excel Master Directory (6,788 rows, 20 columns).
- **Test 15**: Excel Summary Tabs match ground truth sums perfectly (6,788 facilities, 2,411,708 capacity, 2,069,547 population).
- **Test 16**: Excel Data Dictionary features full 3-column Display Header to CSV snake_case key mapping.
- **Test 17**: Master ZIP archive (`prison_data_report.zip`) file integrity and internal file validation.

Both `test_deep_audit.py` and `verify_dataset.py` execute with 0 defects and 100% pass rates.

---

## Final Scorecard

| Category | Max Points | Prior Score | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| **Data Completeness** | 20 | 19 | **20** | Full coverage of 6,788 facilities across 55 jurisdictions; 100% geocoded; 100% FIPS & ZIP completeness; 51 standalone BOP offices included. |
| **Data Accuracy** | 20 | 14 | **20** | Flawless intra-federal entity resolution; strict camp-parity; Scottish/Irish capitalization; valid zero counts preserved; known outliers documented. |
| **Code Quality & Robustness** | 20 | 14 | **20** | Resilient ingestion, clean sentinel filters, modular sanitization functions, nullable integer typing, error-free multi-sheet workbook generation. |
| **Methodology Documentation** | 20 | 16 | **20** | Full 1-to-1 synchronicity across README, Word, PDF, Excel, and JSON; exhaustive limitations section; 3-column data dictionary. |
| **Test Suite Rigor** | 20 | 15 | **20** | 17 non-tautological adversarial assertions validating entire entity classes, bounding boxes, regex patterns, and mathematical sums. |
| **Total** | **100** | **78** | **100** | **Grade: A+ (Production & Publication Ready)** |

---

## Maintenance & Operational Observations

1. **Periodic BOP API Ingestion Refresh (Low Priority)**:
   - When the BOP public directory updates quarterly, running `python3 build_master_dataset.py` automatically pulls new facility additions and refreshes contact metadata.
2. **Census Re-benchmarking (Low Priority)**:
   - When the next decennial or BJS Census of State and Federal Adult Correctional Facilities is released, capacity and population snapshots can be updated via the existing pipeline hooks.
