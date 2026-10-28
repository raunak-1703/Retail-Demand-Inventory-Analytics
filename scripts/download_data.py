"""Download unchanged M5 source files from the public Zenodo research archive."""
from pathlib import Path
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    'calendar.csv': '3ffeab2991b0c8e861d008b39ea4c95c',
    'sales_train_validation.csv': '26a366a25beb57b0a8f4c7b148758f94',
    'sell_prices.csv': '08c591caa99e55daf3e0ccac913f7c85',
}

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'md5').hexdigest()

def main():
    folder = ROOT / 'data/raw'
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for name, expected in FILES.items():
        target = folder / name
        url = f'https://zenodo.org/records/10203108/files/{name}?download=1'
        if not target.exists():
            print(f'Downloading {name}', flush=True)
            tmp = target.with_suffix('.part')
            with requests.get(url, stream=True, timeout=(30, 180)) as response:
                response.raise_for_status()
                with tmp.open('wb') as output:
                    for chunk in response.iter_content(1024 * 1024):
                        output.write(chunk)
            if digest(tmp) != expected:
                raise ValueError(f'Checksum mismatch: {name}; partial file retained for diagnosis')
            tmp.replace(target)
        actual = digest(target)
        if actual != expected:
            raise ValueError(f'Existing file differs from archive: {name}')
        records.append(dict(file=name, bytes=target.stat().st_size, md5=actual, url=url))
        print(f'Verified {name}: {target.stat().st_size:,} bytes', flush=True)
    (folder / 'source_manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
