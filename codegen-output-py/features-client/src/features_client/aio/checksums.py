from smithy_aws_core.aio.interceptors.checksums import AsyncFlexibleChecksumsInterceptor

from features_client.aio.config import AsyncFieldNotesConfig


def flexible_checksums_plugin(config: AsyncFieldNotesConfig) -> None:
    "Add and validate the checksums the operations model."
    config.interceptors.append(AsyncFlexibleChecksumsInterceptor())
