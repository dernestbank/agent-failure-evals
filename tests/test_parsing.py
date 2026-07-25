from agent_failure_evals.providers.base import parse_json_object


def test_parse_json_object_accepts_surrounding_text() -> None:
    parsed = parse_json_object('Result follows: {"status":"ok"} end.')
    assert parsed == {"status": "ok"}


def test_parse_json_object_accepts_direct_json() -> None:
    assert parse_json_object('{"status":"ok"}') == {"status": "ok"}
