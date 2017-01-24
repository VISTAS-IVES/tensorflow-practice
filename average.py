# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:54:24 2017

@author: drake
"""

from extract import Classification
from extract import LABELLED, RAW

import numpy as np

# Import data
classifier = Classification('..', './classification.csv')
data, labels = classifier.get('primet_directions', policy=(LABELLED | RAW), max_row=30)


def angular_average(a):
    """
        Return an angle, in degrees, that is the average of the angles in a.
        Note that angular_interpolate([170, 190]) returns 180, but
        angular_interpolate([10, 350]) returns 0.
    """
    r = np.sum(a) / a.size
#    too_far = sum(abs(r - i) > 90 for i in a) / a.size
    too_far = np.sum(abs(r - a) > 90) / a.size
    if too_far > 0.5: # Most values are on wrong side of circle
        r = max(r - 180, 180 - r)
    return r
