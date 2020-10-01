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


def get_taglist(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    taglist = query._get_entities(name, {}, [])

    return taglist


def get_tags(exp_name):
    taglist = get_taglist(exp_name)
    tags = [x['name'] for x in taglist]

    return tags


def tag_exists(exp_name, tag):
    name = utils.mkup_taglist_name(exp_name)

    tags = get_tags(exp_name)
    if tag in tags:
        return True

    return False


def rename(old_exp_name, new_exp_name):
    old_name = utils.mkup_taglist_name(old_exp_name)
    new_name = utils.mkup_taglist_name(new_exp_name)

    query._rename_table(old_name, new_name)


def rename_tag(exp_name, old, new):
    name = utils.mkup_taglist_name(exp_name)

    # Update taglist
    query._update_row(name, {'name': [old]}, {'name': new})
    # Update table
    query._rename_column(exp_name, old, new)
