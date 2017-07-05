import os
import tornado.httpserver
import tornado.ioloop
import tornado.web
import json
import uuid
import requests


configuration_file = os.path.join(os.path.expanduser('~'), '.alexa.json')


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.config = config

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
            url = "https://api.amazon.com/auth/o2/token"
            r = requests.post(url, data=payload)
            config = r.json()
            self.config['refresh_token'] = config['refresh_token']
            print('save the configuration to {}'.format(configuration_file))
            print(json.dumps(self.config, indent=4))
            with open(configuration_file, 'w') as f:
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
                url = "https://www.amazon.com/ap/oa"
                payload = {
                    "client_id": self.config['client_id'],
                    "scope": "alexa:all",
                    "scope_data": scope_data,
                    "response_type": "code",
                    "redirect_uri": redirect_uri
                }
                req = requests.Request('GET', url, params=payload)
                p = req.prepare()
                self.redirect(p.url)
            else:
                self.write('Already authorized')
                self.finish()
                tornado.ioloop.IOLoop.instance().stop()


def login(config):
    print("Go to http://127.0.0.1:3000 to sign up or login Amazon Alexa Voice Service")
    application = tornado.web.Application([(r".*", MainHandler, dict(config=config))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()


def setup(config):
    import threading
    import webbrowser

    t = threading.Thread(target=login, args=(config,))
    t.start()
    webbrowser.open('http://127.0.0.1:3000')
    t.join()


def main():
    import sys

    if len(sys.argv) < 2:
        print('Usage: {} config.json'.format(sys.argv[0]))
        print('\nWhen you succeed to login Amazon Alexa Voice Service, it will save the configuration to {}'.format(
            configuration_file))
        sys.exit(1)

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
            setup(config)


if __name__ == '__main__':
    main()

