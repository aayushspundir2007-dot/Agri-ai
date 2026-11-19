from pathlib import Path
import json
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
DATA, MODELS, REPORTS = ROOT/'data', ROOT/'models', ROOT/'reports'
for p in (MODELS, REPORTS): p.mkdir(parents=True, exist_ok=True)
def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, default=str), encoding='utf-8')
def rmse(y, p): return float(np.sqrt(np.mean((np.asarray(y)-np.asarray(p))**2)))
def wape(y, p):
    den=np.abs(y).sum()
    return float(np.abs(np.asarray(y)-np.asarray(p)).sum()/den*100) if den else None
