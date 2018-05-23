Python Alexa Voice Service App
==============================

[![](https://img.shields.io/pypi/v/avs.svg)](https://pypi.python.org/pypi/avs)
[![](https://img.shields.io/travis/respeaker/avs.svg)](https://travis-ci.org/respeaker/avs)

### Features
* Support Alexa Voice Service API v20160207
* Support multiple audio players: gstreamer 1.0, mpv and mpg123
* 支持[Baidu DuerOS](https://github.com/respeaker/avs/wiki/%E4%BD%BF%E7%94%A8DuerOS%E7%9A%84AVS%E5%85%BC%E5%AE%B9%E6%9C%8D%E5%8A%A1)


### Requirements

1. Player

    We have 3 players (`mpv`, `mpg123` and gstreamer) to use.
    `SpeechSynthesizer` and `Alerts` prefer `mpg123` which is more responsive.
    `AudioPlayer` likes gstreamer > `mpv` > `mpg123`. Gstreamer supports more audio format and works well on raspberry pi. We can also specify the player of `AudioPlayer` using the environment variable `PLAYER`.

2. Recorder

    2 recorders (pyaudio & `arecord`) are available. We can use environment variable `RECORDER` to specify the recorder. For example, run `RECORDER=pyaudio alexa-tap` will use pyaudio as the recorder. By default, `arecord` is used as the recorder.

3. Keyword detector (optional)

    Use PocketSphinx or Snowboy. To use pocketsphinx, install respeaker python library and pocketsphinx.
    To use Snowboy, go to [Snowboy's Github](https://github.com/Kitt-AI/snowboy) to install it.

>If you use raspberry pi and gstreamer, it is likely that gstreamer's default audio sink is GstOMXHdmiAudioSink. It ignores ALSA configurations and outputs audio to HDMI. If you don't want to use HDMI audio output, you should run `sudo apt remove gstreamer1.0-omx gstreamer1.0-omx-rpi`

### Installation
* For ReSpeaker Core (MT7688)

  gstreamer1.0, pyaudio and pocketsphinx and respeaker python library are already installed by default, just run `pip install avs`

* For Debian/Ubuntu/Raspbian

    sudo apt-install mpg123 mpv
    sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gir1.2-gstreamer-1.0 python-gi python-gst-1.0
    sudo apt-get install python-pyaudio

### Get started

1. run `alexa-audio-check` to check if recording & playing is OK. If RMS is not zero, recording is OK, if you can hear alarm, playing is OK

    $alexa-audio-check
    RMS: 41
    RMS: 43

2. run `alexa-auth` to login Amazon, it will save authorization information to `~/.avs.json`
3. run `alexa-tap`, then press Enter to talk with alexa

>If you want to use a specified player, use the environment variable `PLAYER` to specify it, such as `PLAYER=mpv alexa-tap` or `PLAYER=mpg123 alexa` or `PLAYER=gstreamer alexa`

### Hands-free Alexa
#### Using PocketSphinx for Keyword Spotting
1. install respeaker and pocketsphinx python packages

    `sudo pip install respeaker pocketsphinx  # pocketsphinx requires gcc toolchain and libpulse-dev`

2. run `alexa`, then use "alexa" to start a conversation with alexa, for example, "alexa, what time is it"

#### Using Snowboy for Keyword Spotting
1. Install [Snowboy](https://github.com/Kitt-AI/snowboy)
2. Install voice-engine python library

    `sudo pip install voice-engine`

3. run the following python script and use the keyword `alexa` to start a conversation with alexa


        import signal
        from voice_engine.source import Source
        from voice_engine.kws import KWS
        from avs.alexa import Alexa


        src = Source(rate=16000)
        kws = KWS(model='alexa')
        alexa = Alexa()

        src.pipeline(kws, alexa)

        def on_detected(keyword):
            print('detected {}'.format(keyword))
            alexa.listen()

        kws.set_callback(on_detected)

        is_quit = []
        def signal_handler(signal, frame):
            print('Quit')
            is_quit.append(True)

        signal.signal(signal.SIGINT, signal_handler)

        src.pipeline_start()
        while not is_quit:
            time.sleep(1)
        src.pipeline_stop()

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
