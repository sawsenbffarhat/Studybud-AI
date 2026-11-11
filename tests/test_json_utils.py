"""Run with: python -m tests.test_json_utils"""

from utils.json_utils import parse_llm_json

assert parse_llm_json('[{"a": 1}]') == [{"a": 1}]
assert parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}
assert parse_llm_json('Sure! Here it is:\n[{"a": 1}]\nHope it helps') == [{"a": 1}]

print("JSON parsing works")
