# -*- coding: utf-8 -*-

"""
Hands-free alexa with respeaker using pocketsphinx to search keyword

It depends on respeaker python library (https://github.com/respeaker/respeaker_python_library)
"""


import sys
import time
import threading
try:
    import Queue as queue
except ImportError:
    import queue

import logging

logger = logging.getLogger(__file__)


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
    from avs.alexa import Alexa
    from avs.mic import Audio

    logging.basicConfig(level=logging.DEBUG)

    config = None if len(sys.argv) < 2 else sys.argv[1]

    audio = Audio()
    kws = KWS()
    alexa = Alexa(config)

    audio.link(kws)
    kws.link(alexa)

    def wakeup(keyword):
        if keyword.find('alexa') >= 0:
            alexa.listen()

    kws.set_callback(wakeup)

    alexa.start()
    kws.start()
    audio.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    alexa.stop()
    kws.stop()
    audio.stop()


if __name__ == '__main__':
    main()
