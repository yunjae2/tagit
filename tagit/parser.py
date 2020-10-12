from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import subprocess
import sys

'''
parser table

Table name: _tagit_parser_{name}

Desc: Maintains metadata for parsing rules

Layout:

             rule             |    src_dtag     |      dest_dtag      | updated
------------------------------+-----------------+---------------------+--------
 awk '/^IOPS/{print \$NF}'    | _tagit_data_raw | _tagit_data_iops    | False
 awk '/^latency/{print \$NF}' | _tagit_data_raw | _tagit_data_latency | True

Columns:
- name: The name of a tag
- src_dtag: The source dtag from which the rule will get input
- dest_dtag: The destination dtag to which the rule output will be saved
- updated: Has the rule been updated or newly added since the last parsing,
           so the parsing rules affected by the rule cannot skip during report?

'''


def parser_id(exp_name: str) -> str:
    if utils.is_prohibited_name(exp_name):
        print("Interal error: wrong exp_name format")
        sys.exit(-1)

    return parser_prefix + exp_name


def is_parser_id(table: str) -> bool:
    if table.startswith(parser_prefix):
        return True

    return False


def _exists(pid):
    if query.table_exists(pid):
        return True

    return False


def exists(exp_name):
    pid = parser_id(exp_name)
    return _exists(pid)


def _create(pid):
    query.create_table(pid, ["rule", "src_dtag", "dest_dtag", "updated"])


def create(exp_name):
    pid = parser_id(exp_name)
    _create(pid)


def get(exp_name):
    pid = parser_id(exp_name)

    if _exists(pid):
        data = query.get_entities(pid, {}, [])
    else:
        data = []

    return data


def add(exp_name, rule, dtag_src, dtag_dest):
    pid = parser_id(exp_name)

    # Create parser for the experiment if it has not been created yet
    if not _exists(pid):
        _create(pid)

    params = OrderedDict([
        ("rule", rule),
        ("src_dtag", dtag_src),
        ("dest_dtag", dtag_dest),
        ("updated", "True")
        ])
    query.add_entity(pid, params)


def _delete(pid):
    _validate(pid)
    query.drop_table(pid)


def delete(exp_name):
    pid = parser_id(exp_name)
    _delete(pid)


def rename(old_exp_name, new_exp_name):
    old_pid = parser_id(old_exp_name)
    new_pid = parser_id(new_exp_name)

    query.rename_table(old_pid, new_pid)


def _validate(pid):
    if not _exists(pid):
        print("Internal error: no such parser")
        sys.exit(-1)


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such parser")
        sys.exit(-1)


def reset_status(exp_name: str):
    pid = parser_id(exp_name)
    if not _exists(pid):
        return

    query.update_row(pid, {}, {"updated": "False"})


def build_parsing_graph(exp_name: str):
    pid = parser_id(exp_name)
    if not _exists(pid):
        return {}

    updated_global = False
    graph = {}
    rules = query.get_entities(pid, {}, [])
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

        updated_global |= updated == "True"

    return graph, updated_global


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

    pid = parser_id(exp_name)
    query.delete_rows(pid, OrderedDict([]), offset=rule_id, limit=1)


def remove_all_rules(exp_name):
    pid = parser_id(exp_name)
    query.delete_rows(pid, OrderedDict([]))
