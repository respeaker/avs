class Speaker(object):
    def __init__(self, alexa):
        self.alexa = alexa
        self.volume = 50
        self.muted = False

        self.set_volume_cb = None
        self.get_volume_cb = None
        self.set_mute_cb = None

    def SetVolume(self, directive):
        vol = directive['payload']['volume']
        if self.set_volume_cb:
            self.set_volume_cb(vol)
            self.volume = vol

    def CallbackSetVolume(self, func):
        self.set_volume_cb = func

    def AdjustVolume(self, directive):
        vol = directive['payload']['volume']
        if self.get_volume_cb:
            self.volume = self.get_volume_cb()
        
        self.volume += vol
        if (self.volume > 100):
            self.volume = 100
        elif (self.volume < 0):
            self.volume = 0

        if self.set_volume_cb:
            self.set_volume_cb(self.volume)
            
    
    def CallbackGetVolume(self, func):
        self.get_volume_cb = func

    def VolumeChanged(self):
        event = {
            "event": {
                "header": {
                    "namespace": "Speaker",
                    "name": "VolumeChanged",
                    "messageId": "{{STRING}}"
                },
                "payload": {
                    "volume": self.volume,
                    "muted": self.muted
                }
            }
        }
        self.alexa.send_event(event)

    def SetMute(self, directive):
        muted = directive["payload"]["mute"]
        if self.set_mute_cb:
            self.set_mute_cb(muted)
            self.muted = muted

    
    def CallbackSetMute(self, func):
        self.set_mute_cb = func

    def MuteChanged(self):
        event = {
            "event": {
                "header": {
                    "namespace": "Speaker",
                    "name": "MuteChanged",
                    "messageId": "{{STRING}}"
                },
                "payload": {
                    "volume": self.volume,
                    "muted": self.muted
                }
            }
        }
        self.alexa.send_event(event)

    @property
    def context(self):
        return {
            "header": {
                "namespace": "Speaker",
                "name": "VolumeState"
            },
            "payload": {
                "volume": self.volume,
                "muted": self.muted,
            }
        }

