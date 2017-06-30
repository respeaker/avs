

class Alerts(object):
    STATES = {'IDLE', 'FOREGROUND', 'BACKGROUND'}

    def __init__(self, alexa):
        self.alexa = alexa

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "Alerts",
    #             "name": "SetAlert",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "token": "{{STRING}}",
    #             "type": "{{STRING}}",
    #             "scheduledTime": "{{STRING}}",            
    #         }
    #     }
    # }
    def SetAlert(self):
        pass

    def SetAlertSucceeded(self):
        pass

    def SetAlertFailed(self):
        pass


    def DeleteAlert(self):
        pass
        
    def DeleteAlertSucceeded(self):
        pass

    def DeleteAlertFailed(self):
        pass

    def AlertStarted(self):
        pass


    def AlertStopped(self):
        pass
        
    def AlertEnteredForeground(self):
        pass

    def AlertEnteredBackground(self):
        pass

    @property
    def context(self):
        return {
                    "header": {
                        "namespace": "Alerts",
                        "name": "AlertsState"
                    },
                    "payload": {
                        "allAlerts": [
                                        {
                                "token": "{{STRING}}",
                                "type": "{{STRING}}",
                                "scheduledTime": "{{STRING}}"
                            }
                        ],
                        "activeAlerts": [
                                        {
                                "token": "{{STRING}}",
                                "type": "{{STRING}}",
                                "scheduledTime": "{{STRING}}"
                            }
                        ]
                    }
                }