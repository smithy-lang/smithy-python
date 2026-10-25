/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.Shape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;

public class ParamsIndexTest {

    private static final String NS = "smithy.example";

    private static final String REACHABILITY_MODEL = """
            $version: "2"
            namespace smithy.example

            service TestService {
                version: "2024-01-01"
                operations: [PutThing, StreamThing]
            }

            operation PutThing {
                input: PutThingInput
                output: PutThingOutput
            }

            structure PutThingInput {
                tags: TagList
                attributes: AttributeMap
                choice: Choice
                name: String
            }

            structure PutThingOutput {
                result: OutputOnly
            }

            structure OutputOnly {
                value: String
            }

            list TagList {
                member: Tag
            }

            structure Tag {
                key: String
            }

            map AttributeMap {
                key: String
                value: NestedList
            }

            list NestedList {
                member: Attribute
            }

            structure Attribute {
                value: String
            }

            union Choice {
                quit: Unit
                tag: Tag
            }

            operation StreamThing {
                input: StreamThingInput
            }

            structure StreamThingInput {
                name: String
                stream: Events
            }

            @streaming
            union Events {
                ping: PingEvent
            }

            structure PingEvent {
                message: String
            }
            """;

    @Test
    public void testShapesReachableFromInputsHaveParams() {
        Model model = loadModel(REACHABILITY_MODEL);
        ParamsIndex index = createIndex(model);

        assertEquals(
                new TreeSet<>(List.of(
                        "smithy.api#Unit",
                        NS + "#Attribute",
                        NS + "#Choice",
                        NS + "#PutThingInput",
                        NS + "#StreamThingInput",
                        NS + "#Tag")),
                shapeIds(index.getShapes()));
    }

    @Test
    public void testEventStreamMemberIsNotAParamsKey() {
        Model model = loadModel(REACHABILITY_MODEL);
        ParamsIndex index = createIndex(model);
        var input = model.expectShape(ShapeId.from(NS + "#StreamThingInput"), StructureShape.class);

        assertEquals(List.of("name"), index.getMembers(input).stream().map(MemberShape::getMemberName).toList());
    }

    @Test
    public void testParamsNamesFollowClassNames() {
        Model model = loadModel(REACHABILITY_MODEL);
        ParamsIndex index = createIndex(model);

        assertEquals("TagParams", index.getParamsSymbol(ShapeId.from(NS + "#Tag")).getName());
        assertEquals("ChoiceParams", index.getParamsSymbol(ShapeId.from(NS + "#Choice")).getName());
        assertEquals("ChoiceQuitParams", variantParamsName(model, index, "Choice$quit"));
        assertEquals("UnitParams", index.getParamsSymbol(ShapeId.from("smithy.api#Unit")).getName());
        assertEquals(
                "test_client._params",
                index.getParamsSymbol(ShapeId.from(NS + "#Tag")).getNamespace());
        assertEquals(
                Set.of("AttributeParams",
                        "ChoiceParams",
                        "ChoiceQuitParams",
                        "ChoiceTagParams",
                        "PutThingInputParams",
                        "StreamThingInputParams",
                        "TagParams",
                        "UnitParams"),
                index.getNames());
    }

    @Test
    public void testUnreachableShapeHasNoParams() {
        Model model = loadModel(REACHABILITY_MODEL);
        ParamsIndex index = createIndex(model);

        assertThrows(CodegenException.class, () -> index.getParamsSymbol(ShapeId.from(NS + "#OutputOnly")));
    }

    @Test
    public void testParamsNameTakenByModelNameUsesUnderscoreSeparator() {
        Model model = loadModel("""
                $version: "2"
                namespace smithy.example

                service TestService {
                    version: "2024-01-01"
                    operations: [PutThing]
                }

                operation PutThing {
                    input: PutThingInput
                    output: PutThingOutput
                }

                structure PutThingInput {
                    thing: Thing
                    choice: Choice
                }

                structure Thing {
                    value: String
                }

                // Shadows Thing's Params name, though it isn't an input.
                structure ThingParams {
                    value: String
                }

                structure PutThingOutput {
                    params: ThingParams
                }

                // The variant class ChoiceParams shadows the union's Params name.
                union Choice {
                    params: String
                    other: String
                }
                """);
        ParamsIndex index = createIndex(model);

        assertEquals("Thing_Params", index.getParamsSymbol(ShapeId.from(NS + "#Thing")).getName());
        assertEquals("Choice_Params", index.getParamsSymbol(ShapeId.from(NS + "#Choice")).getName());
        assertEquals("ChoiceParamsParams", variantParamsName(model, index, "Choice$params"));
        assertEquals("ChoiceOtherParams", variantParamsName(model, index, "Choice$other"));
        assertEquals("PutThingInputParams",
                index.getParamsSymbol(ShapeId.from(NS + "#PutThingInput")).getName());
    }

    private static String variantParamsName(Model model, ParamsIndex index, String relativeId) {
        var member = model.expectShape(ShapeId.from(NS + "#" + relativeId), MemberShape.class);
        return index.getVariantParamsSymbol(member).getName();
    }

    private static Set<String> shapeIds(Set<Shape> shapes) {
        var ids = new TreeSet<String>();
        for (Shape shape : shapes) {
            ids.add(shape.getId().toString());
        }
        return ids;
    }

    static Model loadModel(String smithyIdl) {
        return Model.assembler().addUnparsedModel("test.smithy", smithyIdl).assemble().unwrap();
    }

    static PythonSettings createSettings() {
        return PythonSettings.builder()
                .service(ShapeId.from(NS + "#TestService"))
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
    }

    static ParamsIndex createIndex(Model model) {
        var settings = createSettings();
        return ParamsIndex.of(model, settings, new PythonSymbolProvider(model, settings));
    }
}
