from .configs import *
from . import query
from . import utils
from . import parser
from . import taglist
from . import dtaglist
from collections import OrderedDict
import sys

'''
experiment table

Table name: _tagit_exp_{name}

Desc: The main table for an experiment that holds the data

Layout:

  storage  |  mem  |      _tagit_data_raw      | _tagit_stat_raw | _tagit_data_iops | _tagit_stat_iops | ...
-----------+-------+---------------------------+-----------------+------------------+------------------+----
 sata_ssd  | 16GB  | IOPS: 20K\nlatency: 100us | False           | 20K              | False            | ...
 nvme_ssd  | 16GB  | IOPS: 40K\nlatency: 10us  | False           | 40K              | False            | ...
 nvme_ssd  | 32GB  | IOPS: 60K\nlatency: 10us  | True            | 60K              | False            | ...

Components:
- column
    - tag: columns not starting with '_tagit_data'; contains tag value
    - dtag: columns starting with '_tagit_data_'; contains the data for
      the dtag
    - dstat: columns starting with '_tagit_stat_'; describes if
      a data has been updated since the last parsing.
- row: Each recorded data as well as parsed results (in dtag columns)

'''


def exp_name(exp_id):
    if not exp_id.startswith(exp_prefix):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return exp_id[len(exp_prefix):]


def exp_id(exp_name):
    if utils.is_prohibited_name(exp_name):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return exp_prefix + exp_name


def is_exp_id(exp_str):
    if exp_str.startswith(exp_prefix):
        return True

    return False


def exists(exp_name):
    eid = exp_id(exp_name)
    if query.table_exists(eid):
        return True

    return False


def get():
    tables = query.get_tables()
    exps = [exp_name(x) for x in tables if is_exp_id(x)]

    return exps


def _create(eid):
    query.create_table(eid, [default_dtag])
    query.new_column(eid, utils.dtag2dstat(default_dtag))


def create(exp_name):
    eid = exp_id(exp_name)
    _create(eid)

    taglist.create(exp_name)
    dtaglist.create(exp_name)
    parser.create(exp_name)

    print(f"New experiment: [{exp_name}]")


def delete(exp_name: str):
    eid = exp_id(exp_name)
    validate(exp_name)

    query.drop_table(eid)

    taglist.delete(exp_name)
    dtaglist.delete(exp_name)
    parser.delete(exp_name)

    print(f"Experiment deleted: {exp_name}")


def _rename(old, new):
    query.rename_table(old, new)


def rename(exp_old, exp_new):
    # Check the exp existence
    validate(exp_old)

    # Abort if the new exp name already occupied
    if exists(exp_new):
        print(f"Error: {exp_new} already exists")
        sys.exit(-1)

    old_eid = exp_id(exp_old)
    new_eid = exp_id(exp_new)

    _rename(old_eid, new_eid)
    dtaglist.rename(exp_old, exp_new)
    parser.rename(exp_old, exp_new)
    taglist.rename(exp_old, exp_new)


def get_data(exp_name, params, dtags):
    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    eid = exp_id(exp_name)

    tags = taglist.get_tags(exp_name)
    if dtags[0] == "*":
        dtags = dtaglist.get_dtags(exp_name)
    conds = params
    cols = tags + dtags
    entities = query.get_entities(eid, conds, cols)

    data = []
    for entity in entities:
        # Order by params
        # TODO: handle error for wrong params
        ordered = OrderedDict()
        for key in params:
            ordered[key] = entity.pop(key)
        ordered.update(entity)
        for dtag in dtags:
            ordered.move_to_end(dtag)

        data.append(ordered)

    for dat in data:
        for key in dat:
            if dat[key] == None:
                dat[key] = ""

    return data


def get_dstat(exp_name, params, dstats):
    # data: [{tag1: val1, tag2: val2, ..., dstat1: status, ...}, {...}, ...]
    eid = exp_id(exp_name)

    tags = taglist.get_tags(exp_name)
    if dstats[0] == "*":
        dtags = dtaglist.get_dtags(exp_name)
        dstats = [utils.dtag2dstat(x) for x in dtags]
    conds = params
    cols = tags + dstats
    entities = query.get_entities(eid, conds, cols)

    data = []
    for entity in entities:
        # Order by params
        # TODO: handle error for wrong params
        ordered = OrderedDict()
        for key in params:
            ordered[key] = entity.pop(key)
        ordered.update(entity)
        for dstat in dstats:
            ordered.move_to_end(dstat)

        data.append(ordered)

    for dat in data:
        for key in dat:
            if dat[key] == None:
                dat[key] = ""

    return data


# Update dstat to "True"
def update_dstat(exp_name, params, dtags):
    eid = exp_id(exp_name)

    conds = params
    dstats = [utils.dtag2dstat(x) for x in dtags]
    vals = OrderedDict((x, "True") for x in dstats)
    query.update_row(eid, conds, vals)


# Reset dstat to "False"
def reset_dstat(exp_name, params, dtags):
    eid = exp_id(exp_name)

    conds = params
    dstats = [utils.dtag2dstat(x) for x in dtags]
    vals = OrderedDict((x, "False") for x in dstats)
    query.update_row(eid, conds, vals)


def add_data(exp_name, params, dtags, data):
    eid = exp_id(exp_name)

    existing = query.get_entities(eid, params, [])
    if len(existing) != 0:
        print("Warning: data overwritten")
        query.delete_rows(eid, params)

    entity = OrderedDict()
    for key, mvalue in params.items():
        entity[key] = mvalue[0]
    for dtag in dtags:
        entity[dtag] = data

    query.add_entity(eid, entity)

    # Mark updated data categories for lazy parsing
    update_dstat(exp_name, params, dtags)


def _append_data(eid, params, dtag, data):
    query.append_row(eid, params, {dtag: data})


def delete_data(exp_name: str, params: OrderedDict()):
    eid = exp_id(exp_name)
    query.delete_rows(eid, params)


def update_tags(exp_name, params):
    eid = exp_id(exp_name)

    vars_ = list(params.keys())
    curr_vars = query.get_columns(eid)
    new_params = {}

    for k, v in params.items():
        if k not in curr_vars:
            new_params[k] = v

    if new_params:
        # TODO: Show warning if a data exists before a new variable is added
        taglist.add_tags(exp_name, new_params)
        query.new_columns(eid, new_params.keys())

        print(f"[{exp_name}] New tag added:")
        for key in new_params:
            print(f"- {key}")


def update_tag_values(exp_name: str, params: OrderedDict(), uparams: OrderedDict()):
    eid = exp_id(exp_name)

    # Update if new variable added
    update_tags(exp_name, uparams)

    # Abort if the record with the same tags already exists
    params_after = utils.param_after_update(params, uparams)
    existing = query.get_entities(eid, params_after, [])
    if len(existing) != 0:
        print("Error: conflict with existing record")
        sys.exit(-1)

    uparams_ = OrderedDict((k, [v]) for (k, v) in uparams.items())

    # Update tags
    query.update_row(eid, params, uparams)


def update_dtags(exp_name, dtags, derived=False):
    eid = exp_id(exp_name)

    curr_cols = query.get_columns(eid)
    new_cols = []

    for dtag in dtags:
        dstat = utils.mkup_dstat(utils.dtag_name(dtag))
        if dtag not in curr_cols:
            new_cols.append(dtag)
            new_cols.append(dstat)

    query.new_columns(eid, new_cols)

    dtaglist.update(exp_name, dtags, derived)

    if new_cols:
        print(f"[{exp_name}] New data category: ")
        new_dtags = (x for x in new_cols if utils.is_dtag(x))
        for dtag in new_dtags:
            dtag_name = utils.dtag_name(dtag)
            print(f"- {dtag_name}")


# Clear the dtag of the row
def clear_dtag(exp_name, dtag, params):
    eid = exp_id(exp_name)
    query.update_row(eid, params, {dtag: ""})


def validate(exp_name):
    exps = get()
    if exp_name not in exps:
        print("Error: no such experiment")
        print("List of experiments:")
        for exp in exps:
            print(f"- {exp}")

        sys.exit(-1)


def do_list():
    exps = get()
    for exp in exps:
        print(exp)


def _run_parsing_rule(exp_name, src, dest, cmd, params):
    eid = exp_id(exp_name)

    records = get_data(exp_name, params, [src])
    if len(records) != 1:
        if len(records) == 0:
            print("Internal error: target record is missing")
        if len(records) > 1:
            print("Internal error: wrong params or redundant records")
        sys.exit(-1)

    data = records[0][src]
    parsed = parser.parse_data(exp_name, src, dest, cmd, params, data)
    _append_data(eid, params, dest, parsed)

    reset_dstat(exp_name, params, [src])


def _run_backward_each_node(exp_name, graph, params, dtags, node):
    # root sources
    if node not in graph:
        dtags[node]["up-to-date"] = True
        return dtags[node]["updated"]

    edges = graph[node]
    need_update = False
    for edge in edges:
        src = edge["src"]
        rule_updated = (edge["updated"] == "True")
        need_update |= rule_updated
        need_update |= _run_backward_each_node(exp_name, graph, params, dtags, src)

    if need_update:
        clear_dtag(exp_name, node, params)
        for edge in edges:
            src = edge["src"]
            cmd = edge["cmd"]
            _run_parsing_rule(exp_name, src, node, cmd, params)

    dtags[node]["up-to-date"] = True
    return need_update


def _run_backward_each_leaf(exp_name, graph, params, dtags, leaf):
    _run_backward_each_node(exp_name, graph, params, dtags, leaf)


def run_parsing_graph_backward(exp_name, graph, params, dtags):
    if not graph or not dtags:
        return

    leaves = [x for x in dtags]
    for dtag, edges in graph.items():
        for edge in edges:
            src = edge["src"]
            if src in leaves:
                leaves.remove(src)

    for leaf in leaves:
        _run_backward_each_leaf(exp_name, graph, params, dtags, leaf)


def run_parser(exp_name):
    parsing_graph, updated = parser.build_parsing_graph(exp_name)
    rows = get_dstat(exp_name, {}, ["*"])
    target_rows = []

    for row in rows:
        need_run = updated
        params = OrderedDict((k, [v]) for k, v in row.items() if not utils.is_dstat(k))
        dtag_status = OrderedDict((utils.dstat2dtag(k), {"updated": v == "True", \
                "up-to-date": False}) for k, v in row.items() if utils.is_dstat(k))

        if not need_run:
            for dtag, status in dtag_status.items():
                if status["updated"] == True:
                    need_run = True

        if need_run:
            target_rows.append((params, dtag_status))

    for params, dtag_status in target_rows:
        run_parsing_graph_backward(exp_name, parsing_graph, params, dtag_status)

    parser.reset_status(exp_name)


def rename_tag(exp_name, old, new):
    eid = exp_id(exp_name)

    # check the tag existence
    if not taglist.tag_exists(exp_name, old):
        print("Error: no such tag")
        print(f"List of tags in {exp_name}:")
        for tag in tags:
            print(f"- {tag}")
        sys.exit(-1)

    # Abort if the new tag name already occupied
    if taglist.tag_exists(exp_name, new):
        print(f"Error: {new} already exists")
        sys.exit(-1)

    curr_tags = [x for x in query.get_columns(eid) if not utils.is_dtag(x)]
    if old not in curr_tags or new in curr_tags:
        print("Internal error: experiment-taglist incoherent")
        sys.exit(-1)

    # Update taglist
    taglist.rename_tag(exp_name, old, new)

    # Update experiment table
    query.rename_column(eid, old, new)
