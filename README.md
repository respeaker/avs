Python Alexa Voice Service App
==============================

[![](https://img.shields.io/pypi/v/avs.svg)](https://pypi.python.org/pypi/avs)
[![](https://img.shields.io/travis/respeaker/avs.svg)](https://travis-ci.org/respeaker/avs)

### Features
* Support Alexa Voice Service API v20160207
* Support multiple audio players: gstreamer 1.0, mpv and mpg123
* 支持[DuerOS](https://github.com/respeaker/avs/wiki/%E4%BD%BF%E7%94%A8DuerOS%E7%9A%84AVS%E5%85%BC%E5%AE%B9%E6%9C%8D%E5%8A%A1)


### Requirements

Choose a player from `mpv`, `mpg123` and gstreamer.
`SpeechSynthesizer` and `Alerts` prefer `mpg123` as it is more responsive.
`AudioPlayer` likes `mpv` > gstreamer > `mpg123` as `mpv` and gstreamer support more audio format. We can also specify the player of `AudioPlayer` using the environment variable `PLAYER`.

* one of mpg123, mpv and gstreamer 1.0
* python-pyaudio
* respeaker python library and pocketsphinx (optional, for hands-free keyword spotting)


### Installation
* For ReSpeaker Core (MT7688)

  gstreamer1.0, pyaudio and pocketsphinx and respeaker python library are already installed by default, just run `pip install avs`

* For Ubuntu/Debian

    sudo apt-install mpg123 mpv
    sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gir1.2-gstreamer-1.0 python-gi python-gst-1.0
    sudo apt-get install python-pyaudio
    sudo pip install avs respeaker pocketsphinx  # requires gcc toolchain and libpulse-dev

### Get started

1. run ``alexa-audio-check`` to check if recording & playing is OK. If RMS is not zero, recording is OK, if you can hear alarm, playing is OK

    $alexa-audio-check
    RMS: 41
    RMS: 43

2. run `alexa-auth` to login Amazon, it will save authorization information to `~/.avs.json`
3. run `alexa-tap`, then press Enter to talk with alexa
4. run `alexa`, then use "alexa" to start with conversation with alexa, for example, "alexa, what time is it"

>If you want to use a specified player, use the environment variable `PLAYER` to specify it, such as `PLAYER=mpv alexa-tap` or `PLAYER=mpg123 alexa` or `PLAYER=gstreamer alexa`

### To do
* Speaker interface
* Notifications interface

### Change Alexa Voice Service client id and product id
If you want to use your own  client id and product id, try:

1. [register for an Amazon Developer Account](https://github.com/alexa/alexa-avs-raspberry-pi#61---register-your-product-and-create-a-security-profile)

2. create a file named config.json with your product_id, client_id and client_secret

    {
        "product_id": "x",
        "client_id": "y",
        "client_secret": "z"
    }

3. run `alexa-auth -c config.json`

4. run `alexa-tap` or `alexa`

### License
GNU General Public License v3


### Credits
This project is based on [nicholas-gh/python-alexa-client](https://github.com/nicholas-gh/python-alexa-client)

This package was created with Cookiecutter_ and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
