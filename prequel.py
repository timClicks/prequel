"""
prequel.py

loads various datasources to a sqlite3 backend
"""
import codecs
import copy
import datetime
import json
import os
import sqlite3
import string
import tempfile
import warnings

try:
  import unicodecsv
  csv = unicodecsv.csv
except ImportError:
  import sys
  if sys.version_info[0] == 2:
    warnings.warn("In Python 2, CSV lacks good support for Unicode.")
  import csv

from foreign import memorize, pluralize

SAFE_CHARS = frozenset(string.ascii_letters + "_")

TYPE_MAP = {
      "blob"    : "BLOB",
      "category": "INTEGER",
      "id"      : "INTEGER"
      "integer" : "INTEGER",
      "float"   : "REAL",
      "numeric" : "NUMERIC",
      "text"    : "TEXT",
      "object"  : "INTEGER",
      "time"    : "DATETIME",
      "real"    : "REAL",
      ""        : ""
}

@memorize
def make_name_safer(name):
  """
  Translates whitespace to underscores, lowers cases, scraps non-ascii
  """

  safe = SAFE_CHARS
  name = name.lower().replace(" ", "_")
  return filter(lambda char: char in safe, name)

def apply_typehints(value, hint):
  fn = lambda a: a
  if hint == "integer":
    fn = int
  elif hint == "float":
    fn = float
  return fn(value)

def warn_about_name_change(old, new):
  warnings.warn(u"{} will be changed to {}".format(old, new))

def load_json(datasource, key=None):
  """

  The `key` parameter allows you to select a key for an
  object which is holding the actual data you care about.
  You should use key="d" for the following result from a
  web API:

      { "d": [{...}, {...}, {...}]}

  """
  try:
    data = requests.get(datasource).json
  except requests.MissingSchema:
    try:
      data = json.loads(datasource)
    except ValueError:
      data = json.load(datasource)
  if key:
    data = data[key]
  if type(data) == type({}):
    data = (data,)

  # protect ourselves from some objects with missing keys
  field_names = set([])
  for row in data:
      field_names = field_names.union(set(row))
  field_names = set(make_name_safer(name) for name in field_names) # filter
  field_names = list(field_names)
  field_names.sort()

  for i, row in enumerate(data):
    tmp = [None for n in field_names]
    for name, field in row.iter_items():
      idx = field_names.index(make_name_safer(name))
      tmp[idx] = field
    data[i] = tmp
  return field_names, data


def load_csv(datasource, start_at_line=1, encoding=None, field_names=None, typehints=None):
  start_at_line = int(start_at_line)-1
  assert start_at_line >= 0

  if not field_names:
    field_names = []
  clone = copy(field_names)

  clone = [make_name_safer(val) for val in clone]
  for i,new_val in enumerate(clone):
    if new_val != original[i]:
      warn_about_name_change(original[i], new_val)

  try:
    response = requests.get(datasource)
    fn = response.iter_lines
  except requests.MissingSchema:
    try:
      if encoding:
        with codecs.open(datasource, encoding=encoding) as f:
          fn = f.readlines
      else:
        with open(datasource) as f:
          fn = f.readlines
    except IOError:
      pass

  try:
    reader = csv.reader(fn)
  except NameError:
    reader = csv.reader(datasource.splitlines())

  data = []

  for i, row in enumerate(reader):
    if i <= start_at_line:
      continue
    if field_names:
      data.append(row)
    else:
      field_names = [make_name_safer(h) for h in row]
  return field_names, data


def gen_create_table_sql(name, columns, table_constraints=None):
  if not table_constraints:
    table_constraints = []
  typemap = TYPE_MAP

  for i, (column_name, typehint, column_constraints) in enumerate(columns):
    if not column_constraints:
      column_constraints = ""
    if typehint == "category":
      for sql in gen_create_table_sql(pluralize(column_name), [("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"), (column, "", "UNIQUE")])
        yield sql
      c = "FOREIGN KEY({}) REFERENCES {}(id) DEFERRABLE INITIALLY DEFERRED".format(column_name, pluralize(column_name))
      table_constraints.append(c)
    elif typehint == "object":
      raise NotImplementedError("Nested objects are not yet supported. Sorry.")
    columns[i] = "{} {} {}".format(column_name, typemap[typehint], column_constraints)

  columns = ",\n".join(columns)
  table_constraints = ",\n".join(table_constraints)

  sql = """CREATE TABLE {} (
  {}

  {}
  );
  """.format(name, columns, table_constraints)
  yield sql.strip()

def gen_insert_sql(table_name, columns):

  values = ', '.join("?" for column in columns)
  columns = ",\n".join(columns)
  sql = """
  INSERT INTO {} (
    {}
  )
  VALUES (
    {}
  );
  """.format(table_name, columns, values)
  return sql

def main(datasource,
         column_names=None,
         typehints=None,
         column_constraints=None,
         database_main_table_name="prequel"
         database_dir=tempfile.gettempdir(),
         database_file_name="prequel-"+str(datetime.date.today()),
         database_file_extension="db"):

  fname = os.path.split(datasource)[1]
  fname = os.path.splitext(fname)[0]

  database_file = "{}{}{}".format(fname, os.path.extsep, database_file_extension)
  database_path = os.path.join(database_dir, database_file)


  db = sqlite3.connect(database_path)

  try:
    columns, data = load_json(datasource)
  except ValueError:
    columns, data = load_csv(datasource)

  _typehints = [None for i in range(len(columns))]
  if typehints:
    for column_name, typehint in typehints.iteritems():
      idx = column_names.index(column_name)
      _typehints[idx] = typehint
    typehints = _typehints

  _column_constraints = [None for i in range(len(columns))]
  if column_constraints:
    for column_name, c in column_constraints.iteritems():
      idx = column_names.index(column_name)
      _column_constraints[idx] = c
    column_constraints = _column_constraints

  columns = [(column_name, typehints[i], column_constraints[i]) for i, column_name in enumerate(columns)]

  for sql in gen_create_table_sql(database_main_table_name, columns):
    db.execute(sql)

  sql = gen_insert_sql(database_main_table_name)
  db.executemany(sql, data)


