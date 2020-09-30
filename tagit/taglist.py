from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys


def create(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    query.create_table(name, ["name", "explicit", "implicit"])

    _add_tags(name, params)


def add_tags(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    _add_tags(name, params)


def _add_tags(name, params):
    if not params:
        return

    tags = [{"name": k, "explicit": TAGIT_EMPTY, "implicit": TAGIT_EMPTY} for k in params]
    query._add_entities(name, tags)


def update_implicit(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    cond_val = [({"name": [k]}, {"implicit": v[0]}) for k, v in params.items()]
    query._update_rows(name, cond_val)


def set_explicit(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    cond_val = [({"name": [k]}, {"explicit": v[0]}) for k, v in params.items()]
    query._update_rows(name, cond_val)


def unset_explicit(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    cond_val = [({"name": [k]}, {"explicit": TAGIT_EMPTY}) for k in params]
    query._update_rows(name, cond_val)


def mkup_record_params(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)

    params_ = params
    tags = query._get_entities(name, {}, [])
    for tag in tags:
        key = tag["name"]
        explicit = tag["explicit"]
        implicit = tag["implicit"]

        if key not in params_:
            if explicit != TAGIT_EMPTY:
                params_[key] = [explicit]
            elif implicit != TAGIT_EMPTY:
                params_[key] = [implicit]
            else:
                print("Internal error: wrong taglist entry")
                sys.exit(-1)

    return params_


def default_params(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    tags = query._get_entities(name, {}, [])

    params = OrderedDict()
    for tag in tags:
        key = tag["name"]
        explicit = tag["explicit"]
        implicit = tag["implicit"]

        if explicit != TAGIT_EMPTY:
            params[key] = explicit
        elif implicit !=  TAGIT_EMPTY:
            params[key] = implicit
        else:
            print("Internal error: wrong taglist entry")
            sys.exit(-1)

    return params
