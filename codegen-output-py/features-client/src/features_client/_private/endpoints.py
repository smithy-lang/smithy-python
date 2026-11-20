from smithy_core.endpoints import EndpointBdd

# fmt: off
# Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.
BDD = EndpointBdd(
    # (name, type, required, default, builtin, client_context_attribute)
    parameters=(
        ("Endpoint", "string", False, None, "SDK::Endpoint", None),
        ("Region", "string", False, None, "AWS::Region", None),
        ("Stage", "string", False, None, None, "stage"),
        ("ForcePathStyle", "boolean", True, False, None, "force_path_style"),
        ("Name", "string", False, None, None, None),
        ("Kind", "string", False, None, None, None),
    ),
    functions=("booleanEquals", "isSet", "isValidHostLabel"),
    conditions=(
        ((2, "isSet", (0, "Endpoint")), None),  # 0: isSet(Endpoint)
        ((2, "isSet", (0, "Region")), None),  # 1: isSet(Region)
        ((2, "booleanEquals", (0, "ForcePathStyle"), True), None),  # 2: booleanEquals(ForcePathStyle, true)
        ((2, "isSet", (0, "Kind")), None),  # 3: isSet(Kind)
        ((2, "isSet", (0, "Stage")), None),  # 4: isSet(Stage)
        ((2, "isSet", (0, "Name")), None),  # 5: isSet(Name)
        ((2, "isValidHostLabel", (0, "Name"), False), None),  # 6: isValidHostLabel(Name, false)
    ),
    results=(
        None,  # 0: no match
        (6, (0, "Endpoint"), None, ()),  # 1
        (6, "https://{Region}.example.com", None, ()),  # 2
        (6, "https://path.example.com", None, ()),  # 3
        (6, "https://{Name}.{Stage}.example.com", None, (("x-kind", ("{Kind}",)),)),  # 4
        (6, "https://{Stage}.example.com", (4, ("kind",), "{Kind}"), ()),  # 5
        (5, "No stage"),  # 6
    ),
    root=2,
    # (condition, high, low); 1 and -1 are terminals, a negative reference is a
    # complement edge, and 100_000_000 + k is result k.
    nodes=(
        -1, 1, -1,
        0, 100_000_001, 3,
        1, 100_000_002, 4,
        2, 100_000_003, 5,
        3, 6, 100_000_006,
        4, 7, 100_000_006,
        5, 8, 100_000_005,
        6, 100_000_004, 100_000_005,
    ),
)
# fmt: on
