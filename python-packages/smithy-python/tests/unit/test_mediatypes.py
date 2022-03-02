from smithy_python.mediatypes import JsonBlob, JsonString


def test_json_string() -> None:
    json_string = JsonString("{}")
    assert json_string == "{}"
    assert json_string.as_json() == {}
    assert isinstance(json_string, str)


def test_json_string_is_lazy() -> None:
    json_string = JsonString("{}")

    # Since as_json hasn't been called yet, the json shouldn't have been
    # parsed yet.
    assert json_string._json is None

    json_string.as_json()

    # Now that as_json has been called, the parsed result should be
    # cached.
    assert json_string._json == {}


def test_string_from_json_immediately_caches() -> None:
    json_string = JsonString.from_json({})
    assert json_string._json == {}


def test_json_blob() -> None:
    json_blob = JsonBlob(b"{}")
    assert json_blob == b"{}"
    assert json_blob.as_json() == {}
    assert isinstance(json_blob, bytes)


def test_json_blob_is_lazy() -> None:
    json_blob = JsonBlob(b"{}")

    # Since as_json hasn't been called yet, the json shouldn't have been
    # parsed yet.
    assert json_blob._json is None

    json_blob.as_json()

    # Now that as_json has been called, the parsed result should be
    # cached.
    assert json_blob._json == {}


def test_blob_from_json_immediately_caches() -> None:
    json_blob = JsonBlob.from_json({})
    assert json_blob._json == {}
