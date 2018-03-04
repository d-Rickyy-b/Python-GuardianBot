class Incidents(object):
    incidents = []

    def __init__(self):
        pass

    def append(self, inc):
        if inc not in self.incidents:
            self.incidents.append(inc)

    def handle(self, inc):
        for index, incident in enumerate(self.incidents):
            if incident.message_id == inc.message_id and incident.chat_id == inc.chat_id:
                handled_incident = self.incidents.pop(index)
                return handled_incident

    def __contains__(self, inc):
        for incident in self.incidents:
            if incident.message_id == inc.message_id and incident.chat_id == inc.chat_id:
                return True

        return False
