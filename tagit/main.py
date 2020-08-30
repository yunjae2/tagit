from . import query
from . import utils
from .configs import *
import subprocess
import os
import sys
import argparse
import csv
from collections import OrderedDict

"""
Notation
exp: experiment
var: variable
"""
# TODO: Deal with default var values


def exp_exists(name):
    if query.table_exists(name):
        return True
    return False


def create_exp(name):
    query.create_table(name)
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


def update_dtags(name, dtags):
    curr_cols = query.get_columns(name)
    new_dtags = []

    for dtag in dtags:
        if dtag not in curr_cols:
            new_dtags.append(dtag)

    query.new_columns(name, new_dtags)

    if new_dtags:
        print(f"[{name}] New data category: ")
        for dtag in new_dtags:
            dtag_name = utils.dtag_name(dtag)
            print(f"- {dtag_name}")


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


def validate_record_params(params, dtags):
    for key in params.keys():
        if utils.is_dtag(key):
            print(f"Error: tag name cannot start with {dtag_prefix}")
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

    for dtag in dtags:
        if dtag == "*":
            print("Error: wildcard category is not allowed when recording")
            sys.exit(-1)
        elif not utils.is_dtag(dtag):
            print("Internal error: wrong dtag format")
            sys.exit(-1)


def recorder(args):
    # Features
    # Filter using pattern?
    #   - this can be handled in command! its not our responsibility
    exp_name = args.exp_name
    param_str = args.tags
    command = args.command
    stream = args.stream
    dtag_name_str = args.d

    params = utils.param_dict(param_str)
    dtags = utils.mkup_dtag(dtag_name_str)
    validate_record_params(params, dtags)

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
    ret = subprocess.run(command, stdout=stdout, stderr=stderr, text=True)

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
            base_path = os.path.join(base_path, f"{key}-{value}")

        for key, value in dtag_data.items():
            # TODO: extension?
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
            if first:
                first = False
                data_string = data_string + f"- {dtag_name}: {value}"
            else:
                data_string = data_string + f"\n- {dtag_name}: {value}"

        print(param_string)
        print(data_string)


def check_exp_exists(exp_name):
    exps = query.get_tables()
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
    dtags = utils.mkup_dtag(dtag_name_str)

    check_exp_exists(exp_name)
    validate_params(exp_name, params, dtags)

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
    query.drop_table(exp_name)


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
        validate_params(exp_name, params)
        delete_data(exp_name, params)


def list_exps():
    exps = query.get_tables()
    for exp in exps:
        print(exp)


def list_vars(exp_name):
    cols = query.get_columns(exp_name)
    params = [x for x in cols if not utils.is_dtag(x)]
    for param in params:
        print(param)


def lister(args):
    # Features
    # 1. List experiment names
    # 2. List variable names in an experiment
    exp_name = args.exp_name

    if exp_name:
        check_exp_exists(exp_name)
        list_vars(exp_name)
    else:
        list_exps()


def import_dump(filename):
    query.import_dump(filename)


def importer(args):
    filename = args.db_dump
    import_dump(filename)


def dump_all(filename):
    query.dump_db(filename)


def exporter(args):
    filename = args.output_dump
    dump_all(filename)


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
            help='output stream to record')
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

    # TODO: Add parse command

    # List command
    # TODO: Add category list option
    list_parser = subparsers.add_parser('list', help='list experiments or tags')
    list_parser.add_argument('exp_name', type=str, nargs='?',
            help='experiment name')
    list_parser.set_defaults(worker=lister)

    # Import command
    imp_parser = subparsers.add_parser('import', help='import data')
    imp_parser.add_argument('db_dump', type=str,
            help='input dump file (format: sql script)')
    # TODO: Import from csv / file hierarchy
    imp_parser.set_defaults(worker=importer)

    # Export command
    exp_parser = subparsers.add_parser('export', help='export data')
    exp_parser.add_argument('output_dump', type=str,
            help='output file name to dump (format: sql script)')
    exp_parser.set_defaults(worker=exporter)

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
