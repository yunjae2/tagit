from .configs import *
from . import utils
import sqlite3
import os
import sqlitebck
from collections import OrderedDict


def __where(conditions: OrderedDict()):
    sql = ""
    first = True
    for key, mvalue in conditions.items():
        if mvalue[0] == "*":
            continue

        # Operators
        if first:
            first = False
            sql = sql + " WHERE"
        else:
            sql = sql + " AND"

        # Values
        sql = sql + " ("
        first_val = True
        for value in mvalue:
            if first_val:
                first_val = False
                sql = sql + f"{key} = '{value}'"
            else:
                sql = sql + f" OR {key} = '{value}'"
        sql = sql + ")"

    return sql


def __select(cols: []):
    sql = f"SELECT"

    if not cols:
        sql = sql + " *"
    else:
        first = True
        for col in cols:
            if first:
                first = False
                sql = sql + f" {col}"
            else:
                sql = sql + f", {col}"

    return sql


def __set(vals: OrderedDict()):
    sql = " SET"
    first = True
    for key, value in vals.items():
        if first:
            first = False
            sql = sql + f" {key} = '{value}'"
        else:
            sql = sql + f", {key} = '{value}'"

    return sql


def __set_append(vals: OrderedDict()):
    sql = " SET"
    first = True
    for key, value in vals.items():
        if first:
            first = False
            sql = sql + f" {key} = {key} || '{value}'"
        else:
            sql = sql + f", {key} = {key} || '{value}'"

    return sql


def create_connection(db_file):
    dirname = os.path.dirname(db_file)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def table_exists(name):
    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=:name",
            {"name": name})

    tables = c.fetchall()
    if not tables:
        return False

    return True


def create_table(name, cols):
    # TODO: Handle error if the table already exists
    conn = create_connection(db_file)
    c = conn.cursor()

    sql = f"CREATE TABLE {name} ("

    first = True
    for col in cols:
        if first:
            first = False
            sql = sql + f"{col} TEXT"
        else:
            sql = sql + f", {col} TEXT"

    sql = sql + ")"

    c.execute(sql)
    conn.commit()


def get_columns(name):
    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {name}")
    columns = [desc[0] for desc in c.description]

    return columns


def new_columns(name, columns):
    conn = create_connection(db_file)
    c = conn.cursor()
    for column in columns:
        # TODO: Handle error if column already exists
        c.execute(f"ALTER TABLE {name} ADD COLUMN {column} TEXT")

    conn.commit()


def new_column(name, column):
    new_columns(name, [column])


def add_entity(table: str, entity: {}):
    sql = f"INSERT INTO {table}("
    value_sql = f"VALUES("

    first = True
    for key in entity.keys():
        if first:
            sql = sql + key
            value_sql = value_sql + "?"
            first = False
        else:
            sql = sql + ',' + key
            value_sql = value_sql + ",?"

    sql = sql + ")"
    value_sql = value_sql + ")"
    sql = sql + " " + value_sql

    values = list(entity.values())

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exists
    # TODO: Handle error if the columns do not match
    c.execute(sql, values)
    conn.commit()


def add_entities(table: str, entities: []):
    # TODO: Optimization
    for entity in entities:
        add_entity(table, entity)


def get_entities(table, conditions, cols):
    # 1. SELECT cluase
    sql = __select(cols)

    sql = sql + f" FROM {table}"

    # 2. WHERE cluase (if required)
    sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()

    c.execute(sql)

    entities = c.fetchall()
    keys = [x[0] for x in c.description]
    data = []
    for entity in entities:
        data.append(OrderedDict(zip(keys, entity)))

    return data


def drop_table(name: str):
    conn = create_connection(db_file)
    c = conn.cursor()

    # TODO: Handle error if the table does not exist
    c.execute(f"DROP TABLE {name}")
    conn.commit()


def delete_rows(table: str, conditions: OrderedDict(), limit=None, offset=0):
    sql = f"DELETE FROM {table}"

    if limit:
        sql = sql + f" WHERE rowid IN (SELECT rowid FROM {table}"
        sql = sql + __where(conditions)
        sql = sql + f" LIMIT {limit} OFFSET {offset})"
    else:
        sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def get_tables() -> []:
    conn = create_connection(db_file)
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [x[0] for x in c.fetchall()]

    return tables


def dump_db(filename):
    conn = create_connection(db_file)
    backup_conn = create_connection(filename)
    try:
        conn.backup(backup_conn)
    except AttributeError:
        # Python < 3.7
        sqlitebck.copy(conn, backup_conn)


def append_row(table: str, conditions: {}, vals: {}):
    # 1. UPDATE clause
    sql = f"UPDATE {table}"

    # 2. SET clause
    sql = sql + __set_append(vals)

    # 3. WHERE clause
    sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def update_row(table: str, conditions: {}, vals: {}):
    # 1. UPDATE clause
    sql = f"UPDATE {table}"

    # 2. SET clause
    sql = sql + __set(vals)

    # 3. WHERE clause
    sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def update_rows(table: str, cond_vals: []):
    for cond, val in cond_vals:
        update_row(table, cond, val)


def rename_table(old_name: str, new_name: str):
    sql = f"ALTER TABLE {old_name} RENAME TO {new_name}"

    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()


def rename_column(table: str, old_name: str, new_name: str):
    sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"

    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
