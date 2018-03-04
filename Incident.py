from config import admin_channel_id


class Incident(object):

    def __init__(self, chat_id, message_id, admin_channel_message_id=0):
        self.chat_id = int(chat_id)
        self.message_id = int(message_id)
        self.admin_channel_id = admin_channel_id
        self.admin_channel_message_id = admin_channel_message_id
