import tempfile

import prequel

def test_infer_parser_understands_csv():
  with tempfile.NamedTemporaryFile(suffix="csv") as f:
    assert prequel.infer_filetype(f.name) == "csv"

def test_infer_parser_understands_csv():
  with tempfile.NamedTemporaryFile(suffix="json") as f:
    assert prequel.infer_filetype(f.name) == "json"