from dataclasses import dataclass
from koi_net.processor.context import HandlerContext
from slack_bolt import App


@dataclass
class ExtendedHandlerContext(HandlerContext):
    slack_app: App