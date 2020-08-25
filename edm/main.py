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
    param_str = args.p
    command = args.command

    # TODO: Implement tee-like functionality
    ret = subprocess.run(command, capture_output=True, text=True)

    params = utils.param_dict(param_str)

    # Include also stderr? I think it is not our responsibility.
    record_data(exp_name, params, ret.stdout.rstrip())
    print(ret.stdout.rstrip())
    if ret.stderr.strip():
        print(ret.stderr.strip())


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
    param_str = args.p
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


def manager(args):
    # TODO: Implement the body
    # Features
    # 1. add a variable
    # 2. set the default value for a variable
    # 3. manipulate recorded data
    # 4. remove an experiment
    # 5. set argument order
    exp_name = args.e

    print(args)


def parse_args():
    # TODO: Implement the body
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    # Record command
    rec_parser = subparsers.add_parser('record')
    rec_parser.add_argument('-e', type=str, required = True,
            metavar='exp_name', help='experiment name')
    rec_parser.add_argument('-p', type=str, required = True,
            metavar='params', help='parameters')
    # TODO: Fix command in help message (not displayed)
    rec_parser.add_argument('command', nargs=argparse.REMAINDER, type=str,
            help='command to execute')
    rec_parser.set_defaults(worker=recorder)

    # Report command
    rep_parser = subparsers.add_parser('report')
    rep_parser.add_argument('-e', type=str, required = True,
            metavar='exp_name', help='experiment name')
    rep_parser.add_argument('-p', type=str, required = True,
            metavar='params', help='parameters')
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
    man_parser.set_defaults(worker=manager)

    args = parser.parse_args()
    # TODO: print usage if no subcommand is provided
    return args.worker, args


def main():
    # TODO: Implement the body
    worker, args = parse_args()
    worker(args)


if __name__ == '__main__':
    main()
