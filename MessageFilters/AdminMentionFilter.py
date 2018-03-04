from telegram.ext import BaseFilter


class AdminMentionFilter(BaseFilter):
    name = "AdminMentionFilter"

    def filter(self, message):
        if message.text:
            if "@admin" in message.text:
                    return True

        return False
