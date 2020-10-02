from . import query
from . import utils
from . import taglist
from . import dtaglist
from . import parser
from . import experiment
from .configs import *
import subprocess
import os
import sys
import argparse
import csv
import shutil
from tabulate import tabulate
from collections import OrderedDict


def record_data(exp_name, params, dtags, data):
    # Create experiment if it does not exist
    if not experiment.exists(exp_name):
        experiment.create(exp_name)

    # Update if new variable added
    experiment.update_tags(exp_name, params)
    experiment.update_dtags(exp_name, dtags)

    # Fill empty tags with default values
    params_ = taglist.mkup_record_params(exp_name, params)

    existing = query._get_entities(exp_name, params_, [])
    if len(existing) != 0:
        print("Warning: data overwritten")
        query._delete_rows(exp_name, params_)

    # Record data to the experiment
    experiment.add_data(exp_name, params_, dtags, data)


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

    if dtaglist.exists(name):
        dtaglist.validate_derived(name, dtags, derived)


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


def validate_unfix_params(exp_name, params):
    cols = query.get_columns(exp_name)
    tags = [x for x in cols if not utils.is_dtag(x)]

    for param in params:
        if param not in tags:
            print("Error: no such tag")
            print(f"List of tags in {exp_name}:")
            for tag in tags:
                print(f"- {tag}")
            sys.exit(-1)

    bad_values = ["|", ",", "\""]
    for mvalue in params.values():
        if mvalue[0] != "*" or len(mvalue) != 1:
            print(f"Error: tag value specified during unsetting")
            sys.exit(-1)


def validate_fix_params(exp_name, params):
    for key in params.keys():
        if utils.is_prohibited_name(key):
            print(f"Error: tag name cannot start with {tagit_prefix}")
            sys.exit(-1)

    bad_values = ["*", "|", ",", "\""]
    for mvalue in params.values():
        if len(mvalue) != 1:
            print(f"Error: tag value can only be set to single value")
            sys.exit(-1)
        value = mvalue[0]
        for bad_value in bad_values:
            if bad_value in value:
                print(f"Error: the value of a tag cannot contain '{bad_value}'")
                sys.exit(-1)


def validate_update_params(exp_name, params, uparams):
    cols = query.get_columns(exp_name)
    tags = [x for x in cols if not utils.is_dtag(x)]

    for param in params:
        if param not in tags:
            print("Error: no such tag")
            print(f"List of tags in {exp_name}:")
            for tag in tags:
                print(f"- {tag}")
            sys.exit(-1)

    for key in uparams.keys():
        if utils.is_prohibited_name(key):
            print(f"Error: tag name cannot start with {tagit_prefix}")
            sys.exit(-1)

    bad_values = ["*", "|", ",", "\""]
    for value in uparams.values():
        for bad_value in bad_values:
            if bad_value in value:
                print(f"Error: the value of a tag cannot contain '{bad_value}'")
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


def get_from_stdin(quiet: bool):
    if quiet:
        data = sys.stdin.read()
        if data:
            if data.endswith('\n'):
                data = data[:-1]
    else:
        data = ''
        for line in sys.stdin:
            data = data + line
            if line.endswith('\n'):
                line = line[:-1]
            print(line)

        if data.endswith('\n'):
            data = data[:-1]

    return data


def recorder(args):
    exp_name = args.exp_name
    param_str = args.tags
    dtag_name_str = args.d
    quiet = args.quiet

    params = utils.param_dict(param_str)
    dtags = utils.mkup_dtags(dtag_name_str)
    validate_record_params(exp_name, params, dtags)

    data = get_from_stdin(quiet)

    record_data(exp_name, params, dtags, data)


def _refine_dtag_names(data):
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
    data = _refine_dtag_names(data)

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

    experiment.validate(exp_name)
    validate_params(exp_name, params, dtags)

    # Lazy parsing
    experiment.run_parser(exp_name)

    # data: [{tag1: val1, tag2: val2, ..., dtag1: data1, ...}, {...}, ...]
    data = experiment.get_data(exp_name, params, dtags)

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
    # 3. remove rows with params specified
    # 4. regex pattern replace
    # 5. remove an experiment
    # 6. set argument order
    # 7. rename exp
    # 8. rename variable
    exp_name = args.exp_name
    delete = args.d
    delete_param_str = args.r

    experiment.validate(exp_name)

    if delete:
        experiment.delete(exp_name)

    elif delete_param_str:
        params = utils.param_dict(delete_param_str)
        validate_params(exp_name, params, [])
        experiment.delete_data(exp_name, params)


def list_vars(exp_name):
    def_params = taglist.default_params(exp_name)

    print(f"[{exp_name}] List of tags:")
    for k, v in def_params.items():
        if len(v) == 0:
            print(f"- {k}")
        else:
            print(f"- {k} (Fixed to: {v})")


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
        experiment.validate(exp_name)
        list_vars(exp_name)
        list_dtags(exp_name)
    else:
        experiment._list()


def load_dump(filename, yes):
    exps = experiment.get()
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


def add_parsing_rule(exp_name, rule, dtag_src, dtag_dest):
    parser_name = utils.mkup_parser_name(exp_name)

    # Create parser for the experiment if it has not been created yet
    if not parser.exists(exp_name):
        parser.create(parser_name)

    params = OrderedDict([
        ("rule", rule),
        ("src_dtag", dtag_src),
        ("dest_dtag", dtag_dest),
        ("updated", "True")
        ])
    query._add_entity(parser_name, params)


def parse_adder(args):
    exp_name = args.exp_name
    rule = args.rule
    dtag_name_dest = args.dest
    dtag_name_src = args.src

    dtag_dest = utils.mkup_dtag(dtag_name_dest)
    dtag_src = utils.mkup_dtag(dtag_name_src)

    if not experiment.exists(exp_name):
        experiment.create(exp_name)

    validate_src_dtag(exp_name, dtag_src)

    experiment.update_dtags(exp_name, [dtag_dest], derived=True)

    # Add parsing rule to experiment
    rule_id = add_parsing_rule(exp_name, rule, dtag_src, dtag_dest)


def list_rules(exp_name):
    parser_name = utils.mkup_parser_name(exp_name)

    if parser.exists(exp_name):
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

    experiment.validate(exp_name)
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

    experiment.validate(exp_name)
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


def tag_fixer(args):
    exp_name = args.exp_name
    param_str = args.tags

    params = utils.param_dict(param_str)
    validate_fix_params(exp_name, params)

    # Create experiment if it does not exist
    if not experiment.exists(exp_name):
        experiment.create(exp_name)

    # Update if new variable added
    experiment.update_tags(exp_name, params)

    taglist.set_default(exp_name, params)


def tag_unfixer(args):
    exp_name = args.exp_name
    param_str = args.tags

    experiment.validate(exp_name)

    params = utils.param_dict(param_str)
    validate_unfix_params(exp_name, params)

    taglist.unset_default(exp_name, params)


def rename_tag(exp_name, old, new):
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

    taglist.rename_tag(exp_name, old, new)


def exp_renamer(args):
    old_name = args.name
    new_name = args.new_name

    experiment.rename(old_name, new_name)


def tag_renamer(args):
    exp_name = args.exp_name
    old_name = args.name
    new_name = args.new_name

    experiment.validate(exp_name)

    rename_tag(exp_name, old_name, new_name)


def tag_updater(args):
    exp_name = args.exp_name
    param_str = args.tags

    experiment.validate(exp_name)

    params, uparams = utils.param_for_update(param_str)
    validate_update_params(exp_name, params, uparams)
    experiment.update_tag_values(exp_name, params, uparams)


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
    rec_parser.add_argument('-d', type=str, metavar='category', default='raw',
            help='data category to record into (not required in general cases)')
    rec_parser.add_argument('-q', '--quiet', action='store_true',
            help='record data quietly')
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
    # TODO: Move to exp subcommand
    man_parser.add_argument('-d', action='store_true',
            help='delete an experiment')
    man_parser.add_argument('-r', type=str, nargs='?', const=" ",
            metavar='tags', help='delete data with specified tags')
    man_parser.set_defaults(worker=manager)

    # TODO: Separate manage command and remove command
    # TODO: Add data category option to delete


    # exp command
    exp_parser = subparsers.add_parser('exp', help='manage experiments')
    exp_subparsers = exp_parser.add_subparsers(title='subcommands')

    # exp rename command
    exp_ren_parser = exp_subparsers.add_parser('rename', help='rename an experiment')
    exp_ren_parser.add_argument('name', type=str, help='current experiment name')
    exp_ren_parser.add_argument('new_name', type=str, help='new experiment name')
    exp_ren_parser.set_defaults(worker=exp_renamer)


    # tag command
    tag_parser = subparsers.add_parser('tag', help='manage tags')
    tag_subparsers = tag_parser.add_subparsers(title='subcommands')

    # tag rename command
    tag_ren_parser = tag_subparsers.add_parser('rename', help='rename a tag')
    tag_ren_parser.add_argument('exp_name', type=str, help='experiment name')
    tag_ren_parser.add_argument('name', type=str, help='current tag name')
    tag_ren_parser.add_argument('new_name', type=str, help='new tag name')
    tag_ren_parser.set_defaults(worker=tag_renamer)

    # tag fix command
    tag_fix_parser = tag_subparsers.add_parser('fix', help='fix the value of tags')
    tag_fix_parser.add_argument('exp_name', type=str, help='experiment name')
    tag_fix_parser.add_argument('tags', type=str, default="",
            help='"tags" (e.g., "arch=gpt3, train_set=stack_overflow, test_set=quora")')
    tag_fix_parser.set_defaults(worker=tag_fixer)

    # tag unfix command
    tag_unfix_parser = tag_subparsers.add_parser('unfix', help='unfix the value of tags')
    tag_unfix_parser.add_argument('exp_name', type=str, help='experiment name')
    tag_unfix_parser.add_argument('tags', type=str, default="",
            help='"tags" without values (e.g., "arch, train_set, test_set")')
    tag_unfix_parser.set_defaults(worker=tag_unfixer)

    # tag update command
    tag_upd_parser = tag_subparsers.add_parser('update', help='update the value of tags')
    tag_upd_parser.add_argument('exp_name', type=str, help='experiment name')
    tag_upd_parser.add_argument('tags', type=str,
            help='"tags" (e.g., "color=red, shape=cube, weight->20kg, volume->10L)"')
    tag_upd_parser.set_defaults(worker=tag_updater)


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
