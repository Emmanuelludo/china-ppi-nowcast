"""Pack reproducible state for durable GitHub Release storage."""
from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[1]
def pack(destination):
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for folder in ['data','reports']:
            for p in sorted((R/folder).rglob('*')):
                if not p.is_file() or '__pycache__' in p.parts:continue
                rel=p.relative_to(R)
                if str(rel).startswith(('data/v2/runs/','data/prospective/')):continue
                if p.suffix in ['.log']:continue
                z.write(p,rel)
if __name__=='__main__':
    import sys
    pack(sys.argv[1])
