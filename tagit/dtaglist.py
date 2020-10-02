from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys


def exists(exp_name):
    name = utils.mkup_dtag_list_name(exp_name)
    if query.table_exists(name):
        return True

    return False


def create(exp_name):
    name = utils.mkup_dtag_list_name(exp_name)
    query.create_table(name, ["name", "derived", "updated"])


def delete(exp_name):
    validate(exp_name)
    name = utils.mkup_dtag_list_name(exp_name)
    query.drop_table(name)


def rename(old_exp_name, new_exp_name):
    old_name = utils.mkup_dtag_list_name(old_exp_name)
    new_name = utils.mkup_dtag_list_name(new_exp_name)

    query._rename_table(old_name, new_name)


def update(exp_name, dtags, derived):
    name = utils.mkup_dtag_list_name(exp_name)

    validate(exp_name)

    curr_dtag_list = query._get_entities(name, {}, ["name", "derived"])
    curr_dtags = [x["name"] for x in curr_dtag_list]
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_dtags:
            new_dtags.append({
                "name": dtag,
                "derived": str(derived),
                "updated": "False"
                })

    _validate_derived(curr_dtag_list, dtags, derived)
    query._add_entities(name, new_dtags)


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such dtaglist")
        sys.exit(-1)


def _validate_derived(curr_dtags, dtags, derived):
    # Abort if recording to derived data category or deriving recorded data category
    for curr_dtag in curr_dtags:
        name_ = curr_dtag["name"]
        derived_ = curr_dtag["derived"]

        if name_ in dtags and derived_ != str(derived):
            if derived_ == "True":
                print("Error: recording to a derived data category")
            elif derived_ == "False":
                print("Error: deriving a recorded data category directly")
            else:
                print("Internal error: wrong derived value")
            sys.exit(-1)


def validate_derived(exp_name, dtags, derived):
    name = utils.mkup_dtag_list_name(exp_name)

    validate(exp_name)

    curr_dtags = query._get_entities(name, {}, ["name", "derived"])
    _validate_derived(curr_dtags, dtags, derived)


def get_status(exp_name: str):
    name = utils.mkup_dtag_list_name(exp_name)
    if not exists(exp_name):
        return []

    curr_dtag_list = query._get_entities(name, {}, ["name", "updated"])
    dtag_status = OrderedDict((x["name"], {"updated": x["updated"] == "True", \
            "up-to-date": False}) for x in curr_dtag_list)

    return dtag_status


def reset_status(exp_name: str):
    dtag_list_name = utils.mkup_dtag_list_name(exp_name)
    if not exists(exp_name):
        return

    query._update_row(dtag_list_name, {}, {"updated": "False"})


def mark_dtags_updated(exp_name, dtags):
    name = utils.mkup_dtag_list_name(exp_name)
    cond_vals = [({"name": [x]}, {"updated": "True"}) for x in dtags]
    query._update_rows(name, cond_vals)
