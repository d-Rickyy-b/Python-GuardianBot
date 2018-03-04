from telegram.ext import BaseFilter
from config import whitelisted_chats


# A filter which returns True, if a message is sent in an allowed group and False if not.
class AllowedChatsFilter(BaseFilter):
    name = "AllowedChatsFilter"

    def filter(self, message):
        if message.chat_id in whitelisted_chats:
            return True

        return False
