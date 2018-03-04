from telegram.ext import BaseFilter
from config import whitelisted_groups


class GroupForwardFilter(BaseFilter):
    name = "GroupForwardFilter"

    def filter(self, message):
        if message.forward_from_chat:
            print(message.forward_from_chat)
            if message.forward_from_chat.type == "supergroup" or message.forward_from_chat.type == "group":
                if message.forward_from_chat.id not in whitelisted_groups:
                    return True

        return False
