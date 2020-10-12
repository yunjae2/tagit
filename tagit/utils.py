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


# params: params for choosing records
# uparams: params to be updated
def param_for_update(param_str: str) -> (OrderedDict(), OrderedDict()):
    param_list = param_str.split(",")
    params = OrderedDict()
    uparams = OrderedDict()

    if not param_str.strip():
        return params

    for param in param_list:
        if '=' in param:
            key, mvalue = tuple(x.strip() for x in param.split('='))
            values = mvalue.split('|')
            params[key] = values
        elif '->' in param:
            key, value = tuple(x.strip() for x in param.split('->'))
            uparams[key] = value
        else:
            key = param.strip()
            params[key] = ['*']

    return params, uparams


def param_after_update(params: OrderedDict(), uparams: OrderedDict()) -> OrderedDict():
    params_after = OrderedDict(params)
    for key, value in uparams.items():
        params_after[key] = [value]

    return params_after


def mkup_dtags(name_str: str) -> []:
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


def mkup_dtag(name: str) -> str:
    # Convert name: str() -> dtag: str()
    # Make up the internal name of the data category
    dtags = mkup_dtags(name)

    if len(dtags) != 1:
        print("Error: specify only one category")
        sys.exit(-1)

    return dtags[0]


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


def is_prohibited_name(name: str) -> bool:
    if name.startswith(tagit_prefix):
        return True
    return False


def mkup_command(comm_args: []) -> str:
    comm_str = ""
    for arg in comm_args:
        comm_str = comm_str + " " + arg
    return comm_str


def mkup_dstat(name: str) -> str:
    # Convert name: str() -> dstat: str()
    # Make up the internal name of the data status
    if name.startswith(tagit_prefix):
        print("Internal error: wrong dtag name")
        sys.exit(-1)

    return dstat_prefix + name


def is_dstat(col: str) -> bool:
    if col.startswith(dstat_prefix):
        return True
    return False


def dstat_name(dstat: str) -> str:
    if not is_dstat(dstat):
        print("Internal error: wrong dstat format")
        sys.exit(-1)

    return dstat[len(dstat_prefix):]


def dstat2dtag(dstat: str) -> str:
    name = dstat_name(dstat)
    return mkup_dtag(name)


def dtag2dstat(dtag: str) -> str:
    name = dtag_name(dtag)
    return mkup_dstat(name)
