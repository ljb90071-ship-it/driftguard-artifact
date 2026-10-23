import unittest
from unittest.mock import patch
from scripts import analyze


class AnalysisTests(unittest.TestCase):
    def test_comparisons_follow_source_values(self):
        original=analyze.read
        def changed(name):
            rows=original(name)
            if name=='table4_native.csv':
                for row in rows:
                    if row['system']=='HIRE':row.update(point_p99_us='20',peak_gib='4')
            if name=='figure3_load.csv':
                for row in rows:
                    if float(row['offered_mops_s'])==8:row['hire_point_p99_us']='20'
            if name=='table3_ablation.csv':
                for row in rows:
                    if row['policy']=='EWMA-residual':row['cycle_cpu_s']='800'
            if name=='table5_cleanup.csv':
                for row in rows:
                    if row['policy']=='EWMA-residual':row.update(foreground_controller_cpu_s='730',total_cpu_s='828')
            return rows
        with patch.object(analyze,'read',changed):result=analyze.analyze()
        self.assertAlmostEqual(result['native_point_p99_reduction_percent'],35)
        self.assertAlmostEqual(result['native_peak_increase_percent'],30)
        self.assertAlmostEqual(result['ewma_online_reduction_percent'],2.5)
