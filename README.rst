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


3. run::

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

