# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
import os
from concurrent.futures import Future, ThreadPoolExecutor
from unittest.mock import patch

from smithy_aws_core.config import get_shared_resolver, reset_shared_resolver
from smithy_core.config.resolver import ConfigResolver


class TestGetSharedResolver:
    def setup_method(self):
        # Reset the shared resolver before each test
        reset_shared_resolver()

    def test_returns_config_resolver_instance(self):
        resolver = get_shared_resolver()

        assert isinstance(resolver, ConfigResolver)

    def test_returns_same_instance_on_repeated_calls(self):
        resolver1 = get_shared_resolver()
        resolver2 = get_shared_resolver()
        resolver3 = get_shared_resolver()

        assert resolver1 is resolver2
        assert resolver2 is resolver3

    def test_resolves_from_environment_variables(self):
        with patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True):
            resolver = get_shared_resolver()
            value, source = resolver.get("region")

            assert value == "us-west-2"
            assert source == "environment"

    def test_reset_clears_singleton(self):
        resolver1 = get_shared_resolver()

        reset_shared_resolver()

        resolver2 = get_shared_resolver()

        # After reset, it should get a new instance
        assert resolver1 is not resolver2

    def test_multiple_thread_calls_return_same_instance(self) -> None:
        results: list[ConfigResolver] = []

        # Multiple thread calls should use the same resolver instance
        def get_resolver() -> None:
            resolver = get_shared_resolver()
            results.append(resolver)

        # Create 10 threads that all call get_shared_resolver concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures: list[Future[None]] = [
                executor.submit(get_resolver) for _ in range(10)
            ]
            for future in futures:
                future.result()

        first_resolver: ConfigResolver = results[0]
        assert len(results) == 10
        # All threads should have gotten the same resolver instance
        assert all(resolver is first_resolver for resolver in results)
