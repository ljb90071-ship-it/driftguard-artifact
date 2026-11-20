"""Read paper aggregates; validate accounting and derive comparisons."""
from pathlib import Path
import csv,json,math,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.driftguard import affine_gain
def read(n):
 with (ROOT/'results'/n).open(newline='') as f:return list(csv.DictReader(f))
def analyze():
 rows=read('table2_cycle.csv');assert len(rows)==12
 ratio=math.exp(sum(math.log(float(x['driftguard_cpu_s'])/float(x['fresh_cpu_s'])) for x in rows)/len(rows))
 clean={x['policy']:x for x in read('table5_cleanup.csv')}
 for x in clean.values():
  assert sum(float(x[k]) for k in ['foreground_controller_cpu_s','maintenance_cpu_s','cleanup_cpu_s'])==float(x['total_cpu_s'])
 ablation={x['policy']:x for x in read('table3_ablation.csv')}
 for policy,x in clean.items():
  assert float(x['foreground_controller_cpu_s'])+float(x['maintenance_cpu_s'])==float(ablation[policy]['cycle_cpu_s'])
 cfg=json.loads((ROOT/'configs/affine.json').read_text())
 # Equation 5 reports only C_b + E; avoid inferring an unreported split.
 cfg['build_cpu_s']=cfg.pop('transition_plus_interference_cpu_s')
 for x in read('figure3_analytic.csv'):
  g=affine_gain(**cfg,residual_penalty_s=float(x['residual_penalty_us_per_query'])*1e-6)*1000
  assert math.isclose(g,float(x['gain_cpu_ms']),abs_tol=1e-10)
 support=read('support.csv');assert sum(int(x['eligible_checks']) for x in support)==150000
 assert sum(int(x['executed_voluntary']) for x in support)==1710
 native={x['system']:x for x in read('table4_native.csv')}
 load=next(x for x in read('figure3_load.csv') if float(x['offered_mops_s'])==8)
 assert float(load['hire_point_p99_us'])==float(native['HIRE+']['point_p99_us'])
 assert float(load['driftguard_point_p99_us'])==float(native['DriftGuard']['point_p99_us'])
 return {'geomean_cycle_ratio':ratio,'cycle_reduction_percent':100*(1-ratio),
 'ewma_online_reduction_percent':100*(1-float(ablation['DriftGuard']['cycle_cpu_s'])/float(ablation['EWMA-residual']['cycle_cpu_s'])),
 'ewma_cleanup_reduction_percent':100*(1-float(clean['DriftGuard']['total_cpu_s'])/float(clean['EWMA-residual']['total_cpu_s'])),
 'native_point_p99_reduction_percent':100*(1-float(native['DriftGuard']['point_p99_us'])/float(native['HIRE+']['point_p99_us'])),
 'native_peak_increase_percent':100*(float(native['DriftGuard']['peak_gib'])/float(native['HIRE+']['peak_gib'])-1)}
if __name__=='__main__':print(json.dumps(analyze(),indent=2))
