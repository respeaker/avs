
import os
import tempfile


class AudioPlayer(object):
    STATES = {'IDLE', 'PLAYING', 'STOPPED', 'PAUSED', 'BUFFER_UNDERRUN', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa

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
        audio_url = directive['payload']['audioItem']['stream']['url']
        if audio_url.startswith('cid:'):
            mp3_file = os.path.join(tempfile.gettempdir(), audio_url[4:] + '.mp3')
            if os.path.isfile(mp3_file):
                os.system('mpv "{}"'.format(mp3_file))
                os.system('rm -rf "{}"'.format(mp3_file))
        else:
            os.system('mpv {}'.format(audio_url))


    def PlaybackStarted(self):
        pass

    def PlaybackNearlyFinished(self):
        pass

    def ProgressReportDelayElapsed(self):
        pass

    def ProgressReportIntervalElapsed(self):
        pass

    def PlaybackStutterStarted(self):
        pass

    def PlaybackStutterFinished(self):
        pass

    def PlaybackFinished(self):
        pass

    def PlaybackFailed(self):
        pass

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
        pass

    def PlaybackStopped(self):
        pass

    def PlaybackPaused(self):
        pass

    def PlaybackResumed(self):
        pass

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
        behavior = directive['payload']['clearBehavior']
        if behavior == 'CLEAR_ALL':
            pass
        elif behavior == 'CLEAR_ENQUEUED':
            pass


    def PlaybackQueueCleared(self):
        pass

    def StreamMetadataExtracted(self):
        pass

    @property
    def context(self):
        return {
                    "header": {
                        "namespace": "AudioPlayer",
                        "name": "PlaybackState"
                    },
                    "payload": {
                        "token": "{{STRING}}",
                        "offsetInMilliseconds": 0,
                        "playerActivity": "{{STRING}}"
                    }
                }
