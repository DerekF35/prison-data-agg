# United States Correctional Facilities Master Database

A standardized, deduplicated, and verified national database and multi-format spreadsheets (CSV & Excel) of all **6,788 physical correctional facilities** in the United States, spanning federal, state, county, municipal, and private sectors across all 50 states, the District of Columbia, and 5 US territories.

---

## 📑 Deliverables & Formats

| Deliverable | File Path | Format / Details |
| :--- | :--- | :--- |
| **All-in-One Deliverables Archive** | [`output/prison_data_report.zip`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/prison_data_report.zip) | ZIP archive bundling master CSV, Excel workbook, PDF/Word reports, and JSON summary |
| **Master CSV Dataset** | [`output/us_correctional_facilities_master.csv`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/us_correctional_facilities_master.csv) | UTF-8 CSV, 6,788 rows, 20 standardized columns with preserved leading zeroes |
| **Master Excel Workbook** | [`output/us_correctional_facilities_master.xlsx`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/us_correctional_facilities_master.xlsx) | 4-tab workbook: *Master Directory*, *State Summary*, *Jurisdiction Summary*, *Data Dictionary* |
| **Methodology Report (PDF)** | [`output/US_Correctional_Facilities_Methodology_Report.pdf`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/US_Correctional_Facilities_Methodology_Report.pdf) | Print-ready PDF report detailing data provenance and cleaning algorithms |
| **Methodology Report (Word)** | [`output/US_Correctional_Facilities_Methodology_Report.docx`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/US_Correctional_Facilities_Methodology_Report.docx) | Fully styled Microsoft Word document for policy, research, and legal teams |
| **Audit Summary (JSON)** | [`output/dataset_summary.json`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/output/dataset_summary.json) | Programmatic audit metrics and breakdown stats |

---

## 📊 Summary Statistics

* **Total Unique Facilities**: 6,788
* **Geocoded Facilities (Mapped GPS)**: 6,788 (100.0%)
* **Facilities with Street Addresses**: 6,785 (100.0%)
* **Facilities with Telephone Numbers**: 6,244 (92.0%)
* **Total Rated Bed Capacity (Design)**: 2,411,708 beds
* **Total Reported Inmate Population**: 2,069,547 inmates
* **Jurisdictions Covered**: 55 (All 50 US States + District of Columbia + Puerto Rico, Guam, US Virgin Islands, and Northern Mariana Islands)

### Distribution by Jurisdiction
| Jurisdiction Level | Facility Count | Percentage |
| :--- | :---: | :---: |
| **County / Local Jails** | 3,960 | 58.3% |
| **State DOC Facilities** | 2,273 | 33.5% |
| **Federal (BOP & USMS)** | 308 | 4.5% |
| **Municipal / Local Lockups** | 184 | 2.7% |
| **Multi-Jurisdiction Facilities** | 36 | 0.5% |
| **Not Specified (Tribal / Contract / Unrecorded)** | 27 | 0.4% |
| **Total** | **6,788** | **100.0%** |

---

## 🔬 Data Provenance & Aggregation Methodology

### 1. Primary Data Sources
1. **Homeland Infrastructure Foundation-Level Data (HIFLD)**:
   * Programmatic query of the DHS National Critical Infrastructure Prison Points FeatureServer REST layer.
   * Baseline extract contained 10,738 raw feature geometries.
2. **DOJ Federal Bureau of Prisons (BOP)**:
   * Ingestion of the official BOP public institutional directory (`bop.gov/PublicInfo`).
   * Extracted 165 federal locations including operational prisons, regional offices (`RO`), residential reentry centers (`RRM`), training academies (`MSTC`), and headquarters (`HQ`).

---

### 2. Normalization & Deduplication Logic

1. **Multi-Part GIS Polygon Deduplication**:
   * Upstream HIFLD contains multiple polygon centroids per physical campus (e.g. separate boundary nodes for detention barracks, perimeter towers, and administrative wings).
   * Grouped and deduplicated strictly by `FACILITYID`, reducing 10,738 raw GIS feature records to 6,737 unique physical facilities (consolidating 4,001 secondary polygon nodes) while ensuring coordinate retention.
2. **Type-Guarded & Camp-Parity BOP Entity Matching**:
   * To prevent false positives across both county facilities and intra-federal complexes (e.g. Beaumont, Atlanta, Coleman), the pipeline enforces strict federal type guards, separates administrative entities (RRM, Regional Offices, FCC complexes) into standalone records, and enforces camp-to-camp matching parity so satellite camps do not steal parent institution URLs (e.g. *USP Beaumont* correctly receives `/institutions/bmp/` while *FCI Beaumont Low* receives `/institutions/bml/`).
3. **Preservation of Legitimate Zero Counts**:
   * `clean_int()` preserves valid `0` counts for unoccupied, newly constructed, or temporary intake facilities (625 records), while scrubbing negative placeholder sentinels (`-999`, `-1`, `99999`) to clean nulls.
4. **Typography, Acronyms & Scottish/Irish Surnames**:
   * Addresses and names are converted to Title Case while strictly preserving uppercase acronyms (`USP`, `FCI`, `ADX`, `MDC`, `FDC`, `FMC`, `BOP`, `DOC`, `SCI`, `ASPC`, `CCFW`) and Scottish/Irish prefixes (`McDuffie`, `McCreary`, `McKean`, `O'Brien`, `O'Farrell`, `Chain O'Lakes`).
5. **Postal & FIPS Integrity**:
   * Standardized 5-digit ZIP codes with zero-padding for East Coast states (e.g., `01862`, `00921`).
   * Imputed 100% complete County and 5-digit FIPS codes for standalone federal offices and territories (Guam `66010`, US Virgin Islands `78010`, Saipan `69110`), and corrected upstream FIPS typos (Pickens County, AL `10107` $\rightarrow$ `01107`).

---

## ⚠️ Known Data Limitations & Upstream Anomalies

Researchers, auditors, and policy analysts should take note of the following known characteristics and upstream data anomalies present in primary government source records:

1. **Point-in-Time Census Snapshots**:
   * Reported inmate populations reflect point-in-time census figures provided during individual state and federal reporting cycles rather than live daily headcounts.
2. **Upstream Population vs. Capacity Outliers ($>3\times$)**:
   * There are 8 specific county and state facilities where reported population exceeds $3\times$ rated design capacity in the upstream DHS HIFLD layer:
     * *Woodman State Jail* (Gatesville, TX): Reported population 6,478 vs design capacity 900 ($7.2\times$).
     * *Burke County Jail* (Morganton, NC): Reported population 262 vs design capacity 66 ($4.0\times$).
     * *Fulton County Jail* (Rochester, IN): Reported population 133 vs design capacity 35 ($3.8\times$).
     * *Van Buren County Jail* (Spencer, TN): Reported population 50 vs design capacity 13 ($3.8\times$).
     * *Gallia County Jail* (Gallipolis, OH): Reported population 74 vs design capacity 22 ($3.4\times$).
     * *Southwest Virginia Regional Jail - Tazewell* (Tazewell, VA): Reported population 264 vs design capacity 80 ($3.3\times$).
     * *Tuscola County Jail* (Caro, MI): Reported population 242 vs design capacity 80 ($3.0\times$).
     * *Page County Jail* (Luray, VA): Reported population 79 vs design capacity 26 ($3.0\times$).
   * These represent verified upstream HIFLD data artifacts and are preserved as recorded by the source reporting agency.
3. **Campus Co-Location of Distinct Agencies**:
   * A small number of municipal and state facilities share identical street addresses or GPS coordinates due to co-located physical campuses (e.g., county sheriff headquarters and municipal jail in the same civic center, or psychiatric hospital and detention unit on one state hospital campus). These are preserved as separate records with unique primary IDs.

---

## 📖 Standardized Data Dictionary (20 Master Fields)

| Display Header | CSV Field Name (snake_case) | Type | Nullable | Description |
| :--- | :--- | :---: | :---: | :--- |
| **Facility ID** | `facility_id` | String | No | Unique alphanumeric primary key (HIFLD ID or BOP Code). |
| **Facility Name** | `facility_name` | String | No | Official facility title case name with preserved acronyms. |
| **Jurisdiction** | `jurisdiction` | String | No | Level of authority (`Federal`, `State`, `County / Local`, `Municipal / Local`, `Private`, `Multi-Jurisdiction`, `Not Specified`). |
| **Facility Classification** | `facility_type` | String | No | Operational classification (`State / Federal Prison`, `County / Local Jail`, `Juvenile Detention`, `Community Corrections`, `Medical/Psych`). |
| **Security Level** | `security_level` | String | No | Rating (`Maximum`, `Close`, `Medium`, `Minimum`, `Juvenile`, `Multi-Level`, `Administrative`, `Not Specified`). |
| **Operational Status** | `operational_status` | String | No | Status (`Open`, `Closed`, `Not Available`). |
| **Street Address** | `street_address` | String | Yes | Physical street address. |
| **City** | `city` | String | Yes | Physical municipality. |
| **State** | `state` | String | No | Two-letter US postal state/territory code (55 covered). |
| **ZIP Code** | `zip_code` | String | Yes | 5-digit or 9-digit postal ZIP code (leading zeroes intact). |
| **County** | `county` | String | Yes | County, parish, or borough name. |
| **County FIPS** | `county_fips` | String | Yes | 5-digit FIPS county code (leading zeroes intact). |
| **Phone Number** | `phone_number` | String | Yes | Formatted `(XXX) XXX-XXXX` contact telephone. |
| **Website** | `website` | String | Yes | Official facility or governing agency URL. |
| **Latitude** | `latitude` | Float | No | WGS84 Decimal Degrees Latitude (North). |
| **Longitude** | `longitude` | Float | No | WGS84 Decimal Degrees Longitude (West / East). |
| **Design Capacity** | `design_capacity` | Integer | Yes | Rated / design bed capacity. |
| **Population** | `population` | Integer | Yes | Reported inmate population count. |
| **Gender** | `gender` | String | Yes | Housing designation (`Male`, `Female`, `Co-ed`, `Not Specified`). |
| **Data Source** | `data_source` | String | No | Primary origin agency of record. |

---

## 🧪 Automated Verification & Audit Results

The dataset is validated by an automated adversarial test suite ([`test_deep_audit.py`](file:///home/derekf35/Development/PROJECTS/prison-data-agg/test_deep_audit.py)):

```text
===========================================================================
RUNNING ADVERSARIAL FORENSIC DEEP-AUDIT TEST SUITE
===========================================================================
[PASS] CSV deliverable verified (1,885,857 bytes)
[PASS] Excel deliverable verified (1,037,802 bytes)
[PASS] JSON deliverable verified (1,980 bytes)
[PASS] Word deliverable verified (40,845 bytes)
[PASS] PDF deliverable verified (101,230 bytes)
[PASS] ZIP deliverable verified (1,549,950 bytes)

[INFO] Total Records Loaded: 6,788
[PASS] Test 1: 100.0% Unique Facility IDs (0 duplicates)
[PASS] Test 2: Mandatory string fields (Name, State, Jurisdiction, Status) 100% complete
[PASS] Test 3: Exact 55 valid US jurisdictions verified (All 50 states, DC, PR, GU, VI, MP)
[PASS] Test 4: 100.0% Valid WGS84 Coordinates strictly within geographic bounds
[PASS] Test 5: 100.0% Standard 5-digit ZIP codes with preserved leading zeroes
[PASS] Test 6: 100.0% County & 5-digit FIPS code completeness across all 6,788 records
[PASS] Test 7: 6,244 phone numbers strictly match formatted canonical regex
[PASS] Test 8: Capacities/populations stored as discrete integers; exactly 625 zero-population records preserved
[PASS] Test 9: Scottish/Irish name patterns (McDuffie, McCreary, McKean, O'Brien, O'Lakes) correctly capitalized
[PASS] Test 10: BOP entity matching correctly guarded against county jail false positives
[PASS] Test 11: Intra-federal complexes (Beaumont, Atlanta, Miami) and RRM offices strictly mapped with zero cross-overwriting
[PASS] Test 12: All 51 standalone BOP records possess 100.0% valid GPS coordinates
[PASS] Test 13: Accounted for 6 campus co-located records and 6 co-located agency offices within strict <=10 upper bounds
[PASS] Test 14: Exact 1-to-1 parity between CSV and Excel Master Directory (6,788 rows, 20 columns)
[PASS] Test 15: Excel Summary Tabs match ground truth sums perfectly (6,788 facilities, 2,411,708 capacity, 2,069,547 population)
[PASS] Test 16: Excel Data Dictionary features full 3-column Display Header to CSV snake_case key mapping
[PASS] Test 17: Master ZIP archive verified containing all 5 primary deliverables (1,549,950 bytes)

===========================================================================
ALL 17 ADVERSARIAL FORENSIC AUDIT TESTS PASSED WITH ZERO DEFECTS!
===========================================================================
```

---

## ⚙️ Reproduction Instructions

Follow these steps to reproduce the dataset, documentation, and the `prison_data_report.zip` deliverable archive from scratch:

```bash
# 1. Activate Python virtual environment
source .venv/bin/activate

# 2. Run master ETL pipeline (fetches, cleans, deduplicates, and generates CSV & XLSX)
python3 build_master_dataset.py

# 3. Generate Word/PDF methodology reports and automatically build output/prison_data_report.zip
python3 generate_documents.py

# 4. Run comprehensive adversarial test suite
python3 test_deep_audit.py
```

### Manual ZIP Archive Creation
If you wish to package or re-bundle `output/prison_data_report.zip` manually via shell:

```bash
cd output
zip -r prison_data_report.zip \
  us_correctional_facilities_master.csv \
  us_correctional_facilities_master.xlsx \
  US_Correctional_Facilities_Methodology_Report.pdf \
  US_Correctional_Facilities_Methodology_Report.docx \
  dataset_summary.json
cd ..
```
