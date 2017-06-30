



class SpeechSynthesizer(object):
    STATES = {'PLAYING', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa
        self.state = 'PLAYING'
        self.token = ''

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "SpeechSynthesizer",
    #             "name": "Speak",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "url": "{{STRING}}",
    #             "format": "AUDIO_MPEG",
    #             "token": "{{STRING}}"
    #         }
    #     }
    # }

    # Content-Type: application/octet-stream
    # Content-ID: {{Audio Item CID}}

    # {{BINARY AUDIO ATTACHMENT}}
    def Speak(self, playload, attachment):
        pass
        
    # {
    #     "event": {
    #         "header": {
    #             "namespace": "SpeechSynthesizer",
    #             "name": "SpeechStarted",
    #             "messageId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "token": "{{STRING}}"
    #         }
    #     }
    # }
    def SpeechStarted(self):
        pass

    def SpeechFinished(self):
        pass

    @property
    def context(self):
        return {
                    "header": {
                        "namespace": "SpeechSynthesizer",
                        "name": "SpeechState"
                    },
                    "payload": {
                        "token": self.token,
                        "offsetInMilliseconds": 0,
                        "playerActivity": self.state
                    }
                }