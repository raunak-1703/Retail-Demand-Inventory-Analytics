"""Rebuild all file deliverables; refresh Power BI Desktop afterward."""
from pathlib import Path
import subprocess
import sys
HERE=Path(__file__).resolve().parent
for script in ['download_data.py','prepare_data.py','validate_data.py','build_excel.py','write_insights.py','build_powerbi.py']:
    subprocess.run([sys.executable,str(HERE/script)],check=True)
