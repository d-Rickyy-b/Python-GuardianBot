from telegram.ext import BaseFilter
import re


class UserJoinedFilter(BaseFilter):
    name = "UserJoinedFilter"

    def filter(self, message):
        if message.new_chat_members:
            return True

        return False
