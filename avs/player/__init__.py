# -*- coding: utf-8 -*-

"""Player
support mpv, mpg123 and gstreamer 1.0
It likes gstreamer 1.0 > mpv > mpg123
We can specify a player using environment variable PLAYER (mpv, mpg123, gstreamer)
"""

import os

player_option = os.getenv('PLAYER', 'default').lower()

if player_option.find('mpv') >= 0:
    from mpv_player import Player
elif player_option.find('mpg123') >= 0:
    from mpg123_player import Player
elif player_option.find('gstreamer') >= 0:
    from gstreamer_player import Player
else:
    try:
        from gstreamer_player import Player
    except ImportError:
        if os.system('which mpv >/dev/null') == 0:
            from mpv_player import Player
        elif os.system('which mpg123 >/dev/null') == 0:
            from mpg123_player import Player
        else:
            raise ImportError('No player available, install one of the players: gstreamer, mpv and mpg123 first')


__all__ = ['Player']

