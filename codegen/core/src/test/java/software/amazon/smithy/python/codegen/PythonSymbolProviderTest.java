/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.OperationShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.UnionShape;

public class PythonSymbolProviderTest {

    private static final String NS = "smithy.example";

    @Test
    public void testUnionMemberVariantNameCollidingWithShapeUsesUnderscoreSeparator() {
        Model model = loadModel("""
                $version: "2"
                namespace smithy.example

                service TestService {
                    version: "2024-01-01"
                    operations: [TestOp]
                }

                operation TestOp {
                    input: TestOpInput
                }

                structure TestOpInput {
                    principal: Principal
                }

                union Principal {
                    user: PrincipalUser
                }

                structure PrincipalUser {
                    name: String
                }
                """);
        PythonSymbolProvider provider = createProvider(model);
        var userMember = model.expectShape(ShapeId.from(NS + "#Principal$user"), MemberShape.class);

        assertEquals("Principal_User", provider.toSymbol(userMember).getName());
    }

    @Test
    public void testUnionUnknownVariantNameCollidingWithShapeUsesUnderscoreSeparator() {
        Model model = loadModel("""
                $version: "2"
                namespace smithy.example

                service TestService {
                    version: "2024-01-01"
                    operations: [TestOp]
                }

                operation TestOp {
                    input: TestOpInput
                }

                structure TestOpInput {
                    value: MyUnion
                    other: MyUnionUnknown
                }

                union MyUnion {
                    foo: String
                }

                structure MyUnionUnknown {
                    message: String
                }
                """);
        PythonSymbolProvider provider = createProvider(model);
        var union = model.expectShape(ShapeId.from(NS + "#MyUnion"), UnionShape.class);

        assertEquals("MyUnion_Unknown",
                provider.toSymbol(union).expectProperty(SymbolProperties.UNION_UNKNOWN).getName());
    }

    @Test
    public void testOperationNameCollidingWithClientMethodIsEscaped() {
        Model model = loadModel("""
                $version: "2"
                namespace smithy.example

                service TestService {
                    version: "2024-01-01"
                    operations: [Close]
                }

                operation Close {}
                """);
        PythonSymbolProvider provider = createProvider(model);
        var operation = model.expectShape(ShapeId.from(NS + "#Close"), OperationShape.class);

        assertEquals(
                "close_",
                provider.toSymbol(operation)
                        .expectProperty(SymbolProperties.OPERATION_METHOD)
                        .getName());
    }

    @Test
    public void testResponseMetadataIsEscapedOnOutputsAndErrors() {
        Model model = loadModel(RESPONSE_METADATA_MODEL);
        PythonSymbolProvider provider = createProvider(model);

        assertEquals("response_metadata_", memberName(provider, model, "GetThingOutput$responseMetadata"));
        assertEquals("response_metadata_", memberName(provider, model, "ThingError$responseMetadata"));
    }

    @Test
    public void testResponseMetadataIsNotEscapedOnOtherShapes() {
        // Only outputs and errors are given the attribute, so members elsewhere
        // must keep their natural name.
        Model model = loadModel(RESPONSE_METADATA_MODEL);
        PythonSymbolProvider provider = createProvider(model);

        assertEquals("response_metadata", memberName(provider, model, "GetThingInput$responseMetadata"));
        assertEquals("response_metadata", memberName(provider, model, "Nested$responseMetadata"));
    }

    @Test
    public void testUnrelatedMembersOnOutputsAndErrorsAreUnaffected() {
        Model model = loadModel(RESPONSE_METADATA_MODEL);
        PythonSymbolProvider provider = createProvider(model);

        assertEquals("thing_arn", memberName(provider, model, "GetThingOutput$thingArn"));
        assertEquals("retry_after", memberName(provider, model, "ThingError$retryAfter"));
    }

    private static final String RESPONSE_METADATA_MODEL = """
            $version: "2"
            namespace smithy.example

            service TestService {
                version: "2024-01-01"
                operations: [GetThing]
                errors: [ThingError]
            }

            operation GetThing {
                input: GetThingInput
                output: GetThingOutput
            }

            structure GetThingInput {
                responseMetadata: String
            }

            structure GetThingOutput {
                responseMetadata: String
                thingArn: String
                nested: Nested
            }

            structure Nested {
                responseMetadata: String
            }

            @error("client")
            structure ThingError {
                responseMetadata: String
                retryAfter: String
            }
            """;

    private static String memberName(PythonSymbolProvider provider, Model model, String relativeId) {
        var member = model.expectShape(ShapeId.from(NS + "#" + relativeId), MemberShape.class);
        return provider.toMemberName(member);
    }

    private static Model loadModel(String smithyIdl) {
        return Model.assembler().addUnparsedModel("test.smithy", smithyIdl).assemble().unwrap();
    }

    private static PythonSymbolProvider createProvider(Model model) {
        PythonSettings settings = PythonSettings.builder()
                .service(ShapeId.from(NS + "#TestService"))
                .moduleName("test_client")
                .moduleVersion("0.0.1")
                .build();
        return new PythonSymbolProvider(model, settings);
    }
}
