# -*- coding: utf-8 -*-

import os
import subprocess
import threading


class Audio(object):

    def __init__(self, rate=16000, frames_size=160, channels=1, device_name='default'):
        self.rate = rate
        self.frames_size = frames_size
        self.channels = channels
        self.device_name = device_name
        self.done = False
        self.thread = None
        self.sinks = []

    def run(self):
        cmd = [
            'arecord',
            '-t', 'raw',
            '-f', 'S16_LE',
            '-c', str(self.channels),
            '-r', str(self.rate),
            '-D', self.device_name,
            '-q'
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        frames_bytes = int(self.frames_size * self.channels * 2)
        while not self.done:
            audio = process.stdout.read(frames_bytes)
            for sink in self.sinks:
                sink.put(audio)

        process.kill()

    def start(self):
        self.done = False
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.done = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)

    def link(self, sink):
        if hasattr(sink, 'put') and callable(sink.put):
            self.sinks.append(sink)
        else:
            raise ValueError('Not implement put() method')

    def unlink(self, sink):
        self.sinks.remove(sink)
