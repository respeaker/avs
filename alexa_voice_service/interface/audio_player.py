
class AudioPlayer(object):
    STATES = {'IDLE', 'PLAYING', 'STOPPED', 'PAUSED', 'BUFFER_UNDERRUN', 'FINISHED'}

    def __init__(self, alexa):
        self.alexa = alexa
        
    def Play(self):
        pass

    def Stop(self):
        pass
        
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

    def PlaybackStopped(self):
        pass

    def PlaybackPaused(self):
        pass

    def PlaybackResumed(self):
        pass

    def ClearQueue(self):
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