from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor

from ec2query_client import __version__
from ec2query_client.aio.config import AsyncEC2ProtocolConfig


def aws_user_agent_plugin(config: AsyncEC2ProtocolConfig) -> None:
    "Send the AWS user agent with every request."
    config.interceptors.append(
        UserAgentInterceptor(
            ua_suffix=config.user_agent_extra,
            ua_app_id=config.sdk_ua_app_id,
            sdk_version=__version__,
            service_id="EC2_Protocol",
        )
    )
