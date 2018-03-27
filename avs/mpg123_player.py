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
        self.audio = None

        self.event = threading.Event()
        t = threading.Thread(target=self._run)
        t.daemon = True
        t.start()

    def _run(self):
        while True:
            self.event.wait()
            self.event.clear()
            print('Playing {}'.format(self.audio))
            self.process = subprocess.Popen(['mpg123', self.audio])
            self.process.wait()
            print('Finished {}'.format(self.audio))

            if not self.event.is_set():
                self.on_eos()

    def play(self, uri):
        print('play()')


        if uri.startswith('file://'):
            uri = uri[7:]

        self.audio = uri
        self.event.set()

        if self.process and self.process.poll() == None:
            if self.state == 'PAUSED':
                os.kill(self.process.pid, signal.SIGCONT)
            self.process.terminate()
            
        self.state = 'PLAYING'
        
        print('set play event')

    def stop(self):
        if self.process and self.process.poll() == None:
            if self.state == 'PAUSED':
                os.kill(self.process.pid, signal.SIGCONT)
            self.process.terminate()
        self.state = 'NULL'

    def pause(self):
        if self.state == 'PLAYING':
            self.state = 'PAUSED'
            os.kill(self.process.pid, signal.SIGSTOP)

        print('pause()')

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
        self.state = 'NULL'
        if 'eos' in self.callbacks:
            self.callbacks['eos']()

    @property
    def duration(self):
        return 0

    @property
    def position(self):
        return 0
