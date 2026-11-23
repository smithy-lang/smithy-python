from smithy_core.endpoints import EndpointBdd

# fmt: off
# Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.
BDD = EndpointBdd(
    # (name, type, required, default, builtin, client_context_attribute)
    parameters=(
        ("Endpoint", "string", False, None, "SDK::Endpoint", None),
        ("Region", "string", False, None, "AWS::Region", None),
        ("UseFIPS", "boolean", True, False, "AWS::UseFIPS", None),
        ("Stage", "string", False, None, None, "stage"),
        ("ForcePathStyle", "boolean", True, False, None, "force_path_style"),
        ("Name", "string", False, None, None, None),
        ("Kind", "string", False, None, None, None),
    ),
    functions=("aws.partition", "booleanEquals", "isSet", "isValidHostLabel"),
    conditions=(
        ((2, "isSet", (0, "Endpoint")), None),  # 0: isSet(Endpoint)
        ((2, "booleanEquals", (0, "ForcePathStyle"), True), None),  # 1: booleanEquals(ForcePathStyle, true)
        ((2, "isSet", (0, "Kind")), None),  # 2: isSet(Kind)
        ((2, "isSet", (0, "Stage")), None),  # 3: isSet(Stage)
        ((2, "isSet", (0, "Region")), None),  # 4: isSet(Region)
        ((2, "aws.partition", (0, "Region")), "PartitionResult"),  # 5: PartitionResult = aws.partition(Region)
        ((2, "booleanEquals", (0, "UseFIPS"), True), None),  # 6: booleanEquals(UseFIPS, true)
        ((2, "isSet", (0, "Name")), None),  # 7: isSet(Name)
        ((2, "isValidHostLabel", (0, "Name"), False), None),  # 8: isValidHostLabel(Name, false)
    ),
    results=(
        None,  # 0: no match
        (6, (0, "Endpoint"), None, ()),  # 1
        (6, "https://path.example.com", None, ()),  # 2
        (6, "https://{Name}.{Stage}.example.com", None, (("x-kind", ("{Kind}",)),)),  # 3
        (6, "https://{Stage}.example.com", (4, ("kind",), "{Kind}"), ()),  # 4
        (6, "https://fieldnotes-fips.{Region}.{PartitionResult#dnsSuffix}", None, ()),  # 5
        (6, "https://fieldnotes.{Region}.{PartitionResult#dnsSuffix}", (4, ("authSchemes",), (3, (4, ("name", "signingName", "signingRegion"), "sigv4", "fieldnotes", "{Region}"))), ()),  # 6
        (5, "No region or stage"),  # 7
    ),
    root=2,
    # (condition, high, low); 1 and -1 are terminals, a negative reference is a
    # complement edge, and 100_000_000 + k is result k.
    nodes=(
        -1, 1, -1,
        0, 100_000_001, 3,
        1, 100_000_002, 4,
        2, 5, 6,
        3, 9, 6,
        4, 7, 100_000_007,
        5, 8, 100_000_007,
        6, 100_000_005, 100_000_006,
        7, 10, 100_000_004,
        8, 100_000_003, 100_000_004,
    ),
)
# fmt: on
