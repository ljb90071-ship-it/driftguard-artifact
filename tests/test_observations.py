import unittest
from src.observations import ResidenceCap, interference_residual, class_point_cost


class ObservationTests(unittest.TestCase):
    def test_residence_cold_start_hysteresis_and_expiry(self):
        r=ResidenceCap()
        # First interval [0,.2), confirmed exit at .4.
        for i, hot in enumerate([True,True,False,False,False]):
            r.observe((i+1)/10, 30 if hot else 0, 100, 10)
        self.assertAlmostEqual(r.intervals[0][1], .2)
        self.assertEqual(r.horizon(.5),2)  # only one completed interval
        for i, hot in enumerate([True,True,True,True,False,False],start=6):
            r.observe(i/10,30 if hot else 0,100,10)
        self.assertAlmostEqual(r.horizon(1.1),.3)  # durations .2 and .4
        self.assertAlmostEqual(r.horizon(1.1,capacity=.1),.1)
        self.assertEqual(r.horizon(66),2)

    def test_unfinished_interval_and_single_cold_bin(self):
        r=ResidenceCap()
        for i,hot in enumerate([True,True,False,True,True]):
            r.observe((i+1)/10,30 if hot else 0,100,10)
        self.assertTrue(r.hot)
        self.assertEqual(len(r.intervals),0)
        self.assertEqual(r.horizon(.5),2)

    def test_cost_decomposition_and_conditioning(self):
        self.assertAlmostEqual(interference_residual(.62,.70),.08)
        self.assertEqual(interference_residual(.62,.60),0)
        # Logical hits and misses have different termination fractions.
        hit=class_point_cost(100,80,1,2,3)
        miss=class_point_cost(100,20,1,2,4)
        self.assertAlmostEqual(hit,1.8)
        self.assertAlmostEqual(miss,5)
        with self.assertRaises(ValueError):class_point_cost(63,20,1,2,4)
