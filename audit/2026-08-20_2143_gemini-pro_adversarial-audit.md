# Adversarial Audit Report — US Correctional Facilities Aggregator

| Field | Value |
|:---|:---|
| **Date** | 2026-08-20 |
| **Time** | 21:43 EDT |
| **Auditor Model** | Gemini Pro (Google DeepMind) |
| **Requesting Model** | Claude Sonnet 4.6 (Anthropic / Thinking) |
| **Audit Scope** | Full project: pipeline code, CSV dataset, Excel workbook, README, test suite |
| **Final Score** | **78 / 100** |

---

## Scorecard

| Category | Score | Max |
|:---|:---:|:---:|
| Data Completeness | 19 | 20 |
| Data Accuracy | 14 | 20 |
| Code Quality & Robustness | 14 | 20 |
| Methodology Documentation | 16 | 20 |
| Test Suite Rigor | 15 | 20 |
| **Total** | **78** | **100** |

---

## Executive Summary

The project produces a highly complete dataset with 100% geographic boundary validation and 6,768 unique facilities across 55 US jurisdictions. However, the underlying pipeline contains critical logical flaws that undermine data accuracy and reproducibility:

- 🔴 **BOP entity matching introduces false positives** — county jails are incorrectly overwritten with federal BOP metadata
- 🔴 **`clean_int()` silently nullifies valid zero and 9999 capacity values** — erasing real data
- 🟠 **`format_title()` breaks Irish/Scottish name patterns** — `O'Brien` → `O'brien`, `McDuffie` → `Mcduffie`
- 🟠 **Duplicate coordinate pairs exist** in the dataset (4 facilities sharing exact lat/lon)
- 🟡 **README claims "collision-free" entity matching** which is demonstrably false

---

## Section 1: Code Quality — `build_master_dataset.py`

### 🔴 CRITICAL: False Positive Entity Matching (BOP Collisions)

**Rule 1** of the BOP matching algorithm checks `h_name.startswith(f"{bop_code} ")`. The BOP code for MDC Los Angeles is `LOS`. This caused the pipeline to match `Los Angeles County Sybil Brand Institute for Women` (a county jail) and overwrite its `website` field with a `bop.gov` URL.

**Suggested Fix:**
```python
# Before applying Rule 1, guard with a type check:
if bop_code and len(bop_code) >= 3 and h_type in ("FEDERAL", "MULTI"):
    if f" {bop_code} " in f" {h_name} " or h_name.startswith(f"{bop_code} "):
        matched_id = fac_id
        break
```

---

### 🔴 CRITICAL: False Negative Entity Matching

Text normalization using `re.sub(r'[^A-Z]', '', text)` strips spaces and punctuation. `FPC DULUTH` normalizes to `FPCDULUTH`, which does not match `FEDERAL PRISON CAMP` (`FEDERALPRISONCAMP`), creating false negatives where real BOP prisons fail to match their HIFLD counterparts.

**Suggested Fix:** Use token-set comparison or fuzzy matching at city+institution-type level as a fallback:
```python
# Fallback Rule 4: Match on city + first substantive token of name
if bop_city and b_city_norm == h_city_norm and bop_type in ("FEDERAL PRISON", "FPC", "FCI", "USP"):
    matched_id = fac_id
    break
```

---

### 🔴 CRITICAL: `clean_int()` Silently Drops Valid Values

Current logic:
```python
if f <= 0 or f == 9999 or f == 99999 or f == -999 or f == -1:
    return None
```

- `f <= 0` nullifies **valid zero-population counts** (brand-new, temporarily empty, or recently closed facilities)
- `f == 9999` may be a real capacity for large facilities (e.g., Cook County Jail has 10,000)

**Suggested Fix:**
```python
# Only reject known sentinel values, not valid zeros
SENTINEL_INTS = {-999, -1, 99999}
if f in SENTINEL_INTS or f < 0:
    return None
if f == 0:
    return 0  # Preserve valid zero population
return int(round(f))
```

---

### 🟠 HIGH: `format_title()` Breaks Name Patterns

`core.capitalize()` lowercases everything after the first character:
- `O'Brien` → `O'brien`
- `McDuffie` → `Mcduffie`
- `McCreary` → `Mccreary`

**Suggested Fix:** Add `Mc` / `Mac` / `O'` prefix detection:
```python
MC_PATTERN = re.compile(r"^(Mc|Mac)([A-Za-z])", re.IGNORECASE)
O_PATTERN  = re.compile(r"^(O')([A-Za-z])", re.IGNORECASE)

def smart_capitalize(word):
    m = MC_PATTERN.match(word)
    if m:
        return m.group(1).capitalize() + m.group(2).upper() + word[len(m.group(0)):].lower()
    m = O_PATTERN.match(word)
    if m:
        return m.group(1) + m.group(2).upper() + word[len(m.group(0)):].lower()
    return word.capitalize()
```

---

### 🟠 HIGH: Silent Feature Dropping in Deduplication

When two HIFLD features share the same `FACILITYID` and both have valid coordinates, the second feature is silently discarded with no log entry. Records missing `FACILITYID` entirely are also silently dropped.

**Suggested Fix:**
```python
if fac_id not in hifld_dict:
    hifld_dict[fac_id] = (attrs, lat, lon)
else:
    existing_attrs, ex_lat, ex_lon = hifld_dict[fac_id]
    if ex_lat is None and lat is not None:
        hifld_dict[fac_id] = (attrs, lat, lon)
    # NEW: Log any case where a record with coords is overwritten
    elif lat is not None and ex_lat is not None:
        print(f"[WARN] Duplicate FACILITYID with coords: {fac_id} — keeping first geometry")

# NEW: Log records missing FACILITYID
if not fac_id:
    print(f"[WARN] Skipping feature with missing FACILITYID: {attrs.get('NAME', 'UNKNOWN')}")
```

---

### 🟡 MEDIUM: Alaskan Aleutian Islands Longitude Exclusion

`clean_coord()` accepts longitudes only in `(-180 to -64)` or `(144 to 146)`. Valid Alaskan Aleutian Island locations cross the 180th meridian and have **positive** longitudes (e.g., Attu Island at +172°). These would be silently rejected.

**Suggested Fix:**
```python
# Extend to allow positive longitudes for far western Alaska/Aleutians
if (-180.0 <= f <= -64.0) or (144.0 <= f <= 180.0):
    return round(f, 6)
```

---

## Section 2: Data Integrity — `us_correctional_facilities_master.csv`

### Duplicate Name+City+State Triplets (6 found)
| Facility Name | City | State | Note |
|:---|:---|:---|:---|
| Larned State Hospital | Larned | KS | Two distinct buildings, same parent campus |
| Jessup Correctional Institution | Jessup | MD | Same campus, separate records |
| Garza County Jail | Post | TX | Two entries from HIFLD multipart feature |

**Note:** These appear to be intentional — separate buildings on the same campus sharing a name but with distinct HIFLD IDs. However, downstream consumers may interpret these as errors.

### Duplicate Coordinate Pairs (4 facilities, 2 pairs)
| Facility A | Facility B | Lat/Lon |
|:---|:---|:---|
| RO Mid - Atlantic | RRM Baltimore | 39.120272, -76.776849 |
| Grand Prairie | RO South Central | 32.741985, -96.958036 |

These are **BOP administrative offices sharing a building** — not data corruption, but should be noted for mapping use cases.

### Missing Street Addresses (3 facilities)
- `Bullock County Red Williams Detention Center`
- `Phillips County Jail`
- `Saipan Correctional Facility`

### Contact Completeness
**5,791 of 6,768** facilities (85.6%) have `street_address` + `phone_number` + `website` all populated.

### Capacity Anomalies (Population > 3× Capacity)
All 8 flagged anomalies are confirmed **upstream HIFLD data issues**, not pipeline artifacts. They represent facilities that historically expanded population beyond rated design capacity.

### BOP-Only Coordinate Coverage
✅ **0 BOP-only records** are missing GPS coordinates.

---

## Section 3: Excel Workbook — `us_correctional_facilities_master.xlsx`

### 🟡 MEDIUM: Column Header vs. Data Dictionary Mismatch
Sheet 1 uses human-readable display headers (e.g., `Facility Classification`) while the Data Dictionary references programmatic snake_case field names (e.g., `facility_type`). Downstream automated consumers may not be able to map between them.

**Suggested Fix:** Add a "Field Name (CSV)" column to the Data Dictionary tab showing the exact snake_case key.

### ✅ State Summary Integrity
Cross-validation passed — all Pandas `groupby` aggregations written to the Excel file are mathematically perfect.

### ✅ Data Type Fidelity
100% of ZIP codes and County FIPS codes are stored as string primitives. No leading zeroes were lost.

---

## Section 4: Methodology Documentation — `README.md`

### 🟠 HIGH: False "Collision-Free" Claim
README states the BOP entity matching is `"collision-free"`. The Los Angeles false positive proves this is incorrect. The claim should be revised.

**Suggested wording:** `"Collision-guarded entity matching (Federal type check required), with known edge cases for short 3-letter BOP codes in populous cities."`

### 🟡 MEDIUM: Missing Territory FIPS Documentation
The hardcoded Guam (FIPS `66010`) and Virgin Islands (FIPS `78010`) imputations in `STANDALONE_COUNTY_FIPS_MAP` are not mentioned anywhere in the README.

### ✅ Pickens County Mentioned
The upstream HIFLD FIPS correction for Pickens County, Alabama (`10107` → `01107`) is correctly documented.

### 🟡 MEDIUM: Zero-Population Nullification Omission
The README does not disclose that valid zero-population counts are artificially set to null by `clean_int()`.

---

## Section 5: Test Suite — `test_deep_audit.py` & `verify_dataset.py`

### 🟠 HIGH: Tautological Tests
**Test 7 (Phone Quality):** Checks if sentinel strings (`-1--1`, `000-000`) appear in the phone column. These are caught by `clean_phone()` before data is ever written — so the test can never fail. It does **not** validate that the resulting phone strings match a valid `(XXX) XXX-XXXX` regex.

### Missing Tests
| Missing Test | Severity |
|:---|:---|
| Duplicate `(facility_name, city, state)` triplets | Medium |
| Duplicate `(latitude, longitude)` coordinate pairs | Medium |
| Phone number regex conformance: `^\(\d{3}\) \d{3}-\d{4}$` | High |
| BOP-sourced records missing GPS coordinates | Medium |
| `O'` and `Mc` name casing validation | Medium |
| Zero-population facilities not being silently dropped | High |
| Aleutian Island longitude range validity | Low |

---

## Recommended Fixes by Priority

### 🔴 Critical (Fix Before Next Release)
1. **Guard BOP Rule 1 entity matching with `h_type == "FEDERAL"` check** to prevent county jail false positives
2. **Revise `clean_int()`** to preserve `0` population values and not reject `9999` as a sentinel

### 🟠 High (Fix in Next Sprint)
3. **Add `Mc`/`Mac`/`O'` smart capitalization** to `format_title()`
4. **Add warning logs** when features are silently dropped during deduplication
5. **Add phone regex test** to test suite: `^\(\d{3}\) \d{3}-\d{4}$`
6. **Add zero-population preservation test** to test suite
7. **Update README** to remove "collision-free" claim and document territory FIPS imputations

### 🟡 Medium (Backlog)
8. Add a "Field Name (CSV)" column to the Excel Data Dictionary tab
9. Extend Aleutian longitude range in `clean_coord()`
10. Add duplicate coordinate pair detection to test suite
11. Log a warning (not error) for the 6 duplicate name+city+state triplets
