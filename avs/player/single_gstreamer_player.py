# -*- coding: utf-8 -*-

"""Player using gstreamer."""

import time
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import logging

logger = logging.getLogger('Player')
current_player = {}


def on_eos(bus, message):
    current_player['self'].on_eos()

def on_error(bus, message):
    current_player['self'].on_error()


def make_gstreamer_playbin():
    Gst.init(None)
    bin = Gst.ElementFactory.make("playbin", "playbin")
    bus = bin.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect('sync-message::{}'.format('eos'), on_eos)
    bus.connect('sync-message::{}'.format('error'), on_error)

    return bin


playbin = make_gstreamer_playbin()


class Player(object):
    def __init__(self):
        self.uri = None
        self.last_position = 0
        self.callbacks = {}
        self._state = None

    def play(self, uri):
        self.uri = uri

        current_player['self'] = self

        playbin.set_state(Gst.State.NULL)
        playbin.set_property('uri', uri)
        playbin.set_state(Gst.State.PLAYING)

        self._state = 'PLAYING'

    def stop(self):
        if self._state == 'PLAYING':
            playbin.set_state(Gst.State.NULL)

        self._state = 'NULL'

    def pause(self):
        if self._state == 'PLAYING':
            self._state = 'PAUSED'
            playbin.set_state(Gst.State.PAUSED)

            self.last_position = self.position
            logger.info('paused position: {}'.format(self.last_position))

    def resume(self):
        if self._state == 'PAUSED':
            self._state = 'PLAYING'

            playbin.set_state(Gst.State.NULL)

            current_player['callbacks'] = self.callbacks

            playbin.set_property('uri', self.uri)
            playbin.set_state(Gst.State.PLAYING)

            for _ in range(10):
                if playbin.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, self.last_position * Gst.MSECOND):
                    break
                time.sleep(0.1)

            logger.info('resuming position: {}'.format(self.position))


    # name: {eos, ...}
    def add_callback(self, name, callback):
        if not callable(callback):
            return

        self.callbacks[name] = callback

    def on_eos(self):
        self._state = 'NULL'
        if 'eos' in self.callbacks:
            self.callbacks['eos']()
        
    def on_error(self):
        self._state = 'NULL'
        if 'error' in self.callbacks:
            self.callbacks['error']()

    @property
    def duration(self):
        if self._state != 'PLAYING':
            return 0

        for _ in range(10):
            success, duration = playbin.query_duration(Gst.Format.TIME)
            if success:
                break
            time.sleep(0.1)

        return int(duration / Gst.MSECOND)

    @property
    def position(self):
        if self._state == 'PAUSED':
            return self.last_position
        elif self._state != 'PLAYING':
            return 0

        for _ in range(10):
            success, position = playbin.query_position(Gst.Format.TIME)
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
        if self._state == 'PLAYING':
            _, st, _ = playbin.get_state(Gst.SECOND)
            if st == Gst.State.PLAYING:
                return 'PLAYING'
            else:
                self._state = 'NULL'

        return self._state
