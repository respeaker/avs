# -*- coding: utf-8 -*-

"""https://developer.amazon.com/public/solutions/alexa/alexa-voice-service/reference/alerts"""

import os
import time
import datetime
import dateutil.parser
from threading import Timer, Event
import uuid

# prefer mpg123 player as it is more responsive than mpv and gstreamer
if os.system('which mpg123 >/dev/null') == 0:
    from avs.player.mpg123_player import Player
else:
    from avs.player import Player


class Alerts(object):
    STATES = {'IDLE', 'FOREGROUND', 'BACKGROUND'}

    def __init__(self, alexa):
        self.alexa = alexa
        self.player = Player()

        self.player.add_callback('eos', self._stop)
        self.player.add_callback('error', self._stop)

        alarm = os.path.realpath(os.path.join(os.path.dirname(__file__), '../resources/alarm.mp3'))
        self.alarm_uri = 'file://{}'.format(alarm)

        self.all_alerts = {}
        self.active_alerts = {}

        self.state = 'IDLE'
        self.end_event = Event()

    def _stop(self):
        """
        Stop all active alerts
        """
        for token in self.active_alerts.keys():
            self.AlertStopped(token)

        self.active_alerts = {}
        self.state = 'IDLE'

        self.end_event.set()

    def stop(self):
        self.player.stop()
        self._stop()

    def enter_background(self):
        if self.state == 'FOREGROUND':
            self.state = 'BACKGROUND'
            self.player.pause()

    def enter_foreground(self):
        if self.state == 'BACKGROUND':
            self.state = 'FOREGROUND'
            self.player.resume()

    def _start_alert(self, token):
        if token in self.all_alerts:
            while self.alexa.SpeechRecognizer.conversation:
                time.sleep(1)

            if self.alexa.AudioPlayer.state == 'PLAYING':
                self.alexa.AudioPlayer.pause()

            self.AlertStarted(token)

            self.end_event.clear()

            # TODO: repeat play alarm until user stops it or timeout
            self.player.play(self.alarm_uri)

            if not self.end_event.wait(timeout=600):
                self.player.stop()

            if not self.alexa.SpeechRecognizer.conversation:
                if self.alexa.AudioPlayer.state == 'PAUSED':
                    self.alexa.AudioPlayer.resume()

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "Alerts",
    #             "name": "SetAlert",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "token": "{{STRING}}",
    #             "type": "{{STRING}}",
    #             "scheduledTime": "2017-08-07T09:02:58+0000",
    #         }
    #     }
    # }
    def SetAlert(self, directive):
        payload = directive['payload']
        token = payload['token']
        scheduled_time = dateutil.parser.parse(payload['scheduledTime'])

        # Update the alert
        if token in self.all_alerts:
            pass

        self.all_alerts[token] = payload

        interval = scheduled_time - datetime.datetime.now(scheduled_time.tzinfo)
        Timer(interval.seconds, self._start_alert, (token,)).start()

        self.SetAlertSucceeded(token)

    def SetAlertSucceeded(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "SetAlertSucceeded",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def SetAlertFailed(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "SetAlertFailed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "Alerts",
    #             "name": "DeleteAlert",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "token": "{{STRING}}"
    #         }
    #     }
    # }
    def DeleteAlert(self, directive):
        token = directive['payload']['token']

        if token in self.active_alerts:
            self.AlertStopped(token)

        if token in self.all_alerts:
            del self.all_alerts[token]

        self.DeleteAlertSucceeded(token)

    def DeleteAlertSucceeded(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "DeleteAlertSucceeded",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def DeleteAlertFailed(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "DeleteAlertFailed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def AlertStarted(self, token):
        if self.state == 'IDLE':
            self.state = 'FOREGROUND'

        self.active_alerts[token] = self.all_alerts[token]

        event = {
            "header": {
                "namespace": "Alerts",
                "name": "AlertStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def AlertStopped(self, token):
        if token in self.active_alerts:
            del self.active_alerts[token]

        if token in self.all_alerts:
            del self.all_alerts[token]

        if not self.active_alerts:
            self.state = 'IDLE'

        event = {
            "header": {
                "namespace": "Alerts",
                "name": "AlertStopped",
                "messageId": "{STRING}"
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def AlertEnteredForeground(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "AlertEnteredForeground",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    def AlertEnteredBackground(self, token):
        event = {
            "header": {
                "namespace": "Alerts",
                "name": "AlertEnteredBackground",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.alexa.send_event(event)

    @property
    def context(self):
        return {
            "header": {
                "namespace": "Alerts",
                "name": "AlertsState"
            },
            "payload": {
                "allAlerts": list(self.all_alerts.values()),
                "activeAlerts": list(self.active_alerts.values())
            }
        }
