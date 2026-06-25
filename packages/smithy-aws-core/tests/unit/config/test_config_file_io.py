# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


from pathlib import Path

import pytest
from smithy_aws_core.config import load_config
from smithy_aws_core.config.file_parser import parse_config_file


class TestFileIssues:
    """Tests that missing files are treated as empty."""

    @pytest.mark.asyncio
    async def test_config_not_found_returns_empty(self, tmp_path: Path):
        nonexistent = str(tmp_path / "does_not_exist")
        result = await parse_config_file(nonexistent)
        assert result == {}

    @pytest.mark.asyncio
    async def test_load_config_with_missing_files(self, tmp_path: Path):
        config_file = await load_config(
            config_file_path=str(tmp_path / "no_config"),
            credentials_file_path=str(tmp_path / "no_credentials"),
        )
        assert config_file.profiles == {}
        assert config_file.sso_sessions == {}
        assert config_file.services == {}

    @pytest.mark.asyncio
    async def test_permission_denied_returns_empty(self, tmp_path: Path):
        restricted_file = tmp_path / "restricted_config"
        restricted_file.write_text("[profile default]\nregion = us-east-1\n")
        restricted_file.chmod(0o000)
        try:
            result = await parse_config_file(str(restricted_file))
            assert result == {}
        finally:
            restricted_file.chmod(0o644)


class TestEncodingErrors:
    """Tests for files with invalid encoding."""

    @pytest.mark.asyncio
    async def test_bad_unicode_returns_empty(self, tmp_path: Path):
        bad_file = tmp_path / "bad_config"
        bad_file.write_bytes(b"[default]\nregion = \xff\xfe invalid")
        result = await parse_config_file(str(bad_file))
        assert result == {}


class TestMultiFileMerge:
    """Tests for merging config and credentials files with precedence."""

    @pytest.mark.asyncio
    async def test_credentials_override_config(self, tmp_path: Path):
        config = tmp_path / "config"
        config.write_text(
            "[profile default]\nregion = us-east-1\naws_access_key_id = CONFIG_KEY\n"
        )
        credentials = tmp_path / "credentials"
        credentials.write_text(
            "[default]\n"
            "aws_access_key_id = CREDS_KEY\n"
            "aws_secret_access_key = CREDS_SECRET\n"
        )

        result = await load_config(
            config_file_path=str(config),
            credentials_file_path=str(credentials),
        )

        assert result.get("default", "aws_access_key_id") == "CREDS_KEY"
        assert result.get("default", "region") == "us-east-1"
        assert result.get("default", "aws_secret_access_key") == "CREDS_SECRET"

    @pytest.mark.asyncio
    async def test_missing_credentials_file_still_loads_config(self, tmp_path: Path):
        config = tmp_path / "config"
        config.write_text("[profile work]\nregion = us-west-2\n")

        result = await load_config(
            config_file_path=str(config),
            credentials_file_path=str(tmp_path / "nonexistent"),
        )
        assert result.get("work", "region") == "us-west-2"

    @pytest.mark.asyncio
    async def test_missing_config_file_still_loads_credentials(self, tmp_path: Path):
        credentials = tmp_path / "credentials"
        credentials.write_text("[default]\naws_access_key_id = KEY\n")

        result = await load_config(
            config_file_path=str(tmp_path / "nonexistent"),
            credentials_file_path=str(credentials),
        )
        assert result.get("default", "aws_access_key_id") == "KEY"
