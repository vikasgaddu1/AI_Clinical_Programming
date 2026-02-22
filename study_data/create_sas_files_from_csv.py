#!/usr/bin/env python3
"""
Script to Create raw_dm.csv and raw_dm.sas7bdat from messy date data

Purpose:
  - Reads raw demographic data with mixed date formats
  - Ensures ALL dates are in NON-ISO (messy) formats
  - Site-specific date format assignments:
    * Site 101: DD-MON-YYYY (e.g., 04-Sep-1954)
    * Site 102: MM/DD/YYYY (e.g., 09/04/1954)
    * Site 103: DD-MON-YYYY
    * Site 104: DD/MM/YYYY (e.g., 04/09/1954)
    * Site 105: MM/DD/YYYY
    * Site 106: DD-MON-YYYY
  - Saves updated CSV
  - Creates SAS7BDAT file with proper metadata

Author: Claude AI Assistant
Date: 2026-02-16
"""

import pandas as pd
import pyreadstat
import re
from datetime import datetime
import os

# Configuration
INPUT_CSV = os.path.dirname(__file__) + "/raw_dm.csv"
OUTPUT_CSV = os.path.dirname(__file__) + "/raw_dm.csv"
OUTPUT_SAS = os.path.dirname(__file__) + "/raw_dm.sas7bdat"

# Site-specific date formats
SITE_FORMATS = {
    '101': 'DD-MON-YYYY',
    '102': 'MM/DD/YYYY',
    '103': 'DD-MON-YYYY',
    '104': 'DD/MM/YYYY',
    '105': 'MM/DD/YYYY',
    '106': 'DD-MON-YYYY',
}

# SAS column labels
COLUMN_LABELS = {
    'STUDYID': 'Study Identifier',
    'SITEID': 'Site Identifier',
    'SUBJID': 'Subject Identifier for Study',
    'BRTHDT': 'Birth Date',
    'RFSTDTC': 'Reference Start Date/Time',
    'SEX': 'Sex',
    'RACE': 'Race (CDISC Standard Terminology)',
    'RACEOTH': 'Race Other Specify (Free-text)',
    'RACEO': 'Race Other (Alternative Variable Name)',
    'ETHNIC': 'Ethnicity',
    'AGE': 'Age',
    'AGEU': 'Age Units',
    'ARMCD': 'Planned Arm Code',
    'ARM': 'Planned Arm',
    'COUNTRY': 'Country',
    'INVNAM': 'Investigator Name',
}

def convert_iso_date(date_str, target_format):
    """Convert ISO format (YYYY-MM-DD) date to target format"""
    if pd.isna(date_str) or date_str is None or str(date_str).strip() == '':
        return date_str
    
    date_str = str(date_str).strip()
    
    # Check if it's in ISO format (YYYY-MM-DD)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(iso_pattern, date_str):
        return date_str
    
    try:
        # Parse the ISO date
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Convert to target format
        if target_format == 'DD-MON-YYYY':
            return parsed_date.strftime('%d-%b-%Y')
        elif target_format == 'MM/DD/YYYY':
            return parsed_date.strftime('%m/%d/%Y')
        elif target_format == 'DD/MM/YYYY':
            return parsed_date.strftime('%d/%m/%Y')
        else:
            return date_str
    except Exception as e:
        print(f"Error converting date {date_str}: {e}")
        return date_str

def fix_dates(df):
    """Fix ISO format dates in BRTHDT and RFSTDTC columns"""
    conversions = 0
    
    if 'SITEID' not in df.columns:
        return conversions
    
    for col in ['BRTHDT', 'RFSTDTC']:
        if col not in df.columns:
            continue
        
        for idx, row in df.iterrows():
            site_id = str(row['SITEID']).strip()
            if site_id not in SITE_FORMATS:
                continue
            
            target_format = SITE_FORMATS[site_id]
            original_val = row[col] if pd.notna(row[col]) else ''
            converted_val = convert_iso_date(original_val, target_format)
            
            if original_val != converted_val and original_val:
                conversions += 1
            
            df.at[idx, col] = converted_val
    
    return conversions

def main():
    print("="*80)
    print("PROCESSING: Create raw_dm.csv and raw_dm.sas7bdat")
    print("="*80)
    
    # Read CSV
    print("\n1. Reading CSV...")
    df = pd.read_csv(INPUT_CSV, dtype=str)
    print(f"   Records: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    # Fix dates
    print("\n2. Fixing ISO format dates...")
    conversions = fix_dates(df)
    print(f"   Conversions: {conversions}")
    
    # Verify
    iso_count = 0
    for col in ['BRTHDT', 'RFSTDTC']:
        if col in df.columns:
            iso_mask = df[col].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')
            iso_count += iso_mask.sum()
    
    print(f"   Remaining ISO dates: {iso_count}")
    if iso_count == 0:
        print("   ✓ No ISO format dates")
    
    # Save CSV
    print("\n3. Saving CSV...")
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"   ✓ {OUTPUT_CSV}")
    print(f"   Size: {os.path.getsize(OUTPUT_CSV):,} bytes")
    
    # Create SAS7BDAT via XPORT
    print("\n4. Creating SAS7BDAT...")
    
    df_sas = df.copy()
    try:
        df_sas['AGE'] = pd.to_numeric(df['AGE'], errors='coerce')
    except:
        pass
    
    try:
        # Try direct write if available
        pyreadstat.write_sas7bdat(
            df_sas,
            OUTPUT_SAS,
            column_labels=COLUMN_LABELS
        )
        print(f"   ✓ {OUTPUT_SAS}")
        print(f"   Size: {os.path.getsize(OUTPUT_SAS):,} bytes")
    except (AttributeError, TypeError):
        # Fallback to XPORT
        print("   Note: Using XPORT format (SAS compatible)")
        xpt_file = OUTPUT_SAS.replace('.sas7bdat', '.xpt')
        pyreadstat.write_xport(
            df_sas,
            xpt_file,
            column_labels=COLUMN_LABELS
        )
        print(f"   ✓ {xpt_file}")
        print(f"   Size: {os.path.getsize(xpt_file):,} bytes")
    
    print("\n5. Summary")
    print("-"*80)
    print(f"✓ CSV: {OUTPUT_CSV}")
    print(f"✓ SAS: {OUTPUT_SAS}")
    print(f"\nDate Format Mapping:")
    for site in sorted(SITE_FORMATS.keys()):
        print(f"  Site {site}: {SITE_FORMATS[site]}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

