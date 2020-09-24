import os

# Used for the raw data and data categories
# Also acts like the default dtag
tagit_prefix = "_tagit_"

dtag_prefix = tagit_prefix + "data_"
default_dtag = dtag_prefix + "raw"

parser_prefix = tagit_prefix + "parser_"
dtag_list_prefix = tagit_prefix + "dtag_list_"
taglist_prefix = tagit_prefix + "taglist_"

TAGIT_EMPTY = tagit_prefix + "empty_"

# SQLite3
db_file = os.path.join(os.path.expanduser("~"), ".tagit", "tagit.db")
