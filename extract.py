"""
    author: Taylor Mutch
    date: 1/4/2017 12:27pm
"""

# Extracts subsets from classifications based on different policies.

from jerilyn import build_night_classification
from sodar_utils import register_numpy_adapters
import numpy as np
from pprint import pprint

register_numpy_adapters()

# missing data policies
RAW = 0
CLAMP = 1
INTERPOLATE = 2
FILL = 4

NODATA_POLICIES = {'RAW':           RAW,
                   'CLAMP':         CLAMP,
                   'INTERPOLATE':   INTERPOLATE,
                   'FILL':          FILL}

# extraction policies
ALL = 8
LABELLED = 16
NOT_LABELLED = 32

EXTRACTION_POLICIES = {'ALL':           ALL,
                       'LABELLED':      LABELLED,
                       'NOT_LABELLED':  NOT_LABELLED}

# field policites
FIELDS = ['primet_speeds',
          'primet_directions',
          'mcrae_speeds',
          'mcrae_directions']

PHENOMENA = ['mesoscale_forcing','direction','valley_jet','pulsing','similar']

# Inform the interpreter user of the available policies
if __name__ == '__main__':
    print("Available fields:")
    pprint(FIELDS)
    print("\nNo-Data Policies:")
    pprint(NODATA_POLICIES)
    print("\nExtraction Policies:")
    pprint(EXTRACTION_POLICIES)
    print("\nPhenomena (visually identified)")
    pprint(PHENOMENA)

class Classification:
    """ A class for filtering and extracting data from the SoDAR data. """

    def __init__(self, sdr_path, cls_path):

        self._dataset = build_night_classification(sdr_path, cls_path)

    def get(self, field, policy=RAW|ALL, phenomena=None, fill_value=None, max_row=41, min_row=0):
        """ Returns a view of the dataset based on given extraction policies.
            :param field The classification field you wish to extract.
            :param policy The extraction policy. Uses bitwise combinations from EXTRACTION_POLICIES and NODATA_POLICIES
            :param phenomena The visually identified phenomenon to filter by. Accepts a string or list of strings.
            :param fill_value If using the FILL policy, provide a value to fill the data with.
            :return A list of numpy.ndarray objects of shape (145,41), where each row is a column of vectors.
        """

        # Masks for extraction and nodata policies        
        extraction = policy & 0b111000
        nodata = policy & 0b000111
        
        # Apply phenomena policy
        if phenomena is not None:
            if type(phenomena) is list:
                # iterate through phenomena and get union
                subset = list()
                for row in self._dataset:
                    has_all_options = True
                    for option in phenomena:
                        if not row['meta'][option]: # row is false for option
                            breakout = False
                    if has_all_options:
                        subset.append(row)

            elif type(phenomena) is str and phenomena in PHENOMENA:
                subset = [row for row in self._dataset if row['meta'][phenomena]]
            else:
                raise ValueError("Phenomena not found. Value supplied was " + str(phenomena))
        else:
            subset = self._dataset

        # Apply extraction policy
        if extraction == ALL:
            result = [x[field].copy() for x in subset]
            meta = [x['meta'].copy() for x in subset]
        elif extraction == LABELLED:
            result = [x[field].copy() for x in subset if x['is_labelled']]
            meta = [x['meta'].copy() for x in subset if x['is_labelled']]
        elif extraction == NOT_LABELLED:
            result = [x[field].copy() for x in subset if not x['is_labelled']]
            meta = [x['meta'].copy() for x in subset if not x['is_labelled']]
        else:
            raise ValueError("Invalid extraction policy. Use ALL, LABELLED, or NOT_LABELLED")

        if max_row > 41:
            raise ValueError("Can't set max_row > 41.")
        elif max_row < 0:
            raise ValueError("Can't set max_row < 0.")
        elif min_row < 0:
            raise ValueError("Can't set min_row < 0.")
        elif min_row > 41:
            raise ValueError("Can't set min_row > 41.")
        elif min_row > max_row:
            raise ValueError("Can't set min_row > max_row.")
            #result = [x[:,min_row:] for x in result]

        result = [x[:,min_row:max_row].copy() for x in result]

        print('Output size:')
        print(result[0].shape)

        # Apply nodata policy
        if nodata == RAW:
            return result, meta
        elif nodata == CLAMP:
            return _clamp(result), meta
        elif nodata == INTERPOLATE:
            return _interpolate(result), meta
        elif nodata == (CLAMP | INTERPOLATE):
            return _interpolate(_clamp(result)), meta
        elif nodata == FILL:
            if fill_value is not None:
                return _fill(result, fill_value), meta
            else:
                raise ValueError("Set FILL nodata policy but didn't specify fill_value parameter")
        else:
            raise ValueError("Invalid nodata policy. Use RAW, CLAMP, INTERPOLATE, (CLAMP | INTERPOLATE), or FILL (with a fill_value).")

def _clamp(data):
    """ Clamps top value across top of column """

    shape = data[0].shape   # should be (145, 41)
    for subset in data:
        for column in subset:
            i = shape[1] - 1
            while i >= 0:
                if column[i] != -1.0:
                    clamp_value = column[i]
                    j = i
                    while j < shape[1]:
                        column[j] = clamp_value
                        j += 1
                    break

                # move down the column
                i -= 1
    return data


INTERPOLATE_RANGE = 3   # control the breadth of how far we allow interpolation to go.

def _interpolate(data):
    """ 
        Fills holes with average of values above and below. If indices above 
        are all missing, we bail. Use _clamp for filling those ranges. 
    """
    shape = data[0].shape   # should be (145, 41)
    for subset in data:
        missing = np.where(subset==-1.0)
        size = missing[0].size
        for i in range(size):           # Uses reverse iteration, avoiding clamped values along the top
            row = missing[0][size-i-1]
            col = missing[1][size-i-1]

            values = list()
            top = col
            #if top < 40:
            while top < (shape[1]-1) and top-col <= INTERPOLATE_RANGE: # absolute top of the column, with 0 index rather than 1
                top += 1
                if (subset[row][top] != -1.0):
                    values.append(subset[row][top])
                    #break

            if len(values) == 0:
                # all values above are missing, bail on this value, use clamp instead
                continue

            bot = col
            #if col > 0:
            while bot > 0 and abs(bot-col) <= INTERPOLATE_RANGE:
                bot -= 1
                if (subset[row][bot] != -1.0):
                    values.append(subset[row][bot])
                    #break

            values = np.array(values)
            if values.size > 0:
                subset[row][col] = values.sum() / values.size
            #else: # value stays the same
            #    subset[row][col] = -1.0

    return data


def _fill(data, value):
    """ Blanket filling policy across entire dataset """
    for subset in data:
        subset[subset==-1.0] = value

    return data
