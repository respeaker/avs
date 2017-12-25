import os
import tempfile
import threading
import uuid
import base64
import hashlib

from avs.player import Player


class SpeechSynthesizer(object):
    STATES = {'PLAYING', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa
        self.token = ''
        self.state = 'FINISHED'
        self.finished = threading.Event()

        self.player = Player()
        self.player.add_callback('eos', self.SpeechFinished)
        self.player.add_callback('error', self.SpeechFinished)

    def stop(self):
        self.finished.set()
        self.player.stop()
        self.state = 'FINISHED'

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
    def Speak(self, directive):
        # directive from dueros may not have the dialogRequestId
        if 'dialogRequestId' in directive['header']:
            dialog_request_id = directive['header']['dialogRequestId']
            if self.alexa.SpeechRecognizer.dialog_request_id != dialog_request_id:
                return

        self.token = directive['payload']['token']
        url = directive['payload']['url']
        if url.startswith('cid:'):
            filename = base64.urlsafe_b64encode(url[4:])
            filename = hashlib.md5(filename).hexdigest()
            mp3_file = os.path.join(tempfile.gettempdir(), filename + '.mp3')
            if os.path.isfile(mp3_file):
                self.finished.clear()
                # os.system('mpv "{}"'.format(mp3_file))
                self.player.play('file://{}'.format(mp3_file))
                self.SpeechStarted()

                self.alexa.state_listener.on_speaking()

                # will be set at SpeechFinished() if the player reaches the End Of Stream or gets a error
                self.finished.wait()

                os.system('rm -rf "{}"'.format(mp3_file))

    def SpeechStarted(self):
        self.state = 'PLAYING'
        event = {
            "header": {
                "namespace": "SpeechSynthesizer",
                "name": "SpeechStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token
            }
        }
        self.alexa.send_event(event)

    def SpeechFinished(self):
        self.alexa.state_listener.on_finished()

        self.finished.set()
        self.state = 'FINISHED'
        event = {
            "header": {
                "namespace": "SpeechSynthesizer",
                "name": "SpeechFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token
            }
        }
        self.alexa.send_event(event)

    @property
    def context(self):
        offset = self.player.position if self.state == 'PLAYING' else 0

        return {
            "header": {
                "namespace": "SpeechSynthesizer",
                "name": "SpeechState"
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": offset,
                "playerActivity": self.state
            }
        }
