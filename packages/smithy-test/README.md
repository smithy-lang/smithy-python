# smithy-test

Test-support helpers shared by generated Smithy clients, kept out of the runtime
packages. Currently provides `deep_equal`, a structural equality check used by the
generated protocol tests that treats `NaN == NaN`, and `xml_equal`, a semantic XML
equality check. It also provides `verify_models` and `ConformanceError` for
generated conformance tests, `check_rules_case` for endpoint rule tests, and
`mock` with `HTTPMockController`, `HTTPMockExpectation`, `HTTPMockError` and
`HTTPMockMismatchError` for answering a sync client's requests without sending them,
and `instrument` for recording a live-service test and playing it back offline.

## Recording and playing back live-service tests

`instrument` (`instrument_async` for async clients) lets one test run against the
live service once, then run offline from what the service answered. Write the test as
you would a live integration test. Record it to get honest server responses, and
every later run replays them as a functional test with the same assertions.

```py
from aws_sdk_s3.client import S3Client
from aws_sdk_s3.config import S3Config
from smithy_test import instrument


def test_list_buckets() -> None:
    client = S3Client(S3Config.resolve(region="us-west-2"))

    with client, instrument(client):
        buckets = client.list_buckets().buckets or []

    assert all(bucket.name for bucket in buckets)
```

An async client is instrumented the same way, with `await` and `async with`:

```py
async with client, await instrument_async(client):
    ...
```

### Where recordings go

Without a path, the recording is `recordings/<test function>/<client>.py` next to the
file of the function that calls `instrument`. The example above uses
`recordings/test_list_buckets/s3.py`. The client name is the class name without
`Async` and `Client`, in snake case, so a sync and an async client of the same service
share a recording.

Pass `path=`, as in `instrument(client, path=...)`, when `instrument` is called from a helper
instead of the test, which would name the recording after the helper, when a test
instruments two clients of the same service, or when the call has no source file.
Then the inference raises a `ValueError`.

### Modes

The mode comes from the `mode` keyword argument (`"record"` or `"playback"`), then from the
`SMITHY_PYTHON_TEST_MODE` environment variable, and defaults to `playback`.

- `playback` answers each operation from the recording, so the test runs offline.
  The call fails if the recording is missing, and on exit if a recorded call was
  never made.
- `record` sends requests to the live service with the client's own credentials and
  writes the responses to the recording path when the block exits. A block that
  raises writes nothing.

```sh
SMITHY_PYTHON_TEST_MODE=record pytest tests/functional/test_buckets.py
```

Use the `with` form. A recording is written when the block exits, so a call without
`with` plays back but doesn't record.

### What a recording is

A recording is a Python module that calls `controller.expect_operation(...)` once per
operation, with the responses in the order the client received them:

```py
def install(controller: HTTPMockController) -> None:
    (
        controller.expect_operation("ListBuckets")
        .times(1)
        .respond_with(
            status_code=200,
            headers={"Content-Type": "application/xml"},
            body=cleandoc(
                r"""
                <ListAllMyBucketsResult>
                  ...
                </ListAllMyBucketsResult>
                """
            ),
        )
    )
```

- Responses are matched by operation name and never by request, so control flow in the
  test can't hand an operation the response of another one. Requests aren't recorded.
- The same operation called more than once gets its responses in order. A call beyond
  the recorded ones raises, naming the operation.
- One recording serves a sync and an async client alike. If a test runs for both,
  point both at the same path and record either one.
- XML and JSON bodies are written indented. Other bodies, including data streams, are
  written as bytes literals. A data stream is read in full and handed back to the
  client as a new stream, so the live test sees what the service sent.
- Event streams can't be recorded. Instrumenting a call that returns one raises
  `HTTPRecordError`.

You can edit a recording by hand, and
`controller.expect_operation(...)` works in a test with no recording at all.

### What is scrubbed

Recordings are meant to be committed, so responses are scrubbed as they're recorded.
Scrubbing is best effort. Review a recording before you commit it.

- Replaced with stand-ins of the same length: request and host IDs, account IDs (with
  approved fictitious example IDs), access key IDs, UUIDs, IP addresses, email
  addresses, and the role and session names of assumed-role ARNs.
- Refused: the credentials' secret access key or session token appearing anywhere in
  a response, in plain, URL-encoded, JSON-escaped, XML-escaped or base64 form. The
  recording isn't written, and the error is kept even if the test catches it.
- Refused: the access key ID or the account ID in a form that can't be replaced.
- Left alone: payloads covered by a checksum or digest header, which can't change
  without failing validation.

The recorder reads the access key ID, secret, session token and account ID, when the
credentials carry one, from the client's own credentials identity. Pass
`redact=["<value>"]` for anything else that must not appear, such as an account ID the
credentials don't carry. Pass `scrubbers=[...]`, functions from text to text, to scrub
more.
