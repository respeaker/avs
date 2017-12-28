# -*- coding: utf-8 -*-

import json
import os
import sys
import uuid

DEFAULT_CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.avs.json')


def load(configfile=None):
    if configfile is None:
        if os.path.isfile(DEFAULT_CONFIG_FILE):
            configfile = DEFAULT_CONFIG_FILE
        else:
            if sys.argv[0].find('dueros-auth') >= 0:
                product_id = "xiaojing-" + uuid.uuid4().hex
                return {
                    "dueros-device-id": product_id,
                    "client_id": "lud6jnwdVFim4K4Zkoas3BkRVLvCO57Z",
                    "host_url": "dueros-h2.baidu.com",
                    "client_secret": "A017kke1GSSz7hp8Fj6ySoIWrnFraxf5",
                    "product_id": product_id
                }

            else:
                raise Exception('Could not find config file')

    with open(configfile, 'r') as f:
        config = json.load(f)
        require_keys = ['product_id', 'client_id', 'client_secret']
        for key in require_keys:
            if not ((key in config) and config[key]):
                raise KeyError('{} should include "{}"'.format(configfile, key))

    return config


def save(config, configfile=None):
    if configfile is None:
        configfile = DEFAULT_CONFIG_FILE

    with open(configfile, 'w') as f:
        json.dump(config, f, indent=4)
