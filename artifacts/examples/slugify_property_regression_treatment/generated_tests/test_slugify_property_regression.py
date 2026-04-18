from property_checks import assert_slugify_properties

def test_assert_slugify_properties_counterexample() -> None:
    assert_slugify_properties("Hello  World")
