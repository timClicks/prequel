"""
prequel.py

loads various datasources to a sqlite3 backend
"""
from __future__ import print_function

import codecs
import copy
import datetime
import json
import os
import sqlite3
import string
import tempfile
import textwrap
import time
import warnings


import requests

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
      "id"      : "INTEGER",
      "integer" : "INTEGER",
      "float"   : "REAL",
      "numeric" : "NUMERIC",
      "text"    : "TEXT",
      "object"  : "INTEGER",
      "time"    : "DATETIME",
      "real"    : "REAL",
      ""        : "",
      None      : "",
      type("")  : "text",
      type(1)   : "integer",
      type(1L)  : "integer",
      type(0.0) : "float",
      type(u"") : "text",
      type([])  : "category",
      type({})  : "object"
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
  typemap = TYPE_MAP
  try:
    data = requests.get(datasource).json
  except requests.exceptions.MissingSchema:
    try:
      with codecs.open(datasource, encoding="utf-8") as f:
        data = json.load(f)
    except IOError:
      data = json.loads(datasource)
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
  type_hints = [None for n in field_names]

  for i, row in enumerate(data):
    tmp = [None for n in field_names]
    for name, field in row.iteritems():
      idx = field_names.index(make_name_safer(name))
      tmp[idx] = field
      if not type_hints[idx]:
        type_hints[idx] = typemap[type(field)]
    data[i] = tmp

  for i, name in enumerate(field_names):
    field_names[i] = (name, type_hints[i], "")
  return field_names, data


def load_csv(datasource, start_at_line=1, encoding=None, field_names=None, typehints=None):
  start_at_line = int(start_at_line)-1
  assert start_at_line >= 0

  if not field_names:
    field_names = []
  clone = copy.copy(field_names)

  clone = [make_name_safer(val) for val in clone]
  for i,new_val in enumerate(clone):
    if new_val != original[i]:
      warn_about_name_change(original[i], new_val)

  try:
    response = requests.get(datasource)
    fn = response.iter_lines
  except requests.exceptions.MissingSchema:
    try:
      if encoding:
        f = codecs.open(datasource, encoding=encoding)
        fn = f.readlines
      else:
        f = open(datasource)
        fn = f.readlines
    except IOError:
      pass

  try:
    reader = csv.reader(fn())
  except NameError:
    reader = csv.reader(datasource.splitlines())

  data = []

  for i, row in enumerate(reader):
    if i < start_at_line:
      continue
    if field_names:
      data.append(row)
    else:
      field_names = [(make_name_safer(h), "", "") for h in row]
  try:
    f.close()
  except (NameError, AttributeError):
    pass
  return field_names, data


def gen_create_table_sql(name, columns, table_constraints=None):
  if not table_constraints:
    table_constraints = []
  typemap = TYPE_MAP

  for i, (column_name, typehint, column_constraints) in enumerate(columns):
    if not column_constraints:
      column_constraints = ""
    if typehint == "category":
      for sql in gen_create_table_sql(pluralize(column_name), [("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"), (column, "", "UNIQUE")]):
        yield sql
      c = "FOREIGN KEY({}) REFERENCES {}(id) DEFERRABLE INITIALLY DEFERRED".format(column_name, pluralize(column_name))
      table_constraints.append(c)
    elif typehint == "object":
      raise NotImplementedError("Nested objects are not yet supported. Sorry.")
    columns[i] = "{} {} {}".format(column_name, typemap[typehint], column_constraints).strip()

  columns = ",\n ".join(columns)
  table_constraints = ",\n".join(table_constraints)

  sql = ["CREATE TABLE {} (".format(name), columns, table_constraints]

  yield "\n ".join(sql).strip() + "\n);"

def gen_insert_sql(table_name, columns):

  values = ', '.join("?" for column in columns)
  sql = "INSERT INTO {} VALUES ({});".format(table_name, values)
  return sql

def main(datasource,
         column_names=None,
         typehints=None,
         column_constraints=None,
         database_main_table_name=None,
         database_dir=tempfile.gettempdir(),
         database_file_name="prequel-{}{}db".format(os.path.extsep, datetime.date.today()),
         verbose=False):

  fname = os.path.split(datasource)[1]
  fname = os.path.splitext(fname)[0]

  if not database_main_table_name:
    database_main_table_name = fname

  database_path = os.path.join(database_dir, database_file_name)


  db = sqlite3.connect(database_path)


  try:
    columns, data = load_json(datasource)
  except AttributeError:
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

  _columns = []
  for i, (name, inferred_typehint, inferred_constraint) in enumerate(columns):
    n = name
    t = typehints[i] or inferred_typehint
    c = column_constraints[i] or inferred_constraint
    _columns.append((n, t, c))
  columns = _columns

  if verbose:
    print("Creating Tables")
  for sql in gen_create_table_sql(database_main_table_name, columns):
    if verbose > 1:
      print(sql)
    db.execute(sql)

  if verbose:
    print("Inserting data")
  for row in data:
    sql = gen_insert_sql(database_main_table_name, row)
    if verbose:
      lines = textwrap.wrap(unicode(row), 70)
      print(database_main_table_name + " <- " + lines[0])
      for l in lines[1:]:
        print(" " * len(database_main_table_name + " <- ") + l)

        if verbose > 1:
          print("> " + l)
    with db:
      db.execute(sql, row)
  print("OK")


if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("dataset", help="Path to a CSV or JSON formats. Can be local path or a URL.")
  parser.add_argument("--verbose","-v", help="Be verbose", default=False, action='count')
  parser.add_argument("--typehint","-t", help="Add a typehint (optional, more than one okay)", action='append', default=list())
  parser.add_argument("--column-constraint", "-c", help="Add an explicit SQL constraint, e.g. UNIQUE to a column", action='append', default=list())
  parser.add_argument("--column-name","-n", help="Provide a header for a column (optional, more than one okay)", action='append', default=list())
  parser.add_argument("--table-name","-r", help="Provide a name for the main table of the database. (-r switch because tables are also known as relations)")   
  parser.add_argument("--encoding","-e", help="Provide an encoding. May be useful for CSV files.", default="utf-8")
  parser.add_argument("--database-directory", "-d", help="Location to store the database. Defaults to \"{}\".".format(tempfile.gettempdir()), default=tempfile.gettempdir())
  parser.add_argument("--database-filename", help="Defaults to prequel-{}{}db".format(os.path.extsep, datetime.date.today()))
  
  args = parser.parse_args()

  main(datasource=args.dataset,
       column_names=args.column_name,
       typehints=args.typehint,
       column_constraints=args.column_constraint,
       database_main_table_name=args.table_name,
       database_dir=args.database_directory,
       database_file_name=args.database_filename
       verbose=args.verbose)

