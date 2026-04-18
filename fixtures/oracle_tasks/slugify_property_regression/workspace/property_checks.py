from slugify import slugify


def assert_slugify_properties(value: str) -> None:
    result = slugify(value)
    assert result == result.lower(), "slugify must lowercase the output"
    assert " " not in result, "slugify must remove spaces from the output"
    assert "--" not in result, "slugify must collapse repeated separators"
    assert slugify(result) == result, "slugify must be idempotent"
