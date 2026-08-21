# Adversarial Audit Report — US Correctional Facilities Aggregator

| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 22:00 EDT (UTC-4) |
| **Auditor Model** | Claude Sonnet 4.6 (Thinking) — Anthropic |
| **Requesting Model** | Claude Sonnet 4.6 (Thinking) — Antigravity (user-initiated) |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | **74 / 100** |

---

## Executive Summary

1. **CONFIRMED CRITICAL BOP False Positive (Code `LOS`):** The entity-matching Rule 1 (`f" {bop_code} " in f" {h_name} "`) fires against `LOS ANGELES COUNTY SYBIL BRAND INSTITUTE FOR WOMEN` (HIFLD ID `10000894`) *before* it ever reaches the correct target `MDC LOS ANGELES` (`10000892`). This corrupts the county jail record with BOP phone `(213) 485-0439` and BOP URL `https://www.bop.gov/locations/institutions/los/`, while the real federal MDC Los Angeles receives only the generic fallback URL (`https://www.bop.gov/locations/`). The bug exists in the current code and is **reproducible by inspection of dict iteration order**.

2. **`Mc` Prefix Casing Unfixed Across 76 Facilities:** `format_title()` uses `.capitalize()` on the whole word, rendering `McDuffie → Mcduffie`, `McCreary → Mccreary`, `McKean → Mckean`, etc. 76 facility names in the CSV are affected. The prior audit flagged this; it remains unresolved.

3. **`clean_int(f <= 0)` Still Silently Nullifies Valid Zero Values:** The condition `f <= 0` treats `population = 0` or `design_capacity = 0` as a sentinel and returns `None`. Any facility with a legitimately reported population of zero is silently dropped. No warning is logged. Not fixed and not disclosed in the README.

4. **README Jurisdictional Table is Factually Wrong:** The README states `Private / Contract: 27 facilities`. The actual CSV has **zero** records with `jurisdiction = "Private"`. Those 27 records carry `jurisdiction = "Not Specified"`. The README's Federal/State/County counts are also wrong (288/2,273/3,960 actual vs. 253/2,347/3,924 claimed).

5. **Test Suite Lacks All Seven Adversarial Tests from Prior Audit:** Duplicate name+city+state triplets, duplicate coordinate pairs, BOP-source GPS completeness, `O'`/`Mc` casing, phone regex conformance, zero-population preservation, and Aleutian longitude validity are all entirely absent.

---

## Section 1 — Code Quality Review: `build_master_dataset.py`

### 1.1 BOP Entity Matching — Confirmed False Positive

**Rule 1 (Line 318):**
```python
if bop_code and (f" {bop_code} " in f" {h_name} " or h_name.startswith(f"{bop_code} ")):
```

**Status: Bug confirmed and active.** The prior audit identified short 3-letter BOP codes as a false-positive risk. The current fix uses word-boundary spacing which prevents `LOS` from matching inside words like `CLOSE`, but does **not** prevent it from matching `LOS ANGELES COUNTY SYBIL BRAND INSTITUTE FOR WOMEN` — the facility name starts with `LOS`.

Traced execution (Python 3.7+ dict insertion order):
- BOP iterates HIFLD dict for CA facilities
- Facility `10000894` (`LOS ANGELES COUNTY SYBIL BRAND INSTITUTE FOR WOMEN`, TYPE=COUNTY) appears **before** `10000892` (`MDC LOS ANGELES`, TYPE=FEDERAL) in the dict
- Rule 1 fires: `" LOS " in " LOS ANGELES COUNTY SYBIL BRAND INSTITUTE FOR WOMEN "` → `True`
- Loop breaks; `10000894` (a county jail) receives BOP LOS's phone and website
- **Confirmed in CSV:** `10000894` has `phone_number = (213) 485-0439` and `website = https://www.bop.gov/locations/institutions/los/`
- **Confirmed in CSV:** `10000892` (MDC Los Angeles) has only `website = https://www.bop.gov/locations/` (generic fallback — not the specific BOP URL)

**Additional Rule 1 false-positive risk found:** BOP code `FOR` (Arkansas) matches two non-federal facilities: `TUCKER RE-ENTRY FOR WOMEN` (STATE) and `MANSFIELD JUVENILE TREATMENT CENTER & CENTER FOR GIRLS` (STATE) via `" FOR "` substring.

**Fix:** Add `h_type == "FEDERAL"` guard to Rule 1:
```python
if bop_code and h_type == "FEDERAL" and (f" {bop_code} " in f" {h_name} " or h_name.startswith(f"{bop_code} ")):
```

### 1.2 `clean_int()` — Zero Value Nullification (Line 218)

```python
if f <= 0 or f == 9999 or f == 99999 or f == -999 or f == -1:
    return None
```

**Status: Unfixed.** `f <= 0` includes `f == 0`. Facilities with legitimately zero population (newly built, temporarily closed, etc.) are silently nullified. No warning is emitted. Not disclosed in README.

The CSV shows zero records with `population = "0"` or `design_capacity = "0"`, confirming the filter is active and dropping values.

**Also:** `f == 9999` as a capacity sentinel may incorrectly reject a large facility with exactly 9,999 beds (undisclosed exclusion).

**Fix:** Change `f <= 0` to `f < 0`.

### 1.3 `clean_coord()` — Aleutian Islands Longitude (Lines 233–234)

```python
if (-180.0 <= f <= -64.0) or (144.0 <= f <= 146.0):
```

**Status: Latent, not currently triggered.** Far western Aleutian Islands (e.g., Attu) have positive longitudes near `+172°E` — outside both accepted ranges. Any future HIFLD record for an Aleutian facility at a positive longitude would have its coordinates silently set to `None`. Current AK data (34 facilities, longitudes `−131.6° to −166.5°`) is unaffected.

### 1.4 `format_title()` — `Mc` and `O'` Prefix Casing (Lines 264–265)

```python
else:
    core_formatted = core.capitalize()
```

**Status: Unfixed.** `.capitalize()` lowercases all characters after the first:
- `MCDUFFIE → Mcduffie` (should be `McDuffie`) — 76 facilities affected
- `O'BRIEN → O'brien` (should be `O'Brien`) — 3 facilities affected

**Fix:**
```python
core_formatted = re.sub(r"^Mc([a-z])", lambda m: "Mc" + m.group(1).upper(), core_formatted)
core_formatted = re.sub(r"O'([a-z])", lambda m: "O'" + m.group(1).upper(), core_formatted)
```

### 1.5 Silent Attribute Dropping in Deduplication (Lines 288–293)

When a duplicate HIFLD feature is encountered and the existing entry already has valid coordinates, the duplicate is silently discarded — even if it has more complete attributes (phone, address). No warning is logged. The README says the pipeline "selects the primary record possessing valid geospatial coordinate geometry" — accurate but underemphasized.

### 1.6 Sentinel String Gaps

`SENTINEL_STRINGS` does not include `"NOT REPORTED"`, `"NA"` (no slash), or `"UNSPECIFIED"` — common in federal data releases. These were not found in the current CSV snapshot but represent a gap for future HIFLD refreshes.

### 1.7 Inaccurate Docstrings

- Line 3: `"Audited & Flawless"` — inappropriate given confirmed bugs
- Line 354 print: `"collision-free"` — directly contradicted by the `LOS` false positive

---

## Section 2 — Data Integrity Review: CSV

### 2.1 Duplicate Facility Name + City + State Triplets

**3 pairs (6 records) found:**

| Facility Name | City | State | IDs |
|:---|:---|:---:|:---|
| Larned State Hospital | Larned | KS | `10004852`, `10001831` |
| Jessup Correctional Institution | Jessup | MD | `10005831`, `10000919` |
| Garza County Jail | Post | TX | `10005117`, `10001259` |

These are upstream HIFLD records where the `FACILITYID` field itself is non-unique. The pipeline silently produces duplicate output rows. No warning is logged.

### 2.2 Duplicate Coordinates

**4 records** share exact lat/lon pairs (co-located BOP regional offices):

| IDs | Names | City | State |
|:---|:---|:---|:---|
| `BOP-GRA`, `BOP-SCR` | Grand Prairie RRM / RO South Central | Grand Prairie | TX |
| `BOP-MXR`, `BOP-CBR` | RO Mid-Atlantic / RRM Baltimore | Annapolis Junct | MD |

Real-world co-location — not erroneous. But the test suite cannot distinguish expected from unexpected duplication.

### 2.3 Empty Street Addresses

**3 records** have no street address: `10006402` (Bullock Co., AL), `10006478` (Phillips Co., AR), `10006284` (Saipan, MP). The README's claim of "100.0%" completeness is technically correct (6,765/6,768) but misleading.

### 2.4 Phone Number Non-Conformance

**38 phone numbers** fail the canonical regex `^\(\d{3}\) \d{3}-\d{4}$` due to extension suffixes (e.g., `(562) 799-4100 EXT 1116`). The test suite does not check phone format — only sentinel string absence.

### 2.5 Jurisdiction / README Discrepancy

| Jurisdiction | README Claims | CSV Actual |
|:---|:---:|:---:|
| County / Local | 3,924 | **3,960** |
| State | 2,347 | **2,273** |
| Federal | 253 | **288** |
| Municipal / Local | 182 | **184** |
| Multi-Jurisdiction | 35 | **36** |
| **Private / Contract** | **27** | **0 (label nonexistent)** |
| **Not Specified** | *not listed* | **27** |

The label `"Private / Contract"` does not exist in the pipeline output. The 27 `"Not Specified"` records include tribal detention, private youth facilities, police holding, and territory facilities — none correctly described as "Private / Contract."

### 2.6 Population > 3× Design Capacity (8 Facilities)

| Facility | State | Pop | Cap | Ratio |
|:---|:---:|---:|---:|---:|
| Woodman State Jail | TX | 6,478 | 900 | 7.2× |
| Burke County Jail (Downtown Jail) | NC | 262 | 66 | 4.0× |
| Southwest Virginia Regional Jail - Tazewell | VA | 264 | 80 | 3.3× |
| Fulton County Jail | IN | 133 | 35 | 3.8× |
| Tuscola County Jail | MI | 242 | 80 | 3.0× |
| Gallia County Jail | OH | 74 | 22 | 3.4× |
| Van Buren County Jail | TN | 50 | 13 | 3.8× |
| Page County Jail | VA | 79 | 26 | 3.0× |

Upstream HIFLD anomalies — consistent with prior audit. Not data pipeline errors.

### 2.7 BOP Records Without GPS
**0** — All 31 standalone BOP records have coordinates. ✅

### 2.8 ZIP / FIPS Leading Zeros
**0 violations** — All correctly zero-padded as strings. ✅

### 2.9 `O'` and `Mc` Casing in CSV
- `O'` names: `O'brien County Jail`, `Chain O'lakes Correctional Facility`, `The Thomas O'farrell Youth Center` — all incorrectly cased. ❌
- `Mc` names: 76 facilities — all rendered as `Mc[lowercase]` (e.g., `Mccreary`, `Mcduffie`, `Mckean`). ❌

### 2.10 Zero-Population Preservation
No records with `population = 0` in the CSV — consistent with `clean_int(f <= 0)` dropping them silently. ❌

### 2.11 All-Three Completeness (address + phone + website)
**5,791 facilities** — consistent with prior audit. ✅

---

## Section 3 — Excel Workbook Review

### 3.1 Sheet Structure
All 4 required sheets present. Row and column counts match CSV exactly (6,768 + 1 header, 20 columns). ✅

### 3.2 Data Dictionary — Missing "Field Name (CSV)" Column
**Status: Unfixed.** Sheet 4 header is `"Field Name"` / `"Description & Definition"` — no column for programmatic snake_case CSV key. Sheet 1 display names differ from CSV names (e.g., `"Facility Classification"` ≠ `facility_type`), creating a lookup gap for analysts cross-referencing the two. ❌

### 3.3 Data Type Fidelity
ZIP codes and FIPS codes stored as text strings — no leading zeros lost. ✅
Capacity and population stored as integers with `#,##0` format. ✅

### 3.4 State Summary Cross-Validation
Facility counts, total capacity, total population, and jurisdiction sub-totals all match independent `groupby` calculations. ✅

---

## Section 4 — Methodology & Documentation Review: README

### 4.1 "Collision-Free" Claim — Still False
> *"Cross-Jurisdictional Collision-Free Entity Matching"*

Directly contradicted by the confirmed `LOS` false positive. This claim must be removed or corrected. ❌

### 4.2 Disclosure Gaps

| Finding | Status |
|:---|:---:|
| BOP entity matching collision risk disclosed | ❌ Not documented |
| Pickens County AL FIPS correction documented | ✅ Yes |
| Guam/USVI FIPS imputation via `STANDALONE_COUNTY_FIPS_MAP` documented | ❌ Not mentioned |
| 4,000 multipart GIS polygon deduplication documented | ✅ Yes |
| `clean_int()` zero-value exclusion disclosed | ❌ Not disclosed |

### 4.3 Fabricated Self-Assessment Score
The README quotes `"Audit Quality Score: 98.5/100"` inside a code block attributed to `verify_dataset.py`. That script produces no such output — it prints only `"ALL VERIFICATION AUDITS PASSED!"`. This is a fabricated self-certification embedded in documentation. ❌

### 4.4 Jurisdiction Table Accuracy
All six jurisdiction counts in the README are wrong (see Section 2.5). ❌

---

## Section 5 — Test Suite Review

### 5.1 `test_deep_audit.py` — Missing Adversarial Tests

All 7 adversarial tests flagged by the prior audit remain absent:

| Missing Test | Current Risk |
|:---|:---|
| Duplicate `(facility_name, city, state)` triplets | 3 silent duplicates in dataset |
| Duplicate `(latitude, longitude)` coordinate pairs | 4 co-located records undetected |
| Phone regex `^\(\d{3}\) \d{3}-\d{4}$` conformance | 38 non-conforming numbers pass silently |
| BOP-sourced records with no GPS | Not asserted; passes only by coincidence |
| `O'` and `Mc` name casing validation | 79 miscased names undetected |
| Zero-population preservation | Impossible to test from output; must test `clean_int()` directly |
| Aleutian Island longitude validity (`+165° to +180°`) | Latent — would fail silently on future records |

### 5.2 False-PASS Risks

- **Test 4 (Coordinates):** The longitude bounds test uses identical bounds to `clean_coord()` — tautological. Any coordinate that the pipeline accepts will pass this test.
- **Test 7 (Phone Quality):** Checks for sentinel strings only, not format conformance. 38 non-conforming phones pass.
- **Test 5 (ZIP):** Format-correct but semantically unchecked (wrong-state ZIPs would pass).

### 5.3 `verify_dataset.py` Issues

- **Line 59:** Duplicate ID check prints `[INFO]` but does **not** `assert` — failures are not CI-blocking. ❌
- **Lines 68–70:** Latitude bounds checked but **longitude bounds are not** — out-of-range longitudes would pass. ❌

---

## Final Scorecard

| Category | Max | Score | Justification |
|:---|:---:|:---:|:---|
| **Data Completeness** | 20 | 18 | GPS/ZIP/FIPS all complete. Minor: 3 empty addresses, 38 non-conforming phones. |
| **Data Accuracy** | 20 | 14 | Confirmed `LOS` false positive corrupts 2 records. 79 `Mc`/`O'` names miscased. README jurisdiction table has 4 wrong counts and a phantom label. |
| **Code Quality & Robustness** | 20 | 14 | `clean_int(f <= 0)` unresolved. `format_title()` Mc/O' fix missing. BOP Rule 1 collision unfixed. No logging for silent drops. Inaccurate docstrings. |
| **Methodology Documentation** | 20 | 15 | Pickens/GPS bounding documented. "Collision-free" claim false. `clean_int(0)` undisclosed. Private label wrong. Fabricated 98.5/100 self-score. |
| **Test Suite Rigor** | 20 | 13 | 10 structural tests pass. All 7 prior adversarial tests still missing. Tautological coordinate test. Non-asserting duplicate check. |
| **Total** | **100** | **74** | |

---

## Recommended Fixes — Prioritized

### 🔴 Critical

1. **BOP Rule 1 false positive:** Add `h_type == "FEDERAL"` guard before Rule 1 fires.
2. **`clean_int(0)` bug:** Change `f <= 0` to `f < 0`.
3. **Remove `"(collision-free)"` label** (line 354) and `"Audited & Flawless"` docstring (line 3).

### 🟠 High

4. **`format_title()` Mc/O' casing:** Add post-capitalize regex substitution for `Mc` and `O'` prefixes.
5. **Fix README jurisdiction table:** Correct all 6 jurisdiction counts; rename or fix "Private / Contract" → "Not Specified" (or fix the classification logic).
6. **Remove fabricated `98.5/100` self-score** from README.
7. **Disclose `clean_int(0)` behavior** in Known Limitations.

### 🟡 Medium

8. **Phone extension handling:** Strip/store extensions, or document 38 non-conforming numbers.
9. **Add 7 missing adversarial tests** to `test_deep_audit.py` (see Section 5.1 table).
10. **`verify_dataset.py`:** Add longitude bounds check; make duplicate ID check an `assert`.
11. **Data Dictionary:** Add `"Field Name (CSV)"` column showing snake_case keys.

### 🟢 Low

12. **Log a warning** when deduplication silently discards a duplicate feature with valid attributes.
13. **Document Guam/USVI FIPS imputation** in README methodology section.
14. **Expand sentinel string list** with `"NOT REPORTED"`, `"NA"` for future HIFLD resilience.

---

*Report generated by Claude Sonnet 4.6 (Thinking) via Antigravity CLI — 2026-08-20 22:00 EDT*
