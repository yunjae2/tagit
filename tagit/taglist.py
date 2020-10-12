from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys

'''
taglist table

Table name: _tagit_taglist_{name}

Desc: Maintains metadata for tags

Layout:

   name  | default_val
---------+-------------
 storage |
 mem     | 16GB

Columns:
- name: The name of a tag
- default_val: The default value of the tag

'''


def exists(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    if query.table_exists(name):
        return True

    return False


def create(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    query.create_table(name, ["name", "default_val"])


def delete(exp_name):
    validate(exp_name)
    name = utils.mkup_taglist_name(exp_name)
    query.drop_table(name)


def add_tags(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    _add_tags(name, params)


def _add_tags(name, params):
    if not params:
        return

    tags = [{"name": k, "default_val": TAGIT_EMPTY} for k in params]
    query.add_entities(name, tags)


def set_default(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    cond_val = [({"name": [k]}, {"default_val": v[0]}) for k, v in params.items()]
    query.update_rows(name, cond_val)


def unset_default(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)
    cond_val = [({"name": [k]}, {"default_val": TAGIT_EMPTY}) for k in params]
    query.update_rows(name, cond_val)


def mkup_record_params(exp_name, params):
    name = utils.mkup_taglist_name(exp_name)

    params_ = params
    tags = query.get_entities(name, {}, [])
    for tag in tags:
        key = tag["name"]
        default = tag["default_val"]

        if key not in params_:
            if default != TAGIT_EMPTY:
                params_[key] = [default]
            else:
                params_[key] = [None]

    return params_


def default_params(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    tags = query.get_entities(name, {}, [])

    params = OrderedDict()
    for tag in tags:
        key = tag["name"]
        default = tag["default_val"]

        if default != TAGIT_EMPTY:
            params[key] = default
        else:
            params[key] = ""

    return params


def get_taglist(exp_name):
    name = utils.mkup_taglist_name(exp_name)
    taglist = query.get_entities(name, {}, [])

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

    query.rename_table(old_name, new_name)


def rename_tag(exp_name, old, new):
    name = utils.mkup_taglist_name(exp_name)

    # Update taglist
    query.update_row(name, {'name': [old]}, {'name': new})


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such taglist")
        sys.exit(-1)
