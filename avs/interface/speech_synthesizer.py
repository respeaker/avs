
import uuid
import os
import tempfile

from avs.player import Player


class SpeechSynthesizer(object):
    STATES = {'PLAYING', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa
        self.token = ''
        self.state = 'FINISHED'

        self.player = Player()
        self.player.add_callback('eos', self.SpeechFinished)
        self.player.add_callback('error', self.SpeechFinished)

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
        self.token = directive['payload']['token']
        url = directive['payload']['url']
        if url.startswith('cid:'):
            mp3_file = os.path.join(tempfile.gettempdir(), url[4:] + '.mp3')
            if os.path.isfile(mp3_file):
                # os.system('mpv "{}"'.format(mp3_file))
                # os.system('rm -rf "{}"'.format(mp3_file))
                self.player.play('file://{}'.format(mp3_file))
                self.SpeechStarted()

    def SpeechStarted(self):
        self.state = 'PLAYING'
        event = {
            "event": {
                "header": {
                    "namespace": "SpeechSynthesizer",
                    "name": "SpeechStarted",
                    "messageId": uuid.uuid4().hex
                },
                "payload": {
                    "token": self.token
                }
            }
        }
        self.alexa.event_queue.put(event)

    def SpeechFinished(self):
        self.state = 'FINISHED'
        event = {
            "event": {
                "header": {
                    "namespace": "SpeechSynthesizer",
                    "name": "SpeechFinished",
                    "messageId": uuid.uuid4().hex
                },
                "payload": {
                    "token": self.token
                }
            }
        }
        self.alexa.event_queue.put(event)

    @property
    def context(self):
        if self.state != 'PLAYING':
            offset = 0
        else:
            offset = self.player.position * 1000000

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

