# -*- coding: utf-8 -*-


import cgi
import io
import json
import uuid
import requests

try:
    import Queue as queue
except ImportError:
    import queue
import threading
import datetime

import hyper

from avs.interface.alerts import Alerts
from avs.interface.audio_player import AudioPlayer
from avs.interface.speaker import Speaker
from avs.interface.speech_recognizer import SpeechRecognizer
from avs.interface.speech_synthesizer import SpeechSynthesizer
from avs.interface.system import System

import logging
import os
import tempfile
from avs.config import DEFAULT_CONFIG_FILE


log = logging.getLogger(__name__)


class Alexa(object):
    API_VERSION = 'v20160207'
    # API_VERSION = 'dcs/avs-compatible-v20160207'

    def __init__(self, config, audio):
        self.event_queue = queue.Queue()
        self.SpeechRecognizer = SpeechRecognizer(self)
        self.SpeechSynthesizer = SpeechSynthesizer(self)
        self.AudioPlayer = AudioPlayer(self)
        self.Speaker = Speaker(self)
        self.Alerts = Alerts(self)
        self.System = System(self)

        self.ready = threading.Event()
        self.done = threading.Event()

        self.audio = audio

        self.requests = requests.Session()

        self._config = config

        if ('host_url' not in self._config) or (not self._config['host_url']):
            self._config['host_url'] = 'avs-alexa-na.amazon.com'

        if self._config['host_url'] == 'dueros-h2.baidu.com':
            self._config['api'] = 'dcs/avs-compatible-v20160207'
            self._config['refresh_url'] = 'https://openapi.baidu.com/oauth/2.0/token'
        else:
            self._config['api'] = 'v20160207'
            self._config['refresh_url'] = 'https://api.amazon.com/auth/o2/token'

        self._last_activity = None
        self._ping_time = None

    def start(self):
        t = threading.Thread(target=self.loop)
        t.daemon = True
        t.start()
        self.ready.wait(60)

    def stop(self):
        self.done.set()
        self.ready.clear()

    def loop(self):
        while not self.done.is_set():
            try:
                self._loop()
            except Exception as e:
                log.exception(e)
                log.info('reconnect...')

    def _loop(self):
        self.done.clear()
        self.event_queue.queue.clear()

        # ping every 5 minutes (60 seconds early for latency) to maintain the connection
        self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

        conn = hyper.HTTP20Connection('{}:443'.format(self._config['host_url']), force_proto='h2')

        headers = {'authorization': 'Bearer {}'.format(self.token)}
        if 'dueros-device-id' in self._config:
            headers['dueros-device-id'] = self._config['dueros-device-id']

        downchannel_id = conn.request('GET', '/{}/directives'.format(self._config['api']), headers=headers)
        downchannel_response = conn.get_response(downchannel_id)
        if downchannel_response.status != 200:
            raise ValueError("/directive requests returned {}".format(downchannel_response.status))

        ctype, pdict = cgi.parse_header(downchannel_response.headers['content-type'][0].decode('utf-8'))
        downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
        downchannel = conn.streams[downchannel_id]
        downchannel_buffer = io.BytesIO()
        eventchannel_boundary = 'seeed-voice-engine'

        self.System.SynchronizeState()

        self.ready.set()

        while not self.done.is_set():
            # log.info("Waiting for event to send to AVS")
            # log.info("Connection socket can_read %s", conn._sock.can_read)
            try:
                event = self.event_queue.get(timeout=0.25)
            except queue.Empty:
                event = None

            # we want to avoid blocking if the data wasn't for stream downchannel
            while conn._sock.can_read:
                conn._single_read()

            while downchannel.data:
                framebytes = downchannel._read_one_frame()
                self._read_response(
                    framebytes, downchannel_boundary, downchannel_buffer)

            if event is None:
                self._ping(conn)
                continue

            self._last_activity = datetime.datetime.utcnow()

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
                'event': event['event']
            }
            log.debug('metadata: {}'.format(json.dumps(metadata, indent=4)))

            json_part = '--{}\r\n'.format(eventchannel_boundary)
            json_part += 'Content-Disposition: form-data; name="metadata"\r\n'
            json_part += 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
            json_part += json.dumps(metadata)

            conn.send(json_part.encode('utf-8'), final=False, stream_id=stream_id)

            if 'attachment' in event:
                attachment = event['attachment']
                attachment_header = '\r\n--{}\r\n'.format(eventchannel_boundary)
                attachment_header += 'Content-Disposition: form-data; name="audio"\r\n'
                attachment_header += 'Content-Type: application/octet-stream\r\n\r\n'
                conn.send(attachment_header.encode('utf-8'), final=False, stream_id=stream_id)

                # AVS_AUDIO_CHUNK_PREFERENCE = 320
                for chunk in attachment:
                    conn.send(chunk, final=False, stream_id=stream_id)

                    # check if StopCapture directive is received
                    while conn._sock.can_read:
                        conn._single_read()

                    while downchannel.data:
                        framebytes = downchannel._read_one_frame()
                        self._read_response(framebytes, downchannel_boundary, downchannel_buffer)

            end_part = '\r\n--{}--'.format(eventchannel_boundary)
            conn.send(end_part.encode('utf-8'), final=True, stream_id=stream_id)

            log.info("wait for response")
            resp = conn.get_response(stream_id)
            log.info("status code: %s", resp.status)

            if resp.status == 200:
                self._read_response(resp)
            elif resp.status == 204:
                pass
            else:
                log.warning(resp.headers)
                log.warning(resp.read())

    def _read_response(self, response, boundary=None, buffer=None):
        if boundary:
            endboundary = boundary + b"--"
        else:
            ctype, pdict = cgi.parse_header(
                response.headers['content-type'][0].decode('utf-8'))
            boundary = "--{}".format(pdict['boundary']).encode('utf-8')
            endboundary = "--{}--".format(pdict['boundary']).encode('utf-8')

        on_boundary = False
        in_header = False
        in_payload = False
        first_payload_block = False
        content_type = None
        content_id = None

        def iter_lines(response, delimiter=None):
            pending = None
            for chunk in response.read_chunked():
                # log.debug("Chunk size is {}".format(len(chunk)))
                if pending is not None:
                    chunk = pending + chunk
                if delimiter:
                    lines = chunk.split(delimiter)
                else:
                    lines = chunk.splitlines()

                if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
                    pending = lines.pop()
                else:
                    pending = None

                for line in lines:
                    yield line

            if pending is not None:
                yield pending

        # cache them up to execute after we've downloaded any binary attachments
        # so that they have the content available
        directives = []
        if isinstance(response, bytes):
            buffer.seek(0)
            lines = (buffer.read() + response).split(b"\r\n")
            buffer.flush()
        else:
            lines = iter_lines(response, delimiter=b"\r\n")
        for line in lines:
            # log.debug("iter_line is {}...".format(repr(line)[0:30]))
            if line == boundary or line == endboundary:
                # log.debug("Newly on boundary")
                on_boundary = True
                if in_payload:
                    in_payload = False
                    if content_type == "application/json":
                        log.info("Finished downloading JSON")
                        json_payload = json.loads(payload.getvalue().decode('utf-8'))
                        log.debug(json_payload)
                        if 'directive' in json_payload:
                            directives.append(json_payload['directive'])
                    else:
                        log.info("Finished downloading {} which is {}".format(content_type, content_id))
                        payload.seek(0)
                        # TODO, start to stream this to speakers as soon as we start getting bytes
                        # strip < and >
                        content_id = content_id[1:-1]
                        with open(os.path.join(tempfile.gettempdir(), '{}.mp3'.format(content_id)), 'wb') as f:
                            f.write(payload.read())

                        log.info('write audio to {}.mp3'.format(content_id))

                continue
            elif on_boundary:
                # log.debug("Now in header")
                on_boundary = False
                in_header = True
            elif in_header and line == b"":
                # log.debug("Found end of header")
                in_header = False
                in_payload = True
                first_payload_block = True
                payload = io.BytesIO()
                continue

            if in_header:
                # log.debug(repr(line))
                if len(line) > 1:
                    header, value = line.decode('utf-8').split(":", 1)
                    ctype, pdict = cgi.parse_header(value)
                    if header.lower() == "content-type":
                        content_type = ctype
                    if header.lower() == "content-id":
                        content_id = ctype

            if in_payload:
                # add back the bytes that our iter_lines consumed
                log.info("Found %s bytes of %s %s, first_payload_block=%s",
                         len(line), content_id, content_type, first_payload_block)
                if first_payload_block:
                    first_payload_block = False
                else:
                    payload.write(b"\r\n")
                # TODO write this to a queue.Queue in self._content_cache[content_id]
                # so that other threads can start to play it right away
                payload.write(line)

        if buffer is not None:
            if in_payload:
                log.info(
                    "Didn't see an entire directive, buffering to put at top of next frame")
                buffer.write(payload.read())
            else:
                buffer.write(boundary)
                buffer.write(b"\r\n")

        for directive in directives:
            self._handle_directive(directive)

    def _handle_directive(self, directive):
        log.debug(json.dumps(directive, indent=4))
        try:
            namespace = directive['header']['namespace']
            name = directive['header']['name']
            if hasattr(self, namespace):
                interface = getattr(self, namespace)
                directive_func = getattr(interface, name, None)
                if directive_func:
                    directive_func(directive)
                else:
                    log.info('{}.{} is not implemented yet'.format(namespace, name))
            else:
                log.info('{} is not implemented yet'.format(namespace))

        except KeyError as e:
            log.exception(e)
        except Exception as e:
            log.exception(e)

    def _ping(self, connection):
        if datetime.datetime.utcnow() >= self._ping_time:
            # ping_stream_id = connection.request('GET', '/ping',
            #                                     headers={'authorization': 'Bearer {}'.format(self.token)})
            # resp = connection.get_response(ping_stream_id)
            # if resp.status != 200 and resp.status != 204:
            #     log.warning(resp.read())
            #     raise ValueError("/ping requests returned {}".format(resp.status))

            connection.ping(uuid.uuid4().hex[:8])

            # ping every 5 minutes (60 seconds early for latency) to maintain the connection
            self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)
            log.debug('ping at {}'.format(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y")))

    @property
    def context(self):
        # return [self.SpeechRecognizer.context, self.SpeechSynthesizer.context,
        #                    self.AudioPlayer.context, self.Speaker.context, self.Alerts.context]
        return [self.SpeechSynthesizer.context, self.Speaker.context, self.AudioPlayer.context]

    @property
    def token(self):
        date_format = "%a %b %d %H:%M:%S %Y"

        if 'access_token' in self._config:
            if 'expiry' in self._config:
                expiry = datetime.datetime.strptime(self._config['expiry'], date_format)
                # refresh 60 seconds early to avoid chance of using expired access_token
                if (datetime.datetime.utcnow() - expiry) > datetime.timedelta(seconds=60):
                    log.info("Refreshing access_token")
                else:
                    return self._config['access_token']

        payload = {
            'client_id': self._config['client_id'],
            'client_secret': self._config['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self._config['refresh_token']
        }

        r = self.requests.post(self._config['refresh_url'], data=payload)
        if r.status_code != 200:
            log.warning(r.text)
            raise ValueError("refresh token request returned {}".format(r.status))
        config = r.json()
        self._config['access_token'] = config['access_token']

        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
        self._config['expiry'] = expiry_time.strftime(date_format)
        log.debug(json.dumps(config, indent=4))

        return self._config['access_token']

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    from avs.mic import Mic
    import sys

    logging.basicConfig(level=logging.INFO)
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

    audio = Mic()
    with Alexa(config, audio) as alexa:
        while True:
            try:
                try:
                    input('press ENTER to talk\n')
                except SyntaxError:
                    pass

                alexa.SpeechRecognizer.Recognize(audio).wait(20)
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    main()
