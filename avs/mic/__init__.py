# -*- coding: utf-8 -*-

import os


recorder_option = os.getenv('RECORDER', 'default').lower()

if recorder_option.find('pyaudio') >= 0 or os.system('which arecord >/dev/null') != 0:
    from pyaudio_recorder import Audio
else:
    from alsa_recorder import Audio


__all__ = ['Audio']
