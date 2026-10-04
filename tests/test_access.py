import pytest

from lakeforge.serving.access import authenticate, check_sql, load_policy, parse_api_keys

POLICY = {"analyst": frozenset({"gold_daily_summary"})}


def test_parse_api_keys():
    assert parse_api_keys("a:analyst, b:operator,,bad") == {"a": "analyst", "b": "operator"}


def test_authenticate():
    keys = {"secret": "analyst"}
    assert authenticate("secret", keys, POLICY).tables == POLICY["analyst"]
    assert authenticate("nope", keys, POLICY) is None
    assert authenticate(None, keys, POLICY) is None
    assert authenticate("secret", {"secret": "ghost"}, POLICY) is None


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE x",
        "SELECT 1; SELECT 2",
        "SELECT * FROM read_csv('/etc/passwd')",
        "COPY x TO 'out.csv'",
        "",
    ],
)
def test_sql_guard_rejects(sql):
    with pytest.raises(ValueError):
        check_sql(sql)


def test_sql_guard_accepts_select_and_with():
    assert check_sql("SELECT updated_at FROM gold_daily_summary;") == (
        "SELECT updated_at FROM gold_daily_summary"
    )
    assert check_sql("WITH x AS (SELECT 1) SELECT * FROM x").startswith("WITH")


def test_policy_file_loads(base_settings):
    policy = load_policy(base_settings.policy_file)
    assert "gold_daily_summary" in policy["analyst"]
    assert "quarantine_taxi_trips" not in policy["analyst"]
    assert "quarantine_taxi_trips" in policy["operator"]
