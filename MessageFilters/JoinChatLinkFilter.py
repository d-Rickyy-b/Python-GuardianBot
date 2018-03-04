from telegram.ext import BaseFilter
import re


class JoinChatLinkFilter(BaseFilter):
    name = "JoinChatLinkFilter"

    def filter(self, message):
        if message.text:
            if re.search("(t(elegram)?\.(me|dog|org))\/joinchat\/[a-zA-Z0-9\.\_\-]+", message.text, re.IGNORECASE):
                return True

        if message.caption:
            if re.search("(t(elegram)?\.(me|dog|org))\/joinchat\/[a-zA-Z0-9\.\_\-]+", message.caption, re.IGNORECASE):
                return True

        return False
