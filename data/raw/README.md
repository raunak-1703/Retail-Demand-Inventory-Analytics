# Source data (local only)

Run `python scripts/download_data.py` from the repository root. It checks existing
files first and downloads the three unchanged CSVs from the public research archive
https://doi.org/10.5281/zenodo.10203108, attributed there to the University of Nicosia.
The archive explicitly identifies the Kaggle M5 competition as its source.

Official source: https://www.kaggle.com/competitions/m5-forecasting-accuracy/data

Checksums and byte counts are written to `source_manifest.json`. No credentials are
needed for this open archive. Downloads fail on HTTP errors or checksum mismatch.
If the archive stops being publicly available, obtain the same three files through
your authorized Kaggle account after accepting any required competition terms;
place them here. Do not bypass login or acceptance requirements.

The raw CSVs are excluded from Git. Public availability does not establish a right
to redistribute the dataset under this repository's MIT code license.
