
"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/system"""

import uuid
import datetime


class System(object):
    def __init__(self, alexa):
        self.alexa = alexa
        self.last_inactive_report = datetime.datetime.utcnow()

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

        def on_finished():
            self.alexa.state_listener.on_ready()

        self.alexa.send_event(event, listener=on_finished)

    def UserInactivityReport(self):
        current = datetime.datetime.utcnow()
        dt = current - self.last_inactive_report

        # hourly report the amount of time elapsed since the last user activity
        if dt.seconds < (59 * 60):
            return

        self.last_inactive_report = current

        inactive_time = current - self.alexa.last_activity

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
