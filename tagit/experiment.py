from .configs import *
from . import query
from . import utils
from . import parser
from . import taglist
from . import dtaglist
from collections import OrderedDict
import sys


def exists(name):
    if query.table_exists(name):
        return True
    return False


def get():
    tables = query.get_tables()
    exps = [x for x in tables if utils.is_exp_name(x)]

    return exps


def _create(name):
    query.create_table(name, [default_dtag])


def create(name):
    _create(name)
    taglist.create(name)
    dtaglist.create(name)
    parser.create(name)

    print(f"New experiment: [{name}]")


def delete(name: str):
    validate(name)

    query.drop_table(name)

    taglist.delete(name)
    dtaglist.delete(name)
    parser.delete(name)

    print(f"Experiment deleted: {name}")


def _rename(old, new):
    query._rename_table(old, new)


def rename(old, new):
    # Check the exp existence
    validate(old)

    # Abort if the new exp name already occupied
    if exists(new):
        print(f"Error: {new} already exists")
        sys.exit(-1)

    _rename(old, new)
    dtaglist.rename(old, new)
    parser.rename(old, new)
    taglist.rename(old, new)


def get_data(name, params, dtags):
    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    data = query.get_entities(name, params, dtags)
    for dat in data:
        for key in dat:
            if dat[key] == None:
                dat[key] = ""

    return data


def add_data(exp_name, params, dtags, data):
    query.add_entity(exp_name, params, dtags, data)

    # Mark updated data categories for lazy parsing
    dtaglist.mark_dtags_updated(exp_name, dtags)


def _append_data(exp_name, params, dtag, data):
    query._append_row(exp_name, params, {dtag: data})


def delete_data(exp_name: str, params: OrderedDict()):
    query.delete_rows(exp_name, params)


def update_tags(name, params):
    vars_ = list(params.keys())
    curr_vars = query.get_columns(name)
    new_params = {}

    for k, v in params.items():
        if k not in curr_vars:
            new_params[k] = v

    if new_params:
        # TODO: Show warning if a data exists before a new variable is added
        taglist.add_tags(name, new_params)
        query.new_columns(name, new_params.keys())

        print(f"[{name}] New tag added:")
        for key in new_params:
            print(f"- {key}")


def update_tag_values(exp_name: str, params: OrderedDict(), uparams: OrderedDict()):
    # Update if new variable added
    update_tags(exp_name, uparams)

    # Abort if the record with the same tags already exists
    params_after = utils.param_after_update(params, uparams)
    existing = query._get_entities(exp_name, params_after, [])
    if len(existing) != 0:
        print("Error: conflict with existing record")
        sys.exit(-1)

    uparams_ = OrderedDict((k, [v]) for (k, v) in uparams.items())

    # Update tags
    query._update_row(exp_name, params, uparams)


def update_dtags(name, dtags, derived=False):
    curr_cols = query.get_columns(name)
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_cols:
            new_dtags.append(dtag)

    query.new_columns(name, new_dtags)

    dtaglist.update(name, dtags, derived)

    if new_dtags:
        print(f"[{name}] New data category: ")
        for dtag in new_dtags:
            dtag_name = utils.dtag_name(dtag)
            print(f"- {dtag_name}")


def clear_dtag(exp_name, dtag):
    query._update_row(exp_name, {}, {dtag: ""})


def validate(name):
    exps = get()
    if name not in exps:
        print("Error: no such experiment")
        print("List of experiments:")
        for exp in exps:
            print(f"- {exp}")

        sys.exit(-1)


def _list():
    exps = get()
    for exp in exps:
        print(exp)


def _run_parsing_rule(exp_name, src, dest, cmd):
    records = query._get_entities(exp_name, {}, [])
    for record in records:
        data = record[src]
        params = OrderedDict((k, [v]) for (k, v) in record.items() \
                if not utils.is_prohibited_name(k))
        parsed = parser.parse_data(exp_name, src, dest, cmd, params, data)
        _append_data(exp_name, params, dest, parsed)


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


def run_parser(name):
    parsing_graph = parser.build_parsing_graph(name)
    dtag_status = dtaglist.get_status(name)
    run_parsing_graph_backward(name, parsing_graph, dtag_status)
    # Reset 'updated' of each dtag to False
    dtaglist.reset_status(name)
    parser.reset_status(name)
