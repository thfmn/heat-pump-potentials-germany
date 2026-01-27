# Scripts Directory

This directory contains command-line scripts for data processing and validation in the Heat Pump Potentials Germany project.

## Overview

| Script | Purpose | Required Arguments |
|--------|---------|-------------------|
| `fetch_ffe_data.py` | Fetch raw data from FfE API | `--output-dir` |
| `generate_district_csvs.py` | Transform JSON to CSV with geometry | `--input-dir`, `--output-dir` |
| `validate_data.py` | Validate CSV data quality | `--data-dir` |
| `get_timestamp.py` | Get current timestamp (utility) | None |

## Script Details

### fetch_ffe_data.py

Fetches heat pump suitability data from the Forschungsstelle für Energiewirtschaft (FfE) Open Data Portal API.

**Usage:**
```bash
# Fetch all district-level data
python scripts/fetch_ffe_data.py --output-dir data/raw

# Fetch with verbose logging
python scripts/fetch_ffe_data.py --output-dir data/raw --verbose

# View help
python scripts/fetch_ffe_data.py --help
```

**Arguments:**
- `--output-dir` (required): Directory to save the raw JSON response
- `--state` (optional): Filter for a specific German state (note: API returns all data)
- `--verbose`, `-v` (optional): Enable DEBUG logging

**Output:**
- JSON file: `ffe_district_data_all_YYYYMMDD_HHMMSS.json`

**Data Source:**
- FfE Open Data Portal: https://opendata.ffe.de
- Dataset ID: 88 (District-level heat pump suitability, 2022)

---

### generate_district_csvs.py

Transforms raw FfE JSON data into CSV files with WKT geometry for the web application.

**Usage:**
```bash
# Transform all states
python scripts/generate_district_csvs.py \
    --input-dir data/raw \
    --output-dir webapp/data/districts

# Transform a specific state
python scripts/generate_district_csvs.py \
    --input-dir data/raw \
    --output-dir webapp/data/districts \
    --state Bayern

# Use different geometry source
python scripts/generate_district_csvs.py \
    --input-dir data/raw \
    --output-dir output \
    --geometry-dir webapp/data/districts

# View help
python scripts/generate_district_csvs.py --help
```

**Arguments:**
- `--input-dir` (required): Directory containing raw FfE JSON files
- `--output-dir` (required): Directory to save generated CSV files
- `--state` (optional): Generate CSV for a specific state only
- `--geometry-dir` (optional): Directory with existing CSVs for WKT geometry (defaults to `--output-dir`)
- `--verbose`, `-v` (optional): Enable DEBUG logging

**Output:**
- CSV files: `{state_abbrev}_full_data.csv` (e.g., `by_full_data.csv` for Bayern)

**Output Schema:**
| Column | Type | Description |
|--------|------|-------------|
| district | String | District name |
| building_type | Integer | Building type code (1, 6, 9, 11, 38, 100) |
| heat_source | Integer | Heat source code (0-4) |
| value | Float | Suitability proportion (0.0-1.0) |
| federal_state | String | German state name |
| district_type | String | District classification |
| geometry | String | WKT polygon geometry |

**Note:** This script requires existing CSV files with WKT geometry data. The geometry was originally processed from GeoJSON with manual corrections in the `notebooks/district_map_generation.ipynb` notebook.

---

### validate_data.py

Validates the quality and schema compliance of district CSV data files.

**Usage:**
```bash
# Validate all district CSV files
python scripts/validate_data.py --data-dir webapp/data/districts

# Validate a specific state
python scripts/validate_data.py --data-dir webapp/data/districts --state Bayern

# Save report to file
python scripts/validate_data.py --data-dir webapp/data/districts --output report.txt

# Verbose output
python scripts/validate_data.py --data-dir webapp/data/districts --verbose

# View help
python scripts/validate_data.py --help
```

**Arguments:**
- `--data-dir` (required): Directory containing district CSV files
- `--state` (optional): Validate only a specific state's data
- `--output`, `-o` (optional): Save report to file (default: print to stdout)
- `--verbose`, `-v` (optional): Enable DEBUG logging

**Validation Checks:**
1. **Column existence**: All 7 required columns present
2. **Value ranges**: Values in [0.0, 1.0] range
3. **Geometry completeness**: No null or empty WKT geometries
4. **Building type codes**: Valid codes (1, 6, 9, 11, 38, 100)
5. **Heat source codes**: Valid codes (0, 1, 2, 3, 4)
6. **State consistency**: federal_state matches expected state

**Exit Codes:**
- `0`: All validations passed
- `1`: One or more validations failed

---

### get_timestamp.py

Utility script to get the current timestamp in Asia/Bangkok timezone (UTC+7).

**Usage:**
```bash
python scripts/get_timestamp.py
# Output: 2026-01-27 15:59:06
```

**Output Format:** `YYYY-MM-DD HH:MM:SS`

---

## Typical Workflow

For a complete data refresh:

```bash
# 1. Fetch fresh data from FfE API
python scripts/fetch_ffe_data.py --output-dir data/raw

# 2. Transform to CSV format (requires existing geometry)
python scripts/generate_district_csvs.py \
    --input-dir data/raw \
    --output-dir webapp/data/districts

# 3. Validate the generated files
python scripts/validate_data.py --data-dir webapp/data/districts
```

## State Abbreviations

| State | Abbreviation | CSV Filename |
|-------|--------------|--------------|
| Baden-Württemberg | bw | bw_full_data.csv |
| Bayern | by | by_full_data.csv |
| Brandenburg | bb | bb_full_data.csv |
| Bremen | hb | hb_full_data.csv |
| Hamburg | hh | hh_full_data.csv |
| Hessen | he | he_full_data.csv |
| Mecklenburg-Vorpommern | mv | mv_full_data.csv |
| Niedersachsen | ni | ni_full_data.csv |
| Nordrhein-Westfalen | nw | nw_full_data.csv |
| Rheinland-Pfalz | rp | rp_full_data.csv |
| Saarland | sl | sl_full_data.csv |
| Sachsen | sn | sn_full_data.csv |
| Sachsen-Anhalt | st | st_full_data.csv |
| Schleswig-Holstein | sh | sh_full_data.csv |
| Thüringen | th | th_full_data.csv |

## Dependencies

All scripts require the project's Python dependencies. Install with:

```bash
uv sync
```

Key dependencies used:
- `requests`: HTTP client for API calls
- `pandas`: Data manipulation
- `tqdm`: Progress bars
