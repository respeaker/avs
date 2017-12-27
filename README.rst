==============================
Python Alexa Voice Service App
==============================

.. image:: https://img.shields.io/pypi/v/avs.svg
        :target: https://pypi.python.org/pypi/avs

.. image:: https://img.shields.io/travis/respeaker/avs.svg
        :target: https://travis-ci.org/respeaker/avs


Features
--------

* Support Alexa Voice Service API v20160207
* `支持DuerOS <https://github.com/respeaker/avs/wiki/%E4%BD%BF%E7%94%A8DuerOS%E7%9A%84AVS%E5%85%BC%E5%AE%B9%E6%9C%8D%E5%8A%A1>`_


To do
-----

* Speaker interface
* Notifications interface

Requirements
-------------

* gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gir1.2-gstreamer-1.0
* python-gi python-gst-1.0 python-pyaudio
* respeaker python library  and pocketsphinx (optional, for hands-free keyword spotting)


Installation
-------------

* For ReSpeaker Core (MT7688), gstreamer, pyaudio and pocketsphinx and respeaker python library are installed by default, just run ``pip install avs``
* For Ubuntu/Debian::

    sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gir1.2-gstreamer-1.0 python-gi python-gst-1.0 python-pyaudio
    sudo pip install avs respeaker pocketsphinx


Get started
------------

1. run ``alexa-audio-check`` to check if recording & playing is OK. If RMS is not zero, recording is OK, if you can hear alarm, playing is OK.

    $alexa-audio-check
    RMS: 41
    RMS: 43

2. run ``alexa-auth`` to login Amazon, it will save authorization information to ``~/.avs.json``
3. run ``alexa-tap``, then press Enter to talk with alexa
4. run ``alexa``, then use "alexa" to start with conversation with alexa, for example, "alexa, what time is it"


Change Alexa Voice Service client id and product id
----------------------------------------------------

If you want to use your own  client id and product id, try:

1. `register for an Amazon Developer Account. <https://github.com/alexa/alexa-avs-raspberry-pi#61---register-your-product-and-create-a-security-profile>`_

2. create a file named config.json with your product_id, client_id and client_secret::

    {
        "product_id": "x",
        "client_id": "y",
        "client_secret": "z"
    }

3. run ``alexa-auth -c config.json``

4. run ``alexa-tap`` or ``alexa``

License
-------
* Free software: GNU General Public License v3


Credits
-------

This project is based on `nicholas-gh/python-alexa-client`_.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _`nicholas-gh/python-alexa-client`: https://github.com/nicholas-gh/python-alexa-client
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

