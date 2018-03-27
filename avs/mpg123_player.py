# -*- coding: utf-8 -*-

"""Player using mpg123"""

import os
import signal
import threading
import subprocess


def popen(cmd, on_finished):
    p = subprocess.Popen(cmd)

    def run(process, on_finished):
        process.wait()
        on_finished()

    threading.Thread(target=run, args=(p, on_finished)).start()

    return p


class Player(object):
    def __init__(self):
        self.callbacks = {}
        self.process = None
        self.state = 'NULL'

    def play(self, uri):
        self.state = 'PLAYING'
        if uri.startswith('file://'):
            uri = uri[7:]
        
        print(uri)
        self.process = popen(['mpg123', uri], self.on_eos)

    def stop(self):
        if self.state == 'PLAYING':
            self.state = 'NULL'
            self.process.terminate()

    def pause(self):
        if self.state == 'PLAYING':
            self.state = 'PAUSED'
            os.kill(self.process.pid, signal.SIGSTOP)

    def resume(self):
        if self.state == 'PAUSED':
            self.state = 'PLAYING'
            os.kill(self.process.pid, signal.SIGCONT)

    # name: {eos, ...}
    def add_callback(self, name, callback):
        if not callable(callback):
            return

        self.callbacks[name] = callback

    def on_eos(self):
        self._state = 'NULL'
        if 'eos' in self.callbacks:
            self.callbacks['eos']()

    @property
    def duration(self):
        return 0

    @property
    def position(self):
        return 0
