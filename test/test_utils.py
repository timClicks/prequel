import tempfile

import prequel

def test_infer_parser_understands_csv():
  with tempfile.NamedTemporaryFile(suffix="csv") as f:
    assert prequel.infer_filetype(f.name) == "csv"

def test_infer_parser_understands_csv():
  with tempfile.NamedTemporaryFile(suffix="json") as f:
    assert prequel.infer_filetype(f.name) == "json"

def test_load_json_understands_urls():
  r = prequel.load_json("http://httpbin.org/get")
  assert 'headers' in r
