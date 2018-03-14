# -*- coding: utf-8 -*-
import time
from datetime import datetime
from config import flood_time_in_secs, flood_nr_of_msgs


class FloodBuffer(object):

    def __init__(self):
        self.messages = []

    def add_message(self, message):
        self.messages.append(message)
        self.remove_old_messages()

    def flood_reached(self, user_id):
        counter = 0
        for message in self.messages:
            if message.from_user:
                if message.from_user.id == user_id:
                    counter += 1

        return counter >= flood_nr_of_msgs

    def remove_old_messages(self):
        current_timestamp = int(time.mktime(datetime.now().timetuple()))

        for message in self.messages:
            message_timestamp = int(time.mktime(message.date.timetuple()))
            if message_timestamp < (current_timestamp - (flood_time_in_secs + 1)):
                self.messages.remove(message)
