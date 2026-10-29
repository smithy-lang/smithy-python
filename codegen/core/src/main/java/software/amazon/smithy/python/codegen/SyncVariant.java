/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen;

import java.util.ArrayList;
import java.util.Map;
import java.util.Set;
import java.util.function.UnaryOperator;
import java.util.regex.Pattern;
import software.amazon.smithy.codegen.core.Symbol;
import software.amazon.smithy.codegen.core.SymbolReference;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * Derives the sync variant of generated client code from its async variant.
 *
 * <p>Runtime libraries pair every async component with a sync twin by convention: the
 * async one lives under an {@code aio} package and carries an {@code Async} prefix, the
 * sync one drops both. Generators therefore write each file once, and the sync pass
 * maps symbols and strips {@code async}/{@code await} from the code templates.
 */
@SmithyInternalApi
public final class SyncVariant {

    private static final Pattern ASYNC_PREFIX = Pattern.compile("\\bAsync(?=[A-Z])");
    private static final Pattern ASYNC_KEYWORD = Pattern.compile("\\basync (?=def |with |for )");
    private static final Pattern AWAIT_KEYWORD = Pattern.compile("\\bawait ");

    // Sync twins that don't follow the naming convention.
    private static final Map<String, Symbol> SPECIAL_CASES = Map.of(
            "smithy_http.aio.aiohttp.AIOHTTPClient",
            Symbol.builder()
                    .name("Urllib3HTTPClient")
                    .namespace("smithy_http.urllib3", ".")
                    .addDependency(SmithyPythonDependency.SMITHY_HTTP.withOptionalDependencies("urllib3"))
                    .build());

    // Generated modules typed by the config, so each has a sync twin.
    private static final Set<String> SYNC_MODULES = Set.of("client", "config", "user_agent");

    private SyncVariant() {}

    /**
     * Strips the {@code async} and {@code await} keywords from a code template.
     *
     * <p>Only apply this to code templates, never to documentation pulled from a model.
     *
     * @param template The async code template.
     * @return Returns the sync code template.
     */
    public static String toSyncCode(String template) {
        return AWAIT_KEYWORD.matcher(ASYNC_KEYWORD.matcher(template).replaceAll("")).replaceAll("");
    }

    /**
     * @param name An async class or type name, such as {@code AsyncSTSClient}.
     * @return Returns the name of its sync twin, such as {@code STSClient}.
     */
    public static String toSyncName(String name) {
        return ASYNC_PREFIX.matcher(name).replaceAll("");
    }

    /**
     * Maps an async runtime symbol to its sync twin.
     *
     * @param symbol The symbol to map.
     * @return Returns the sync twin, or the symbol itself if it is mode-neutral.
     */
    public static Symbol toSync(Symbol symbol) {
        var special = SPECIAL_CASES.get(symbol.getFullName());
        if (special != null) {
            return special;
        }
        var references = new ArrayList<SymbolReference>();
        var name = symbol.getName();
        var changed = false;
        for (var reference : symbol.getReferences()) {
            var mapped = toSync(reference.getSymbol());
            if (!mapped.equals(reference.getSymbol())) {
                changed = true;
                name = Pattern.compile("\\b" + Pattern.quote(reference.getSymbol().getName()) + "\\b")
                        .matcher(name)
                        .replaceAll(mapped.getName());
            }
            var alias = reference.getAlias().equals(reference.getSymbol().getName())
                    ? mapped.getName()
                    : reference.getAlias();
            references.add(reference.toBuilder().symbol(mapped).alias(alias).build());
        }
        var namespace = symbol.getNamespace();
        if (isAioNamespace(namespace)) {
            namespace = namespace.replace(".aio.", ".").replaceAll("\\.aio$", "");
            name = toSyncName(name);
            changed = true;
        }
        if (!changed) {
            return symbol;
        }
        return symbol.toBuilder()
                .name(name)
                .namespace(namespace, ".")
                .references(references)
                .build();
    }

    /**
     * Creates the symbol mapper for the sync variant of a generated client.
     *
     * <p>Generated symbols typed by the config move into the {@code sync} subpackage; all
     * other symbols map through {@link #toSync(Symbol)}.
     *
     * @param settings The client settings.
     * @return Returns the mapper.
     */
    public static UnaryOperator<Symbol> mapper(PythonSettings settings) {
        var module = settings.moduleName();
        return symbol -> {
            var namespace = symbol.getNamespace();
            if (namespace.startsWith(module + ".")
                    && SYNC_MODULES.contains(namespace.substring(module.length() + 1))) {
                var file = namespace.substring(module.length() + 1);
                return symbol.toBuilder()
                        .name(toSyncName(symbol.getName()))
                        .namespace(module + ".sync." + file, ".")
                        .definitionFile("./src/" + module + "/sync/" + file + ".py")
                        .build();
            }
            return toSync(symbol);
        };
    }

    private static boolean isAioNamespace(String namespace) {
        return namespace.contains(".aio.") || namespace.endsWith(".aio");
    }
}
