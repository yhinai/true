from slugify import slugify


def test_slugify_basic_case() -> None:
    assert slugify("Hello World") == "hello-world"
