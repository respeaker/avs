# -*- coding: utf-8 -*-


import cgi
import io
import json
import uuid

try:
    import Queue as queue
except ImportError:
    import queue
import threading
import datetime

import hyper

from interface.alerts import Alerts
from interface.audio_player import AudioPlayer
from interface.speaker import Speaker
from interface.speech_recognizer import SpeechRecognizer
from interface.speech_synthesizer import SpeechSynthesizer
from interface.system import System

import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class Alexa(object):
    API_VERSION = 'v20160207'

    def __init__(self, tokens_filename, audio):
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

        self._tokens_filename = tokens_filename
        self._tokens = None

        self._last_activity = None

    def start(self):
        t = threading.Thread(target=self.loop)
        t.daemon = True
        t.start()
        self.ready.wait()

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

        conn = hyper.HTTP20Connection(
            'avs-alexa-na.amazon.com:443', force_proto='h2')

        downchannel_id = conn.request(
            'GET',
            '/{}/directives'.format(self.API_VERSION),
            headers={'authorization': 'Bearer {}'.format(self.token)}
        )
        downchannel_response = conn.get_response(downchannel_id)
        if downchannel_response.status != 200:
            raise ValueError(
                "/directive requests returned {}".format(downchannel_response.status))
        ctype, pdict = cgi.parse_header(
            downchannel_response.headers['content-type'][0].decode('utf-8'))

        downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
        downchannel = conn.streams[downchannel_id]

        self.System.SynchronizeState()

        self.ready.set()

        downchannel_buffer = io.BytesIO()
        boundary = 'this-is-a-boundary'
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
                ':path': '/{}/events'.format(self.API_VERSION),
                'authorization': 'Bearer {}'.format(self.token),
                'content-type': 'multipart/form-data; boundary={}'.format(boundary)
            }
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

            json_part = '--{}\r\n'.format(boundary)
            json_part += 'Content-Disposition: form-data; name="metadata"\r\n'
            json_part += 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
            json_part += json.dumps(metadata)

            conn.send(json_part.encode('utf-8'), final=False, stream_id=stream_id)

            if 'attachment' in event:
                attachment = event['attachment']
                attachment_header = '\r\n--{}\r\n'.format(boundary)
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

            end_part = '\r\n--{}--'.format(boundary)
            conn.send(end_part.encode('utf-8'), final=True, stream_id=stream_id)

            log.info("wait for response")
            resp = conn.get_response(stream_id)
            log.info("status code: %s", resp.status)

            if resp.status == 200:
                self._read_response(resp)
            elif resp.status == 204:
                pass
            else:
                log.warning("unexpected status code: %s", resp.status)
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
                        with open('{}.mp3'.format(content_id), 'wb') as f:
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
        # ping every 5 minutes (30 seconds early for latency) to maintain the connection
        if datetime.datetime.utcnow() - self._last_activity > datetime.timedelta(seconds=270):
            # ping_stream_id = connection.request('GET', '/ping',
            #                                     headers={'authorization': 'Bearer {}'.format(self.token)})
            # resp = connection.get_response(ping_stream_id)
            # if resp.status != 200 and resp.status != 204:
            #     raise ValueError("/ping requests returned {}".format(resp.status))

            connection.ping(uuid.uuid4().hex[:8])

            self._last_activity = datetime.datetime.utcnow()

            log.debug('ping at {}'.format(self._last_activity.strftime("%a %b %d %H:%M:%S %Y")))

    @property
    def context(self):
        # return [self.SpeechRecognizer.context, self.SpeechSynthesizer.context,
        #                    self.AudioPlayer.context, self.Speaker.context, self.Alerts.context]
        return [self.SpeechSynthesizer.context, self.Speaker.context]

    @property
    def token(self):
        date_format = "%a %b %d %H:%M:%S %Y"

        if not self._tokens:
            with open(self._tokens_filename, 'r') as f:
                self._tokens = json.loads(f.read())

        if 'access_token' in self._tokens:
            if 'expiry' in self._tokens:
                expiry = datetime.datetime.strptime(self._tokens['expiry'], date_format)
                # refresh 60 seconds early to avoid chance of using expired access_token
                if (datetime.datetime.utcnow() - expiry) > datetime.timedelta(seconds=60):
                    log.info("Refreshing access_token")
                else:
                    log.info("access_token should be OK, expires %s", expiry)
                    return self._tokens['access_token']

        payload = {
            'client_id': self._tokens['client_id'],
            'client_secret': self._tokens['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self._tokens['refresh_token']
        }

        conn = hyper.HTTPConnection('api.amazon.com:443', secure=True, force_proto="h2")
        conn.request("POST", "/auth/o2/token",
                     headers={'Content-Type': "application/json"},
                     body=json.dumps(payload).encode('utf-8'))
        r = conn.get_response()
        if r.status == 200:
            tokens = json.loads(r.read().decode('utf-8'))
            expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=tokens['expires_in'])
            self._tokens['expiry'] = expiry_time.strftime(date_format)
            with open(self._tokens_filename, 'w') as f:
                f.write(json.dumps(self._tokens, indent=4))

            return tokens['access_token']
        else:
            raise ValueError("refresh token request returned {}".format(r.status))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    from mic import Mic
    import sys

    if len(sys.argv) < 2:
        print('Usage: {} tokens.json'.format(sys.argv[0]))
        sys.exit(1)

    audio = Mic()
    with Alexa(sys.argv[1], audio) as alexa:
        while True:
            try:
                try:
                    input('press ENTER to talk with alexa')
                except SyntaxError:
                    pass

                alexa.SpeechRecognizer.Recognize(audio).wait(20)
            except KeyboardInterrupt:
                break


if __name__ == '__main__':
    main()
