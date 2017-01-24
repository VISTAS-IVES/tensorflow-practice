# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 12:25:01 2017

@author: drake
"""

import unittest
import numpy as np
from average import angular_average, masked_angular_average


class TestAverage(unittest.TestCase):
    
    def test_average(self):
        self.assertAlmostEqual(angular_average(np.array([170, 190])), 180)

    def test_wraparound(self):
        self.assertAlmostEqual(angular_average(np.array([10, 350])), 0)
    
    def test_wraparound_several_values(self):
        self.assertAlmostEqual(angular_average(np.array([10, 20, 30, 190, 210])), 20)

    def test_ignore_missing(self):
        self.assertAlmostEqual(masked_angular_average(np.array([10, 350, -1])), 0)

if __name__ == '__main__':
    unittest.main()
