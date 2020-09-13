from . import query
from . import utils
from .configs import *
import subprocess
import os
import sys
import argparse
import csv
import shutil
from tabulate import tabulate
from collections import OrderedDict

"""
Notation
exp: experiment
var: variable
"""
# TODO: Deal with default var values


def get_exps():
    tables = query.get_tables()
    exps = [x for x in tables if utils.is_exp_name(x)]

    return exps


def exp_exists(name):
    if query.table_exists(name):
        return True
    return False


def create_exp(name):
    parser_name = utils.mkup_parser_name(name)
    query.create_table(name, [default_dtag])
    create_parser(parser_name)
    print(f"New experiment: [{name}]")


def update_vars(name, params):
    vars_ = list(params.keys())
    curr_vars = query.get_columns(name)
    new_vars = []

    for var in vars_:
        if var not in curr_vars:
            new_vars.append(var)

    # TODO: Show warning if a data exists before a new variable is added
    query.new_columns(name, new_vars)

    if new_vars:
        print(f"[{name}] New tag added:")
        for var in new_vars:
            print(f"- {var}")


def dtag_list_exists(name):
    if query.table_exists(name):
        return True
    return False


def create_dtag_list(name):
    query.create_table(name, ["name", "derived", "updated"])


def update_dtag_list(name, dtags, derived):
    dtag_list_name = utils.mkup_dtag_list_name(name)

    if not dtag_list_exists(dtag_list_name):
        create_dtag_list(dtag_list_name)

    curr_dtag_list = query._get_entities(dtag_list_name, {}, ["name", "derived"])
    curr_dtags = [x["name"] for x in curr_dtag_list]
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_dtags:
            new_dtags.append({
                "name": dtag,
                "derived": str(derived),
                "updated": "False"
                })

    _validate_dtags_derived(curr_dtag_list, dtags, derived)
    query._add_entities(dtag_list_name, new_dtags)


def update_dtags(name, dtags, derived=False):
    curr_cols = query.get_columns(name)
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_cols:
            new_dtags.append(dtag)

    query.new_columns(name, new_dtags)

    update_dtag_list(name, dtags, derived)

    if new_dtags:
        print(f"[{name}] New data category: ")
        for dtag in new_dtags:
            dtag_name = utils.dtag_name(dtag)
            print(f"- {dtag_name}")


def mark_dtags_updated(exp_name, dtags):
    dtag_list_name = utils.mkup_dtag_list_name(exp_name)
    cond_vals = [({"name": x}, {"updated": "True"}) for x in dtags]
    query._update_rows(dtag_list_name, cond_vals)


def record_data(exp_name, params, dtags, data):
    # Create experiment if it does not exist
    if not exp_exists(exp_name):
        create_exp(exp_name)

    # Update if new variable added
    update_vars(exp_name, params)
    update_dtags(exp_name, dtags)

    # TODO: Show warning if the data already exists
    # The new data is recorded while the old data is kept as well

    # Record data to the experiment
    query.add_entity(exp_name, params, dtags, data)

    # Mark updated data categories for lazy parsing
    mark_dtags_updated(exp_name, dtags)


def _validate_dtags_derived(curr_dtags, dtags, derived):
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



def validate_dtags_derived(name, dtags, derived):
    dtag_list_name = utils.mkup_dtag_list_name(name)

    if not dtag_list_exists(dtag_list_name):
        create_dtag_list(dtag_list_name)

    curr_dtags = query._get_entities(dtag_list_name, {}, ["name", "derived"])
    _validate_dtags_derived(curr_dtags, dtags, derived)


def validate_dtags(name, dtags, derived):
    # Validate dtag names
    bad_values = ["*", "|", ",", "\""]
    for dtag in dtags:
        if dtag == "*":
            print("Error: wildcard category is not allowed when recording")
            sys.exit(-1)
        elif not utils.is_dtag(dtag):
            print("Internal error: wrong dtag format")
            sys.exit(-1)

        for bad_value in bad_values:
            if bad_value in dtag:
                print(f"Error: the name of a category cannot contain '{bad_value}'")
                sys.exit(-1)

    validate_dtags_derived(name, dtags, derived)


def validate_record_params(exp_name, params, dtags):
    for key in params.keys():
        if utils.is_prohibited_name(key):
            print(f"Error: tag name cannot start with {tagit_prefix}")
            sys.exit(-1)

    bad_values = ["*", "|", ",", "\""]
    for mvalue in params.values():
        if len(mvalue) != 1:
            print(f"Error: multi-valued tag record detected")
            sys.exit(-1)
        value = mvalue[0]
        for bad_value in bad_values:
            if bad_value in value:
                print(f"Error: the value of a tag cannot contain '{bad_value}'")
                sys.exit(-1)

    validate_dtags(exp_name, dtags, derived=False)


def recorder(args):
    # Features
    # Filter using pattern?
    #   - this can be handled in command! its not our responsibility
    exp_name = args.exp_name
    param_str = args.tags
    command_args = args.command
    stream = args.stream
    dtag_name_str = args.d

    command = utils.mkup_command(command_args)
    params = utils.param_dict(param_str)
    dtags = utils.mkup_dtags(dtag_name_str)
    validate_record_params(exp_name, params, dtags)

    if stream == "all":
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT
    elif stream == "stdout":
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    elif stream == "stderr":
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    else:
        print("Internal bug; wrong stream format")
        sys.exit(-1)

    # TODO: Implement tee-like functionality
    ret = subprocess.run(command, stdout=stdout, stderr=stderr,
            shell=True, text=True)

    ret_stdout = ret.stdout
    ret_stderr = ret.stderr

    if ret_stdout:
        if ret_stdout.endswith('\n'):
            ret_stdout = ret_stdout[:-1]
        print(ret_stdout)
    if ret_stderr:
        if ret_stderr.endswith('\n'):
            ret_stderr = ret_stderr[:-1]
        print(ret_stderr)

    if stream == "all":
        data = ret_stdout
    elif stream == "stdout":
        data = ret_stdout
    elif stream == "stderr":
        data = ret_stderr
    else:
        print("Internal bug; wrong stream format")
        sys.exit(-1)

    record_data(exp_name, params, dtags, data)


def refine_dtag_names(data):
    refined = []
    for data_single in data:
        refined_single = OrderedDict()
        for key in data_single:
            value = data_single[key]
            if utils.is_dtag(key):
                dtag_name = utils.dtag_name(key)
                refined_single[dtag_name] = value
            else:
                refined_single[key] = value

        refined.append(refined_single)

    return refined


def report_csv(exp_name: str, params: OrderedDict, data: [], filename: str):
    data = refine_dtag_names(data)

    with open(filename, 'w', newline='') as csvfile:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data_single in data:
            writer.writerow(data_single)


def report_hrchy(exp_name: str, params: OrderedDict, data: [], path: str):
    for data_single in data:
        tag_data = OrderedDict((k, data_single[k]) for k in data_single \
                if not utils.is_dtag(k))
        dtag_data = OrderedDict((k, data_single[k]) for k in data_single \
                if utils.is_dtag(k))

        base_path = os.path.join(path, f"{exp_name}")
        for key, value in tag_data.items():
            base_path = os.path.join(base_path, f"{key}")
            base_path = os.path.join(base_path, f"{value}")

        for key, value in dtag_data.items():
            if value is None:
                value = ""
            dtag_name = utils.dtag_name(key)
            file_path = os.path.join(base_path, dtag_name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(value)


def report_std(exp_name: str, params: OrderedDict, data: []):
    for data_single in data:
        tag_data = OrderedDict((k, data_single[k]) for k in data_single \
                if not utils.is_dtag(k))
        dtag_data = OrderedDict((k, data_single[k]) for k in data_single \
                if utils.is_dtag(k))

        # Parameter
        param_string = f'[{exp_name}] ('

        first = True
        for key in tag_data:
            if first:
                param_string += f'{key}={data_single[key]}'
                first = False
            else:
                param_string += f', {key}={data_single[key]}'
        param_string += f')'

        # Data
        data_string = ""

        first = True
        for key in dtag_data:
            dtag_name = utils.dtag_name(key)
            value = dtag_data[key]
            if not value:
                value = ""
            elif value.endswith("\n"):
                value = value[:-1]

            if first:
                first = False
                data_string = data_string + f"- {dtag_name}: {value}"
            else:
                data_string = data_string + f"\n- {dtag_name}: {value}"

        print(param_string)
        print(data_string)


def check_exp_exists(exp_name):
    exps = get_exps()
    if exp_name not in exps:
        print("Error: no such experiment")
        print("List of experiments:")
        for exp in exps:
            print(f"- {exp}")

        sys.exit(-1)


def validate_params(exp_name, params, dtags):
    cols = query.get_columns(exp_name)
    tags = [x for x in cols if not utils.is_dtag(x)]
    curr_dtags = [x for x in cols if utils.is_dtag(x)]

    for param in params:
        if param not in tags:
            print("Error: no such tag")
            print(f"List of tags in {exp_name}:")
            for tag in tags:
                print(f"- {tag}")
            sys.exit(-1)

    cols = tags
    for dtag in dtags:
        if dtag == "*":
            continue
        if dtag not in curr_dtags:
            print("Error: no such category")
            print(f"List of categories in {exp_name}:")
            for curr_dtag in curr_dtags:
                dtag_name = utils.dtag_name(curr_dtag)
                print(f"- {dtag_name}")
            sys.exit(-1)


def reporter(args):
    # TODO: Implement the body
    # Features
    # 1. refining data to report
    #   - regex
    # 2. Export results
    #   - terminal
    #   - csv
    #   - hierarchical files
    #   - spreadsheet (MS Excel, Google spreadsheet)

    exp_name = args.exp_name
    param_str = args.tags
    csv_file = args.csv
    hrchy_path = args.f
    dtag_name_str = args.d

    params = utils.param_dict(param_str)
    dtags = utils.mkup_dtags(dtag_name_str)

    check_exp_exists(exp_name)
    validate_params(exp_name, params, dtags)

    # Lazy parsing
    run_parsing_graph(exp_name)

    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    data = query.get_entities(exp_name, params, dtags)

    if csv_file:
        if csv_file == "_use_exp_name.csv":
            csv_file = f"{exp_name}.csv"
        report_csv(exp_name, params, data, csv_file)
    elif hrchy_path:
        report_hrchy(exp_name, params, data, hrchy_path)
    else:
        report_std(exp_name, params, data)


def delete_data(exp_name: str, params: OrderedDict()):
    query.delete_rows(exp_name, params)


def delete_exp(exp_name: str):
    parser_name = utils.mkup_parser_name(exp_name)
    dtag_list_name = utils.mkup_dtag_list_name(exp_name)

    query.drop_table(exp_name)

    if parser_exists(parser_name):
        query.drop_table(parser_name)
    if dtag_list_exists(dtag_list_name):
        query.drop_table(dtag_list_name)


def manager(args):
    # TODO: Implement the body
    # Features
    # 1. add a variable
    # 2. set the default value for a variable
    # 3. remove rows with params specified
    # 4. regex pattern replace
    # 5. remove an experiment
    # 6. set argument order
    # 7. rename exp
    # 8. rename variable
    exp_name = args.exp_name
    delete = args.d
    delete_param_str = args.r

    check_exp_exists(exp_name)

    if delete:
        delete_exp(exp_name)

    elif delete_param_str:
        params = utils.param_dict(delete_param_str)
        validate_params(exp_name, params, [])
        delete_data(exp_name, params)


def list_exps():
    exps = get_exps()
    for exp in exps:
        print(exp)


def list_vars(exp_name):
    cols = query.get_columns(exp_name)
    params = [x for x in cols if not utils.is_dtag(x)]

    print(f"[{exp_name}] List of tags:")
    for param in params:
        print(f"- {param}")


def list_dtags(exp_name):
    # TODO: separate derived and not derived ones
    cols = query.get_columns(exp_name)
    dtags = [utils.dtag_name(x) for x in cols if utils.is_dtag(x)]

    print(f"[{exp_name}] List of data categories:")
    for dtag in dtags:
        print(f"- {dtag}")


def lister(args):
    # Features
    # 1. List experiment names
    # 2. List variable names in an experiment
    exp_name = args.exp_name

    if exp_name:
        check_exp_exists(exp_name)
        list_vars(exp_name)
        list_dtags(exp_name)
    else:
        list_exps()


def load_dump(filename, yes):
    exps = get_exps()
    if exps and not yes:
        answer = input("Existing records will be deleted; import? [y/N]: ")
        if answer.strip().lower() != "y":
            return

    print("Importing...")
    dirname = os.path.dirname(db_file)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    shutil.copyfile(filename, db_file)

    print("Import done")


def importer(args):
    filename = args.db_dump
    yes = args.y

    load_dump(filename, yes)


def dump_all(filename):
    query.dump_db(filename)


def exporter(args):
    filename = args.output_dump
    dump_all(filename)


def validate_src_dtag(exp_name, dtag_src):
    cols = query.get_columns(exp_name)
    curr_dtags = [x for x in cols if utils.is_dtag(x)]

    if dtag_src not in curr_dtags:
        print("Error: source data category does not exist")
        sys.exit(-1)


def parser_exists(parser_name) -> bool:
    if query.table_exists(parser_name):
        return True
    return False


def create_parser(parser_name):
    query.create_table(parser_name, ["rule", "src_dtag", "dest_dtag", "updated"])


def add_parsing_rule(exp_name, rule, dtag_src, dtag_dest):
    parser_name = utils.mkup_parser_name(exp_name)

    # Create parser for the experiment if it has not been created yet
    if not parser_exists(parser_name):
        create_parser(parser_name)

    params = OrderedDict([
        ("rule", rule),
        ("src_dtag", dtag_src),
        ("dest_dtag", dtag_dest),
        ("updated", "True")
        ])
    query._add_entity(parser_name, params)


def build_parsing_graph(exp_name: str):
    parser_name = utils.mkup_parser_name(exp_name)
    if not parser_exists(parser_name):
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


def get_dtag_status(exp_name: str):
    dtag_list_name = utils.mkup_dtag_list_name(exp_name)
    if not dtag_list_exists(dtag_list_name):
        return []

    curr_dtag_list = query._get_entities(dtag_list_name, {}, ["name", "updated"])
    dtag_status = OrderedDict((x["name"], {"updated": x["updated"] == "True", \
            "up-to-date": False}) for x in curr_dtag_list)

    return dtag_status


def parse_data(exp_name, src, dest, cmd, params, data):
    if data is None:
        return "\n"

    ret = subprocess.run(cmd, input=data, capture_output=True,
            shell=True, text=True)

    ret_stdout = ret.stdout
    ret_stderr = ret.stderr

    if ret_stderr:
        if ret_stderr.endswith('\n'):
            ret_stderr = ret_stderr[:-1]
        print(ret_stderr)

    return ret_stdout


def append_data(exp_name, params, dtag, new_data):
    query._append_row(exp_name, params, {dtag: new_data})


def run_parsing_rule(exp_name, src, dest, cmd):
    records = query._get_entities(exp_name, {}, [])
    for record in records:
        data = record[src]
        params = OrderedDict((k, v) for (k, v) in record.items() \
                if not utils.is_prohibited_name(k))
        parsed = parse_data(exp_name, src, dest, cmd, params, data)
        append_data(exp_name, params, dest, parsed)


def clear_dtag_data(exp_name, dtag):
    query._update_row(exp_name, {}, {dtag: ""})


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
        clear_dtag_data(exp_name, node)
        for edge in edges:
            src = edge["src"]
            cmd = edge["cmd"]
            run_parsing_rule(exp_name, src, node, cmd)

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


def reset_dtag_status(exp_name: str):
    dtag_list_name = utils.mkup_dtag_list_name(exp_name)
    if not dtag_list_exists(dtag_list_name):
        return

    query._update_row(dtag_list_name, {}, {"updated": "False"})


def reset_rule_status(exp_name: str):
    parser_name = utils.mkup_parser_name(exp_name)
    if not parser_exists(parser_name):
        return

    query._update_row(parser_name, {}, {"updated": "False"})


def run_parsing_graph(exp_name):
    parsing_graph = build_parsing_graph(exp_name)
    dtag_status = get_dtag_status(exp_name)
    run_parsing_graph_backward(exp_name, parsing_graph, dtag_status)
    # Reset 'updated' of each dtag to False
    reset_dtag_status(exp_name)
    reset_rule_status(exp_name)


def parse_adder(args):
    exp_name = args.exp_name
    rule = args.rule
    dtag_name_dest = args.dest
    dtag_name_src = args.src

    dtag_dest = utils.mkup_dtag(dtag_name_dest)
    dtag_src = utils.mkup_dtag(dtag_name_src)

    if not exp_exists(exp_name):
        create_exp(exp_name)

    validate_src_dtag(exp_name, dtag_src)

    update_dtags(exp_name, [dtag_dest], derived=True)

    # Add parsing rule to experiment
    rule_id = add_parsing_rule(exp_name, rule, dtag_src, dtag_dest)


def list_rules(exp_name):
    parser_name = utils.mkup_parser_name(exp_name)

    if parser_exists(parser_name):
        data = query._get_entities(parser_name, {}, [])
    else:
        data = []

    headers = ["id", "rule", "src", "dest", "updated"]

    values = []
    for data_single in data:
        data_single_values = []
        for key, value in data_single.items():
            if utils.is_dtag(value):
                value = utils.dtag_name(value)
            data_single_values.append(value)
        values.append(data_single_values)

    print(tabulate(values, headers=headers, showindex="always"))


def parse_lister(args):
    exp_name = args.exp_name

    check_exp_exists(exp_name)
    list_rules(exp_name)


def remove_all_rules(exp_name):
    parser_name = utils.mkup_parser_name(exp_name)
    query._delete_rows(parser_name, OrderedDict([]))


def remove_rule(exp_name, rule_id):
    # TODO: support multi-valued rule_id
    if rule_id is None:
        print("Error: no parsing rule id is provided")
        sys.exit(-1)
    parser_name = utils.mkup_parser_name(exp_name)
    query._delete_rows(parser_name, OrderedDict([]), offset=rule_id, limit=1)


def parse_remover(args):
    exp_name = args.exp_name
    remove_all = args.all
    rule_id = args.rule_id

    check_exp_exists(exp_name)
    if remove_all:
        remove_all_rules(exp_name)
    else:
        remove_rule(exp_name, rule_id)


def reset_all(yes: bool):
    if not yes:
        answer = input("Existing data will be deleted; reset? [y/N]: ")
        if answer.strip().lower() != "y":
            return

    print("Resetting...")
    if os.path.exists(db_file):
        os.remove(db_file)

    print("Reset done")


def resetter(args):
    yes = args.y
    reset_all(yes)


def parse_args():
    # TODO: Implement the body
    parser = argparse.ArgumentParser()
    parser.set_defaults(worker=None)
    subparsers = parser.add_subparsers(title='subcommands')

    # Record command
    rec_parser = subparsers.add_parser('record', help='record data with tags')
    rec_parser.add_argument('exp_name', type=str, help='experiment name')
    rec_parser.add_argument('tags', type=str,
            help='"tags" (e.g., "arch=gpt3, train_set=stack_overflow, test_set=quora")')
    rec_parser.add_argument('command', nargs='+', type=str,
            help='command to execute')
    rec_parser.add_argument('-s', '--stream', type=str, default='all',
            metavar='stream', choices=['stdout', 'stderr', 'all'],
            help='output stream to record (choose from: stdout, stderr, all)')
    rec_parser.add_argument('-d', type=str, metavar='category', default='raw',
            help='data category to record into (not required in general cases)')
    rec_parser.set_defaults(worker=recorder)

    # Report command
    rep_parser = subparsers.add_parser('report', help='report data by tags')
    rep_parser.add_argument('exp_name', type=str, help='experiment name')
    rep_parser.add_argument('tags', type=str, nargs='?', default="",
            help='"tags" (e.g., "arch=gpt3, train_set=stack_overflow, test_set=quora")')
    rep_parser.add_argument('-c', '--csv', type=str, nargs='?',
            const='_use_exp_name.csv', metavar='csv_file',
            help='Save result in csv format (default: {exp_name}.csv)')
    # TODO: Add spreadsheet option (1. copy to clipboard, 2. save as .xlsx)
    rep_parser.add_argument('-f', type=str, metavar='path',
            help='Save results in hierarchical files')
    rep_parser.add_argument('-d', type=str, metavar='categories', default='*',
            help='data category to report (e.g., "latency, throughput")')
    rep_parser.set_defaults(worker=reporter)

    # Manage command
    man_parser = subparsers.add_parser('manage', help='manage recorded data and tags')
    man_parser.add_argument('exp_name', type=str, help='experiment name')
    man_parser.add_argument('-d', action='store_true',
            help='delete an experiment')
    man_parser.add_argument('-r', type=str, nargs='?', const=" ",
            metavar='tags', help='delete data with specified tags')
    # TODO: Add default value option
    man_parser.set_defaults(worker=manager)

    # TODO: Separate manage command and remove command
    # TODO: Add data category option to delete

    # Parse command
    par_parser = subparsers.add_parser('parse',
            help='parse recorded data into data categories')
    par_subparsers = par_parser.add_subparsers(title='subcommands')

    # Parse add command
    par_add_parser = par_subparsers.add_parser('add',
            help='add a parsing rule')
    par_add_parser.add_argument('exp_name', type=str, help='experiment name')
    par_add_parser.add_argument('dest', type=str,
            help='target data category to save parsing output to')
    par_add_parser.add_argument('rule', type=str,
            help='parsing rule (e.g., "awk /^latency/{print $NF}")')
    par_add_parser.add_argument('-s', '--src', type=str, metavar='src',
            default='raw', help='source data category to parse')
    par_add_parser.set_defaults(worker=parse_adder)

    # Parse list command
    par_list_parser = par_subparsers.add_parser('list',
            help='list current parsing rules')
    par_list_parser.add_argument('exp_name', type=str, help='experiment name')
    par_list_parser.set_defaults(worker=parse_lister)

    # Parse remove command
    par_rem_parser = par_subparsers.add_parser('remove',
            help='remove a parsing rule')
    par_rem_parser.add_argument('exp_name', type=str, help='experiment name')
    par_rem_parser.add_argument('rule_id', type=int, nargs='?',
            help='id of the parsing rule to remove')
    par_rem_parser.add_argument('-a', '--all', action='store_true',
            help='remove all rules')
    par_rem_parser.set_defaults(worker=parse_remover)

    # List command
    list_parser = subparsers.add_parser('list', help='list experiments or tags')
    list_parser.add_argument('exp_name', type=str, nargs='?',
            help='experiment name')
    list_parser.set_defaults(worker=lister)

    # Import command
    imp_parser = subparsers.add_parser('import', help='import data')
    imp_parser.add_argument('db_dump', type=str,
            help='input dump file')
    imp_parser.add_argument('-y', action="store_true",
            help='Automatic yes to prompts')
    # TODO: Import from csv / file hierarchy
    imp_parser.set_defaults(worker=importer)

    # Export command
    exp_parser = subparsers.add_parser('export', help='export data')
    exp_parser.add_argument('output_dump', type=str,
            help='output file name to dump')
    exp_parser.set_defaults(worker=exporter)

    # Reset command
    reset_parser = subparsers.add_parser('reset', help='reset tagit')
    reset_parser.add_argument('-y', action="store_true",
            help='Automatic yes to prompts')
    reset_parser.set_defaults(worker=resetter)

    args = parser.parse_args()

    if args.worker is None:
        parser.print_help()

    return args.worker, args


def main():
    worker, args = parse_args()
    if worker:
        worker(args)


if __name__ == '__main__':
    main()
