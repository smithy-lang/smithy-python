from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor

from awsquery_client import __version__
from awsquery_client.config import QueryProtocolConfig


def aws_user_agent_plugin(config: QueryProtocolConfig) -> None:
    "Send the AWS user agent with every request."
    config.interceptors.append(
        UserAgentInterceptor(
            ua_suffix=config.user_agent_extra,
            ua_app_id=config.sdk_ua_app_id,
            sdk_version=__version__,
            service_id="Query_Protocol",
        )
    )
