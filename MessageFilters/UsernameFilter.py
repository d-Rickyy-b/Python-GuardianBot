from telegram.ext import BaseFilter
import re


class UsernameFilter(BaseFilter):
    name = "UsernameFilter"

    def filter(self, message):
        if message.text:
            if re.search("((t(elegram)?\.(me|dog|org))\/(?!joinchat).+|@.+)", message.text, re.IGNORECASE):
                return True

        if message.caption:
            if re.search("((t(elegram)?\.(me|dog|org))\/(?!joinchat).+|@.+)", message.caption, re.IGNORECASE):
                return True

        return False
