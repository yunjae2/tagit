import os

# Used for the raw data and data categories
# Also acts like the default dtag
tagit_prefix = "_tagit_"

dtag_prefix = tagit_prefix + "data_"
dstat_prefix = tagit_prefix + "stat_"
default_dtag = dtag_prefix + "raw"

exp_prefix = tagit_prefix + "exp_"
taglist_prefix = tagit_prefix + "taglist_"
dtaglist_prefix = tagit_prefix + "dtaglist_"
parser_prefix = tagit_prefix + "parser_"

TAGIT_EMPTY = tagit_prefix + "empty_"

# SQLite3
db_file = os.path.join(os.path.expanduser("~"), ".tagit", "tagit.db")
