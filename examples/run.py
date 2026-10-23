"""Execute a freeze/build/write/publish example from JSON."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.driftguard import Range
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'examples/operations.json'
x=json.loads(p.read_text());r=Range(dict(x['base']))
for k,v in x['before_freeze']:r.write(k,v)
token=r.freeze();candidate=r.construct(token);active_id=id(r.active)
for k,v in x['during_build']:r.write(k,v)
keys=[k for k,v in x['base']+x['before_freeze']+x['during_build']]
low=min(keys,default=0);high=max(keys,default=0)+1
before=r.scan(low,high);r.publish(token,candidate)
assert r.scan(low,high)==before and id(r.active)==active_id
print(json.dumps({'logical_records':before,'base_after_publication':list(r.base.items()),'residual':list(r.active.items()),'same_active_object':id(r.active)==active_id},indent=2))
