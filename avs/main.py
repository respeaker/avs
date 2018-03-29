# -*- coding: utf-8 -*-

"""
Hands-free alexa with respeaker using pocketsphinx to search keyword

It depends on respeaker python library (https://github.com/respeaker/respeaker_python_library)
"""


import sys
import signal
import time
import threading
import logging

if sys.version_info < (3, 0):
    import Queue as queue
else:
    import queue

from avs.alexa import Alexa
from avs.mic import Audio
from respeaker.pixel_ring import pixel_ring


logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.INFO)

class KWS(object):
    def __init__(self):
        self.queue = queue.Queue()

        self.sinks = []
        self._callback = None

        self.done = False

    def put(self, data):
        self.queue.put(data)

    def start(self):
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.done = True

    def link(self, sink):
        if hasattr(sink, 'put') and callable(sink.put):
            self.sinks.append(sink)
        else:
            raise ValueError('Not implement put() method')

    def unlink(self, sink):
        self.sinks.remove(sink)

    def set_callback(self, callback):
        self._callback = callback

    def run(self):
        from respeaker.microphone import Microphone

        decoder = Microphone.create_decoder()
        decoder.start_utt()

        while not self.done:
            chunk = self.queue.get()
            decoder.process_raw(chunk, False, False)
            hypothesis = decoder.hyp()
            if hypothesis:
                keyword = hypothesis.hypstr
                logger.info('Detected {}'.format(keyword))

                if callable(self._callback):
                    self._callback(keyword)

                decoder.end_utt()
                decoder.start_utt()

            for sink in self.sinks:
                sink.put(chunk)


def main():
    config = None if len(sys.argv) < 2 else sys.argv[1]

    audio = Audio(frames_size=1600)
    kws = KWS()
    alexa = Alexa(config)

    def speak():
        pixel_ring.speak(10, 0)

    alexa.state_listener.on_listening = pixel_ring.listen
    alexa.state_listener.on_thinking = pixel_ring.wait
    alexa.state_listener.on_speaking = speak
    alexa.state_listener.on_finished = pixel_ring.off

    audio.link(kws)
    kws.link(alexa)

    def wakeup(keyword):
        if keyword.find('alexa') >= 0:
            alexa.listen()

    kws.set_callback(wakeup)

    alexa.start()
    kws.start()
    audio.start()

    is_quit = threading.Event()
    
    def signal_handler(signal, frame):
        print('Quit')
        is_quit.set()

    signal.signal(signal.SIGINT, signal_handler)

    while not is_quit.is_set():
        time.sleep(1)

    alexa.stop()
    kws.stop()
    audio.stop()


if __name__ == '__main__':
    main()
