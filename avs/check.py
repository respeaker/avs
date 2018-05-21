# -*- coding: utf-8 -*-

"""
Hands-free alexa with respeaker using pocketsphinx to search keyword

It depends on respeaker python library (https://github.com/respeaker/respeaker_python_library)
"""

import signal
import audioop
import os
import time
from avs.mic import Audio
from avs.player import Player


class RMS(object):
    def __init__(self):
        pass

    def put(self, data):
        print('RMS: {}'.format(audioop.rms(data, 2)))


def main():
    audio = Audio(frames_size=1600)
    rms = RMS()

    audio.link(rms)

    audio.start()

    alarm = os.path.realpath(os.path.join(os.path.dirname(__file__), 'resources/alarm.mp3'))
    alarm_uri = 'file://{}'.format(alarm)

    player1 = Player()
    player2 = Player()

    is_quit = []
    def signal_handler(signal, frame):
        print('Quit')
        is_quit.append(True)

    signal.signal(signal.SIGINT, signal_handler)

    while not is_quit:
        player1.play(alarm_uri)
        time.sleep(1)
        player1.pause()
        player2.play(alarm_uri)
        time.sleep(3)
        player2.pause()


    audio.stop()


if __name__ == '__main__':
    main()
