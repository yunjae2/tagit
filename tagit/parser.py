from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys


def rename(old_exp_name, new_exp_name):
    old_name = utils.mkup_parser_name(old_exp_name)
    new_name = utils.mkup_parser_name(new_exp_name)

    query._rename_table(old_name, new_name)
