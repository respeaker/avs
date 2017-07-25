==============================
Python Alexa Voice Service App
==============================

.. image:: https://img.shields.io/pypi/v/avs.svg
        :target: https://pypi.python.org/pypi/avs

.. image:: https://img.shields.io/travis/respeaker/avs.svg
        :target: https://travis-ci.org/respeaker/avs

.. image:: https://readthedocs.org/projects/avs/badge/?version=latest
        :target: https://avs.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Features
--------

* Implement Alexa Voice Service API v20160207
* Support DuerOS AVS compatible service

To do
-----

* Alerts interface
* Speaker interface
* Notifications interface

Usage
-----

1. `register for an Amazon Developer Account. <https://github.com/alexa/alexa-avs-raspberry-pi#61---register-your-product-and-create-a-security-profile>`_

2. create a file named config.json with your product_id, client_id and client_secret::

    {
        "product_id": "x",
        "client_id": "y",
        "client_secret": "z"
    }

    For DuerOS, set OAUTH CONFIG URL to `http://127.0.0.1:3000/authresponse` and add `host_url` and `dueros-device-id` to the config.json, for example

    {
        "host_url": "dueros-h2.baidu.com",
        "dueros-device-id": "storyteller0001",
        "product_id": "x",
        "client_id": "y",
        "client_secret": "z"
    }



3. run::

    sudo apt-get install python-gi python-gst gir1.2-gstreamer-1.0    # if using python3, these packages should be python3-gi, python3-gst and gir1.2-gstreamer-1.0
    pip install avs
    alexa-auth config.json  # oauth
    alexa-tap               # press enter and talk


4. If you want to run hands free alexa, install `respeaker python library <https://github.com/respeaker/respeaker_python_library>`_ and run::

    alexa


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

