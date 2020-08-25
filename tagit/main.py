from . import query
from . import utils
import subprocess
import os
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


def update_vars(name, params):
    vars_ = list(params.keys())
    curr_vars = query.get_columns(name)
    new_vars = []

    for var in vars_:
        if var not in curr_vars:
            new_vars.append(var)

    # TODO: Show warning if a data exists before a new variable is added
    query.new_columns(name, new_vars)


def record_data(exp_name, params, data):
    # Create experiment if it does not exist
    if not exp_exists(exp_name):
        create_exp(exp_name)

    # Update if new variable added
    update_vars(exp_name, params)

    # TODO: Show warning if the data already exists
    # The new data is recorded while the old data is kept as well

    # Record data to the experiment
    query.add_entity(exp_name, params, data)


def recorder(args):
    # Features
    # Filter using pattern?
    #   - this can be handled in command! its not our responsibility
    exp_name = args.e
    param_str = args.t
    command = args.command

    # TODO: Implement tee-like functionality
    ret = subprocess.run(command, capture_output=True, text=True)

    params = utils.param_dict(param_str)

    stdout = ret.stdout
    stderr = ret.stderr
    if stdout.endswith('\n'):
        stdout = stdout[:-1]
    if stderr.endswith('\n'):
        stderr = stderr[:-1]

    # Include also stderr? I think it is not our responsibility.
    record_data(exp_name, params, stdout)

    print(stdout)
    if stderr:
        print(stderr)


def report_csv(exp_name: str, params: OrderedDict, data: [], filename: str):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data_single in data:
            writer.writerow(data_single)


def report_hrchy(exp_name: str, params: OrderedDict, data: [], path: str):
    for data_single in data:
        data_value = data_single.pop('_data', None)
        file_path = os.path.join(path, f"{exp_name}")
        for key, value in data_single.items():
            file_path = os.path.join(file_path, f"{key}-{value}")
        # TODO: extension?
        file_path = os.path.join(file_path, "data")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(data_value)


def report_std(exp_name: str, params: OrderedDict, data: []):
    for data_single in data:
        data_value = data_single.pop('_data', None)
        param_string = f'[EDM] exp: {exp_name}\n'
        param_string += f'[EDM] param: '

        first = True
        for key in data_single:
            if first:
                param_string += f'{key} = {data_single[key]}'
                first = False
            else:
                param_string += f', {key} = {data_single[key]}'

        print(param_string)
        print(data_value)


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

    exp_name = args.e
    param_str = args.t
    csv_file = args.csv
    hrchy_path = args.f

    params = utils.param_dict(param_str)
    data = query.get_entities(exp_name, params)

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
    exp_name = args.e
    delete = args.d
    delete_param_str = args.r

    if delete:
        delete_exp(exp_name)

    elif delete_param_str:
        params = utils.param_dict(delete_param_str)
        delete_data(exp_name, params)


def list_exps():
    exps = query.get_tables()
    for exp in exps:
        print(exp)


def list_vars(exp_name):
    params = query.get_columns(exp_name)
    params.remove('_data')
    for param in params:
        print(param)


def lister(args):
    # Features
    # 1. List experiment names
    # 2. List variable names in an experiment
    exp_name = args.e

    if exp_name:
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
    subparsers = parser.add_subparsers(title='subcommands')

    # Record command
    rec_parser = subparsers.add_parser('record')
    rec_parser.add_argument('-e', type=str, required = True,
            metavar='exp_name', help='experiment name')
    rec_parser.add_argument('-t', type=str, required = True,
            metavar='tags', help='tags')
    # TODO: Fix command in help message (not displayed)
    rec_parser.add_argument('command', nargs=argparse.REMAINDER, type=str,
            help='command to execute')
    rec_parser.set_defaults(worker=recorder)

    # Report command
    rep_parser = subparsers.add_parser('report')
    rep_parser.add_argument('-e', type=str, required = True,
            metavar='exp_name', help='experiment name')
    rep_parser.add_argument('-t', type=str, default = "",
            metavar='tags', help='tags')
    rep_parser.add_argument('-c', '--csv', type=str, nargs='?',
            const='_use_exp_name.csv', metavar='csv_file',
            help='Save result in csv_file in csv format')
    # TODO: Add spreadsheet option (1. copy to clipboard, 2. save as .xlsx)
    # TODO: Add directory hierarchy option (the order of params
    # is set by params argument)
    rep_parser.add_argument('-f', type=str, metavar='path',
            help='Save results in hierarchical files')
    rep_parser.set_defaults(worker=reporter)

    # Manage command
    man_parser = subparsers.add_parser('manage')
    man_parser.add_argument('-e', type=str, required = True,
            metavar='exp_name', help='experiment name')
    man_parser.add_argument('-d', action='store_true',
            help='delete an experiment')
    # TODO: Add row removal option
    man_parser.add_argument('-r', type=str,
            metavar='tags', help='delete rows with specified tags')
    # TODO: Add default value option
    man_parser.set_defaults(worker=manager)

    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('-e', type=str,
            metavar='exp_name', help='experiment name')
    list_parser.set_defaults(worker=lister)

    imp_parser = subparsers.add_parser('import')
    imp_parser.add_argument('db_dump', type=str,
            help='input dump file')
    # TODO: Import from csv / file hierarchy
    imp_parser.set_defaults(worker=importer)

    exp_parser = subparsers.add_parser('export')
    exp_parser.add_argument('output_dump', type=str,
            help='output file name to dump')
    exp_parser.set_defaults(worker=exporter)

    args = parser.parse_args()
    # TODO: print usage if no subcommand is provided
    return args.worker, args


def main():
    # TODO: Implement the body
    worker, args = parse_args()
    worker(args)


if __name__ == '__main__':
    main()