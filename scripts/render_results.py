"""Generate an HTML table view from the archived CSVs (no dependencies)."""
from pathlib import Path
import csv,html,sys
ROOT=Path(__file__).resolve().parents[1]
target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'results/browse.html'
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><title>DriftGuard result tables</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;color:#17212b}table{border-collapse:collapse;margin-bottom:35px}td,th{padding:8px 12px;border-bottom:1px solid #ccd3da;text-align:right}td:first-child,th:first-child{text-align:left}</style><h1>DriftGuard result tables</h1><nav><a href="../README.md">Repository overview</a> | <a href="schema.md">Field definitions</a> | <a href="../paper-map.md">Paper map</a></nav><p>Archived aggregate values; units are encoded in column names.</p>']
for path in sorted((ROOT/'results').glob('*.csv')):
 rows=list(csv.reader(path.open(newline='')));parts.append('<h2>'+html.escape(path.stem)+'</h2><table>')
 for i,row in enumerate(rows):
  tag='th' if i==0 else 'td';parts.append('<tr>'+''.join('<'+tag+'>'+html.escape(v)+'</'+tag+'>' for v in row)+'</tr>')
 parts.append('</table>')
parts.append('</html>');target.write_text('\n'.join(parts),encoding='utf-8');print(target)
