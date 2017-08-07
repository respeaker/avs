# -*- coding: utf-8 -*-


import pyaudio
try:
    import Queue as queue
except ImportError:
    import queue
import threading
import logging


log = logging.getLogger(__name__)


class Audio(object):

    def __init__(self, rate=16000, channels=1, chunk_size=None):
        self.channels = channels
        self.sample_rate = rate
        self.chunk_size = chunk_size if chunk_size else rate / 100

        self.pyaudio_instance = pyaudio.PyAudio()
        self.queue = queue.Queue()
        self.quit_event = threading.Event()

        self.stream = self.pyaudio_instance.open(
            start=False,
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=int(self.sample_rate),
            frames_per_buffer=int(self.chunk_size),
            stream_callback=self._callback,
            input=True
        )

        self.sinks = []

    def _callback(self, in_data, frame_count, time_info, status):
        for sink in self.sinks:
            sink.put(in_data)
        return None, pyaudio.paContinue

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()

    def link(self, sink):
        if hasattr(sink, 'put') and callable(sink.put):
            self.sinks.append(sink)
        else:
            raise ValueError('Not implement put() method')

    def unlink(self, sink):
        self.sinks.remove(sink)


