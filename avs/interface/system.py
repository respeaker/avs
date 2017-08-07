import uuid
import datetime


class System(object):
    def __init__(self, alexa):
        self.alexa = alexa

    def SynchronizeState(self):
        event = {
            "header": {
                "namespace": "System",
                "name": "SynchronizeState",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
            }
        }

        self.alexa.send_event(event)

    def UserInactivityReport(self):
        inactive_time = datetime.datetime.utcnow() - self.alexa.last_activity

        event = {
            "header": {
                "namespace": "System",
                "name": "UserInactivityReport",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "inactiveTimeInSeconds": inactive_time.seconds
            }

        }

        self.alexa.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "System",
    #             "name": "ResetUserInactivity",
    #             "messageId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def ResetUserInactivity(self, directive):
        self.alexa.last_activity = datetime.datetime.utcnow()

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "System",
    #             "name": "SetEndpoint",
    #             "messageId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "endpoint": "{{STRING}}"
    #         }
    #     }
    # }
    def SetEndpoint(self, directive):
        pass

    def ExceptionEncountered(self):
        event = {
            "header": {
                "namespace": "System",
                "name": "ExceptionEncountered",
                "messageId": "{{STRING}}"
            },
            "payload": {
                "unparsedDirective": "{{STRING}}",
                "error": {
                    "type": "{{STRING}}",
                    "message": "{{STRING}}"
                }
            }
        }
        self.alexa.send_event(event)
