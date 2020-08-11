import sqlite3

# TODO: DB file path
db_file = 'edms.db'
conn = sqlite3.connect(db_file)


def create_connection(db_file):
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
    c.execute(f"CREATE TABLE {name} (data TEXT)")


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
    # TODO: Implement the body
    #params = {"name": "John", "age": 13}

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

    sql = sql + ",data) "
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
