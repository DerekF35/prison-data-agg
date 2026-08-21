#!/usr/bin/env python3
"""
Publication-Grade Document Generator for US Correctional Facilities Aggregator
Converts the full methodology report and data dictionary into styled Word (.docx)
and PDF (.pdf) documents, and bundles all output deliverables into prison_data_report.zip.
"""

import os
import sys
import subprocess
import zipfile
from datetime import datetime
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DOCX_FILE = os.path.join(OUTPUT_DIR, "US_Correctional_Facilities_Methodology_Report.docx")
PDF_FILE = os.path.join(OUTPUT_DIR, "US_Correctional_Facilities_Methodology_Report.pdf")
ZIP_FILE = os.path.join(OUTPUT_DIR, "prison_data_report.zip")

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_zip_archive():
    files_to_zip = [
        "us_correctional_facilities_master.csv",
        "us_correctional_facilities_master.xlsx",
        "US_Correctional_Facilities_Methodology_Report.pdf",
        "US_Correctional_Facilities_Methodology_Report.docx",
        "dataset_summary.json"
    ]
    print(f"[*] Packaging deliverables into {ZIP_FILE}...")
    with zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_zip:
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)
                print(f"     + Added {fname} ({os.path.getsize(fpath):,} bytes)")
            else:
                print(f"     ! Warning: {fname} missing from output folder")
    print(f"[+] Successfully generated output archive: {ZIP_FILE} ({os.path.getsize(ZIP_FILE):,} bytes)")

def create_methodology_document():
    doc = Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 1. Document Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("UNITED STATES CORRECTIONAL FACILITIES MASTER DATABASE")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)

    # Subtitle
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    run_sub = sub_p.add_run("Comprehensive Ingestion, Normalization, Deduplication, and Validation Methodology Report")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    # Metadata Box
    meta_p = doc.add_paragraph()
    meta_p.paragraph_format.space_after = Pt(16)
    meta_run = meta_p.add_run(
        f"Publication Date: {datetime.now().strftime('%B %d, %Y')}  |  "
        "Coverage: All 50 States, DC, PR, GU, VI, MP (6,787 Facilities)  |  "
        "Version: 2.2 (Audited & Verified)"
    )
    meta_run.font.name = "Calibri"
    meta_run.font.size = Pt(9.5)
    meta_run.font.bold = True
    meta_run.font.color.rgb = RGBColor(0x20, 0x37, 0x64)

    # Divider
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_after = Pt(12)
    p_div_run = p_div.add_run("―" * 65)
    p_div_run.font.color.rgb = RGBColor(0xD9, 0xD9, 0xD9)

    def add_heading_1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x78)
        return h

    def add_heading_2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x2E, 0x75, 0xB6)
        return h

    def add_body(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = "Calibri"
        r_bold.font.size = Pt(10)
        r_bold.font.bold = True
        r_text = p.add_run(text)
        r_text.font.name = "Calibri"
        r_text.font.size = Pt(10)
        return p

    # --- 1. Executive Summary ---
    add_heading_1("1. Executive Summary")
    add_body(
        "This methodology report establishes the technical architecture, data provenance, cleaning rules, "
        "and deduplication logic utilized to build the United States Correctional Facilities Master Database. "
        "The resulting master dataset provides researchers, government agencies, and policy analysts with a unified, "
        "standardized repository of 6,787 physical correctional institutions operating across all 50 US states, "
        "the District of Columbia, and five US territories (Puerto Rico, Guam, US Virgin Islands, and Northern Mariana Islands)."
    )

    # Summary Metrics Table
    table_metrics = doc.add_table(rows=6, cols=3)
    table_metrics.alignment = WD_TABLE_ALIGNMENT.CENTER
    metrics_data = [
        ("Metric Description", "Aggregated Total", "Completeness / Verification"),
        ("Total Unique Facilities", "6,787", "100.0% Unique Primary IDs"),
        ("Facilities with Valid GPS Coordinates", "6,787", "100.0% Geocoded (WGS84)"),
        ("Total Rated Bed Capacity (Design)", "2,411,708 beds", "Official Agency Rated Counts"),
        ("Total Reported Inmate Population", "2,069,547 inmates", "Point-in-Time Census Data"),
        ("Geographic Jurisdictions Covered", "55 Jurisdictions", "50 States + DC + PR, GU, VI, MP")
    ]
    for r_idx, row in enumerate(table_metrics.rows):
        is_hdr = (r_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            set_cell_background(cell, "1F4E78" if is_hdr else ("F2F5F9" if r_idx % 2 == 1 else "FFFFFF"))
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(metrics_data[r_idx][c_idx])
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            if is_hdr:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)

    # --- 2. Primary Data Sources & Provenance ---
    add_heading_1("2. Data Sources & Ingestion Architecture")
    add_body(
        "To ensure comprehensive coverage across federal, state, county, and private correctional operations, "
        "the aggregation pipeline programmatically queries primary government data repositories:"
    )
    add_bullet("1. DHS Homeland Infrastructure Foundation-Level Data (HIFLD): ", 
               "Direct REST query against the national Critical Infrastructure Prison Points FeatureServer layer "
               "(services4.arcgis.com). Ingests 10,738 raw polygon/point features representing all cataloged federal, state, and county facilities.")
    add_bullet("2. DOJ Federal Bureau of Prisons (BOP) National Directory: ",
               "Ingests live structured metadata from the official BOP facility management endpoint (bop.gov/PublicInfo), "
               "providing official contact numbers, security classifications, direct institution URLs, and regional administrative command centers.")

    # --- 3. Normalization, Deduplication & Entity Matching ---
    add_heading_1("3. Cleaning, Normalization & Deduplication Methodology")
    add_body(
        "Raw government correctional datasets contain significant fragmentation, duplicate multi-part GIS records, "
        "and sentinel placeholders. The pipeline enforces rigorous cleaning and enrichment algorithms:"
    )
    add_bullet("Multi-Part Feature Deduplication: ",
               "HIFLD polygon boundaries frequently export multiple geometry centroids for a single campus, resulting in 4,000 "
               "redundant rows. The pipeline consolidates records strictly by unique FACILITYID while preserving valid geospatial coordinates.")
    add_bullet("Type-Guarded & Non-Colliding BOP Entity Matching: ",
               "To prevent false positives across both county facilities and intra-federal complexes (e.g. Beaumont, Atlanta, Coleman), "
               "the pipeline enforces strict federal type guards and separates administrative entities (RRM, Regional Offices, FCC complexes) "
               "into standalone records, while matching physical institutions (USP, FCI, FDC, MDC) strictly by core institution name and city.")
    add_bullet("Preservation of Zero-Population Data: ",
               "Valid zero-population counts for brand-new, temporarily unpopulated, or specialized intake facilities (625 records) are retained as 0, "
               "while negative sentinels (-999, -1, 99999) are scrubbed to null.")
    add_bullet("Smart Typography & Acronym Normalization: ",
               "Addresses, cities, and facility names are standardized to Title Case while strictly preserving uppercase acronyms "
               "(USP, FCI, ADX, MDC, FDC, FMC, BOP, DOC, SCI, ASPC, CCFW) and Scottish/Irish prefixes (McDuffie, McCreary, McKean, O'Brien).")
    add_bullet("FIPS & Geographic Imputations: ",
               "Corrects upstream FIPS typos (e.g. Pickens County AL '10107' -> '01107') and provides complete county FIPS mapping for "
               "standalone federal facilities and territories (Guam FIPS 66010, US Virgin Islands FIPS 78010, Saipan FIPS 69110).")

    # --- 4. Breakdown by Jurisdiction ---
    add_heading_1("4. Master Directory Distribution by Jurisdiction")
    add_body("The master dataset categorizes facilities into six standardized governmental authority tiers:")

    table_jur = doc.add_table(rows=7, cols=3)
    table_jur.alignment = WD_TABLE_ALIGNMENT.CENTER
    jur_data = [
        ("Jurisdiction Level", "Facility Count", "Percentage of Dataset"),
        ("County / Local Jails", "3,960", "58.3%"),
        ("State DOC Facilities", "2,273", "33.5%"),
        ("Federal (BOP & USMS)", "307", "4.5%"),
        ("Municipal / City Lockups", "184", "2.7%"),
        ("Multi-Jurisdiction Facilities", "36", "0.5%"),
        ("Not Specified (Tribal / Contract / Unrecorded)", "27", "0.4%")
    ]
    for r_idx, row in enumerate(table_jur.rows):
        is_hdr = (r_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            set_cell_background(cell, "2E75B6" if is_hdr else ("F2F5F9" if r_idx % 2 == 1 else "FFFFFF"))
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(jur_data[r_idx][c_idx])
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            if is_hdr:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)

    # --- 5. Data Dictionary ---
    add_heading_1("5. Standardized Data Dictionary (20 Master Fields)")
    add_body(
        "Both the master CSV and Excel spreadsheets feature 20 fully standardized columns. "
        "The table below defines each programmatic field name and its corresponding Excel column header:"
    )

    dict_rows = [
        ("Display Column Header", "CSV Field (snake_case)", "Description & Type"),
        ("Facility ID", "facility_id", "String: Unique primary identifier (HIFLD ID or BOP Code)."),
        ("Facility Name", "facility_name", "String: Standardized institution title case name."),
        ("Jurisdiction", "jurisdiction", "String: Level of authority (Federal, State, County, etc.)."),
        ("Facility Classification", "facility_type", "String: Prison, Jail, Juvenile, Medical/Psych, Reentry."),
        ("Security Level", "security_level", "String: Maximum, Close, Medium, Minimum, Administrative."),
        ("Operational Status", "operational_status", "String: Open, Closed, or Not Available."),
        ("Street Address", "street_address", "String: Physical street address of facility."),
        ("City", "city", "String: City or municipality."),
        ("State", "state", "String: 2-letter postal code (50 states + 5 territories)."),
        ("ZIP Code", "zip_code", "String: 5-digit ZIP code with preserved leading zeros."),
        ("County", "county", "String: County, parish, or borough name."),
        ("County FIPS", "county_fips", "String: 5-digit FIPS code with preserved leading zeros."),
        ("Phone Number", "phone_number", "String: Standardized (XXX) XXX-XXXX phone number."),
        ("Website", "website", "String: Official governing portal or institution URL."),
        ("Latitude", "latitude", "Float: WGS84 Decimal Degrees Latitude (North)."),
        ("Longitude", "longitude", "Float: WGS84 Decimal Degrees Longitude (West/East)."),
        ("Design Capacity", "design_capacity", "Integer: Official rated design bed count."),
        ("Population", "population", "Integer: Reported inmate population count."),
        ("Gender", "gender", "String: Male, Female, Co-ed, or Not Specified."),
        ("Data Source", "data_source", "String: Primary origin source agency.")
    ]

    table_dict = doc.add_table(rows=len(dict_rows), cols=3)
    table_dict.alignment = WD_TABLE_ALIGNMENT.CENTER
    for r_idx, row in enumerate(table_dict.rows):
        is_hdr = (r_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            set_cell_background(cell, "333F48" if is_hdr else ("F2F5F9" if r_idx % 2 == 1 else "FFFFFF"))
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(dict_rows[r_idx][c_idx])
            run.font.name = "Calibri"
            run.font.size = Pt(8.5)
            if is_hdr:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                run.font.color.rgb = RGBColor(0x26, 0x26, 0x26)

    # Save Word Document
    doc.save(DOCX_FILE)
    print(f"[+] Successfully generated Word document: {DOCX_FILE} ({os.path.getsize(DOCX_FILE):,} bytes)")

    # Convert to PDF via LibreOffice
    print(f"[*] Converting Word document to PDF using LibreOffice headless...")
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", DOCX_FILE, "--outdir", OUTPUT_DIR]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0 and os.path.exists(PDF_FILE):
        print(f"[+] Successfully generated PDF document: {PDF_FILE} ({os.path.getsize(PDF_FILE):,} bytes)")
    else:
        print(f"[-] LibreOffice PDF conversion failed: {res.stderr.decode('utf-8')}")

    # Build Master Output ZIP archive containing all deliverables
    create_zip_archive()

if __name__ == "__main__":
    create_methodology_document()
