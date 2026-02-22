"""
Compare production and QC datasets (Python).

Reads production and QC outputs (Parquet, CSV, or RDS), compares them with
pandas, and writes a comparison report. Parquet is the primary format.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd


def read_dataset(path: str) -> pd.DataFrame:
    """
    Read a dataset file.

    Supported formats:
      .parquet  — pd.read_parquet (requires pyarrow)
      .csv      — pd.read_csv
      .rds      — pyreadr (install separately)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    suffix = p.suffix.lower()

    if suffix == ".parquet":
        return pd.read_parquet(p)

    if suffix == ".csv":
        return pd.read_csv(p, dtype=str)

    if suffix == ".rds":
        try:
            import pyreadr
            robj = pyreadr.read_r(str(p))
            key = list(robj.keys())[0]
            return robj[key]
        except ImportError:
            raise RuntimeError(
                "Reading RDS requires pyreadr. Install with: pip install pyreadr"
            )

    raise ValueError(
        f"Unsupported format: {p.suffix}. Supported: .parquet, .csv, .rds"
    )


def compare_datasets(
    production_path: str,
    qc_path: str,
    id_column: str = "USUBJID",
) -> Tuple[bool, str]:
    """
    Compare production and QC datasets. Sort by id_column before comparing.

    Returns:
        (match: bool, report_text: str)
    """
    prod = read_dataset(production_path)
    qc   = read_dataset(qc_path)

    if id_column in prod.columns and id_column in qc.columns:
        prod = prod.sort_values(id_column).reset_index(drop=True)
        qc   = qc.sort_values(id_column).reset_index(drop=True)

    # Align to common columns (production defines expected set)
    common   = [c for c in prod.columns if c in qc.columns]
    prod_sub = prod[common].copy()
    qc_sub   = qc[common].copy()

    # Normalise to string and treat NA consistently
    for c in common:
        prod_sub[c] = prod_sub[c].fillna("").astype(str)
        qc_sub[c]   = qc_sub[c].fillna("").astype(str)

    diff = prod_sub != qc_sub
    if not diff.any().any():
        report = "Comparison: MATCH. No differences between production and QC datasets.\n"
        return True, report

    lines = ["Comparison: MISMATCH. Differences found.\n"]
    for col in common:
        if diff[col].any():
            n = int(diff[col].sum())
            lines.append(f"  Column '{col}': {n} row(s) differ.")
    report = "\n".join(lines)
    return False, report
