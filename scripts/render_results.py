"""Generate an HTML table view from the system and replay CSVs."""
from pathlib import Path
import csv,html,sys
ROOT=Path(__file__).resolve().parents[1]
target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/browse.html'
parts=['''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DriftGuard results</title>
<style>
body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#171717}
.table-scroll{overflow-x:auto;margin-bottom:30px}
table{border-collapse:collapse}
td,th{padding:8px 12px;border-bottom:1px solid #ccd3da;text-align:right}
td:first-child,th:first-child{text-align:left}
</style>
<h1>DriftGuard results</h1>
<nav><a href="../README.md">Overview</a> | <a href="schema.md">Field definitions</a> |
<a href="../paper-map.md">Paper map</a></nav>
<p>System summaries and fixed-cost residence replay. Column names give the units.</p>''']
for path in sorted((ROOT/'results').glob('*.csv')):
 with path.open(encoding='utf-8',newline='') as stream:
  rows=list(csv.reader(stream))
 parts.append('<h2>'+html.escape(path.stem)+'</h2><div class="table-scroll"><table>')
 for i,row in enumerate(rows):
  tag='th' if i==0 else 'td';parts.append('<tr>'+''.join('<'+tag+'>'+html.escape(v)+'</'+tag+'>' for v in row)+'</tr>')
 parts.append('</table></div>')
parts.append('</html>');target.write_text('\n'.join(parts),encoding='utf-8');print(target)
