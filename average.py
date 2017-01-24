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
        Returna an angle, in degrees, that is the average of the angles in a.
        Note that angular_interpolate([170, 190]) returns 180, but
        angular_interpolate([10, 350]) returns 0.
    """
    return np.sum(a) / a.size
