

class SpeechRecognizer(object):
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}

    def __init__(self, alexa):
        self.alexa = alexa

    # {
    #   "context": [
    #       {{...}}        
    #   ],   
    #   "event": {
    #     "header": {
    #       "namespace": "SpeechRecognizer",
    #       "name": "Recognize",
    #       "messageId": "{{STRING}}",
    #       "dialogRequestId": "{{STRING}}"
    #     },
    #     "payload": {
    #       "profile": "{{STRING}}",
    #       "format": "AUDIO_L16_RATE_16000_CHANNELS_1",
    #       "initiator": {
    #         "type": "{{STRING}}",
    #         "payload": {
    #           "wakeWordIndices": {
    #             "startIndexInSamples": {{LONG}},
    #             "endIndexInSamples": {{LONG}}
    #           }   
    #         }
    #       }
    #     }
    #   }
    # }

    # Content-Disposition: form-data; name="audio"
    # Content-Type: application/octet-stream

    # {{BINARY AUDIO ATTACHMENT}}
    def Recognize(self, initiator, timeout=None):
        pass

    # {
    #   "directive": {
    #         "header": {
    #             "namespace": "SpeechRecognizer",
    #             "name": "StopCapture",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def StopCapture(self, directive):
        pass

    # {
    #   "directive": {
    #     "header": {
    #       "namespace": "SpeechRecognizer",
    #       "name": "ExpectSpeech",
    #       "messageId": "{{STRING}}",
    #       "dialogRequestId": "{{STRING}}"
    #     },
    #     "payload": {
    #       "timeoutInMilliseconds": {{LONG}},
    #       "initiator": "{{STRING}}"
    #     }
    #   }
    # }
    def ExpectSpeech(self, directive):
        pass

    # {
    #   "event": {
    #         "header": {
    #             "namespace": "SpeechRecognizer",
    #             "name": "ExpectSpeechTimedOut",
    #             "messageId": "{{STRING}}",
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def ExpectSpeechTimedOut(self):
        pass

    @property
    def context(self):
        return {
                    "header": {
                        "namespace": "SpeechRecognizer",
                        "name": "RecognizerState"
                    },
                    "payload": {
                        "wakeword": "ALEXA"
                    }
                }
