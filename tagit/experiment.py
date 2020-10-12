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

Desc: The main table for an experiment that holds the data

Layout:

  storage  |  mem  |      _tagit_data_raw      | _tagit_data_iops | _tagit_data_latency
-----------+-------+---------------------------+---------------------------------------
 sata_ssd  | 16GB  | IOPS: 20K\nlatency: 100us | 20K              | 100us
 nvme_ssd  | 16GB  | IOPS: 40K\nlatency: 10us  | 40K              | 10us
 nvme_ssd  | 32GB  | IOPS: 60K\nlatency: 10us  | 60K              | 10us

Components:
- column: A tag or dtag; columns starting with '_tagit_data_' is dtag columns.
- row: Each recorded data as well as parsed results (in dtag columns)

'''


def external_name(name):
    if not name.startswith(exp_prefix):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return name[len(exp_prefix):]


def internal_name(exp_name):
    if utils.is_prohibited_name(exp_name):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return exp_prefix + exp_name


def exists(exp_name):
    name = internal_name(exp_name)
    if query.table_exists(name):
        return True

    return False


def get():
    tables = query.get_tables()
    exps = [external_name(x) for x in tables if utils.is_exp_name(x)]

    return exps


def _create(exp_name):
    name = internal_name(exp_name)
    query.create_table(name, [default_dtag])


def create(name):
    _create(name)
    taglist.create(name)
    dtaglist.create(name)
    parser.create(name)

    print(f"New experiment: [{name}]")


def delete(exp_name: str):
    name = internal_name(exp_name)
    validate(exp_name)

    query.drop_table(name)

    taglist.delete(exp_name)
    dtaglist.delete(exp_name)
    parser.delete(exp_name)

    print(f"Experiment deleted: {name}")


def _rename(old, new):
    query.rename_table(old, new)


def rename(exp_old, exp_new):
    # Check the exp existence
    validate(exp_old)

    # Abort if the new exp name already occupied
    if exists(exp_new):
        print(f"Error: {exp_new} already exists")
        sys.exit(-1)

    old = internal_name(exp_old)
    new = internal_name(exp_new)

    _rename(old, new)
    dtaglist.rename(exp_old, exp_new)
    parser.rename(exp_old, exp_new)
    taglist.rename(exp_old, exp_new)


def get_data(exp_name, params, dtags):
    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    name = internal_name(exp_name)

    tags = taglist.get_tags(exp_name)
    if dtags[0] == "*":
        dtags = dtaglist.get_dtags(exp_name)
    conds = params
    cols = tags + dtags
    entities = query.get_entities(name, conds, cols)

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


def add_data(exp_name, params, dtags, data):
    name = internal_name(exp_name)

    existing = query.get_entities(name, params, [])
    if len(existing) != 0:
        print("Warning: data overwritten")
        query.delete_rows(name, params)

    entity = OrderedDict()
    for key, mvalue in params.items():
        entity[key] = mvalue[0]
    for dtag in dtags:
        entity[dtag] = data

    query.add_entity(name, entity)

    # Mark updated data categories for lazy parsing
    dtaglist.mark_dtags_updated(exp_name, dtags)


def _append_data(name, params, dtag, data):
    query.append_row(name, params, {dtag: data})


def delete_data(exp_name: str, params: OrderedDict()):
    name = internal_name(exp_name)
    query.delete_rows(name, params)


def update_tags(exp_name, params):
    name = internal_name(exp_name)

    vars_ = list(params.keys())
    curr_vars = query.get_columns(name)
    new_params = {}

    for k, v in params.items():
        if k not in curr_vars:
            new_params[k] = v

    if new_params:
        # TODO: Show warning if a data exists before a new variable is added
        taglist.add_tags(exp_name, new_params)
        query.new_columns(name, new_params.keys())

        print(f"[{exp_name}] New tag added:")
        for key in new_params:
            print(f"- {key}")


def update_tag_values(exp_name: str, params: OrderedDict(), uparams: OrderedDict()):
    name = internal_name(exp_name)

    # Update if new variable added
    update_tags(exp_name, uparams)

    # Abort if the record with the same tags already exists
    params_after = utils.param_after_update(params, uparams)
    existing = query.get_entities(name, params_after, [])
    if len(existing) != 0:
        print("Error: conflict with existing record")
        sys.exit(-1)

    uparams_ = OrderedDict((k, [v]) for (k, v) in uparams.items())

    # Update tags
    query.update_row(name, params, uparams)


def update_dtags(exp_name, dtags, derived=False):
    name = internal_name(exp_name)

    curr_cols = query.get_columns(name)
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_cols:
            new_dtags.append(dtag)

    query.new_columns(name, new_dtags)

    dtaglist.update(exp_name, dtags, derived)

    if new_dtags:
        print(f"[{exp_name}] New data category: ")
        for dtag in new_dtags:
            dtag_name = utils.dtag_name(dtag)
            print(f"- {dtag_name}")


def clear_dtag(exp_name, dtag):
    name = internal_name(exp_name)
    query.update_row(name, {}, {dtag: ""})


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


def _run_parsing_rule(exp_name, src, dest, cmd):
    name = internal_name(exp_name)

    records = query.get_entities(name, {}, [])
    for record in records:
        data = record[src]
        params = OrderedDict((k, [v]) for (k, v) in record.items() \
                if not utils.is_prohibited_name(k))
        parsed = parser.parse_data(exp_name, src, dest, cmd, params, data)
        _append_data(name, params, dest, parsed)


def _run_backward_each_node(exp_name, graph, dtags, node):
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
        need_update |= _run_backward_each_node(exp_name, graph, dtags, src)

    if need_update:
        clear_dtag(exp_name, node)
        for edge in edges:
            src = edge["src"]
            cmd = edge["cmd"]
            _run_parsing_rule(exp_name, src, node, cmd)

    dtags[node]["up-to-date"] = True
    return need_update


def _run_backward_each_leaf(exp_name, graph, dtags, leaf):
    _run_backward_each_node(exp_name, graph, dtags, leaf)


def run_parsing_graph_backward(exp_name, graph, dtags):
    if not graph or not dtags:
        return

    leaves = [x for x in dtags]
    for dtag, edges in graph.items():
        for edge in edges:
            src = edge["src"]
            if src in leaves:
                leaves.remove(src)

    for leaf in leaves:
        _run_backward_each_leaf(exp_name, graph, dtags, leaf)


def run_parser(exp_name):
    parsing_graph = parser.build_parsing_graph(exp_name)
    dtag_status = dtaglist.get_status(exp_name)
    run_parsing_graph_backward(exp_name, parsing_graph, dtag_status)
    # Reset 'updated' of each dtag to False
    dtaglist.reset_status(exp_name)
    parser.reset_status(exp_name)


def rename_tag(exp_name, old, new):
    name = internal_name(exp_name)

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

    curr_tags = [x for x in query.get_columns(name) if not utils.is_dtag(x)]
    if old not in curr_tags or new in curr_tags:
        print("Internal error: experiment-taglist incoherent")
        sys.exit(-1)

    # Update taglist
    taglist.rename_tag(exp_name, old, new)

    # Update experiment table
    query.rename_column(name, old, new)
