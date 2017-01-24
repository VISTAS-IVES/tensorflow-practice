
'''
    Collect each of Jerilyn's nights into a dictionary structure, and packs and reloads it from a db if necessary for speed.
    Each element of the list contains a dictionary
'''

import os
import sys
import csv
import sqlite3
import datetime
from sodar_utils import SodarCollection, register_numpy_adapters, datetime_to_name

register_numpy_adapters()  # registers numpy array adapters


def bool_string(value):
    # Convert 1's and 0's to python booleans
    return True if value == 1 or value == '1' else False

def read_classification_data(path):
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]

    for row in data:
        for attribute in row.keys():
            if attribute not in ['year','month','day']:
                value = row[attribute]
                row[attribute] = bool_string(value)

    return data


def _build_from_db(path):

    con = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM night")
        data = cur.fetchall()

    result = [{
        'speeds': row[2],
        'directions': row[3],
        'date': row[1]
    } for row in data]

    return result


def _build_db(sodar_path):

    sodars = SodarCollection(sodar_path, make_db=True)


def _rebuild_classification(db_path):
    classification = list()
    con = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM night")
        data = cur.fetchall()

    for row in data:
        classification.append({
                'date': row[1],
                'is_labelled': row[2],
                'primet_speeds': row[3],
                'primet_directions': row[4],
                'mcrae_speeds': row[5],
                'mcrae_directions': row[6],
                'meta': {
                    'date': row[1],
                    'mesoscale_forcing': bool_string(row[7]),
                    'direction': bool_string(row[8]),
                    'valley_jet': bool_string(row[9]),
                    'pulsing': bool_string(row[10]),
                    'similar': bool_string(row[11]),
                    'year': row[1].year,
                    'month': row[1].month,
                    'day': row[1].day
                }                   
            })
        
    return classification


def build_night_classification(directory, class_path, rebuild=False):
    """ Generate a list of dictionaries that contain the classification and data for each pair of nights
    :param directory: The directory to the sodar date you want to load.
    :param class_path: The path to the classification data.
    :return: A list of dictionaries containing the classification and raw data for each night.
    """

    # sanity checking
    directory_contents = os.listdir(directory)
    mcrae_path = os.path.abspath(os.path.join(directory, 'mcrae'))
    primet_path = os.path.abspath(os.path.join(directory, 'primet'))
    found_mcrae = 'mcrae' in directory_contents and os.path.isdir(mcrae_path)
    found_primet = 'primet' in directory_contents and os.path.isdir(primet_path)

    if found_mcrae and found_primet:

        classification_db = os.path.abspath(os.path.join(directory, 'classification.db'))

        if os.path.exists(classification_db):

            if not rebuild:
                return _rebuild_classification(classification_db)
            else:
                os.remove(classification_db)

        # else, rebuild the classification db

        meta = read_classification_data(class_path)  # the original classification
        for row in meta:
            row.update({'date': datetime.date(int(row['year']), int(row['month']), int(row['day']))})

        paths = [mcrae_path, primet_path]
        night_lists = list()

        for path in paths:
            db_path = ''.join([path, os.sep, 'collection.db'])
            if os.path.exists(db_path):
                night_lists.append(_build_from_db(db_path))
            else:
                _build_db(path)
                night_lists.append(_build_from_db(db_path))

        classification = list()
        mcrae, primet = night_lists
        for m in mcrae:
            for p in primet:
                if m['date'] == p['date']:

                    # find the night in the meta
                    night_classification = None
                    is_labelled = False
                    for night in meta:
                        if m['date'] == night['date']:
                            night_classification = night
                            is_labelled = True
                            break

                    classification.append({
                        'date': m['date'],
                        'primet_speeds': p['speeds'],
                        'primet_directions': p['directions'],
                        'mcrae_speeds': m['speeds'],
                        'mcrae_directions': p['directions'],
                        'meta' : night_classification,
                        'is_labelled': is_labelled
                    })
                    break

        
        # build a db so we don't have to index every time
        if not os.path.exists(classification_db):
            con = sqlite3.connect(classification_db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            with con:
                cur = con.cursor()
                cur.execute("CREATE TABLE night (id integer primary key, timestamp date, is_labelled bool,"
                    "primet_speeds array, primet_directions array,"
                    "mcrae_speeds array, mcrae_directions array,"
                    "mesoscale_forcing bool, direction bool, valley_jet bool, pulsing bool, similar bool)")

                for row in classification:
                    t = row['date']
                    l = row['is_labelled']
                    ps = row['primet_speeds']
                    pd = row['primet_directions']
                    ms = row['mcrae_speeds']
                    md = row['mcrae_directions']
                    m = row['meta']['mesoscale_forcing'] if row['meta'] else 'NULL'
                    d = row['meta']['direction']         if row['meta'] else 'NULL'
                    v = row['meta']['valley_jet']        if row['meta'] else 'NULL'
                    pu = row['meta']['pulsing']          if row['meta'] else 'NULL'
                    s = row['meta']['similar']           if row['meta'] else 'NULL'
                    cur.execute("INSERT INTO night VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)", (t,l,ps,pd,ms,md,m,d,v,pu,s))
        

        return classification
    else:
        raise FileNotFoundError('Could not find the McRae and Primet directories. Are you pointing this '
                                'to the right directory?')




if __name__ == '__main__':
    """ (Re)builds the night classification from multiple datasets """
    jerilyn_classification = build_night_classification(sys.argv[1], sys.argv[2], rebuild=True)
