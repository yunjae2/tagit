from .configs import *
from collections import OrderedDict
import sys


def param_dict(param_str: str) -> OrderedDict():
    # Convert param_str: str() -> params: OrderedDict()
    param_list = param_str.split(",")
    params = OrderedDict()

    if not param_str.strip():
        return params

    for param in param_list:
        if '=' in param:
            key, mvalue = tuple(x.strip() for x in param.split('='))
            values = mvalue.split('|')
            params[key] = values
        else:
            key = param.strip()
            params[key] = ['*']

    return params


def mkup_dtag(name_str: str) -> []:
    # Convert name_str: str() -> dtags: []
    # Make up the internal names of the data categories

    dtags = [dtag_prefix + x.strip() for x in name_str.split(",")]

    for dtag in dtags:
        if dtag == dtag_prefix:
            print("Error: the name of data category is empty")
            sys.exit(-1)

    # wildcard
    for dtag in dtags:
        if dtag == dtag_prefix + "*":
            return ["*"]

    return dtags


def dtag_name(dtag: str) -> str:
    # Extract the name of the data category
    if not is_dtag(dtag):
        print("Internal error: wrong dtag format")
        sys.exit(-1)

    return dtag[len(dtag_prefix):]


def is_dtag(col: str) -> bool:
    if col.startswith(dtag_prefix):
        return True
    return False
