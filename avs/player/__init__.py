# -*- coding: utf-8 -*-

"""Player
support mpv, mpg123 and gstreamer 1.0
It prefers mpv if it is available, otherwise use gstreamer 1.0
We can specify a player using environment variable PLAYER (mpv, mpg123, gstreamer, single_gstreamer)
"""

import os

player_option = os.getenv('PLAYER', 'default').lower()

if player_option.find('mpv') >= 0:
    from mpv_player import Player
elif player_option.find('mpg123') >= 0:
    from mpg123_player import Player
elif player_option.find('single') >= 0:
    from single_gstreamer_player import Player
elif player_option.find('gstreamer') >= 0:
    from gstreamer_player import Player
else:
    if os.system('which mpv') == 0:
        from mpv_player import Player
    else:
        from gstreamer_player import Player


__all__ = ['Player']

