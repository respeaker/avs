# -*- coding: utf-8 -*-

"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/speechrecognizer"""

import logging
import uuid

try:
    import Queue as queue
except ImportError:
    import queue

logger = logging.getLogger('SpeechRecognizer')


class SpeechRecognizer(object):
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}
    PRESS_AND_HOLD = {'type': 'PRESS_AND_HOLD', 'payload': {}}
    TAP = {'type': 'TAP', 'payload': {}}

    def __init__(self, alexa):
        self.alexa = alexa
        self.profile = 'FAR_FIELD'

        self.dialog_request_id = ''

        self.listening = False
        self.audio_queue = queue.Queue(maxsize=1000)

    def put(self, audio):
        """
        Put audio into queue when listening
        :param audio: S16_LE format, sample rate 16000 bps audio data
        :return: None
        """
        if self.listening:
            self.audio_queue.put(audio)

    def Recognize(self, dialog=None, initiator=None, timeout=10000):
        """
        recognize
        :param dialog:
        :param initiator:
        :param timeout:
        :return:
        """

        if self.listening:
            return

        self.audio_queue.queue.clear()
        self.listening = True

        def on_finished():
            self.alexa.state_listener.on_finished()

            if self.alexa.AudioPlayer.state == 'PAUSED':
                self.alexa.AudioPlayer.resume()

        # Stop playing if Alexa is speaking or AudioPlayer is playing
        if self.alexa.SpeechSynthesizer.state == 'PLAYING':
            self.alexa.SpeechSynthesizer.stop()
            self.alexa.listener_canceler.set()
        elif self.alexa.AudioPlayer.state == 'PLAYING':
            self.alexa.AudioPlayer.pause()
            self.alexa.listener_canceler.set()

        self.alexa.state_listener.on_listening()

        self.dialog_request_id = dialog if dialog else uuid.uuid4().hex

        # TODO: set initiator properly
        if initiator is None:
            initiator = ""

        event = {
            "header": {
                "namespace": "SpeechRecognizer",
                "name": "Recognize",
                "messageId": uuid.uuid4().hex,
                "dialogRequestId": self.dialog_request_id
            },
            "payload": {
                "profile": self.profile,
                "format": "AUDIO_L16_RATE_16000_CHANNELS_1",
                'initiator': initiator
            }
        }

        def gen():
            time_elapsed = 0
            while self.listening or time_elapsed >= timeout:
                try:
                    chunk = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    break

                yield chunk
                time_elapsed += 10  # 10 ms chunk

            self.listening = False
            self.alexa.state_listener.on_thinking()

        self.alexa.send_event(event, listener=on_finished, attachment=gen())

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
        self.listening = False
        logger.info('StopCapture')

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

        self.alexa.listener_canceler.set()
        self.Recognize(dialog=dialog, initiator=initiator, timeout=timeout)

    def ExpectSpeechTimedOut(self):
        event = {
            "header": {
                "namespace": "SpeechRecognizer",
                "name": "ExpectSpeechTimedOut",
                "messageId": uuid.uuid4().hex,
            },
            "payload": {}
        }
        self.alexa.send_event(event)

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
