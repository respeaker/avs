# -*- coding: utf-8 -*-

"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/audioplayer"""

import os
import tempfile
import uuid
import base64
import hashlib
import requests
import logging

from avs.player import Player

logger = logging.getLogger('AudioPlayer')


class AudioPlayer(object):
    STATES = {'IDLE', 'PLAYING', 'STOPPED', 'PAUSED', 'BUFFER_UNDERRUN', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa
        self.token = ''
        self.state = 'IDLE'

        self.player = Player()
        self.player.add_callback('eos', self.PlaybackFinished)
        self.player.add_callback('error', self.PlaybackFailed)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "Play",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "playBehavior": "{{STRING}}",
    #             "audioItem": {
    #                 "audioItemId": "{{STRING}}",
    #                 "stream": {
    #                     "url": "{{STRING}}",
    #                     "streamFormat": "AUDIO_MPEG"
    #                     "offsetInMilliseconds": {{LONG}},
    #                     "expiryTime": "{{STRING}}",
    #                     "progressReport": {
    #                         "progressReportDelayInMilliseconds": {{LONG}},
    #                         "progressReportIntervalInMilliseconds": {{LONG}}
    #                     },
    #                     "token": "{{STRING}}",
    #                     "expectedPreviousToken": "{{STRING}}"
    #                 }
    #             }
    #         }
    #     }
    # }
    def Play(self, directive):
        behavior = directive['payload']['playBehavior']
        self.token = directive['payload']['audioItem']['stream']['token']
        audio_url = directive['payload']['audioItem']['stream']['url']
        if audio_url.startswith('cid:'):
            filename = base64.urlsafe_b64encode(audio_url[4:])
            filename = hashlib.md5(filename).hexdigest()
            mp3_file = os.path.join(tempfile.gettempdir(), filename + '.mp3')
            if os.path.isfile(mp3_file):
                # os.system('mpv "{}"'.format(mp3_file))
                # os.system('rm -rf "{}"'.format(mp3_file))
                self.player.play('file://{}'.format(mp3_file))
                self.PlaybackStarted()
        else:
            if audio_url.find('radiotime.com') >= 0:
                logger.debug('parse TuneIn audio stream: {}'.format(audio_url))

                try:
                    response = requests.get(audio_url)
                    lines = response.content.decode().split('\n')
                    logger.debug(lines)
                    if lines and lines[0]:
                        audio_url = lines[0]
                except Exception:
                    pass

            # os.system('mpv {}'.format(audio_url))
            self.player.play(audio_url)
            self.PlaybackStarted()

    def PlaybackStarted(self):
        self.state = 'PLAYING'

        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }

        self.alexa.send_event(event)

    def PlaybackNearlyFinished(self):
        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackNearlyFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.alexa.send_event(event)

    def ProgressReportDelayElapsed(self):
        pass

    def ProgressReportIntervalElapsed(self):
        pass

    def PlaybackStutterStarted(self):
        pass

    def PlaybackStutterFinished(self):
        pass

    def PlaybackFinished(self):
        self.state = 'FINISHED'

        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.alexa.send_event(event)

    def PlaybackFailed(self):
        self.state = 'STOPPED'

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "Stop",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def Stop(self, directive):
        self.player.stop()
        self.PlaybackStopped()

    def PlaybackStopped(self):
        self.state = 'STOPPED'
        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackStopped",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.alexa.send_event(event)

    def pause(self):
        self.player.pause()
        self.PlaybackPaused()

    def PlaybackPaused(self):
        self.state = 'PAUSED'
        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackPaused",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.alexa.send_event(event)

    def resume(self):
        self.player.resume()
        self.PlaybackResumed()

    def PlaybackResumed(self):
        self.state = 'PLAYING'
        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackResumed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.alexa.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "ClearQueue",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "clearBehavior": "{{STRING}}"
    #         }
    #     }
    # }
    def ClearQueue(self, directive):
        self.PlaybackQueueCleared()
        behavior = directive['payload']['clearBehavior']
        if behavior == 'CLEAR_ALL':
            self.player.stop()
        elif behavior == 'CLEAR_ENQUEUED':
            pass

    def PlaybackQueueCleared(self):
        event = {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackQueueCleared",
                "messageId": uuid.uuid4().hex
            },
            "payload": {}
        }
        self.alexa.send_event(event)

    def StreamMetadataExtracted(self):
        pass

    @property
    def context(self):
        if self.state != 'PLAYING':
            offset = 0
        else:
            offset = self.player.position

        return {
            "header": {
                "namespace": "AudioPlayer",
                "name": "PlaybackState"
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": offset,
                "playerActivity": self.state
            }
        }
