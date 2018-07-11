import datetime
import json
import os
import time
import uuid

import click
import requests
import tornado.httpserver
import tornado.ioloop
import tornado.web

import avs.config


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, config, output):
        self.config = config
        self.output = output

    @tornado.web.asynchronous
    def get(self):
        redirect_uri = self.request.protocol + "://" + self.request.host + "/authresponse"
        if self.request.path == '/authresponse':
            code = self.get_argument("code")
            payload = {
                "client_id": self.config['client_id'],
                "client_secret": self.config['client_secret'],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }

            if self.config['host_url'] == 'dueros-h2.baidu.com':
                token_url = 'https://openapi.baidu.com/oauth/2.0/token'
                message = 'Succeed to login Baidu DuerOS'
            else:
                token_url = 'https://api.amazon.com/auth/o2/token'
                message = 'Succeed to login Amazon Alexa Voice Service'

            r = requests.post(token_url, data=payload)
            config = r.json()
            self.config['refresh_token'] = config['refresh_token']

            if 'access_token' in config:
                date_format = "%a %b %d %H:%M:%S %Y"
                expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
                self.config['expiry'] = expiry_time.strftime(date_format)
                self.config['access_token'] = config['access_token']

            print(json.dumps(self.config, indent=4))
            avs.config.save(self.config, configfile=self.output)

            self.write(message)
            self.finish()
            tornado.ioloop.IOLoop.instance().stop()
        elif self.request.path == '/alexa':
            self.alexa_oauth()
        elif self.request.path == '/dueros':
            self.dueros_oauth()
        elif self.request.path == '/':
            index_html = os.path.realpath(os.path.join(os.path.dirname(__file__), 'resources/web/index.html'))
            with open(index_html) as f:
                self.write(f.read())
                self.finish()

    def alexa_oauth(self):
        if 'client_secret' not in self.config:
            self.config.update(avs.config.alexa())
        if 'dueros-device-id' in self.config:
            del self.config['dueros-device-id']
            self.config.update(avs.config.alexa())

        oauth_url = 'https://www.amazon.com/ap/oa'
        redirect_uri = self.request.protocol + "://" + self.request.host + "/authresponse"

        scope_data = json.dumps({
            "alexa:all": {
                "productID": self.config['product_id'],
                "productInstanceAttributes": {
                    "deviceSerialNumber": uuid.uuid4().hex
                }
            }
        })
        payload = {
            "client_id": self.config['client_id'],
            "scope": "alexa:all",
            "scope_data": scope_data,
            "response_type": "code",
            "redirect_uri": redirect_uri
        }

        req = requests.Request('GET', oauth_url, params=payload)
        p = req.prepare()
        self.redirect(p.url)

    def dueros_oauth(self):
        if 'client_secret' not in self.config:
            self.config.update(avs.config.dueros())
        
        oauth_url = 'https://openapi.baidu.com/oauth/2.0/authorize'
        redirect_uri = self.request.protocol + "://" + self.request.host + "/authresponse"

        payload = {
            "client_id": self.config["client_id"],
            "scope": "basic",
            "response_type": "code",
            "redirect_uri": redirect_uri
        }

        req = requests.Request('GET', oauth_url, params=payload)
        p = req.prepare()
        self.redirect(p.url)


def open_webbrowser():
    try:
        import webbrowser
    except ImportError:
        print('Go to http://{your device IP}:3000 to start')
        return

    time.sleep(0.1)
    print("A web page should is opened. If not, go to http://127.0.0.1:3000 to start")
    webbrowser.open('http://127.0.0.1:3000')


def auth(config, output):
    import threading
    threading.Thread(target=open_webbrowser).start()

    config = avs.config.load(config) if config else {}

    application = tornado.web.Application([(r".*", MainHandler, dict(config=config, output=output))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()

@click.command()
@click.option('--config', '-c', help='configuration json file with product_id, client_id and client_secret')
@click.option('--output', '-o', default=avs.config.DEFAULT_CONFIG_FILE, help='output json file with refresh token')
def main(config, output):
    auth(config, output)


if __name__ == '__main__':
    main()
