# -*- coding: utf-8 -*-

import xbmc

try:
    import requests
    existe_script = True
except:
    existe_script = False

from threading import Thread

from core import scrapertools
from platformcode import logger, config, platformtools


PY3 = False
if config.get_setting('PY3', default=''): PY3 = True

if PY3:
    from http.server import BaseHTTPRequestHandler, HTTPServer
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


domain = ""


class HandleRequests(BaseHTTPRequestHandler):
    def do_GET(self):
        if not existe_script:
            platformtools.dialog_notification(config.__addon_name, '[B][COLOR red]Falta script.module.requests[/COLOR][/B]')
        else:
            url = '%s%s' % (domain, self.path)

            if 'redirect.php' in url: url = requests.get(url, allow_redirects=False).headers["location"]

            data = requests.get(url, stream=True).raw

            chunk = data.read()[4:]
            self.wfile.write(chunk)
            self.wfile.close()


def run():
    server_address = ('', 8781)
    httpd = HTTPServer(server_address, HandleRequests)

    monitor = xbmc.Monitor()
    httpd.timeout = 15

    while not monitor.abortRequested():
        try:
            httpd.handle_request()
        except Exception as e:
            logger.error(e)

    httpd.socket.close()


def start(base_url):
    logger.info()

    global domain

    domain = base_url

    Thread(target=run).start()
