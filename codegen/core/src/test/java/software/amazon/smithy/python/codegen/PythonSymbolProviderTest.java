/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
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
