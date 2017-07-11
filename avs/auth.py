
import sys
import tornado.httpserver
import tornado.ioloop
import tornado.web
import json
import uuid
import requests
import datetime

from avs.config import DEFAULT_CONFIG_FILE


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, config, output):
        self.config = config
        self.output = output

        if ('host_url' in self.config) and self.config['host_url'] == 'dueros-h2.baidu.com':
            self.token_url = 'https://openapi.baidu.com/oauth/2.0/token'
            self.oauth_url = 'https://openapi.baidu.com/oauth/2.0/authorize'
            self.scope = 'basic'
        else:
            self.token_url = 'https://api.amazon.com/auth/o2/token'
            self.oauth_url = 'https://www.amazon.com/ap/oa'
            self.scope = 'alexa:all'

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

            r = requests.post(self.token_url, data=payload)
            config = r.json()
            self.config['refresh_token'] = config['refresh_token']

            if 'access_token' in config:
                date_format = "%a %b %d %H:%M:%S %Y"
                expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
                self.config['expiry'] = expiry_time.strftime(date_format)
                self.config['access_token'] = config['access_token']

            print('save the configuration to {}'.format(self.output))
            print(json.dumps(self.config, indent=4))
            with open(self.output, 'w') as f:
                json.dump(self.config, f, indent=4)

            self.write('Succeed to login Amazon Alexa Voice Service')
            self.finish()
            tornado.ioloop.IOLoop.instance().stop()
        else:
            if 'refresh_token' not in self.config:
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
                    "scope": self.scope,
                    "scope_data": scope_data,
                    "response_type": "code",
                    "redirect_uri": redirect_uri
                }

                req = requests.Request('GET', self.oauth_url, params=payload)
                p = req.prepare()
                self.redirect(p.url)
            else:
                self.write('Already authorized')
                self.finish()
                tornado.ioloop.IOLoop.instance().stop()


def login(config, output):
    application = tornado.web.Application([(r".*", MainHandler, dict(config=config, output=output))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()


def setup(config, output):
    try:
        import webbrowser
    except ImportError:
        print('Go to http://{your device IP}:3000 to start')
        login(config, output)
        return

    import threading
    t = threading.Thread(target=login, args=(config, output))
    t.start()
    print("A web page should is opened. If not, go to http://127.0.0.1:3000 to start")
    webbrowser.open('http://127.0.0.1:3000')
    t.join()


def main():
    if len(sys.argv) < 2:
        print('Usage: {} config.json [output.json]'.format(sys.argv[0]))
        sys.exit(1)

    if len(sys.argv) < 3:
        output = DEFAULT_CONFIG_FILE
    else:
        output = sys.argv[2]

    with open(sys.argv[1], 'r') as f:
        config = json.load(f)
        require_keys = ['product_id', 'client_id', 'client_secret']
        for key in require_keys:
            if not ((key in config) and config[key]):
                print('You should include "{}" in {}'.format(key, sys.argv[1]))
                sys.exit(2)

        if ('refresh_token' in config) and config['refresh_token']:
            print('Already authorized')
        else:
            setup(config, output)


if __name__ == '__main__':
    main()

