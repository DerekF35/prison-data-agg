import os

content = """| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 22:34 EDT |
| **Auditor Model** | Gemini Pro |
| **Requesting Model** | user |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | 89 / 100 |

## Executive Summary
* **CRITICAL:** The BOP entity matching logic still contains a collision flaw for intra-federal complexes. Because it uses a simple substring check (`b_core in h_core`), shorter names (like `USP Beaumont`) are overwritten by longer names (`USP Beaumont Camp`), causing the primary facility to lose its dedicated BOP URL.
* **HIGH:** `build_master_dataset.py` silently drops duplicate spatial features. If two features share a `FACILITYID` and both have valid coordinates, the first one is kept and the second is discarded without any `[WARN]` log.
* **HIGH:** The test suite (`test_deep_audit.py`) contains a False Pass for Test 11. It checks that `FCI Beaumont Low` has the correct URL but fails to check that `USP Beaumont` lost its URL entirely, falsely asserting "zero cross-overwriting."
* **MEDIUM:** The README falsely claims the entity matching is "Non-Colliding," which is incorrect given the intra-complex overwriting bug.
* **RESOLVED:** The previous false positive bug for `LOS` matching county jails has been fixed, and Irish/Scottish prefixes (`O'Brien`, `McDuffie`) are now correctly capitalized. Zero-population records are successfully preserved.

## 1. CODE QUALITY REVIEW — `build_master_dataset.py`
* **Silent Dropping of Coordinates:** In the HIFLD deduplication loop (lines 320-325), if `fac_id` already exists and BOTH the existing record and the new record have valid coordinates, the new record is silently discarded without logging a warning.
* **BOP Entity Matching Flaw:** The rule checking `b_core in h_core` (line 380) causes false negatives for primary federal institutions. For example, `b_core = BEAUMONT` matches `h_core = BEAUMONTCAMP`. Because of the loop structure, `USP Beaumont Camp` is matched to the primary `USP Beaumont` record, stealing its URL and leaving the actual `USP Beaumont` unmatched with a generic `https://www.bop.gov/locations/` URL. This affects Beaumont, Atlanta, Coleman, and Florence.
* **County Jail False Positives Fixed:** The `LOS` code matching `Los Angeles County Sybil Brand Institute` has been successfully fixed by enforcing a leading space in the substring check (`h_name.startswith(f"{bop_code} ")`) and checking the `is_fed` guard.
* **Sentinel Filters & clean_int():** The `clean_int()` function is robust. It properly preserves valid zero populations (`f == 0`) while scrubbing negative placeholders (`-1`, `-999`).
* **Coordinates:** `clean_coord()` correctly allows longitudes up to `+180.0` to account for Aleutian Islands crossing the antimeridian, and latitudes between 13.0 and 72.0.
* **Title Formatting:** `format_title()` properly capitalizes `Mc` and `O'` names using regex lambda replacements. It successfully formats `O'Brien`, `McDuffie`, and even `McDonald's`.

## 2. DATA INTEGRITY REVIEW — `output/us_correctional_facilities_master.csv`
* **Duplicates:** Found 6 distinct facilities sharing exact `(facility_name, city, state)` (e.g., Larned State Hospital, Garza County Jail) and 6 instances of duplicate coordinates across distinct facility IDs (e.g., RO Mid-Atlantic and RRM Baltimore). These are legitimate campus overlaps.
* **Data Completeness:** 5,805 records have `street_address`, `phone_number`, AND `website` populated.
* **Anomalies:** There are 8 facilities where `population > 3× design_capacity` (e.g., Woodman State Jail: pop 6478, cap 900), which are known upstream HIFLD anomalies.
* **Zero Population:** Exactly 625 zero-population records are successfully preserved.
* **Postal & FIPS Codes:** 100% of ZIP codes and FIPS codes preserve their leading zeroes (no 4-digit ZIPs exist).
* **Missing GPS:** 0 BOP-only records are missing GPS coordinates.

## 3. EXCEL WORKBOOK REVIEW — `output/us_correctional_facilities_master.xlsx`
* **Data Dictionary:** The Data Dictionary tab now explicitly maps the 20 Display Headers to the CSV snake_case fields.
* **Aggregations:** The State Summary tab perfectly matches the raw CSV ground truth (6,787 total facilities, 2,411,708 capacity, 2,069,547 population).
* **Data Types:** ZIP codes and FIPS codes are stored as text to preserve leading zeroes.

## 4. METHODOLOGY & DOCUMENTATION REVIEW — `README.md`
* **Disclosure:** The README accurately documents the zero-population preservation logic in `clean_int()` and the FIPS code corrections for Guam, Virgin Islands, and Pickens County, AL. It also specifies the deduplication of 10,738 raw features into 6,737.
* **False Claims:** The README claims "Type-Guarded & Non-Colliding BOP Entity Matching", which is false due to the substring collision bug that overwrites intra-federal complexes.

## 5. TEST SUITE REVIEW — `test_deep_audit.py` and `verify_dataset.py`
* **False Pass on Test 11:** Test 11 asserts "zero cross-overwriting" in intra-federal complexes by checking if `FCI Beaumont Low` has the correct URL. However, it fails to check `USP Beaumont`, which was falsely overwritten by `USP Beaumont Camp`. This is a massive blind spot.
* **Aleutian Longitude Check:** Test 4 checks that longitudes fall within the valid bounds but does not actively inject a dummy coordinate like `+172.0` to ensure `clean_coord()` processes it correctly.
* **Duplicate Warnings:** Test 13 prints the number of duplicate `(facility_name, city, state)` triplets but does not issue a `[WARN]` to standard out, it merely logs them as `[PASS] Accounted for...`.

## 6. FINAL SCORING

| Category | Max Points | Awarded | Justification |
|:---|:---:|:---:|:---|
| Data Completeness | 20 | 20 | 100% geocoded, zero populations preserved, leading zeroes preserved. |
| Data Accuracy | 20 | 18 | `Mc`/`O'` prefixes fixed, but intra-federal complex matching overrides primary URLs. |
| Code Quality & Robustness | 20 | 17 | Deduplication silently drops valid coords; regex `b_core in h_core` is a structural flaw. |
| Methodology Documentation | 20 | 18 | Zero-population and FIPS imputation documented, but falsely claims collision-free matching. |
| Test Suite Rigor | 20 | 16 | Test 11 yields a False Pass. Missing active bounds checking for Aleutian coordinates. |
| **Total** | **100** | **89** | |

## 7. RECOMMENDED FIXES
1. **CRITICAL:** Fix the BOP matching logic in `build_master_dataset.py`. Instead of checking `b_core in h_core`, ensure exact boundary matching or prevent `CAMP` from matching a non-camp BOP entry.
2. **HIGH:** Add a `print(f"[WARN] Silently dropping duplicate coordinates for {fac_id}")` to the deduplication block in `build_master_dataset.py`.
3. **HIGH:** Update `test_deep_audit.py` Test 11 to check `USP Beaumont` and `USP Atlanta` directly to prevent False Passes.
4. **MEDIUM:** Update the README to remove the claim of "Non-Colliding" matching until the bug is fixed.
"""

with open('audit/2026-08-20_2234_gemini-pro_adversarial-audit.md', 'w') as f:
    f.write(content)
