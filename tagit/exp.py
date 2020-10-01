from .configs import *
from . import query
from . import utils
from collections import OrderedDict
import sys


def rename(old, new):
    query.rename_table(old, new)
