"""Append a content-addressed, timestamped snapshot; never backdate issuance.
Run immediately after a successful update. Existing snapshots are never edited.
This is an audit archive, not proof of external publication or WORM storage.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, tempfile, os
R=Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def archive(root=R):
    root=Path(root)
    files=[]
    for pattern in ['scripts/v[234]*.py','src/**/*.py','data/v4/*.csv',
                    'data/v4/fitted/*','data/v2/targets/*.csv',
                    'data/v2/post_release/*.csv','data/v2/products/*.csv',
                    'data/interim/nbs_market_prices/*.csv','pyproject.toml']:
        files.extend(p for p in root.glob(pattern) if p.is_file())
    hashes={str(p.relative_to(root)):digest(p) for p in sorted(set(files))}
    if not any(k.endswith('.joblib') for k in hashes):
        raise ValueError('No fitted model artifacts; refusing empty registration')
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    base=root/'data/prospective';base.mkdir(parents=True,exist_ok=True)
    dest=base/fingerprint
    if dest.exists():
        manifest=json.loads((dest/'manifest.json').read_text())
        for name,sha in manifest['sha256'].items():
            if digest(dest/name)!=sha:raise ValueError('Archived snapshot integrity failure')
        return dest
    stage=Path(tempfile.mkdtemp(prefix='.pending-',dir=base))
    try:
        for name in hashes:
            out=stage/name;out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/name,out)
        manifest=dict(recorded_at=datetime.now(timezone.utc).isoformat(),
                      fingerprint=fingerprint,sha256=hashes,
                      status='Captured now, never use source cutoff as issuance timestamp',
                      evaluation='Only targets released after recorded_at may count prospectively; historical rows remain retrospective')
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2))
        os.rename(stage,dest)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return dest
if __name__=='__main__':print(archive())
