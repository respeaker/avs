import uuid


class System(object):

    def __init__(self, alexa):
        self.alexa = alexa

    def SynchronizeState(self):
        event = {
            "event": {
                "header": {
                    "namespace": "System",
                    "name": "SynchronizeState",
                    "messageId": uuid.uuid4().hex
                },
                "payload": {
                }
            }
        }

        self.alexa.event_queue.put(event)

    def UserInactivityReport(self):
        event = {
            "event": {
                "header": {
                    "namespace": "System",
                    "name": "UserInactivityReport",
                    "messageId": uuid.uuid4().hex
                },
                "payload": {
                    "inactiveTimeInSeconds": 0
                }

            }

        }

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
        pass

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
            "event": {
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
        }

    @property
    def context(self):
        pass
