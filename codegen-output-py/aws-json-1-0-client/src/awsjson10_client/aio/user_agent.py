from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor

from awsjson10_client import __version__
from awsjson10_client.aio.config import AsyncJSONRPC10Config


def aws_user_agent_plugin(config: AsyncJSONRPC10Config) -> None:
    "Send the AWS user agent with every request."
    config.interceptors.append(
        UserAgentInterceptor(
            ua_suffix=config.user_agent_extra,
            ua_app_id=config.sdk_ua_app_id,
            sdk_version=__version__,
            service_id="JSON_RPC_10",
        )
    )
