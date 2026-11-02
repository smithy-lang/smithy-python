/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.model.node.ObjectNode;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;

public class EndpointBddGeneratorTest {

    private static final String PARAMETERS = """
            {
              "Region": {"type": "String", "builtIn": "AWS::Region", "documentation": "The region."},
              "UseFIPS": {"type": "Boolean", "required": true, "default": false, "builtIn": "AWS::UseFIPS",
                          "deprecated": {"message": "old"}},
              "Endpoint": {"type": "string", "builtIn": "SDK::Endpoint"},
              "Key": {"type": "string"},
              "Bucket": {"type": "String", "required": true},
              "ForcePathStyle": {"type": "boolean", "builtIn": "AWS::S3::ForcePathStyle"},
              "Tables": {"type": "stringArray", "required": true, "default": ["a", "b"]},
              "Unused": {"type": "boolean", "default": true, "required": true}
            }
            """;

    private static final String CONDITIONS = """
            [
              {"fn": "isSet", "argv": [{"ref": "Endpoint"}]},
              {"fn": "parseURL", "argv": ["{Endpoint}"], "assign": "url"},
              {"fn": "booleanEquals", "argv": [{"ref": "UseFIPS"}, true]},
              {"fn": "stringEquals", "argv": [{"fn": "getAttr", "argv": [{"ref": "url"}, "scheme"]}, "http"]},
              {"fn": "isSet", "argv": [{"ref": "Region"}]},
              {"fn": "isValidHostLabel", "argv": [{"ref": "Region"}, false]},
              {"fn": "stringEquals", "argv": [
                {"fn": "coalesce", "argv": [{"fn": "substring", "argv": [{"ref": "Bucket"}, 0, 4, false]}, ""]},
                "ab{{c}}"]},
              {"fn": "split", "argv": [{"ref": "Bucket"}, "--", 0], "assign": "parts"},
              {"fn": "isSet", "argv": [{"fn": "getAttr", "argv": [{"ref": "parts"}, "[-1]"]}]},
              {"fn": "ite", "argv": [{"fn": "coalesce", "argv": [{"ref": "ForcePathStyle"}, false]}, "path", "vhost"],
               "assign": "style"}
            ]
            """;

    private static final String RESULTS = """
            [
              {"conditions": [], "type": "error", "error": "Invalid {Region}: {{escaped}} {Bucket}{Bucket}"},
              {"conditions": [], "type": "endpoint", "endpoint": {
                "url": "{url#scheme}://{url#authority}{url#path}",
                "properties": {
                  "authSchemes": [{"name": "sigv4", "signingRegion": "{Region}", "disableDoubleEncoding": true}],
                  "literal": {"ref": "Region", "fn": "isSet", "n": 2, "list": ["{style}", ["x"]]}
                },
                "headers": {"x-b": ["{Region}", "b"], "x-a": []}
              }},
              {"conditions": [], "type": "endpoint", "endpoint": {"url": {"ref": "Endpoint"}, "properties": {},
               "headers": {}}},
              {"conditions": [], "type": "endpoint", "endpoint": {"url": "https://{Bucket}.example.com"}}
            ]
            """;

    private static final int[] NODES = {
            -1,
            1,
            -1,
            0,
            3,
            100_000_003,
            1,
            100_000_002,
            100_000_001,
    };

    @Test
    public void rejectsOtherTraitVersions() {
        var e = assertThrows(CodegenException.class,
                () -> lower(trait("1.2", PARAMETERS, CONDITIONS, RESULTS, 2, NODES)));
        assertTrue(e.getMessage().contains("version 1.2"));
    }

    @Test
    public void normalizesAndDropsParameters() {
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, NODES), Set.of("ForcePathStyle"));
        // Key is optional and unread, so it is dropped; Unused and Tables are required, so they stay.
        assertEquals(
                "((\"Region\", \"string\", False, None, \"AWS::Region\", False), "
                        + "(\"UseFIPS\", \"boolean\", True, False, \"AWS::UseFIPS\", False), "
                        + "(\"Endpoint\", \"string\", False, None, \"SDK::Endpoint\", False), "
                        + "(\"Bucket\", \"string\", True, None, None, False), "
                        + "(\"ForcePathStyle\", \"boolean\", False, None, \"AWS::S3::ForcePathStyle\", True), "
                        + "(\"Tables\", \"stringArray\", True, (\"a\", \"b\"), None, False), "
                        + "(\"Unused\", \"boolean\", True, True, None, False))",
                EndpointBddGenerator.literal(bdd.parameters()));
    }

    @Test
    public void keepsParametersReadAsGetAttrBases() {
        var parameters = """
                {"A": {"type": "string"}, "T": {"type": "stringArray"}, "C": {"type": "string"}}
                """;
        var conditions = """
                [{"fn": "isSet", "argv": [{"ref": "A"}]},
                 {"fn": "isSet", "argv": [{"ref": "T"}]},
                 {"fn": "isSet", "argv": [{"fn": "getAttr", "argv": [{"ref": "T"}, "[0]"]}]}]
                """;
        var results = """
                [{"conditions": [], "type": "error", "error": "{A}"}]
                """;
        var bdd = lower(trait("1.1", parameters, conditions, results, 100_000_001, -1, 1, -1));
        // C is optional and unread, so it is dropped.
        assertEquals(
                "((\"A\", \"string\", False, None, None, False), "
                        + "(\"T\", \"stringArray\", False, None, None, False))",
                EndpointBddGenerator.literal(bdd.parameters()));
    }

    @Test
    public void sortsFunctionsByCodePoint() {
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, NODES));
        assertEquals(
                "(\"booleanEquals\", \"coalesce\", \"isSet\", \"isValidHostLabel\", \"ite\", \"parseURL\", "
                        + "\"split\", \"stringEquals\", \"substring\")",
                EndpointBddGenerator.literal(bdd.functions()));
    }

    @Test
    public void lowersConditions() {
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, NODES));
        var conditions = lines(bdd.conditions());
        assertEquals("((2, \"isSet\", (0, \"Endpoint\")), None)", conditions.get(0));
        // A string argument that is a single placeholder is still a template.
        assertEquals("((2, \"parseURL\", \"{Endpoint}\"), \"url\")", conditions.get(1));
        assertEquals("((2, \"booleanEquals\", (0, \"UseFIPS\"), True), None)", conditions.get(2));
        assertEquals(
                "((2, \"stringEquals\", (1, (0, \"url\"), \"scheme\"), \"http\"), None)",
                conditions.get(3));
        assertEquals("((2, \"isValidHostLabel\", (0, \"Region\"), False), None)", conditions.get(5));
        // Literal strings keep their escaped braces; integers stay integers.
        assertEquals(
                "((2, \"stringEquals\", (2, \"coalesce\", "
                        + "(2, \"substring\", (0, \"Bucket\"), 0, 4, False), \"\"), \"ab{{c}}\"), None)",
                conditions.get(6));
        assertEquals("((2, \"split\", (0, \"Bucket\"), \"--\", 0), \"parts\")", conditions.get(7));
        // Paths are written as in the trait; a negative index counts from the end.
        assertEquals("((2, \"isSet\", (1, (0, \"parts\"), \"[-1]\")), None)", conditions.get(8));
        assertEquals(
                "((2, \"ite\", (2, \"coalesce\", (0, \"ForcePathStyle\"), False), "
                        + "\"path\", \"vhost\"), \"style\")",
                conditions.get(9));
    }

    @Test
    public void lowersResults() {
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, NODES));
        var results = lines(bdd.results());
        assertEquals(5, results.size());
        assertEquals("None", results.get(0));
        // Templates are kept as written, escaped braces included.
        assertEquals("(5, \"Invalid {Region}: {{escaped}} {Bucket}{Bucket}\")", results.get(1));
        // Objects in properties are maps even when they have ref or fn keys; header order is kept.
        assertEquals(
                "(6, \"{url#scheme}://{url#authority}{url#path}\", "
                        + "(4, (\"authSchemes\", \"literal\"), "
                        + "(3, (4, (\"name\", \"signingRegion\", \"disableDoubleEncoding\"), \"sigv4\", "
                        + "\"{Region}\", True)), "
                        + "(4, (\"ref\", \"fn\", \"n\", \"list\"), \"Region\", \"isSet\", 2, "
                        + "(3, \"{style}\", (3, \"x\")))), "
                        + "((\"x-b\", (\"{Region}\", \"b\")), (\"x-a\", ())))",
                results.get(2));
        // Empty properties become None and empty headers ().
        assertEquals("(6, (0, \"Endpoint\"), None, ())", results.get(3));
        assertEquals("(6, \"https://{Bucket}.example.com\", None, ())", results.get(4));
    }

    @Test
    public void rendersTemplatesAsWritten() {
        var parameters = """
                {"Endpoint": {"type": "string", "required": true}}
                """;
        var conditions = """
                [{"fn": "parseURL", "argv": [{"ref": "Endpoint"}], "assign": "url"}]
                """;
        var results = """
                [{"conditions": [], "type": "error", "error": "{{{url#authority} }} {Endpoint}{{}}"}]
                """;
        var bdd = lower(trait("1.1", parameters, conditions, results, 2, -1, 1, -1, 0, 100_000_001, 1));
        // Smithy's parts are rendered back to the trait's string, escapes and getAttr paths included.
        assertEquals("(5, \"{{{url#authority} }} {Endpoint}{{}}\")", lines(bdd.results()).get(1));
    }

    @Test
    public void lowersPathIndexes() {
        var parameters = """
                {"Bucket": {"type": "string", "required": true}}
                """;
        var conditions = """
                [{"fn": "split", "argv": [{"ref": "Bucket"}, "-", 2], "assign": "parts"},
                 {"fn": "isSet", "argv": [{"fn": "getAttr", "argv": [{"ref": "parts"}, "[1]"]}]}]
                """;
        var results = """
                [{"conditions": [], "type": "error", "error": "{Bucket}"}]
                """;
        var bdd = lower(trait("1.1", parameters, conditions, results, 2, -1, 1, -1, 0, 100_000_001, 1));
        assertEquals(
                "((2, \"isSet\", (1, (0, \"parts\"), \"[1]\")), None)",
                lines(bdd.conditions()).get(1));
    }

    @Test
    public void copiesNodesVerbatim() {
        var nodes = new int[] {-1, 1, -1, 0, -3, 1, 1, 100_000_001, -1};
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, nodes));
        assertEquals("(-1, 1, -1, 0, -3, 1, 1, 100000001, -1)", EndpointBddGenerator.literal(bdd.nodes()));
    }

    @Test
    public void acceptsTerminalRoot() {
        var bdd = lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, -1, -1, 1, -1));
        assertEquals(-1, bdd.root());
        assertEquals("(-1, 1, -1)", EndpointBddGenerator.literal(bdd.nodes()));
    }

    @Test
    public void rejectsComplementedResultReference() {
        // Smithy's validator doesn't catch this one.
        var e = assertThrows(CodegenException.class,
                () -> lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, -1, 1, -1, 0, -100_000_001, 1)));
        assertTrue(e.getMessage().contains("node 1 complements a result reference"));
    }

    @Test
    public void rejectsMalformedTerminalNode() {
        var e = assertThrows(CodegenException.class,
                () -> lower(trait("1.1", PARAMETERS, CONDITIONS, RESULTS, 2, 0, 1, -1, 0, 1, -1)));
        assertTrue(e.getMessage().contains("node 0"));
    }

    @Test
    public void rendersLiterals() {
        assertEquals("()", EndpointBddGenerator.literal(List.of()));
        assertEquals("(\"a\",)", EndpointBddGenerator.literal(List.of("a")));
        assertEquals("(None, True, False, -5)",
                EndpointBddGenerator.literal(java.util.Arrays.asList(
                        null,
                        true,
                        false,
                        -5)));
        assertEquals(
                "\"q\\\"b\\\\n\\n\\t\\x01\\u00e9\\U0001f600\"",
                EndpointBddGenerator.literal("q\"b\\n\n\t\u0001é😀"));
    }

    @Test
    public void rendersModule() {
        var parameters = """
                {"Endpoint": {"type": "string", "builtIn": "SDK::Endpoint"}}
                """;
        var conditions = """
                [{"fn": "isSet", "argv": [{"ref": "Endpoint"}]}]
                """;
        var results = """
                [{"conditions": [], "type": "endpoint", "endpoint": {"url": {"ref": "Endpoint"}}},
                 {"conditions": [], "type": "error", "error": "no endpoint"}]
                """;
        var trait = trait("1.1", parameters, conditions, results, 2, -1, 1, -1, 0, 100_000_001, 100_000_002);
        var source = EndpointBddGenerator.render("example#Service", trait, lower(trait));
        assertEquals("""
                # Code generated by smithy-python-codegen DO NOT EDIT.

                \"""Endpoint BDD for example#Service.\"""

                from smithy_core.endpoints import EndpointBdd

                # fmt: off
                # Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.
                BDD = EndpointBdd(
                    # (name, type, required, default, builtin, client_context)
                    parameters=(
                        ("Endpoint", "string", False, None, "SDK::Endpoint", False),
                    ),
                    functions=("isSet",),
                    conditions=(
                        ((2, "isSet", (0, "Endpoint")), None),  # 0: isSet(Endpoint)
                    ),
                    results=(
                        None,  # 0: no match
                        (6, (0, "Endpoint"), None, ()),  # 1
                        (5, "no endpoint"),  # 2
                    ),
                    root=2,
                    # (condition, high, low); 1 and -1 are terminals, a negative reference is a
                    # complement edge, and 100_000_000 + k is result k.
                    nodes=(
                        -1, 1, -1,
                        0, 100_000_001, 100_000_002,
                    ),
                )
                # fmt: on
                """, source);
    }

    private static EndpointBddGenerator.EndpointBdd lower(EndpointBddTrait trait) {
        return lower(trait, Set.of());
    }

    private static EndpointBddGenerator.EndpointBdd lower(EndpointBddTrait trait, Set<String> clientContext) {
        return EndpointBddGenerator.lower(trait, clientContext);
    }

    private static List<String> lines(List<Object> section) {
        var out = new ArrayList<String>();
        for (Object item : section) {
            out.add(EndpointBddGenerator.literal(item));
        }
        return out;
    }

    static EndpointBddTrait trait(
            String version,
            String parameters,
            String conditions,
            String results,
            int root,
            int... nodes
    ) {
        var buffer = ByteBuffer.allocate(nodes.length * 4);
        for (int n : nodes) {
            buffer.putInt(n);
        }
        var node = ObjectNode.builder()
                .withMember("version", version)
                .withMember("parameters", Node.parse(parameters))
                .withMember("conditions", Node.parse(conditions))
                .withMember("results", Node.parse(results))
                .withMember("root", root)
                .withMember("nodeCount", nodes.length / 3)
                .withMember("nodes", Base64.getEncoder().encodeToString(buffer.array()))
                .build();
        return EndpointBddTrait.fromNode(node);
    }
}
