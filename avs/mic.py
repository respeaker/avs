

import pyaudio
try:
    import Queue as queue
except ImportError:
    import queue
import threading
import logging


log = logging.getLogger(__name__)


class Mic(object):

    def __init__(self, rate=16000, chunk_size=None):
        self.channels = 1
        self.sample_rate = rate
        self.chunk_size = chunk_size if chunk_size else rate / 100

        self.pyaudio_instance = pyaudio.PyAudio()
        self.queue = queue.Queue()
        self.quit_event = threading.Event()

        self.stream = self.pyaudio_instance.open(
            start=False,
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=int(self.sample_rate),
            frames_per_buffer=int(self.chunk_size),
            stream_callback=self._callback,
            input=True
        )

    def _callback(self, in_data, frame_count, time_info, status):
        self.queue.put(in_data)
        return None, pyaudio.paContinue

    def start(self):
        if self.stream.is_stopped():
            self.queue.queue.clear()
            self.stream.start_stream()
            log.info('start recording')
        else:
            log.info('already started')

    def stop(self):
        if not self.stream.is_stopped():
            self.quit_event.set()
            self.stream.stop_stream()
            self.queue.put('')
            log.info('stop recording')
        else:
            log.info('already stopped')

    def read_chunked(self):
        self.quit_event.clear()
        while not self.quit_event.is_set():
            try:
                frames = self.queue.get(timeout=0.5)
            except queue.Empty:
                log.debug('timeout')
                break

            if not frames:
                log.debug('done')
                break

            yield frames

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __iter__(self):
        self.start()
        return self.read_chunked()


def main():
    import signal

    is_quit = threading.Event()

    def signal_handler(sig, num):
        is_quit.set()
        print('Quit')

    signal.signal(signal.SIGINT, signal_handler)

    with Mic() as mic:
        for chunk in mic:
            pass

            if is_quit.is_set():
                break

if __name__ == '__main__':
    main()
