import sqlite3
import os
from collections import OrderedDict

db_file = os.path.join(os.path.expanduser("~"), ".tagit", "tagit.db")


def create_connection(db_file):
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
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


def create_table(name):
    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table already exists
    # TODO: Handle injection?
    c.execute(f"CREATE TABLE {name} (_data TEXT)")


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


def add_entity(name, params, data):
    # TODO: BUG if params has '*' parameters
    # params = {"name": "John", "age": 13}

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

    sql = sql + ",_data) "
    value_sql = value_sql + ",?)"
    sql = sql + value_sql

    values = list(params.values())
    values.append(data)

    conn = create_connection(db_file)
    c = conn.cursor()
    # TODO: Handle error if the table does not exists
    # TODO: Handle error if the columns do not match
    c.execute(sql, values)
    conn.commit()


def get_entities(name, params):
    conn = create_connection(db_file)
    c = conn.cursor()

    sql = f"SELECT * FROM {name}"

    first = True
    for key in params.keys():
        if params[key] == "*":
            continue
        if first:
            sql = sql + f" WHERE {key} = '{params[key]}'"
            first = False
        else:
            sql = sql + f" AND {key} = '{params[key]}'"

    c.execute(sql)

    entities = c.fetchall()
    keys = [x[0] for x in c.description]
    data = []
    for entity in entities:
        entity_kv = {}
        for idx, value in enumerate(entity):
            key = keys[idx]
            entity_kv[key] = value
        # Order by params
        # TODO: handle error for wrong params
        ordered = OrderedDict()
        for key in params:
            ordered[key] = entity_kv.pop(key)
        ordered.update(entity_kv)
        ordered.move_to_end("_data")

        data.append(ordered)

    return data


def drop_table(name: str):
    conn = create_connection(db_file)
    c = conn.cursor()

    # TODO: Handle error if the table does not exist
    c.execute(f"DROP TABLE {name}")


def delete_rows(name: str, params: OrderedDict()):
    conn = create_connection(db_file)
    c = conn.cursor()

    sql = f"DELETE FROM {name}"

    first = True
    for key in params.keys():
        if params[key] == "*":
            continue
        if first:
            sql = sql + f" WHERE {key} = '{params[key]}'"
            first = False
        else:
            sql = sql + f" AND {key} = '{params[key]}'"

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
    c = conn.cursor()

    with open(filename, 'w') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")


def import_dump(filename):
    conn = create_connection(db_file)
    c = conn.cursor()

    with open(filename, 'r') as f:
        sql = f.read()

    c.executescript(sql)
