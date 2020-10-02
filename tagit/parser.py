from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import subprocess
import sys


def exists(exp_name):
    name = utils.mkup_parser_name(exp_name)
    if query.table_exists(name):
        return True

    return False


def create(exp_name):
    name = utils.mkup_parser_name(exp_name)
    query.create_table(name, ["rule", "src_dtag", "dest_dtag", "updated"])


def delete(exp_name):
    validate(exp_name)
    name = utils.mkup_parser_name(exp_name)
    query.drop_table(name)


def rename(old_exp_name, new_exp_name):
    old_name = utils.mkup_parser_name(old_exp_name)
    new_name = utils.mkup_parser_name(new_exp_name)

    query._rename_table(old_name, new_name)


def validate(exp_name):
    if not exists(exp_name):
        print("Internal error: no such parser")
        sys.exit(-1)


def reset_status(exp_name: str):
    parser_name = utils.mkup_parser_name(exp_name)
    if not exists(exp_name):
        return

    query._update_row(parser_name, {}, {"updated": "False"})


def build_parsing_graph(exp_name: str):
    parser_name = utils.mkup_parser_name(exp_name)
    if not exists(exp_name):
        return {}

    graph = {}
    rules = query._get_entities(parser_name, {}, [])
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
