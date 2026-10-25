/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.model.Model;
import software.amazon.smithy.model.shapes.MemberShape;
import software.amazon.smithy.model.shapes.ShapeId;
import software.amazon.smithy.model.shapes.StructureShape;
import software.amazon.smithy.python.codegen.writer.PythonWriter;

public class ParamTypeRendererTest {

    private static final Model MODEL = ParamsIndexTest.loadModel("""
            $version: "2"
            namespace smithy.example

            service TestService {
                version: "2024-01-01"
                operations: [PutThing]
            }

            operation PutThing {
                input: PutThingInput
            }

            structure PutThingInput {
                tag: Tag
                tags: TagList
                sparseNames: SparseNames
                tagsByName: TagMap
                choice: Choice
                document: Document
                name: String
                @required
                count: Integer
                createdAt: Timestamp
                color: Color
                json: JsonText
            }

            structure Tag {
                key: String
            }

            list TagList {
                member: Tag
            }

            @sparse
            list SparseNames {
                member: String
            }

            map TagMap {
                key: String
                value: TagList
            }

            union Choice {
                tag: Tag
                name: String
            }

            enum Color {
                RED
            }

            @mediaType("application/json")
            string JsonText
            """);

    @Test
    public void testStructuresAndUnionsAcceptTheirParamsForm() {
        assertEquals("Tag | TagParams", render("PutThingInput$tag"));
        assertEquals("Choice | ChoiceParams", render("PutThingInput$choice"));
        assertEquals("Tag | TagParams", render("Choice$tag"));
    }

    @Test
    public void testCollectionsAreSequencesAndMappings() {
        assertEquals("Sequence[Tag | TagParams]", render("PutThingInput$tags"));
        assertEquals("Sequence[str | None]", render("PutThingInput$sparseNames"));
        assertEquals("Mapping[str, Sequence[Tag | TagParams]]", render("PutThingInput$tagsByName"));
    }

    @Test
    public void testDocumentsAcceptRawValues() {
        assertEquals("Document | DocumentValue", render("PutThingInput$document"));
    }

    @Test
    public void testOtherMembersUseTheirSymbol() {
        assertEquals("str", render("PutThingInput$name"));
        assertEquals("int", render("PutThingInput$count"));
        assertEquals("datetime", render("PutThingInput$createdAt"));
        assertEquals("str", render("PutThingInput$color"));
        assertEquals("str", render("Choice$name"));
        assertEquals("str | JsonString", render("PutThingInput$json"));
    }

    @Test
    public void testParametersListMembersInModelOrder() {
        var writer = createWriter();
        var input = MODEL.expectShape(ShapeId.from("smithy.example#PutThingInput"), StructureShape.class);
        var parameters = renderer().parameters(writer, input, false);

        assertEquals(
                List.of("tag",
                        "tags",
                        "sparse_names",
                        "tags_by_name",
                        "choice",
                        "document",
                        "name",
                        "count",
                        "created_at",
                        "color",
                        "json"),
                parameters.stream().map(ParamTypeRenderer.Parameter::name).toList());
        assertEquals(
                List.of("count"),
                parameters.stream()
                        .filter(ParamTypeRenderer.Parameter::required)
                        .map(ParamTypeRenderer.Parameter::name)
                        .toList());
    }

    @Test
    public void testTypeCheckingOnlyImportsUnderTypeChecking() {
        var writer = createWriter();
        writer.write("x: $L", renderer().render(writer, member("PutThingInput$tags"), true));
        String out = writer.toString();

        var typeChecking = out.indexOf("if TYPE_CHECKING:");
        assertTrue(typeChecking >= 0, out);
        assertFalse(out.substring(0, typeChecking).contains("Sequence"), out);
        assertFalse(out.substring(0, typeChecking).contains("Tag"), out);
        assertTrue(out.contains("from collections.abc import Sequence"), out);
        assertTrue(out.contains("from ._params import TagParams"), out);
        assertTrue(out.contains("from .models import Tag"), out);
    }

    private static String render(String relativeId) {
        var writer = createWriter();
        writer.write("x: $L", renderer().render(writer, member(relativeId), false));
        String out = writer.toString();
        return out.substring(out.indexOf("x: ") + 3).trim();
    }

    private static ParamTypeRenderer renderer() {
        var settings = ParamsIndexTest.createSettings();
        var symbolProvider = new PythonSymbolProvider(MODEL, settings);
        return new ParamTypeRenderer(MODEL, symbolProvider, ParamsIndex.of(MODEL, settings, symbolProvider));
    }

    private static MemberShape member(String relativeId) {
        return MODEL.expectShape(ShapeId.from("smithy.example#" + relativeId), MemberShape.class);
    }

    private static PythonWriter createWriter() {
        return new PythonWriter(ParamsIndexTest.createSettings(), "test_client.client");
    }
}
