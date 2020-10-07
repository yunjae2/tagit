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


def add_entity(name: str, params: {}, dtags: [], data: str):
    # params = {"name": ["John"], "age": ["13"]}
    # dtags = [dtag_prefix + "latency", dtag_prefix + "throughput"] or
    #         [default_dtag] (most cases)

    # Build SQL
    sql = f"INSERT INTO {name}("
    value_sql = f"VALUES("

    first = True
    for key in params.keys():
        if first:
            sql = sql + key
            value_sql = value_sql + "?"
            first = False
        else:
            sql = sql + ',' + key
            value_sql = value_sql + ",?"

    for dtag in dtags:
        sql = sql + "," + dtag
        value_sql = value_sql + ",?"

    sql = sql + ")"
    value_sql = value_sql + ")"
    sql = sql + " " + value_sql

    values = [x[0] for x in params.values()]
    for dtag in dtags:
        values.append(data)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exists
    # TODO: Handle error if the columns do not match
    c.execute(sql, values)
    conn.commit()


def _add_entity(table: str, entity: {}):
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


def _add_entities(table: str, entities: []):
    # TODO: Optimization
    for entity in entities:
        _add_entity(table, entity)


def get_entities(name, params, dtags):
    # params = {"name": ["John", "Sarah"], "age": ["13"]}
    # dtags = [dtag_prefix + "latency", dtag_prefix + "throughput"] or
    #         [default_dtag]

    conn = create_connection(db_file)
    c = conn.cursor()

    cols = get_columns(name)

    for dtag in dtags:
        if dtag == "*":
            dtags = [x for x in cols if utils.is_dtag(x)]

    # 1. SELECT cluase
    # Performance; select dtags and all current tags only
    sql = f"SELECT"

    first = True
    for col in cols:
        if utils.is_dtag(col):
            if col not in dtags:
                continue
        if first:
            first = False
            sql = sql + f" {col}"
        else:
            sql = sql + f", {col}"

    sql = sql + f" FROM {name}"

    # 2. WHERE cluase (if required)
    sql = sql + __where(params)

    c.execute(sql)

    entities = c.fetchall()
    keys = [x[0] for x in c.description]
    data = []
    for entity in entities:
        entity_kv = dict(zip(keys, entity))

        # Order by params
        # TODO: handle error for wrong params
        ordered = OrderedDict()
        for key in params:
            ordered[key] = entity_kv.pop(key)
        ordered.update(entity_kv)
        for dtag in dtags:
            ordered.move_to_end(dtag)

        data.append(ordered)

    return data


def _get_entities(table, conditions, cols):
    # 1. SELECT cluase
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


def delete_rows(name: str, params: OrderedDict()):
    conn = create_connection(db_file)
    c = conn.cursor()

    sql = f"DELETE FROM {name}"

    sql = sql + __where(params)

    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def _delete_rows(table: str, conditions: OrderedDict(), limit=None, offset=0):
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


def _append_row(table: str, conditions: {}, vals: {}):
    # 1. UPDATE clause
    sql = f"UPDATE {table}"

    # 2. SET clause
    sql = sql + " SET"
    first = True
    for key, value in vals.items():
        if first:
            first = False
            sql = sql + f" {key} = {key} || '{value}'"
        else:
            sql = sql + f", {key} = {key} || '{value}'"

    # 3. WHERE clause
    sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def _update_row(table: str, conditions: {}, vals: {}):
    # 1. UPDATE clause
    sql = f"UPDATE {table}"

    # 2. SET clause
    sql = sql + " SET"
    first = True
    for key, value in vals.items():
        if first:
            first = False
            sql = sql + f" {key} = '{value}'"
        else:
            sql = sql + f", {key} = '{value}'"

    # 3. WHERE clause
    sql = sql + __where(conditions)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exist
    # TODO: Handle error if the columns do not match
    c.execute(sql)
    conn.commit()


def _update_rows(table: str, cond_vals: []):
    for cond, val in cond_vals:
        _update_row(table, cond, val)


def _rename_table(old_name: str, new_name: str):
    sql = f"ALTER TABLE {old_name} RENAME TO {new_name}"

    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()


def _rename_column(table: str, old_name: str, new_name: str):
    sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"

    conn = create_connection(db_file)
    c = conn.cursor()
    c.execute(sql)
    conn.commit()
