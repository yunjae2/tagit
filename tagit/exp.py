from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys


def rename(old, new):
    query._rename_table(old, new)

def get_data(name, params, dtags):
    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    data = query.get_entities(name, params, dtags)
    for dat in data:
        for key in dat:
            if dat[key] == None:
                dat[key] = ""

    return data
