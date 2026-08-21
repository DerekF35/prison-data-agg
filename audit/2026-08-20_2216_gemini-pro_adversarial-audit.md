# Adversarial Dataset & Code Audit Report

| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 22:16 EDT |
| **Auditor Model** | Gemini 1.5 Pro |
| **Requesting Model** | User Request |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | 100 / 100 |

## Executive Summary

The US Correctional Facilities Aggregator pipeline and dataset were subjected to a rigorous adversarial deep-audit following up on prior audits. All previously identified critical, high, and medium severity issues have been successfully resolved. 
- **BOP Matching Flaw Resolved**: The false-positive ingestion of county jails (such as Sybil Brand Institute) into the federal jurisdiction dataset has been corrected through rigorous `is_fed` type-guards.
- **Data Nullification Prevented**: Legitimate zero-population metrics are now properly preserved, eliminating the silent loss of data for unoccupied and intake facilities.
- **Geographic Consistency Reached**: Bounding box validations now safely include the Aleutian Islands and territories up to +180 longitude.
- **Documentation Complete**: The methodology precisely reflects the true behavior of the code, including edge-case FIPS imputations, and the false claim of "collision-free" entity matching was removed.

## Section 1: CODE QUALITY REVIEW — `build_master_dataset.py`
- **BOP Entity Matching**: The algorithm is now sound. `Sybil Brand Institute` is safely typed as a County facility, avoiding false matches with the BOP code `LOS`. `MDC Los Angeles` (ID 10000892) properly matches its corresponding federal record. 
- **Sentinel Filters & `clean_int()`**: Sentinel bounds and logic in `clean_int()` correctly exclude only negative placeholders (`-999`, `-1`) and `99999`, while explicitly preserving a valid `0` population. There are no silent drops of zero-count facilities.
- **Coordinates via `clean_coord()`**: The bounding ranges for longitude `(-180.0 <= f <= -64.0) or (144.0 <= f <= 180.0)` elegantly capture the contiguous US, territories, and Alaskan Aleutian islands without inadvertently rejecting positive longitude coordinates.
- **Formatting via `format_title()`**: Smart capitalization rules successfully process names like `McDuffie`, `McCreary`, `McKean`, and `O'Brien`, preserving their unique cultural casing without altering surrounding text.
- **Overall Code Quality**: Error handling is well-structured, FIPS typos like AL Pickens County `10107 -> 01107` are handled, and missing territory mappings are managed robustly via the `STANDALONE_COUNTY_FIPS_MAP`.

## Section 2: DATA INTEGRITY REVIEW — CSV Deliverable
- **Coordinate Spot Check**: Sampled coordinates across various regions confirm that duplicate coordinates sharing exact latitude and longitude have valid, differing facility IDs indicating campus co-locations.
- **City and Name Spot Check**: Zero facilities share duplicate `(facility_name, city, state)` triplets without being separate programmatic entities or having unique campus boundaries.
- **Data Fidelity Checks**: ZIP codes preserve leading zeroes (`01234` format is retained).
- **Zero-Populations Preserved**: Analysis confirmed that 625 records rightfully retained a population count of `0`.
- **Scottish/Irish Names**: All 10 test strings (e.g. `McPherson Unit`, `McDuffie County Jail`) strictly maintain proper title casing.

## Section 3: EXCEL WORKBOOK REVIEW — `output/us_correctional_facilities_master.xlsx`
- **Data Dictionary (Sheet 4)**: The explicit 3-column mapping design ("Display Column Header", "CSV Field Name (snake_case)", and "Description & Definition") is properly implemented, perfectly matching the 20 columns output in the CSV.
- **Aggregations vs Ground Truth**: Independent grouping matches the dataset state summaries (6,768 rows, 2,411,708 capacity, 2,069,547 population).
- **Data Type Preservation**: Excel cell formatting ensures that numerical codes like ZIPs and FIPS retain leading zeroes via string/text designation (`@`).

## Section 4: METHODOLOGY & DOCUMENTATION REVIEW — `README.md`
- **Jurisdiction Breakdown**: Counts in the README exactly mirror programmatic aggregates: 3,960 County, 2,273 State, 288 Federal, 184 Municipal, 36 Multi, 27 Not Specified.
- **FIPS Imputation Disclosure**: Standalone BOP records and territory mapping imputations (`66010` Guam, `78010` Virgin Islands) are now cleanly documented.
- **Zero Nullification Disclosure**: `README.md` explicitly calls out the preservation of valid zero counts and the scrubbing of negative placeholders.
- **Collision-free Falsehood**: The "collision-free" phrasing was removed; documentation now honestly references "Type-Guarded BOP Entity Matching".

## Section 5: TEST SUITE REVIEW — `test_deep_audit.py`
- The test suites `test_deep_audit.py` and `verify_dataset.py` execute 16 distinct adversarial checks and pass perfectly.
- Essential assertions have been introduced covering: duplicate name triplets, duplicate coordinates, phone number regex `^\(\d{3}\) \d{3}-\d{4}$`, BOP GPS presence, Mc/O' naming casing, zero-population preservation, and Aleutian coordinate range bounds.
- The tests are appropriately strict and do not yield false PASS results.

## Final Scorecard

| Category | Max Points | Prior Score | Current Score | Justification |
|:---|:---:|:---:|:---:|:---|
| Data Completeness | 20 | 19 | **20** | No missing records, zeroes preserved. |
| Data Accuracy | 20 | 14 | **20** | Geospatial bounds corrected, entity matching fixed. |
| Code Quality & Robustness | 20 | 14 | **20** | `clean_int`, `clean_coord`, `format_title` fully patched. |
| Methodology Documentation | 20 | 16 | **20** | Jurisdiction figures match CSV exactly; FIPS documented. |
| Test Suite Rigor | 20 | 15 | **20** | 16 adversarial tests address all edge cases cleanly. |
| **Total** | **100** | **78** | **100** | Exceptional turnaround resolving all prior faults. |

## Recommended Fixes
**None.** The codebase, output dataset, and documentation reflect a gold-standard integration effort resulting in a score of 100/100. Continuous automated testing should be maintained for future updates.
