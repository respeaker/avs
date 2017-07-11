# -*- coding: utf-8 -*-

"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/speechrecognizer"""

import uuid
from threading import Event
import logging

log = logging.getLogger('SpeechRecognizer')


class SpeechRecognizer(object):
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}
    PRESS_AND_HOLD = {'type': 'PRESS_AND_HOLD', 'payload': {}}
    TAP = {'type': 'TAP', 'payload': {}}

    def __init__(self, alexa):
        self.alexa = alexa
        self.profile = 'NEAR_FIELD'
        self.done = Event()

    def Recognize(self, audio, dialog=None, initiator=None, timeout=12000):
        if self.alexa.AudioPlayer.state == 'PLAYING':
            self.alexa.AudioPlayer.pause()

        if dialog is None:
            dialog = uuid.uuid4().hex

        if initiator is None:
            initiator = self.TAP

        event = {
            "event": {
                "header": {
                    "namespace": "SpeechRecognizer",
                    "name": "Recognize",
                    "messageId": uuid.uuid4().hex,
                    "dialogRequestId": dialog
                },
                "payload": {
                    "profile": self.profile,
                    "format": "AUDIO_L16_RATE_16000_CHANNELS_1",
                    'initiator': initiator
                }
            }
        }

        audio.start()
        self.done.clear()

        def gen():
            time_elapsed = 0
            for chunk in audio:
                if self.done.is_set() or time_elapsed >= timeout:
                    log.info('stop recording')
                    break
                yield chunk
                time_elapsed += 10  # 10 ms chunk

            audio.stop()
            self.done.set()

        event['attachment'] = gen()
        self.alexa.event_queue.put(event)

        return self.done

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
        self.done.set()
        log.info('StopCapture')

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
        dialog = directive['header']['dialogRequestId']
        timeout = directive['payload']['timeoutInMilliseconds']

        initiator = None
        if 'initiator' in directive['payload']:
            initiator = directive['payload']['initiator']

        self.Recognize(self.alexa.audio, dialog=dialog, initiator=initiator, timeout=timeout)

    def ExpectSpeechTimedOut(self):
        event = {
            "event": {
                "header": {
                    "namespace": "SpeechRecognizer",
                    "name": "ExpectSpeechTimedOut",
                    "messageId": uuid.uuid4().hex,
                },
                "payload": {}
            }
        }
        self.alexa.event_queue.put(event)

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
