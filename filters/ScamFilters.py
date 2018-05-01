import re

from telegram.ext import BaseFilter

from config import whitelisted_channels, whitelisted_chats, whitelisted_groups, allowed_usernames


class _JoinChatLinkFilter(BaseFilter):
    name = "JoinChatLinkFilter"

    def filter(self, message):
        if message.text:
            if re.search("(t(elegram)?\.(me|dog|org))\/joinchat\/[a-zA-Z0-9\.\_\-]+", message.text, re.IGNORECASE):
                return True
            if re.search("tg:\/\/join\?invite=[a-zA-Z0-9\.\_\-]+", message.text, re.IGNORECASE):
                return True

        if message.caption:
            if re.search("(t(elegram)?\.(me|dog|org))\/joinchat\/[a-zA-Z0-9\.\_\-]+", message.caption, re.IGNORECASE):
                return True
            if re.search("tg:\/\/join\?invite=[a-zA-Z0-9\.\_\-]+", message.caption, re.IGNORECASE):
                return True

        return False


class _ChannelForwardFilter(BaseFilter):
    name = "ChannelForwardFilter"

    def filter(self, message):
        if message.forward_from_chat:
            if message.forward_from_chat.type == "channel":
                if message.forward_from_chat.id not in whitelisted_channels:
                    return True

        return False


class _GroupForwardFilter(BaseFilter):
    name = "GroupForwardFilter"

    def filter(self, message):
        if message.forward_from_chat:
            print(message.forward_from_chat)
            if message.forward_from_chat.type == "supergroup" or message.forward_from_chat.type == "group":
                if message.forward_from_chat.id not in whitelisted_groups:
                    return True

        return False


class _UserJoinedFilter(BaseFilter):
    name = "UserJoinedFilter"

    def filter(self, message):
        if message.new_chat_members:
            return True

        return False


class _UsernameFilter(BaseFilter):
    name = "UsernameFilter"

    def filter(self, message):
        entities = []

        if message.text:
            entities = message.parse_entities(types="mention")
        elif message.caption:
            entities = message.parse_caption_entities(types="mention")

        for entity, username in entities.items():
            if username.lower() not in [x.lower() for x in allowed_usernames]:
                return True

        return False


class _TDotMeUsernameFilter(BaseFilter):
    name = "TDotMeUsernameFilter"

    def filter(self, message):
        text = ""
        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption

        if re.search("((t(elegram)?\.(me|dog|org))\/(?!joinchat).+)", text, re.IGNORECASE):
            return True

        return False


# A filter which returns True, if a message is sent in an allowed group and False if not.
class _AllowedChatsFilter(BaseFilter):
    name = "AllowedChatsFilter"

    def filter(self, message):
        if message.chat_id in whitelisted_chats:
            return True

        return False


joinChatLinkFilter = _JoinChatLinkFilter()
channelForwardFilter = _ChannelForwardFilter()
groupForwardFilter = _GroupForwardFilter()
userJoinedFilter = _UserJoinedFilter()
usernameFilter = _UsernameFilter()
tDotMeUsernameFilter = _TDotMeUsernameFilter()
allowedChatsFilter = _AllowedChatsFilter()
