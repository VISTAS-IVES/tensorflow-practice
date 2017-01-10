#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 12:03:28 2017

@author: drake
"""

# Using an example from Lubanovic, Introducing Python, p. 313
def just_do_it(text):
    import re
    segments = re.split(r'([^a-zA-z\']+)', text)  
    return ''.join(a.capitalize() + b.capitalize()
                    for a, b in zip(segments[::2], segments[1::2] + ['']))
