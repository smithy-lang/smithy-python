/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: Apache-2.0
 */
package software.amazon.smithy.python.codegen.writer;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Logger;
import software.amazon.smithy.codegen.core.CodegenException;
import software.amazon.smithy.utils.SmithyInternalApi;

/**
 * A Pandoc process that converts documentation for the duration of one generation.
 *
 * <p>Starting Pandoc costs far more than converting a documentation string, so
 * {@link MarkdownConverter} sends the conversions of a generation to one
 * {@code pandoc lua} process running {@code pandoc-worker.lua} instead of starting
 * Pandoc per string. The script uses Pandoc's own reader and writer with the
 * settings of the {@code pandoc} command line, and this class applies the input
 * handling the command line does before reading.
 *
 * <p>{@code convert} returns empty whenever its result could differ from the
 * command line: when this Pandoc lacks the Lua API the worker needs (Pandoc
 * 3.2 or later), on Windows, after {@link #close}, or when Pandoc logs a message or
 * fails for a document. The caller then runs the command line, which reproduces its
 * exact output, warnings, and errors. A timeout, interruption, or broken exchange
 * stops the process and throws instead.
 *
 * <p>The process starts on the first conversion and must be closed when the
 * generation ends.
 */
@SmithyInternalApi
public final class PandocWorker implements AutoCloseable {

    private static final Logger LOGGER = Logger.getLogger(PandocWorker.class.getName());
    private static final Duration TIMEOUT = Duration.ofSeconds(10);
    private static final long CLOSE_WAIT_SECONDS = 2;
    private static final int MAX_HEADER_BYTES = 256;
    private static final int MAX_REPLY_BYTES = 64 * 1024 * 1024;
    private static final int TAB_STOP = 4;
    private static final char BYTE_ORDER_MARK = 0xFEFF;

    private enum State {
        NEW, READY, UNAVAILABLE, FAILED, CLOSED
    }

    private final List<String> command;
    private final Duration timeout;
    // Serializes conversions. close() never takes it, so it cannot wait on a conversion.
    private final Object conversionLock = new Object();
    private final AtomicReference<State> state = new AtomicReference<>(State.NEW);
    private final AtomicInteger fallbacks = new AtomicInteger();
    private volatile Process process;
    private volatile ExecutorService executor;
    private volatile OutputStream requests;
    private volatile InputStream replies;

    /**
     * Creates a worker that starts {@code pandoc lua} on first use.
     */
    public PandocWorker() {
        this(null, TIMEOUT);
    }

    /**
     * @param command The command to start instead of {@code pandoc lua}, or null.
     * @param timeout The deadline for starting and for each conversion.
     */
    PandocWorker(List<String> command, Duration timeout) {
        this.command = command;
        this.timeout = timeout;
    }

    /**
     * Converts one document with the worker.
     *
     * @param input The document, exactly as it would be written to the command line's stdin.
     * @param fromFormat The Pandoc input format.
     * @param toFormat The Pandoc output format.
     * @return The raw Pandoc output, or empty if the caller must use the command line.
     * @throws IOException if the exchange with the worker breaks.
     * @throws InterruptedException if interrupted while waiting for the worker.
     */
    Optional<String> convert(String input, String fromFormat, String toFormat)
            throws IOException, InterruptedException {
        synchronized (conversionLock) {
            if (!ensureStarted()) {
                return Optional.empty();
            }
            byte[] body = prepareInput(input).getBytes(StandardCharsets.UTF_8);
            OutputStream out = requests;
            InputStream in = replies;
            Optional<String> output = call(() -> exchange(out, in, fromFormat, toFormat, body));
            if (output.isEmpty()) {
                fallbacks.incrementAndGet();
            }
            return output;
        }
    }

    /**
     * @return Returns true while the worker process is alive.
     */
    boolean isRunning() {
        Process current = process;
        return current != null && current.isAlive();
    }

    /**
     * Stops the worker. Later conversions use the command line, and a conversion
     * still in progress fails.
     */
    @Override
    public void close() {
        State previous = state.getAndSet(State.CLOSED);
        if (previous == State.CLOSED) {
            return;
        }
        // The worker holds no state worth a graceful exit, so it is killed first. A
        // conversion blocked on its pipes may hold their locks, and the kill breaks the
        // pipes, which releases them.
        stop(State.CLOSED);
        Process current = process;
        if (current != null) {
            try {
                if (!current.waitFor(CLOSE_WAIT_SECONDS, TimeUnit.SECONDS)) {
                    LOGGER.warning("The pandoc worker did not exit after it was stopped.");
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        int count = fallbacks.get();
        if (count > 0) {
            LOGGER.info(() -> count + " documentation conversions ran a separate pandoc process because "
                    + "Pandoc logged a message or failed for them.");
        }
    }

    private boolean ensureStarted() throws IOException, InterruptedException {
        switch (state.get()) {
            case READY:
                return true;
            case UNAVAILABLE:
            case CLOSED:
                return false;
            case FAILED:
                throw new IOException("The pandoc worker stopped after an earlier failure.");
            default:
                break;
        }

        if (System.getProperty("os.name", "").startsWith("Windows")) {
            // Lua writes stdout in text mode there, which breaks the byte counts of replies.
            state.compareAndSet(State.NEW, State.UNAVAILABLE);
            return false;
        }

        List<String> startCommand = command != null
                ? command
                : List.of("pandoc", "lua", "-e", loadScript());
        Process started;
        try {
            started = new ProcessBuilder(startCommand)
                    .redirectError(ProcessBuilder.Redirect.DISCARD)
                    .start();
        } catch (IOException e) {
            // For example, pandoc is not on the PATH. The command line reports that itself.
            LOGGER.fine(() -> "Unable to start the pandoc worker: " + e.getMessage());
            state.compareAndSet(State.NEW, State.UNAVAILABLE);
            return false;
        }
        process = started;
        requests = new BufferedOutputStream(started.getOutputStream());
        replies = new BufferedInputStream(started.getInputStream());
        executor = Executors.newSingleThreadExecutor(PandocWorker::newDaemonThread);
        if (state.get() == State.CLOSED) {
            stop(State.CLOSED);
            return false;
        }

        InputStream in = replies;
        String handshake = call(() -> readLine(in));
        if (handshake == null || !handshake.startsWith("READY ")) {
            // The process exited or answered without the protocol, e.g. Pandoc older than 3.0
            // has no "lua" command and 3.0 to 3.1 report UNSUPPORTED.
            stop(State.UNAVAILABLE);
            LOGGER.warning("This pandoc cannot run a reusable documentation worker, which requires Pandoc 3.2 "
                    + "or later. Starting a separate pandoc process for each documentation string instead.");
            return false;
        }
        if (!state.compareAndSet(State.NEW, State.READY)) {
            stop(State.CLOSED);
            return false;
        }
        LOGGER.fine(() -> "Started a pandoc worker for " + handshake.substring("READY ".length()));
        return true;
    }

    /**
     * Runs one complete exchange with the worker under the deadline. Any failure
     * stops the worker, so a stuck write or read can never outlive the call.
     */
    private <T> T call(Callable<T> exchange) throws IOException, InterruptedException {
        Future<T> future;
        try {
            future = executor.submit(exchange);
        } catch (RejectedExecutionException e) {
            // close() or a failure on another thread already stopped the worker.
            stop(State.FAILED);
            throw new IOException("The pandoc worker stopped during a conversion.", e);
        }
        try {
            return future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            stop(State.FAILED);
            throw new CodegenException("Pandoc process timed out after " + timeout.toSeconds() + " seconds");
        } catch (InterruptedException e) {
            stop(State.FAILED);
            throw e;
        } catch (ExecutionException e) {
            stop(State.FAILED);
            if (e.getCause() instanceof IOException) {
                throw (IOException) e.getCause();
            }
            throw new CodegenException("The pandoc worker failed: " + e.getCause(), e.getCause());
        }
    }

    // Kills the process without waiting. Its pipes close, which ends any blocked exchange.
    private void stop(State next) {
        state.updateAndGet(current -> current == State.CLOSED ? State.CLOSED : next);
        Process current = process;
        if (current != null) {
            current.destroyForcibly();
        }
        ExecutorService currentExecutor = executor;
        if (currentExecutor != null) {
            currentExecutor.shutdownNow();
        }
    }

    private static Optional<String> exchange(
            OutputStream out,
            InputStream in,
            String fromFormat,
            String toFormat,
            byte[] body
    ) throws IOException {
        String header = fromFormat + "\n" + toFormat + "\n" + body.length + "\n";
        out.write(header.getBytes(StandardCharsets.US_ASCII));
        out.write(body);
        out.flush();

        String reply = readLine(in);
        if (reply == null) {
            throw new EOFException("The pandoc worker exited unexpectedly.");
        }
        if (reply.equals("FALLBACK")) {
            return Optional.empty();
        }
        if (!reply.startsWith("OK ")) {
            throw malformed(reply);
        }
        int size;
        try {
            size = Integer.parseInt(reply.substring("OK ".length()));
        } catch (NumberFormatException e) {
            throw malformed(reply);
        }
        if (size < 0 || size > MAX_REPLY_BYTES) {
            throw malformed(reply);
        }
        byte[] output = in.readNBytes(size);
        if (output.length != size) {
            throw new EOFException("The pandoc worker exited unexpectedly.");
        }
        return Optional.of(new String(output, StandardCharsets.UTF_8));
    }

    // Reads one short ASCII line, or returns null at the end of the stream.
    private static String readLine(InputStream in) throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        while (true) {
            int next = in.read();
            if (next == -1) {
                return null;
            }
            if (next == '\n') {
                return line.toString(StandardCharsets.US_ASCII);
            }
            if (line.size() >= MAX_HEADER_BYTES) {
                throw malformed(line.toString(StandardCharsets.US_ASCII));
            }
            line.write(next);
        }
    }

    private static IOException malformed(String reply) {
        return new IOException("Malformed reply from the pandoc worker: " + reply);
    }

    /**
     * Applies the input handling of the pandoc command line, which {@code pandoc.read}
     * does not do: it drops a byte order mark and carriage returns, then expands tabs
     * to tab stops every four columns on each line, which also ends the text with a newline.
     */
    static String prepareInput(String input) {
        String text = !input.isEmpty() && input.charAt(0) == BYTE_ORDER_MARK ? input.substring(1) : input;
        text = text.replace("\r", "");
        StringBuilder result = new StringBuilder(text.length() + 1);
        int column = 0;
        int index = 0;
        while (index < text.length()) {
            int codePoint = text.codePointAt(index);
            index += Character.charCount(codePoint);
            if (codePoint == '\n') {
                result.append('\n');
                column = 0;
            } else if (codePoint == '\t') {
                int spaces = TAB_STOP - (column % TAB_STOP);
                result.append(" ".repeat(spaces));
                column += spaces;
            } else {
                result.appendCodePoint(codePoint);
                column++;
            }
        }
        if (result.length() > 0 && result.charAt(result.length() - 1) != '\n') {
            result.append('\n');
        }
        return result.toString();
    }

    private static String loadScript() throws IOException {
        InputStream stream = PandocWorker.class.getResourceAsStream("pandoc-worker.lua");
        if (stream == null) {
            throw new IOException("Missing resource pandoc-worker.lua");
        }
        try {
            return new String(stream.readAllBytes(), StandardCharsets.UTF_8);
        } finally {
            stream.close();
        }
    }

    private static Thread newDaemonThread(Runnable runnable) {
        Thread thread = new Thread(runnable, "smithy-python-pandoc-worker");
        thread.setDaemon(true);
        return thread;
    }
}
