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


def taglist_id(exp_name: str) -> str:
    if utils.is_prohibited_name(exp_name):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return taglist_prefix + exp_name


def exists(exp_name):
    tid = taglist_id(exp_name)
    if query.table_exists(tid):
        return True

    return False


def create(exp_name):
    tid = taglist_id(exp_name)
    query.create_table(tid, ["name", "default_val"])


def delete(exp_name):
    validate(exp_name)
    tid = taglist_id(exp_name)
    query.drop_table(tid)


def add_tags(exp_name, params):
    tid = taglist_id(exp_name)
    _add_tags(tid, params)


def _add_tags(tid, params):
    if not params:
        return

    tags = [{"name": k, "default_val": TAGIT_EMPTY} for k in params]
    query.add_entities(tid, tags)


def set_default(exp_name, params):
    tid = taglist_id(exp_name)
    cond_val = [({"name": [k]}, {"default_val": v[0]}) for k, v in params.items()]
    query.update_rows(tid, cond_val)


def unset_default(exp_name, params):
    tid = taglist_id(exp_name)
    cond_val = [({"name": [k]}, {"default_val": TAGIT_EMPTY}) for k in params]
    query.update_rows(tid, cond_val)


def mkup_record_params(exp_name, params):
    tid = taglist_id(exp_name)

    params_ = params
    tags = query.get_entities(tid, {}, [])
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
    tid = taglist_id(exp_name)
    tags = query.get_entities(tid, {}, [])

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
    tid = taglist_id(exp_name)
    taglist = query.get_entities(tid, {}, [])

    return taglist


def get_tags(exp_name):
    taglist = get_taglist(exp_name)
    tags = [x['name'] for x in taglist]

    return tags


def tag_exists(exp_name, tag):
    tid = taglist_id(exp_name)

    tags = get_tags(exp_name)
    if tag in tags:
        return True

    return False


def rename(old_exp_name, new_exp_name):
    old_tid = taglist_id(old_exp_name)
    new_tid = taglist_id(new_exp_name)

    query.rename_table(old_tid, new_tid)


def rename_tag(exp_name, old, new):
    tid = taglist_id(exp_name)

    # Update taglist
    query.update_row(tid, {'name': [old]}, {'name': new})


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such taglist")
        sys.exit(-1)
