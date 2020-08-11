import query
import subprocess
import os
import argparse

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

    # Convert param_str: str() -> params: {}
    params = dict(item.split("=") for item in param_str.split(","))
    params = {k.strip(): v.strip() for k, v in params.items()}

    # TODO: Include also stderr? I think it is not our responsibility.
    record_data(exp_name, params, ret.stdout)
    print(ret.stdout.strip())
    print(ret.stderr.strip())


def reporter(args):
    # TODO: Implement the body
    # Features
    # 1. refining data to report
    #   - regex
    # 2. Export results
    #   - terminal
    #   - csv
    #   - spreadsheet (MS Excel, Google spreadsheet)

    exp_name = args.e
    params = args.p
    print(params)


def manager(args):
    # TODO: Implement the body
    # Features
    # 1. add a variable
    # 2. set the default value for a variable
    # 3. manipulate recorded data
    # 4. remove an experiment
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
