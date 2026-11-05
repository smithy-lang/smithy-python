/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.generators;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.model.node.Node;
import software.amazon.smithy.python.codegen.GenerationContext;
import software.amazon.smithy.python.codegen.PythonSettings;
import software.amazon.smithy.rulesengine.language.Endpoint;
import software.amazon.smithy.rulesengine.language.RulesVersion;
import software.amazon.smithy.rulesengine.language.evaluation.value.Value;
import software.amazon.smithy.rulesengine.language.syntax.Identifier;
import software.amazon.smithy.rulesengine.language.syntax.expressions.Expression;
import software.amazon.smithy.rulesengine.language.syntax.expressions.Reference;
import software.amazon.smithy.rulesengine.language.syntax.expressions.Template;
import software.amazon.smithy.rulesengine.language.syntax.expressions.functions.GetAttr;
import software.amazon.smithy.rulesengine.language.syntax.expressions.functions.LibraryFunction;
import software.amazon.smithy.rulesengine.language.syntax.expressions.literal.Literal;
import software.amazon.smithy.rulesengine.language.syntax.expressions.literal.LiteralVisitor;
import software.amazon.smithy.rulesengine.language.syntax.parameters.Parameter;
import software.amazon.smithy.rulesengine.language.syntax.parameters.ParameterType;
import software.amazon.smithy.rulesengine.language.syntax.rule.Condition;
import software.amazon.smithy.rulesengine.language.syntax.rule.EndpointRule;
import software.amazon.smithy.rulesengine.language.syntax.rule.ErrorRule;
import software.amazon.smithy.rulesengine.language.syntax.rule.Rule;
import software.amazon.smithy.rulesengine.logic.bdd.Bdd;
import software.amazon.smithy.rulesengine.traits.EndpointBddTrait;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Lowers a service's {@code smithy.rules#endpointBdd} trait into an endpoint BDD and writes it
 * to {@code <pkg>/_private/endpoints.py}.
 *
 * <p>The BDD is a {@code smithy_core.endpoints.EndpointBdd} of Python literals that
 * re-encodes the trait. Lowering keeps no engine decisions: names stay names, tags are
 * small ints, and the trait's nodes are copied verbatim. Python values are modeled here
 * as {@code String}, {@code Boolean}, {@code Integer}, {@code null} and {@link List}
 * (a tuple).
 */
@SmithyInternalApi
public final class EndpointBddGenerator implements Runnable {

    private static final int RESULT_OFFSET = Bdd.RESULT_OFFSET;

    // Tags lead expression and result tuples; smithy_core.endpoints._types.Tag has the same values.
    private static final int REF = 0;
    private static final int ATTR = 1;
    private static final int CALL = 2;
    private static final int LIST = 3;
    private static final int MAP = 4;
    private static final int ERROR = 5;
    private static final int ENDPOINT = 6;
    private static final String TAG_LEGEND = "# Tags: ref=0, attr=1, call=2, list=3, map=4, error=5, endpoint=6.\n";
    private static final Comparator<String> CODE_POINT_ORDER = (a, b) -> Arrays.compare(
            a.codePoints().toArray(),
            b.codePoints().toArray());

    private final GenerationContext context;

    public EndpointBddGenerator(GenerationContext context) {
        this.context = context;
    }

    /**
     * A lowered endpoint BDD: the fields of a Python {@code EndpointBdd}.
     *
     * @param parameters the parameters field.
     * @param functions the functions field.
     * @param conditions the conditions field.
     * @param results the results field.
     * @param root the root field.
     * @param nodes the nodes field.
     */
    public record EndpointBdd(
            List<Object> parameters,
            List<Object> functions,
            List<Object> conditions,
            List<Object> results,
            int root,
            List<Object> nodes) {}

    @Override
    public void run() {
        var filename = String.format("src/%s/_private/endpoints.py", context.settings().moduleName());
        context.fileManifest().writeFile(filename, renderModule(context));
    }

    /**
     * The {@code BDD} constant of a client's generated endpoints module.
     *
     * @param settings the client's settings.
     * @return the symbol.
     */
    public static Symbol bddSymbol(PythonSettings settings) {
        var namespace = String.format("%s._private.endpoints", settings.moduleName());
        return Symbol.builder()
                .name("BDD")
                .namespace(namespace, ".")
                .definitionFile(String.format("./src/%s/_private/endpoints.py", settings.moduleName()))
                .build();
    }

    /**
     * Lowers the service's endpointBdd trait and renders the endpoints module source.
     *
     * @param context the generation context of the service carrying the endpointBdd trait.
     * @return the module source.
     */
    private static String renderModule(GenerationContext context) {
        var service = context.settings().service(context.model());
        var trait = service.getTrait(EndpointBddTrait.class)
                .orElseThrow(() -> new CodegenException(service.getId() + " has no endpointBdd trait"));
        var clientContextAttributes = new LinkedHashMap<String, String>();
        ConfigGenerator.clientContextFields(context)
                .forEach((name, field) -> clientContextAttributes.put(name, field.name()));
        return render(service.getId().toString(), trait, lower(trait, clientContextAttributes));
    }

    /**
     * Lowers an endpointBdd trait into an endpoint BDD.
     *
     * @param trait the trait to lower.
     * @param clientContextAttributes the config attribute each of the service's
     *     clientContextParams reads, by parameter name.
     * @return the BDD.
     */
    public static EndpointBdd lower(EndpointBddTrait trait, Map<String, String> clientContextAttributes) {
        return new Lowering(trait, Map.copyOf(clientContextAttributes)).bdd();
    }

    /**
     * Renders a lowered BDD as the source of a generated endpoints module.
     *
     * @param serviceId the service shape ID, used in the module docstring.
     * @param trait the trait the BDD was lowered from, used for comments.
     * @param bdd the lowered BDD.
     * @return the module source.
     */
    public static String render(String serviceId, EndpointBddTrait trait, EndpointBdd bdd) {
        var out = new StringBuilder();
        out.append("# Code generated by smithy-python-codegen DO NOT EDIT.\n\n");
        out.append("\"\"\"Endpoint BDD for ").append(serviceId).append(".\"\"\"\n\n");
        out.append("from smithy_core.endpoints import EndpointBdd\n\n");
        // The generator lays the literal out one entry per line; keep formatters from exploding it.
        out.append("# fmt: off\n");
        out.append(TAG_LEGEND);
        out.append("BDD = EndpointBdd(\n");
        if (!bdd.parameters().isEmpty()) {
            out.append("    # (name, type, required, default, builtin, client_context_attribute)\n");
        }
        writeLines(out, "parameters", bdd.parameters(), null);
        out.append("    functions=").append(literal(bdd.functions())).append(",\n");
        var conditionComments = new ArrayList<String>();
        for (var condition : trait.getConditions()) {
            conditionComments.add(condition.toString());
        }
        writeLines(out, "conditions", bdd.conditions(), conditionComments);
        // Nodes point at results by index, so each result carries its index.
        var resultComments = new ArrayList<String>();
        resultComments.add("no match");
        while (resultComments.size() < bdd.results().size()) {
            resultComments.add("");
        }
        writeLines(out, "results", bdd.results(), resultComments);
        out.append("    root=").append(formatReference(bdd.root())).append(",\n");
        writeNodes(out, bdd.nodes());
        out.append(")\n");
        out.append("# fmt: on\n");
        return out.toString();
    }

    private static void writeLines(StringBuilder out, String field, List<Object> items, List<String> comments) {
        out.append("    ").append(field).append('=');
        if (items.isEmpty()) {
            out.append("(),\n");
            return;
        }
        out.append("(\n");
        for (int i = 0; i < items.size(); i++) {
            out.append("        ").append(literal(items.get(i))).append(',');
            if (comments != null) {
                out.append("  # ").append(i);
                var comment = comments.get(i);
                if (!comment.isEmpty() && isPrintableAscii(comment)) {
                    out.append(": ").append(comment);
                }
            }
            out.append('\n');
        }
        out.append("    ),\n");
    }

    private static void writeNodes(StringBuilder out, List<Object> nodes) {
        if (!nodes.isEmpty()) {
            out.append("    # (condition, high, low); 1 and -1 are terminals, a negative reference is a\n");
            out.append("    # complement edge, and 100_000_000 + k is result k.\n");
        }
        out.append("    nodes=");
        if (nodes.isEmpty()) {
            out.append("(),\n");
            return;
        }
        out.append("(\n");
        for (int i = 0; i < nodes.size(); i += 3) {
            out.append("        ")
                    .append(nodes.get(i))
                    .append(", ")
                    .append(formatReference((Integer) nodes.get(i + 1)))
                    .append(", ")
                    .append(formatReference((Integer) nodes.get(i + 2)))
                    .append(",\n");
        }
        out.append("    ),\n");
    }

    // A node or result reference; result references are written 100_000_000 + k, so k is easy to read.
    private static String formatReference(int ref) {
        if (ref < RESULT_OFFSET) {
            return Integer.toString(ref);
        }
        return String.format(Locale.ROOT, "%,d", ref).replace(',', '_');
    }

    private static boolean isPrintableAscii(String s) {
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < 0x20 || c > 0x7e) {
                return false;
            }
        }
        return true;
    }

    /**
     * Renders a lowered value as a Python literal on one line.
     *
     * @param value a String, Boolean, Integer, null or List (a tuple).
     * @return the Python literal.
     */
    public static String literal(Object value) {
        var out = new StringBuilder();
        writeLiteral(out, value);
        return out.toString();
    }

    private static void writeLiteral(StringBuilder out, Object value) {
        if (value == null) {
            out.append("None");
        } else if (value instanceof Boolean b) {
            out.append(b ? "True" : "False");
        } else if (value instanceof Integer i) {
            out.append(i);
        } else if (value instanceof String s) {
            writeString(out, s);
        } else if (value instanceof List<?> items) {
            out.append('(');
            for (int i = 0; i < items.size(); i++) {
                if (i > 0) {
                    out.append(", ");
                }
                writeLiteral(out, items.get(i));
            }
            if (items.size() == 1) {
                out.append(',');
            }
            out.append(')');
        } else {
            throw new CodegenException("Unexpected endpoint BDD value: " + value);
        }
    }

    // Writes an ASCII-only, double-quoted Python str literal.
    private static void writeString(StringBuilder out, String s) {
        out.append('"');
        s.codePoints().forEach(c -> {
            switch (c) {
                case '\\' -> out.append("\\\\");
                case '"' -> out.append("\\\"");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20 || c == 0x7f) {
                        out.append(String.format("\\x%02x", c));
                    } else if (c < 0x7f) {
                        out.append((char) c);
                    } else if (c <= 0xffff) {
                        out.append(String.format("\\u%04x", c));
                    } else {
                        out.append(String.format("\\U%08x", c));
                    }
                }
            }
        });
        out.append('"');
    }

    private static List<Object> tuple(Object... items) {
        return Arrays.asList(items);
    }

    private static final class Lowering {
        private final EndpointBddTrait trait;
        private final Map<String, String> clientContextAttributes;
        private final Map<String, Parameter> parameters = new LinkedHashMap<>();
        private final Set<String> references = new HashSet<>();
        private final Set<String> functions = new TreeSet<>(CODE_POINT_ORDER);

        Lowering(EndpointBddTrait trait, Map<String, String> clientContextAttributes) {
            this.trait = trait;
            this.clientContextAttributes = clientContextAttributes;
        }

        EndpointBdd bdd() {
            // One trait version.
            if (!RulesVersion.V1_1.equals(trait.getVersion())) {
                throw invalid("endpointBdd version " + trait.getVersion() + " is not supported; expected 1.1");
            }
            for (Parameter parameter : trait.getParameters()) {
                parameters.put(parameter.getNameString(), parameter);
            }
            var conditions = new ArrayList<Object>();
            for (Condition condition : trait.getConditions()) {
                conditions.add(tuple(
                        expression(condition.getFunction()),
                        condition.getResult().map(Identifier::toString).orElse(null)));
            }
            var results = new ArrayList<Object>();
            List<Rule> rules = trait.getResults();
            for (int i = 0; i < rules.size(); i++) {
                results.add(result(i, rules.get(i)));
            }

            var nodes = nodes();
            return new EndpointBdd(
                    parameters(),
                    new ArrayList<Object>(functions),
                    conditions,
                    results,
                    trait.getBdd().getRootRef(),
                    nodes);
        }

        // Normalized parameter fields; unread optional parameters are dropped.
        private List<Object> parameters() {
            var out = new ArrayList<Object>();
            for (Parameter parameter : parameters.values()) {
                String name = parameter.getNameString();
                if (!parameter.isRequired() && !references.contains(name)) {
                    continue;
                }
                out.add(tuple(
                        name,
                        type(parameter.getType()),
                        parameter.isRequired(),
                        parameter.getDefault().map(this::defaultValue).orElse(null),
                        parameter.getBuiltIn().orElse(null),
                        clientContextAttributes.get(name)));
            }
            return out;
        }

        private static String type(ParameterType type) {
            return switch (type) {
                case STRING -> "string";
                case BOOLEAN -> "boolean";
                case STRING_ARRAY -> "stringArray";
            };
        }

        private Object defaultValue(Value value) {
            Node node = value.toNode();
            if (node.isStringNode()) {
                return node.expectStringNode().getValue();
            } else if (node.isBooleanNode()) {
                return node.expectBooleanNode().getValue();
            } else if (node.isArrayNode()) {
                var out = new ArrayList<Object>();
                for (Node element : node.expectArrayNode().getElements()) {
                    out.add(element.expectStringNode().getValue());
                }
                return out;
            }
            throw invalid("unsupported parameter default " + Node.printJson(node));
        }

        // Results, with the no-match result at index 0.
        private Object result(int index, Rule rule) {
            if (index == 0) {
                return null;
            }
            if (rule instanceof ErrorRule error) {
                return tuple(ERROR, expression(error.getError()));
            } else if (rule instanceof EndpointRule endpointRule) {
                Endpoint endpoint = endpointRule.getEndpoint();
                Object properties = null;
                if (!endpoint.getProperties().isEmpty()) {
                    properties = map(endpoint.getProperties());
                }
                var headers = new ArrayList<Object>();
                for (Map.Entry<String, List<Expression>> header : endpoint.getHeaders().entrySet()) {
                    var values = new ArrayList<Object>();
                    for (Expression value : header.getValue()) {
                        values.add(expression(value));
                    }
                    headers.add(tuple(header.getKey(), values));
                }
                return tuple(ENDPOINT, expression(endpoint.getUrl()), properties, headers);
            }
            throw invalid("result " + index + " is not an endpoint or error result");
        }

        private Object expression(Expression expression) {
            if (expression instanceof Literal literal) {
                return literal(literal);
            } else if (expression instanceof Reference reference) {
                return reference(reference);
            } else if (expression instanceof GetAttr getAttr) {
                return tuple(ATTR, expression(getAttr.getTarget()), path(getAttr));
            } else if (expression instanceof LibraryFunction function) {
                functions.add(function.getName());
                var call = new ArrayList<Object>();
                call.add(CALL);
                call.add(function.getName());
                for (Expression argument : function.getArguments()) {
                    call.add(expression(argument));
                }
                return call;
            }
            throw invalid("unsupported expression " + expression);
        }

        private Object reference(Reference reference) {
            return tuple(REF, name(reference));
        }

        private String name(Reference reference) {
            String name = reference.getName().toString();
            references.add(name);
            return name;
        }

        // getAttr paths, parsed by Smithy and written back as text: keys joined by '.', each index
        // as [i].
        private String path(GetAttr getAttr) {
            var path = new StringBuilder();
            for (GetAttr.Part part : getAttr.getPath()) {
                if (part instanceof GetAttr.Part.Key key) {
                    path.append(path.isEmpty() ? "" : ".").append(key.key());
                } else if (part instanceof GetAttr.Part.Index index) {
                    path.append('[').append(index.index()).append(']');
                } else {
                    throw invalid("unsupported getAttr path part " + part);
                }
            }
            if (path.isEmpty()) {
                throw invalid("empty getAttr path in " + getAttr);
            }
            return path.toString();
        }

        private Object literal(Literal literal) {
            return literal.accept(new LiteralVisitor<Object>() {
                @Override
                public Object visitBoolean(boolean b) {
                    return b;
                }

                @Override
                public Object visitString(Template value) {
                    return template(value);
                }

                @Override
                public Object visitRecord(Map<Identifier, Literal> members) {
                    return map(members);
                }

                @Override
                public Object visitTuple(List<Literal> members) {
                    var list = new ArrayList<Object>();
                    list.add(LIST);
                    for (Literal member : members) {
                        list.add(literal(member));
                    }
                    return list;
                }

                @Override
                public Object visitInteger(int value) {
                    return value;
                }
            });
        }

        private List<Object> map(Map<Identifier, Literal> members) {
            var keys = new ArrayList<Object>();
            var map = new ArrayList<Object>();
            map.add(MAP);
            map.add(keys);
            for (Map.Entry<Identifier, Literal> member : members.entrySet()) {
                keys.add(member.getKey().toString());
                map.add(literal(member.getValue()));
            }
            return map;
        }

        // Every string in an expression position is a template, kept as a template string.
        // It is rendered back from Smithy's parts, because Template.toNode() drops the escapes.
        private String template(Template template) {
            var out = new StringBuilder();
            for (Template.Part part : template.getParts()) {
                if (part instanceof Template.Literal literal) {
                    out.append(literal.getValue().replace("{", "{{").replace("}", "}}"));
                } else if (part instanceof Template.Dynamic placeholder) {
                    out.append('{').append(placeholder(template, placeholder.toExpression())).append('}');
                } else {
                    throw invalid("unsupported template part in " + template);
                }
            }
            return out.toString();
        }

        private String placeholder(Template template, Expression expression) {
            if (expression instanceof Reference reference) {
                return name(reference);
            } else if (expression instanceof GetAttr getAttr && getAttr.getTarget() instanceof Reference base) {
                return name(base) + "#" + path(getAttr);
            }
            throw invalid("malformed template placeholder in " + template);
        }

        // Nodes copied verbatim. Smithy's validator checks the indexes and references, but
        // not that node 0 is the terminal the runtime relies on, nor that no edge
        // complements a result reference.
        private List<Object> nodes() {
            Bdd bdd = trait.getBdd();
            int nodeCount = bdd.getNodeCount();
            if (nodeCount < 1 || bdd.getVariable(0) != -1 || bdd.getHigh(0) != 1 || bdd.getLow(0) != -1) {
                throw invalid("node 0 must be the terminal (-1, 1, -1)");
            }
            var nodes = new ArrayList<Object>(nodeCount * 3);
            for (int i = 0; i < nodeCount; i++) {
                int high = bdd.getHigh(i);
                int low = bdd.getLow(i);
                if (high <= -RESULT_OFFSET || low <= -RESULT_OFFSET) {
                    throw invalid("node " + i + " complements a result reference");
                }
                nodes.add(bdd.getVariable(i));
                nodes.add(high);
                nodes.add(low);
            }
            return nodes;
        }

        private static CodegenException invalid(String message) {
            return new CodegenException("Invalid endpointBdd trait: " + message);
        }
    }
}
