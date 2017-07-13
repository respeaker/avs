

import os
import json

from avs.alexa import Alexa
from avs.config import DEFAULT_CONFIG_FILE

import logging


class Audio(object):
    def __init__(self):
        from respeaker import Microphone

        self.mic = Microphone()

    def wakeup(self):
        return self.mic.wakeup('alexa')

    def start(self):
        pass

    def __iter__(self):
        return self.mic.listen()

    def stop(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def main():
    import sys

    logging.basicConfig(level=logging.DEBUG)
    configuration_file = DEFAULT_CONFIG_FILE

    if len(sys.argv) < 2:
        if not os.path.isfile(configuration_file):
            print('Usage: {} [configuration.json]'.format(sys.argv[0]))
            print('\nIf configuration file is not provided, {} will be used'.format(configuration_file))
            sys.exit(1)
    else:
        configuration_file = sys.argv[1]

    with open(configuration_file, 'r') as f:
        config = json.load(f)
        require_keys = ['product_id', 'client_id', 'client_secret']
        for key in require_keys:
            if not ((key in config) and config[key]):
                print('{} should include "{}"'.format(configuration_file, key))
                sys.exit(2)

            if not ('refresh_token' in config) and config['refresh_token']:
                print('Not "refresh_token" available. you should run `alexa-auth {}` first'.format(configuration_file))
                sys.exit(3)

    audio = Audio()
    with Alexa(config, audio) as alexa:
        while True:
            if audio.wakeup():
                alexa.SpeechRecognizer.Recognize(audio).wait(60)


if __name__ == '__main__':
    main()
