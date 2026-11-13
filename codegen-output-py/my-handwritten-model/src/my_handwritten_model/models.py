from smithy_core._dynamic_models import ModelRegistry
from smithy_core.exceptions import ModeledError

from ._private import schemas


class ServiceError(ModeledError):
    """
    Base error for all errors in the service.

    Some exceptions do not extend from this class, including synthetic,
    implicit, and shared exception types.
    """


_MODEL_INDEX = {
    "Alpha": "ALPHA",
    "DifferentShapeName": "DIFFERENT_SHAPE_NAME",
    "Gamma": "GAMMA",
    "GammaPayload": "GAMMA_PAYLOAD",
    "HeartbeatEvent": "HEARTBEAT_EVENT",
    "LogEvent": "LOG_EVENT",
    "MetricEvent": "METRIC_EVENT",
    "NotificationEvent": "NOTIFICATION_EVENT",
    "PublishEventStream": "PUBLISH_EVENT_STREAM",
    "PublishEventStreamLog": "PUBLISH_EVENT_STREAM",
    "PublishEventStreamMetric": "PUBLISH_EVENT_STREAM",
    "PublishEventStreamUnknown": "PUBLISH_EVENT_STREAM",
    "PublishEventsInput": "PUBLISH_EVENTS_INPUT",
    "PublishEventsOutput": "PUBLISH_EVENTS_OUTPUT",
    "StreamServiceError": "STREAM_SERVICE_ERROR",
    "SubscribeEventStream": "SUBSCRIBE_EVENT_STREAM",
    "SubscribeEventStreamNotification": "SUBSCRIBE_EVENT_STREAM",
    "SubscribeEventStreamHeartbeat": "SUBSCRIBE_EVENT_STREAM",
    "SubscribeEventStreamUnknown": "SUBSCRIBE_EVENT_STREAM",
    "SubscribeToEventsInput": "SUBSCRIBE_TO_EVENTS_INPUT",
    "SubscribeToEventsOutput": "SUBSCRIBE_TO_EVENTS_OUTPUT",
    "ThrottlingEvent": "THROTTLING_EVENT",
    "TradeEventStreamInput": "TRADE_EVENT_STREAM_INPUT",
    "TradeEventStreamOutput": "TRADE_EVENT_STREAM_OUTPUT",
    "TradeEvents": "TRADE_EVENTS",
    "TradeEventsAlpha": "TRADE_EVENTS",
    "TradeEventsBeta": "TRADE_EVENTS",
    "TradeEventsGamma": "TRADE_EVENTS",
    "TradeEventsDelta": "TRADE_EVENTS",
    "TradeEventsThrottle": "TRADE_EVENTS",
    "TradeEventsUnknown": "TRADE_EVENTS",
}

_RENAMES: dict[str, str] = {}

_TARGET_NAMES: dict[str, str] = {}

_MODEL_NAMES = (*tuple(_MODEL_INDEX), "Unit")
__all__ = ("ServiceError", *_MODEL_NAMES)  # pyright: ignore[reportUnsupportedDunderAll]


_registry = ModelRegistry(
    schemas,
    renames=_RENAMES,
    index=_MODEL_INDEX,
    target_names=_TARGET_NAMES,
    shape_names=frozenset(
        {
            "Alpha",
            "DifferentShapeName",
            "Gamma",
            "GammaPayload",
            "HeartbeatEvent",
            "LogEvent",
            "MetricEvent",
            "NotificationEvent",
            "PublishEventStream",
            "PublishEventsInput",
            "PublishEventsOutput",
            "StreamServiceError",
            "SubscribeEventStream",
            "SubscribeToEventsInput",
            "SubscribeToEventsOutput",
            "ThrottlingEvent",
            "TradeEventStreamInput",
            "TradeEventStreamOutput",
            "TradeEvents",
            "Unit",
        }
    ),
    service_error="ServiceError",
)
del schemas, ModelRegistry, ModeledError


def __getattr__(name: str):
    value = _registry.build(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *__all__})
