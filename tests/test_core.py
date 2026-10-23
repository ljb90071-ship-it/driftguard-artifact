import itertools
import math
import unittest
from src.driftguard import (Range, KMV, fit_growth, checked_lower_bound,
    affine_gain, trajectory_gain, dispatch, adverse_costs, point_cost,
    BuildRecord, predict_candidate)


class ProtocolTests(unittest.TestCase):
    def test_exhaustive_writes_across_publication(self):
        operations = [(k, v) for k in range(3) for v in (None, 7)]
        for sequence in itertools.product(operations, repeat=4):
            r = Range({0: 10, 2: 20}); oracle = {0: 10, 2: 20}
            for k, v in sequence[:2]:
                r.write(k, v); oracle[k] = v
            token = r.freeze(); active = r.active
            with self.assertRaises(MemoryError): r.construct(token, fail=True)
            for k, v in sequence[2:]:
                r.write(k, v); oracle[k] = v
                self.assertEqual(r.scan(0, 3), sorted((k,v) for k,v in oracle.items() if v is not None))
            r.publish(token, r.construct(token))
            self.assertIs(r.active, active)
            self.assertEqual(r.scan(0, 3), sorted((k,v) for k,v in oracle.items() if v is not None))
            for k in range(3): self.assertEqual(r.get(k), oracle.get(k))

    def test_no_second_freeze_or_stale_publish(self):
        r = Range({1: 2});t = r.freeze();c = r.construct(t)
        with self.assertRaises(RuntimeError):r.freeze()
        r.publish(t, c);r.write(2, 4);t2 = r.freeze()
        with self.assertRaises(RuntimeError):r.publish(t, c)
        r.publish(t2, r.construct(t2));self.assertEqual(r.get(2), 4)

    def test_all_rank_proposals(self):
        keys = [0, 4, 7, 10]
        for query in range(-1, 12):
            expected = sum(k < query for k in keys)
            for proposed in range(-1, 6):
                self.assertEqual(checked_lower_bound(keys, query, proposed), expected)
        self.assertEqual(checked_lower_bound([], 3, 10), 0)


class PolicyTests(unittest.TestCase):
    def test_midpoint_split_at_publication(self):
        # T is deliberately not a multiple of the 100-ms observation bin.
        g = trajectory_gain(1, .23, lambda t: 3, lambda t: 4,
                            lambda t: 1, .1)
        self.assertAlmostEqual(g, -.23 + .77*2 - .1)

    def test_affine_and_trajectory_agree(self):
        g = affine_gain(2, .2, 200000, .6e-6, .3e-6, .28e-6, .035)
        self.assertAlmostEqual(g, -.0278)
        numerical = trajectory_gain(2, .2, lambda t: .12,
            lambda t: .12, lambda t: 200000*.58e-6, .035)
        self.assertAlmostEqual(g, numerical)

    def test_capacity_overrides_economic_rejection(self):
        params = dict(frozen=False, mandatory=False, memory_reserved=True,
                      gain_envelope=[.01, -.01], horizon_s=2, build_s=.2)
        self.assertEqual(dispatch(**params), 'continue_serving')
        params.update(mandatory=True, supported=False)
        self.assertEqual(dispatch(**params), 'mandatory')
        params['frozen'] = True
        self.assertEqual(dispatch(**params), 'retry_or_finish')

    def test_no_publication_before_horizon(self):
        for t in [2, 3]:
            self.assertEqual(dispatch(frozen=False, mandatory=False, memory_reserved=True,
                gain_envelope=[10], horizon_s=2, build_s=t), 'continue_serving')

    def test_adverse_composition(self):
        old, new = adverse_costs([1, 3], [2, 5])
        for p in [0, .25, .5, .75, 1]:
            for q in [0, .25, .5, .75, 1]:
                self.assertLessEqual(old-new, (p+3*(1-p))-(2*q+5*(1-q)))
        self.assertEqual(point_cost(.25, 1, 2, 3), 4)
        with self.assertRaises(ValueError): adverse_costs([], [1])

    def test_distinct_repetition_and_union(self):
        a, b = KMV(64), KMV(64)
        for key in list(range(10))*5:a.add(key)
        for key in range(5, 20):b.add(key)
        self.assertEqual(a.estimate(), 10)
        self.assertEqual(a.union(b).estimate(), 20)
        large = KMV(64)
        for key in range(2000):large.add(key)
        self.assertTrue(1200 < large.estimate() < 2800)

    def test_growth_fit(self):
        kind, rate, predict = fit_growth([.1,.2,.3], [10,20,30], 100)
        self.assertEqual(kind, 'linear');self.assertAlmostEqual(predict(.5), 50)
        times = [.1,.2,.3,.4]
        counts = [1024*(1-math.exp(-10000*t/1024)) for t in times]
        kind, k, predict = fit_growth(times, counts, 10000)
        self.assertEqual((kind,k), ('saturating',1024))

    def test_candidate_support_and_probe_charged_once(self):
        record = BuildRecord(100,20,110,4,1920,110,5,.02,.003,.04,1)
        self.assertIsNone(predict_candidate(record, [record]*3))
        prediction = predict_candidate(record, [record]*4)
        self.assertEqual(prediction['segments'], 5)
        self.assertAlmostEqual(prediction['cpu_s'], .02)
        self.assertAlmostEqual(prediction['build_cpu_s'], .023)
        self.assertAlmostEqual(prediction['wall_s'], .04)


if __name__ == '__main__': unittest.main()
