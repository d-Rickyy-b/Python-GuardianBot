from telegram.ext import BaseFilter
from config import whitelisted_channels


class ChannelForwardFilter(BaseFilter):
    name = "ChannelForwardFilter"

    def filter(self, message):
        if message.forward_from_chat:
            if message.forward_from_chat.type == "channel":
                if message.forward_from_chat.id not in whitelisted_channels:
                    return True

        return False
