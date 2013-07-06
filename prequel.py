"""
prequel.py

loads various datasources to a sqlite3 backend
"""
import json
import os
import sqlite3

import unicodecsv


def infer_filetype(datasource):
  if not os.path.isfile(datasource):
    raise ValueError("At the moment, PREQUEL needs to be given a file".format(datasource))
  if datasource.endswith(".csv"):
    return "csv"
  if datasource.endswith(".json"):
    return "json"
  raise ValueError("No known parser for {}.".format(datasource))


def load(datasource, filetype):
  parsers = {
      "csv": unicodecsv.reader,
      "json": json.load
  }

  parser = parsers[filetype]




class Dataset(object):
  def __init__(self, datasource, filetype=None):
    self.datasource = datasource

    if not filetype:
      filetype = infer_filetype(datasource)
