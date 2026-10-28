"""Validate PBIR JSON using Microsoft's published schemas (network required)."""
from pathlib import Path
import json
import requests
import jsonschema
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]

def retrieve(uri):
    response=requests.get(uri,timeout=60)
    response.raise_for_status()
    return Resource.from_contents(response.json())

def main():
    registry=Registry(retrieve=retrieve)
    count=0
    for path in (ROOT/'powerbi').rglob('*.json'):
        obj=json.loads(path.read_text(encoding='utf-8-sig'))
        if '$schema' not in obj: continue
        schema=requests.get(obj['$schema'],timeout=60).json()
        validator=jsonschema.Draft7Validator(schema,registry=registry)
        errors=list(validator.iter_errors(obj))
        if errors: raise ValueError(f'{path}: '+ '\n'.join(str(e) for e in errors))
        count+=1
    print(f'{count} Power BI JSON definitions passed Microsoft schema validation')

if __name__=='__main__': main()
