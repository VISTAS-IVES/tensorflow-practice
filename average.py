# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:54:24 2017

@author: drake
"""

from extract import Classification
from extract import LABELLED, RAW
import math
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
    r = np.deg2rad(a)
    x = np.mean(np.cos(r))
    y = np.mean(np.sin(r))
    return (math.degrees(math.atan2(y, x)) + 360) % 360   

def masked_angular_average(a):
    """
        Like angular_average, but masks out any values of -1.
    """
    masked = np.ma.masked_array(a, np.equal(a, -1))
    return angular_average(masked)
