# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from smithy_python.clients import ClientPlan, normalize_client_model
from smithy_python.exceptions import InvalidInvocationError, ModelError
from smithy_python.generation import ClientSettings, GenerationPlan
from smithy_python.model import (
    Model,
    OperationShape,
    ServiceShape,
    ShapeId,
    ShapeType,
    StructureShape,
    load_model,
)
from smithy_python.selection import (
    contained_operations,
    select_shapes,
    select_type_shapes,
)
from smithy_python.symbols import ClientSymbolProvider, SymbolProvider

_SETTINGS = ClientSettings("example_client", "1.0.0", None)
_ORIGINAL = "smithy.synthetic#originalShapeId"


def _model(shapes: dict[str, object]) -> Model:
    return load_model({"smithy": "2.0", "shapes": shapes})


def _service(model: Model) -> ServiceShape:
    return model.expect_shape("example#Service", ServiceShape)


def _symbols(model: Model) -> ClientSymbolProvider:
    service = _service(model)
    return ClientSymbolProvider(
        model,
        select_shapes(model),
        package="example_client",
        operations=contained_operations(model, service),
    )


def test_settings_are_immutable_and_use_shared_partition_defaults() -> None:
    assert _SETTINGS.protocol is None
    assert _SETTINGS.schema_partition_size == 100
    assert _SETTINGS.stub_partition_size == 250
    with pytest.raises(FrozenInstanceError):
        setattr(_SETTINGS, "package", "changed")
    settings = ClientSettings(
        "example",
        "1.0.0",
        None,
        protocol=ShapeId("smithy.protocols", "rpcv2Cbor"),
        schema_partition_size=None,
        stub_partition_size=None,
    )
    assert settings.protocol == ShapeId("smithy.protocols", "rpcv2Cbor")


@pytest.mark.parametrize("field", ["schema_partition_size", "stub_partition_size"])
@pytest.mark.parametrize("size", [0, -1])
def test_settings_reject_invalid_partition_sizes(field: str, size: int) -> None:
    with pytest.raises(ValueError, match="Partition sizes"):
        ClientSettings(
            "example",
            "1.0.0",
            None,
            schema_partition_size=size if field == "schema_partition_size" else 100,
            stub_partition_size=size if field == "stub_partition_size" else 250,
        )


def test_settings_reject_protocol_member_ids() -> None:
    with pytest.raises(ValueError, match="non-member"):
        ClientSettings("example", "1.0.0", None, ShapeId("example", "Protocol", "x"))


@pytest.mark.parametrize(
    "relationship",
    [
        "create",
        "put",
        "read",
        "update",
        "delete",
        "list",
        "operations",
        "collectionOperations",
    ],
)
def test_discovery_follows_all_resource_operation_relationships(
    relationship: str,
) -> None:
    reference = {"target": "example#Nested"}
    model = _model(
        {
            "example#Nested": {"type": "operation"},
            "example#Direct": {"type": "operation"},
            "example#Unrelated": {"type": "operation"},
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Direct"}],
                "resources": [{"target": "example#Parent"}],
            },
            "example#Parent": {
                "type": "resource",
                "resources": [{"target": "example#Child"}],
            },
            "example#Child": {
                "type": "resource",
                relationship: (
                    [reference]
                    if relationship in ("operations", "collectionOperations")
                    else reference
                ),
                "resources": [{"target": "example#Parent"}],
            },
        }
    )
    assert [op.id.name for op in contained_operations(model, _service(model))] == [
        "Nested",
        "Direct",
    ]


def test_discovery_deduplicates_operations_and_handles_deep_resource_graphs() -> None:
    shapes: dict[str, object] = {
        "example#Op": {"type": "operation"},
        "example#Service": {
            "type": "service",
            "operations": [{"target": "example#Op"}],
            "resources": [{"target": "example#Resource0"}],
        },
    }
    for index in range(1500):
        shapes[f"example#Resource{index}"] = {
            "type": "resource",
            "operations": [{"target": "example#Op"}],
            "resources": [{"target": f"example#Resource{(index + 1) % 1500}"}],
        }
    model = _model(shapes)
    assert [op.id.name for op in contained_operations(model, _service(model))] == ["Op"]


def test_discovery_reports_invalid_control_relationships() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Data"}],
            },
            "example#Data": {"type": "structure"},
        }
    )
    with pytest.raises(ModelError, match="Expected an operation or resource"):
        contained_operations(model, _service(model))


def test_normalization_preserves_source_members_traits_and_separate_io_roles() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Echo"}],
            },
            "example#Echo": {
                "type": "operation",
                "input": {"target": "example#Shared"},
                "output": {"target": "example#Shared"},
            },
            "example#Base": {
                "type": "structure",
                "traits": {"smithy.api#mixin": {}},
                "members": {
                    "first": {
                        "target": "smithy.api#String",
                        "traits": {"smithy.api#required": {}},
                    }
                },
            },
            "example#Shared": {
                "type": "structure",
                "mixins": [{"target": "example#Base"}],
                "traits": {
                    "smithy.api#documentation": "Shared documentation",
                    "smithy.api#input": {},
                    "smithy.api#output": {},
                },
                "members": {
                    "second": {"target": "smithy.api#Integer"},
                    "nested": {"target": "example#Shared"},
                },
            },
        }
    )
    original = model.expect_shape("example#Shared", StructureShape)
    normalized = normalize_client_model(
        model, _service(model), package="example_client"
    )
    operation = normalized.expect_shape("example#Echo", OperationShape)
    assert operation.input == ShapeId("example", "EchoInput")
    assert operation.output == ShapeId("example", "EchoOutput")
    assert normalized.get_shape(original.id) is original
    assert model.expect_shape(operation.id, OperationShape).input == original.id
    for shape_id, role, opposite in (
        (operation.input, "input", "output"),
        (operation.output, "output", "input"),
    ):
        shape = normalized.expect_shape(shape_id, StructureShape)
        assert tuple(shape.members) == ("first", "second", "nested")
        assert shape.has_trait(role) and not shape.has_trait(opposite)
        assert shape.get_trait("documentation") == "Shared documentation"
        assert shape.get_trait(_ORIGINAL) == "example#Shared"
        assert shape.members["first"].has_trait("required")
        assert shape.members["first"].id == shape_id.with_member("first")
        assert shape.members["nested"].target == original.id
        with pytest.raises(TypeError):
            shape.traits[ShapeId("example", "trait")] = None  # type: ignore[index]
    assert original.has_trait("input") and original.has_trait("output")


def test_unit_and_explicit_empty_io_remain_distinguishable() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [
                    {"target": "example#NoIO"},
                    {"target": "example#Empty"},
                ],
            },
            "example#NoIO": {"type": "operation"},
            "example#Empty": {
                "type": "operation",
                "input": {"target": "example#EmptyStructure"},
                "output": {"target": "example#EmptyStructure"},
            },
            "example#EmptyStructure": {"type": "structure"},
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert [op.method_name for op in plan.operations] == ["no_io", "empty"]
    for name, original in (
        ("NoIO", "smithy.api#Unit"),
        ("Empty", "example#EmptyStructure"),
    ):
        operation = plan.model.expect_shape(f"example#{name}", OperationShape)
        for shape_id in (operation.input, operation.output):
            shape = plan.model.expect_shape(shape_id, StructureShape)
            assert not shape.members
            assert shape.get_trait(_ORIGINAL) == original
    assert not model.get_shape("smithy.api#Unit").has_trait(_ORIGINAL)


def test_canonical_io_is_reused_only_when_it_has_no_other_references() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Op"}],
            },
            "example#Op": {
                "type": "operation",
                "input": {"target": "example#OpInput"},
                "output": {"target": "example#OpOutput"},
            },
            "example#OpInput": {"type": "structure"},
            "example#OpOutput": {"type": "structure"},
            "other#Holder": {
                "type": "structure",
                "members": {"value": {"target": "example#OpOutput"}},
            },
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    operation = plan.operations[0].operation
    assert operation.input == ShapeId("example", "OpInput")
    assert operation.output == ShapeId("example", "OpOutput2")
    assert plan.model.get_shape("example#OpOutput") is model.get_shape(
        "example#OpOutput"
    )
    assert plan.model.get_shape("example#OpInput") is not model.get_shape(
        "example#OpInput"
    )
    assert not model.get_shape("example#OpInput").has_trait("input")


def test_normalization_inherits_errors_once_and_leaves_other_services_unchanged() -> (
    None
):
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Op"}],
                "errors": [
                    {"target": "example#SharedError"},
                    {"target": "example#ServiceFault"},
                ],
            },
            "example#Other": {
                "type": "service",
                "operations": [{"target": "example#OtherOp"}],
            },
            "example#Op": {
                "type": "operation",
                "errors": [
                    {"target": "example#OpFault"},
                    {"target": "example#SharedError"},
                ],
            },
            "example#OtherOp": {"type": "operation"},
            **{
                f"example#{name}": {
                    "type": "structure",
                    "traits": {"smithy.api#error": "client"},
                }
                for name in ("SharedError", "ServiceFault", "OpFault")
            },
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS, service_id="example#Service")
    assert [error.name for error in plan.operations[0].operation.errors] == [
        "OpFault",
        "SharedError",
        "ServiceFault",
    ]
    assert plan.model.get_shape("example#OtherOp") is model.get_shape("example#OtherOp")
    assert len(model.expect_shape("example#Op", OperationShape).errors) == 2
    with pytest.raises(InvalidInvocationError, match="Multiple services"):
        ClientPlan.from_model(model, _SETTINGS)


def test_io_allocation_accounts_for_renames_and_union_variant_names() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#UnionOutput"}],
                "rename": {"example#Occupied": "UnionOutputOutput"},
            },
            "example#UnionOutput": {
                "type": "operation",
                "input": {"target": "example#Shared"},
            },
            "example#Shared": {
                "type": "structure",
                "members": {
                    "renamed": {"target": "example#Occupied"},
                    "choice": {"target": "example#Union"},
                },
            },
            "example#Occupied": {"type": "structure"},
            "example#Union": {
                "type": "union",
                "members": {"outputInput": {"target": "smithy.api#String"}},
            },
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert plan.operations[0].input_name == "UnionOutputInput2"
    assert plan.operations[0].output_name == "UnionOutputOutput2"
    assert (
        plan.models.declaration_names[ShapeId("example", "Occupied")]
        == "UnionOutputOutput"
    )


def test_operation_and_control_names_respect_runtime_and_schema_collisions() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [
                    {"target": "example#Close"},
                    {"target": "example#Close_"},
                    {"target": "example#_invoke"},
                ],
            },
            "example#Close": {
                "type": "operation",
                "input": {"target": "other#Close__"},
            },
            "example#Close_": {"type": "operation"},
            "example#_invoke": {"type": "operation"},
            "other#Close__": {
                "type": "structure",
                "members": {"same": {"target": "other#Close__"}},
            },
        }
    )
    symbols = _symbols(model)
    assert symbols.operation_name("example#Close") == "close__"
    assert symbols.operation_name("example#Close_") == "close_"
    assert symbols.operation_name("example#_invoke") == "_invoke_"
    assert symbols.schema_name("example#Close") == "CLOSE_2"
    assert symbols.schema_name("other#Close__") == "CLOSE"
    assert symbols.schema_name("example#Service") == "SERVICE"
    assert symbols.service_name == "Service"
    assert symbols.aio_service_name == "AsyncService"


def test_ambiguous_operation_names_report_both_shape_ids() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [
                    {"target": "example#GetURL"},
                    {"target": "example#Get_URL"},
                ],
            },
            "example#GetURL": {"type": "operation"},
            "example#Get_URL": {"type": "operation"},
        }
    )
    with pytest.raises(ModelError, match="example#GetURL, example#Get_URL"):
        _symbols(model)


def test_service_and_operation_renames_do_not_change_wire_identifiers() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Original"}],
                "rename": {"example#Original": "getURL"},
            },
            "example#Original": {"type": "operation"},
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    operation = plan.operations[0]
    assert operation.operation.id == ShapeId("example", "Original")
    assert operation.method_name == "get_url"
    assert operation.schema_name == "GET_URL"
    assert operation.input_name == "GetURLInput"


def test_plan_composes_existing_data_plans_and_excludes_unreachable_source_io() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Op"}],
            },
            "example#Op": {
                "type": "operation",
                "input": {"target": "example#Shared"},
                "output": {"target": "example#Shared"},
            },
            "example#Shared": {"type": "structure"},
        }
    )
    standalone = select_type_shapes(model, generate_inputs_and_outputs=True)
    old_symbols = SymbolProvider(model, standalone, package="example_types")
    old_plan = GenerationPlan.from_selection(model, standalone, old_symbols)
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert [shape.id.name for shape in plan.selection.shapes] == ["OpInput", "OpOutput"]
    assert all(shape.type is ShapeType.STRUCTURE for shape in plan.schemas.shapes)
    shared = GenerationPlan.from_selection(plan.model, plan.selection, plan.symbols)
    assert plan.schemas == shared.schemas
    assert plan.models == shared.models
    assert old_plan == GenerationPlan.from_selection(model, standalone, old_symbols)
    assert not model.get_shape("example#Shared").has_trait(_ORIGINAL)
    assert plan.model.get_shape("example#Shared") is model.get_shape("example#Shared")


def test_repeated_normalization_preserves_ids_and_original_shape_metadata() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [
                    {"target": "example#Op"},
                    {"target": "example#Op_"},
                ],
            },
            "example#Op": {"type": "operation"},
            "example#Op_": {"type": "operation"},
        }
    )
    first = ClientPlan.from_model(model, _SETTINGS)
    second = ClientPlan.from_model(first.model, _SETTINGS)
    assert [
        (op.operation.id, op.operation.input, op.operation.output)
        for op in second.operations
    ] == [
        (op.operation.id, op.operation.input, op.operation.output)
        for op in first.operations
    ]
    for operation in second.operations:
        for shape_id in (operation.operation.input, operation.operation.output):
            assert (
                second.model.get_shape(shape_id).get_trait(_ORIGINAL)
                == "smithy.api#Unit"
            )


def test_canonical_io_renames_are_retained_in_operation_and_model_plans() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Op"}],
                "rename": {
                    "example#OpInput": "Request",
                    "example#Fault": "RenamedFault",
                },
            },
            "example#Op": {
                "type": "operation",
                "input": {"target": "example#OpInput"},
                "errors": [{"target": "example#Fault"}],
            },
            "example#OpInput": {"type": "structure"},
            "example#Fault": {
                "type": "structure",
                "traits": {"smithy.api#error": "client"},
            },
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert plan.operations[0].input_name == "Request"
    assert plan.operations[0].operation.input == ShapeId("example", "OpInput")
    assert plan.models.target_names["example#OpInput"] == "Request"
    assert plan.models.target_names["example#Fault"] == "RenamedFault"


def test_client_class_names_do_not_shadow_public_configs() -> None:
    model = _model({"example#Config": {"type": "service"}})
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert plan.symbols.service_name == "Config_"
    assert plan.symbols.aio_service_name == "AsyncConfig_"


def test_planning_preserves_event_streams_without_selecting_an_implementation() -> None:
    model = _model(
        {
            "example#Service": {
                "type": "service",
                "operations": [{"target": "example#Stream"}],
                "traits": {"custom#protocol": {}},
            },
            "example#Stream": {
                "type": "operation",
                "input": {"target": "example#StreamInput"},
            },
            "example#StreamInput": {
                "type": "structure",
                "members": {"events": {"target": "example#Events"}},
            },
            "example#Events": {
                "type": "union",
                "traits": {"smithy.api#streaming": {}},
                "members": {"event": {"target": "example#Event"}},
            },
            "example#Event": {
                "type": "structure",
                "members": {"message": {"target": "smithy.api#String"}},
            },
        }
    )
    plan = ClientPlan.from_model(model, _SETTINGS)
    assert plan.model.get_shape("example#Events").has_trait("streaming")
    assert plan.operations[0].input_name == "StreamInput"
    assert ShapeId("example", "Events") in plan.models.declaration_names


def test_empty_service_is_a_valid_plan_and_missing_service_is_an_invocation_error() -> (
    None
):
    plan = ClientPlan.from_model(
        _model({"example#Service": {"type": "service"}}), _SETTINGS
    )
    assert not plan.operations
    assert not plan.models.shapes
    assert not plan.schemas.shapes
    with pytest.raises(InvalidInvocationError, match="requires a service"):
        ClientPlan.from_model(_model({}), _SETTINGS)


def test_rpcv2_cbor_projection_can_be_planned_without_emitting_files() -> None:
    root = Path(__file__).resolve().parents[4]
    model = load_model(
        (root / "scripts/codegen-output-py/models/rpcv2-cbor.json").read_bytes()
    )
    settings = ClientSettings("rpcv2cbor", "0.0.1", None)
    plan = ClientPlan.from_model(model, settings)
    assert len(plan.operations) == 14
    assert plan.symbols.service_name == "RpcV2Protocol"
    assert plan.symbols.aio_service_name == "AsyncRpcV2Protocol"
    assert plan.selection.service is not None
    assert plan.selection.service.has_trait("smithy.protocols#rpcv2Cbor")
    assert len({op.operation.input for op in plan.operations}) == 14
    assert len({op.operation.output for op in plan.operations}) == 14
    assert all(op.input_name.endswith("Input") for op in plan.operations)
    assert all(op.output_name.endswith("Output") for op in plan.operations)
