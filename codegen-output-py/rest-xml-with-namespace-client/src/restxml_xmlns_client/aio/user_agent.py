from smithy_aws_core.interceptors.user_agent import UserAgentInterceptor

from restxml_xmlns_client import __version__
from restxml_xmlns_client.aio.config import AsyncRestXmlProtocolNamespaceConfig


def aws_user_agent_plugin(config: AsyncRestXmlProtocolNamespaceConfig) -> None:
    "Send the AWS user agent with every request."
    config.interceptors.append(
        UserAgentInterceptor(
            ua_suffix=config.user_agent_extra,
            ua_app_id=config.sdk_ua_app_id,
            sdk_version=__version__,
            service_id="Rest_Xml_Protocol_Namespace",
        )
    )
