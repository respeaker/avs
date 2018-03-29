# -*- coding: utf-8 -*-

"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/speechrecognizer"""

import logging
import sys
import time
import threading
import uuid

if sys.version_info < (3, 0):
    import Queue as queue
else:
    import queue

logger = logging.getLogger('SpeechRecognizer')


class SpeechRecognizer(object):
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}
    PRESS_AND_HOLD = {'type': 'PRESS_AND_HOLD', 'payload': {}}
    TAP = {'type': 'TAP', 'payload': {}}
    WAKEWORD = {'type': 'WAKEWORD', 'payload': {}}

    def __init__(self, alexa):
        self.alexa = alexa
        self.profile = 'FAR_FIELD'

        self.dialog_request_id = ''

        self.audio_queue = queue.Queue(maxsize=1000)
        self.listening = False
        self.conversation = 0
        self.lock = threading.RLock()

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
            logger.debug('Already listening. Ignore')
            return

        logger.debug('Starting listening')

        self.audio_queue.queue.clear()
        self.listening = True

        with self.lock:
            self.conversation += 1

        def on_finished():
            if self.alexa.SpeechSynthesizer.state == 'PLAYING':
                logger.info('wait until speech synthesizer is finished')
                self.alexa.SpeechSynthesizer.wait()
                logger.info('synthesizer is finished')

            with self.lock:
                self.conversation -= 1
            logger.info('conversation = {}'.format(self.conversation))
            if not self.conversation:
                self.alexa.state_listener.on_finished()

                if self.alexa.AudioPlayer.state == 'PAUSED':
                    self.alexa.AudioPlayer.resume()

        # Stop playing if Alexa is speaking or AudioPlayer is playing
        if self.alexa.SpeechSynthesizer.state == 'PLAYING':
            logger.info('stop speech synthesizer')
            self.alexa.SpeechSynthesizer.stop()
        elif self.alexa.Alerts.state == 'FOREGROUND':
            logger.info('stop alert(s)')
            self.alexa.Alerts.stop()
        elif self.alexa.AudioPlayer.state == 'PLAYING':
            logger.info('pause audio player')
            self.alexa.AudioPlayer.pause()

        self.alexa.state_listener.on_listening()

        self.dialog_request_id = dialog if dialog else uuid.uuid4().hex

        if initiator is None:
            initiator = self.WAKEWORD

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
            while self.listening and time_elapsed <= timeout:
                try:
                    chunk = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    break

                yield chunk
                time_elapsed += len(chunk) * 1000 / (2 * 16000)  # 16000 fs, 2 bytes width
                logger.debug('Sending chunk, time_elapsed = {}'.format(time_elapsed))

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
        while self.alexa.SpeechSynthesizer.state == 'PLAYING':
            time.sleep(0.1)

        dialog = directive['header']['dialogRequestId']
        timeout = directive['payload']['timeoutInMilliseconds']

        initiator = None
        if 'initiator' in directive['payload']:
            initiator = directive['payload']['initiator']

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
