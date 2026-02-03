from koi_net.processor.context import HandlerContext
from slack_bolt import App


class ExtendedHandlerContext(HandlerContext):
    slack_app: App