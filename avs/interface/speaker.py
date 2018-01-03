class Speaker(object):
    def __init__(self, event_queue):
        pass

    def AdjustVolume(self, directive):
        pass

    def VolumeChanged(self):
        pass

    def SetMute(self, directive):
        pass

    def MuteChanged(self):
        pass

    @property
    def context(self):
        return {
            "header": {
                "namespace": "Speaker",
                "name": "VolumeState"
            },
            "payload": {
                "volume": 50,
                "muted": False
            }
        }
