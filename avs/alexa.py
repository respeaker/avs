# -*- coding: utf-8 -*-


import cgi
import io
import json
import logging
import os
import sys
import tempfile
import uuid
import base64
import signal
import threading

if sys.version_info < (3, 0):
    import Queue as queue
else:
    import queue

import requests
import datetime
import hyper

from avs.mic import Audio

from avs.interface.alerts import Alerts
from avs.interface.audio_player import AudioPlayer
from avs.interface.speaker import Speaker
from avs.interface.speech_recognizer import SpeechRecognizer
from avs.interface.speech_synthesizer import SpeechSynthesizer
from avs.interface.system import System
import avs.config

logger = logging.getLogger(__name__)


class AlexaStateListener(object):
    def __init__(self):
        pass

    def on_ready(self):
        logger.info('on_ready')

    def on_disconnected(self):
        logger.info('on_disconnected')

    def on_listening(self):
        logger.info('on_listening')

    def on_thinking(self):
        logger.info('on_thinking')

    def on_speaking(self):
        logger.info('on_speaking')

    def on_finished(self):
        logger.info('on_finished')


class Alexa(object):
    API_VERSION = 'v20160207'

    def __init__(self, config=None):
        self.event_queue = queue.Queue()
        self.SpeechRecognizer = SpeechRecognizer(self)
        self.SpeechSynthesizer = SpeechSynthesizer(self)
        self.AudioPlayer = AudioPlayer(self)
        self.Speaker = Speaker(self)
        self.Alerts = Alerts(self)
        self.System = System(self)

        self.state_listener = AlexaStateListener()

        # put() will send audio to speech recognizer
        self.put = self.SpeechRecognizer.put

        # listen() will trigger SpeechRecognizer's Recognize event
        self.listen = self.SpeechRecognizer.Recognize

        self.done = False

        self.requests = requests.Session()

        self._configfile = config
        self._config = avs.config.load(configfile=config)

        self.last_activity = datetime.datetime.utcnow()
        self._ping_time = None

    def set_state_listener(self, listner):
        self.state_listener = listner

    def start(self):
        self.done = False

        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def stop(self):
        self.done = True

    def send_event(self, event, listener=None, attachment=None):
        self.event_queue.put((event, listener, attachment))

    def run(self):
        while not self.done:
            try:
                self._run()
            except AttributeError as e:
                logger.exception(e)
                continue
            except hyper.http20.exceptions.StreamResetError as e:
                logger.exception(e)
                continue
            except ValueError as e:
                logging.exception(e)
                # failed to get an access token, exit
                sys.exit(1)
            except Exception as e:
                logging.exception(e)
                continue

    def _run(self):
        conn = hyper.HTTP20Connection('{}:443'.format(
            self._config['host_url']), force_proto='h2')

        headers = {'authorization': 'Bearer {}'.format(self.token)}
        if 'dueros-device-id' in self._config:
            headers['dueros-device-id'] = self._config['dueros-device-id']

        downchannel_id = conn.request(
            'GET', '/{}/directives'.format(self._config['api']), headers=headers)
        downchannel_response = conn.get_response(downchannel_id)
        if downchannel_response.status != 200:
            raise ValueError(
                "/directive requests returned {}".format(downchannel_response.status))

        _, pdict = cgi.parse_header(
            downchannel_response.headers['content-type'][0].decode('utf-8'))
        downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
        downchannel = conn.streams[downchannel_id]
        downchannel_buffer = ''
        eventchannel_boundary = 'seeed-voice-engine'

        # ping every 5 minutes (60 seconds early for latency) to maintain the connection
        self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)
        self.event_queue.queue.clear()
        self.System.SynchronizeState()
        while not self.done:
            # logger.info("Waiting for event to send to AVS")
            # logger.info("Connection socket can_read %s", conn._sock.can_read)
            try:
                event, listener, attachment = self.event_queue.get(
                    timeout=0.25)
            except queue.Empty:
                event = None

            # we want to avoid blocking if the data wasn't for stream downchannel
            while conn._sock.can_read:
                conn._single_read()

            while downchannel.data:
                framebytes = downchannel._read_one_frame()
                downchannel_buffer = self._parse_response(
                    framebytes, downchannel_boundary, downchannel_buffer
                )

            if event is None:
                self._ping(conn)
                self.System.UserInactivityReport()
                continue

            headers = {
                ':method': 'POST',
                ':scheme': 'https',
                ':path': '/{}/events'.format(self._config['api']),
                'authorization': 'Bearer {}'.format(self.token),
                'content-type': 'multipart/form-data; boundary={}'.format(eventchannel_boundary)
            }
            if 'dueros-device-id' in self._config:
                headers['dueros-device-id'] = self._config['dueros-device-id']

            stream_id = conn.putrequest(headers[':method'], headers[':path'])
            default_headers = (':method', ':scheme', ':authority', ':path')
            for name, value in headers.items():
                is_default = name in default_headers
                conn.putheader(name, value, stream_id, replace=is_default)
            conn.endheaders(final=False, stream_id=stream_id)

            metadata = {
                'context': self.context,
                'event': event
            }
            logger.info('metadata: {}'.format(json.dumps(metadata, indent=4)))

            json_part = '--{}\r\n'.format(eventchannel_boundary)
            json_part += 'Content-Disposition: form-data; name="metadata"\r\n'
            json_part += 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
            json_part += json.dumps(metadata)

            conn.send(json_part.encode('utf-8'),
                      final=False, stream_id=stream_id)

            if attachment:
                attachment_header = '\r\n--{}\r\n'.format(
                    eventchannel_boundary)
                attachment_header += 'Content-Disposition: form-data; name="audio"\r\n'
                attachment_header += 'Content-Type: application/octet-stream\r\n\r\n'
                conn.send(attachment_header.encode('utf-8'),
                          final=False, stream_id=stream_id)

                # AVS_AUDIO_CHUNK_PREFERENCE = 320
                for chunk in attachment:
                    conn.send(chunk, final=False, stream_id=stream_id)

                    # check if StopCapture directive is received
                    while conn._sock.can_read:
                        conn._single_read()

                    while downchannel.data:
                        framebytes = downchannel._read_one_frame()
                        downchannel_buffer = self._parse_response(
                            framebytes, downchannel_boundary, downchannel_buffer
                        )

                self.last_activity = datetime.datetime.utcnow()

            end_part = '\r\n--{}--'.format(eventchannel_boundary)
            conn.send(end_part.encode('utf-8'),
                      final=True, stream_id=stream_id)

            logger.info("wait for response")
            response = conn.get_response(stream_id)
            logger.info("status code: %s", response.status)

            if response.status == 200:
                _, pdict = cgi.parse_header(
                    response.headers['content-type'][0].decode('utf-8'))
                boundary = b'--{}'.format(pdict['boundary'])
                self._parse_response(response.read(), boundary)
            elif response.status == 204:
                pass
            else:
                logger.warning(response.headers)
                logger.warning(response.read())

            if listener and callable(listener):
                listener()

    def _parse_response(self, response, boundary, buffer=''):
        directives = []
        blen = len(boundary)
        response = buffer + response
        while response:
            pos = response.find(boundary)
            if pos < 0:
                break

            # skip small data block
            if pos > blen:
                # a blank line is between parts
                parts = response[:pos-2].split('\r\n\r\n', 1)
                if parts[0].find('application/json') >= 0:
                    metadata = json.loads(parts[1].decode('utf-8'))
                    if 'directive' in metadata:
                        directives.append(metadata['directive'])
                elif parts[0].find('application/octet-stream') >= 0:
                    for line in parts[0].splitlines():
                        name, value = line.split(':', 1)
                        if name.lower() == 'content-id':
                            content_id = value.strip()[1:-1]
                            filename = base64.urlsafe_b64encode(content_id)[:8]
                            with open(os.path.join(tempfile.gettempdir(), '{}.mp3'.format(filename)), 'wb') as f:
                                f.write(parts[1])
                            logger.info('write audio to {}.mp3'.format(filename))
                            break

            response = response[pos+blen+2:]

        for directive in directives:
            self._handle_directive(directive)

        return response

    def _handle_directive(self, directive):
        logger.info(json.dumps(directive, indent=4))
        try:
            namespace = directive['header']['namespace']
            name = directive['header']['name']
            if hasattr(self, namespace):
                interface = getattr(self, namespace)
                directive_func = getattr(interface, name, None)
                if directive_func:
                    directive_func(directive)
                else:
                    logger.info(
                        '{}.{} is not implemented yet'.format(namespace, name))
            else:
                logger.info('{} is not implemented yet'.format(namespace))

        except KeyError as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)

    def _ping(self, connection):
        if datetime.datetime.utcnow() >= self._ping_time:
            connection.ping(uuid.uuid4().hex[:8])

            logger.debug('ping at {}'.format(
                datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y")))

            # ping every 5 minutes (60 seconds early for latency) to maintain the connection
            self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

    @property
    def context(self):
        # return [self.SpeechRecognizer.context, self.SpeechSynthesizer.context,
        #                    self.AudioPlayer.context, self.Speaker.context, self.Alerts.context]
        return [self.SpeechSynthesizer.context, self.Speaker.context, self.AudioPlayer.context, self.Alerts.context]

    @property
    def token(self):
        date_format = "%a %b %d %H:%M:%S %Y"

        if 'access_token' in self._config:
            if 'expiry' in self._config:
                expiry = datetime.datetime.strptime(
                    self._config['expiry'], date_format)
                # refresh 60 seconds early to avoid chance of using expired access_token
                if (datetime.datetime.utcnow() - expiry) > datetime.timedelta(seconds=60):
                    logger.info("Refreshing access_token")
                else:
                    return self._config['access_token']

        payload = {
            'client_id': self._config['client_id'],
            'client_secret': self._config['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self._config['refresh_token']
        }

        response = None

        # try to request an access token 3 times
        for _ in range(3):
            try:
                response = self.requests.post(
                    self._config['refresh_url'], data=payload)
                if response.status_code != 200:
                    logger.warning(response.text)
                else:
                    break
            except Exception as e:
                logger.exception(e)
                continue

        if (response is None) or (not hasattr(response, 'status_code')) or response.status_code != 200:
            raise ValueError(
                "refresh token request returned {}".format(response.status))

        config = response.json()
        self._config['access_token'] = config['access_token']

        expiry_time = datetime.datetime.utcnow(
        ) + datetime.timedelta(seconds=config['expires_in'])
        self._config['expiry'] = expiry_time.strftime(date_format)
        logger.debug(json.dumps(self._config, indent=4))

        avs.config.save(self._config, configfile=self._configfile)

        return self._config['access_token']

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    logging.basicConfig(level=logging.INFO)

    config = None if len(sys.argv) < 2 else sys.argv[1]

    audio = Audio()
    alexa = Alexa(config)

    audio.link(alexa)

    alexa.start()
    audio.start()

    is_quit = threading.Event()

    def signal_handler(signal, frame):
        print('Quit')
        is_quit.set()

    signal.signal(signal.SIGINT, signal_handler)

    while not is_quit.is_set():
        try:
            input('press ENTER to talk\n')
        except SyntaxError:
            pass
        except NameError:
            pass

        alexa.listen()

    alexa.stop()
    audio.stop()


if __name__ == '__main__':
    main()
