from smithy_aws_core.interceptors.checksums import FlexibleChecksumsInterceptor

from features_client.config import FieldNotesConfig


def flexible_checksums_plugin(config: FieldNotesConfig) -> None:
    "Add and validate the checksums the operations model."
    config.interceptors.append(FlexibleChecksumsInterceptor())
