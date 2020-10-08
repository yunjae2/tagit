from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import subprocess
import sys


def _exists(name):
    if query.table_exists(name):
        return True

    return False


def exists(exp_name):
    name = utils.mkup_parser_name(exp_name)
    return _exists(name)


def _create(name):
    query.create_table(name, ["rule", "src_dtag", "dest_dtag", "updated"])


def create(exp_name):
    name = utils.mkup_parser_name(exp_name)
    _create(name)


def get(exp_name):
    name = utils.mkup_parser_name(exp_name)

    if _exists(name):
        data = query.get_entities(name, {}, [])
    else:
        data = []

    return data


def add(exp_name, rule, dtag_src, dtag_dest):
    name = utils.mkup_parser_name(exp_name)

    # Create parser for the experiment if it has not been created yet
    if not _exists(name):
        _create(name)

    params = OrderedDict([
        ("rule", rule),
        ("src_dtag", dtag_src),
        ("dest_dtag", dtag_dest),
        ("updated", "True")
        ])
    query.add_entity(name, params)


def _delete(name):
    _validate(name)
    query.drop_table(name)


def delete(exp_name):
    name = utils.mkup_parser_name(exp_name)
    _delete(name)


def rename(old_exp_name, new_exp_name):
    old_name = utils.mkup_parser_name(old_exp_name)
    new_name = utils.mkup_parser_name(new_exp_name)

    query.rename_table(old_name, new_name)


def _validate(name):
    if not _exists(name):
        print("Internal error: no such parser")
        sys.exit(-1)


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such parser")
        sys.exit(-1)


def reset_status(exp_name: str):
    name = utils.mkup_parser_name(exp_name)
    if not _exists(name):
        return

    query.update_row(name, {}, {"updated": "False"})


def build_parsing_graph(exp_name: str):
    name = utils.mkup_parser_name(exp_name)
    if not _exists(name):
        return {}

    graph = {}
    rules = query.get_entities(name, {}, [])
    for rule in rules:
        src = rule['src_dtag']
        dest = rule['dest_dtag']
        cmd = rule['rule']
        updated = rule['updated']
        edge = {'src': src, 'cmd': cmd, 'updated': updated}

        if dest in graph:
            graph[dest].append(edge)
        else:
            graph[dest] = [edge]

    return graph


def parse_data(exp_name, src, dest, cmd, params, data):
    if data is None:
        return "\n"

    try:
        ret = subprocess.run(cmd, input=data, capture_output=True,
                shell=True, text=True)
    except TypeError:
        # Python < 3.7
        ret = subprocess.run(cmd, input=data, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=True, universal_newlines=True)

    ret_stdout = ret.stdout
    ret_stderr = ret.stderr

    if ret_stderr:
        if ret_stderr.endswith('\n'):
            ret_stderr = ret_stderr[:-1]
        print(ret_stderr)

    return ret_stdout


def remove_rule(exp_name, rule_id):
    # TODO: support multi-valued rule_id
    if rule_id is None:
        print("Error: no parsing rule id is provided")
        sys.exit(-1)

    name = utils.mkup_parser_name(exp_name)
    query.delete_rows(name, OrderedDict([]), offset=rule_id, limit=1)


def remove_all_rules(exp_name):
    name = utils.mkup_parser_name(exp_name)
    query.delete_rows(name, OrderedDict([]))
