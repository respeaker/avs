# -*- coding: utf-8 -*-

"""Player using gstreamer."""

import time
import threading

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject


def setup():
    GObject.threads_init()
    Gst.init(None)
    loop = GLib.MainLoop()

    t = threading.Thread(target=loop.run)
    t.daemon = True
    t.start()

setup()


class Player(object):
    def __init__(self):
        self.callbacks = {}

        self.player = Gst.ElementFactory.make("playbin", "player")

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        # bus.enable_sync_message_emission()
        # bus.connect('sync-message::eos', self.on_eos)

    def play(self, uri):
        self.player.set_state(Gst.State.NULL)
        self.player.set_property('uri', uri)
        self.player.set_state(Gst.State.PLAYING)

    def stop(self):
        self.player.set_state(Gst.State.NULL)

    def pause(self):
        self.player.set_state(Gst.State.PAUSED)

    def resume(self):
        self.player.set_state(Gst.State.PLAYING)

    # name: {eos, error, ...}
    def add_callback(self, name, callback):
        if not callable(callback):
            return

        self.callbacks[name] = callback

    def on_message(self, bus, message):
        if message.type == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            if 'eos' in self.callbacks:
                self.callbacks['eos']()
        elif message.type == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            if 'error' in self.callbacks:
                self.callbacks['error']()
        # else:
        #     print(message.type)

    @property
    def duration(self):
        for _ in range(10):
            success, duration = self.player.query_duration(Gst.Format.TIME)
            if success:
                break
            time.sleep(0.1)

        return int(duration / Gst.MSECOND)

    @property
    def position(self):
        for _ in range(10):
            success, position = self.player.query_position(Gst.Format.TIME)
            if success:
                break
            time.sleep(0.1)

        return int(position / Gst.MSECOND)

    @property
    def state(self):
        # GST_STATE_VOID_PENDING        no pending state.
        # GST_STATE_NULL                the NULL state or initial state of an element.
        # GST_STATE_READY               the element is ready to go to PAUSED.
        # GST_STATE_PAUSED              the element is PAUSED, it is ready to accept and process data.
        #                               Sink elements however only accept one buffer and then block.
        # GST_STATE_PLAYING             the element is PLAYING, the GstClock is running and the data is flowing.
        _, state, _ = self.player.get_state(Gst.SECOND)
        return 'FINISHED' if state != Gst.State.PLAYING else 'PLAYING'

