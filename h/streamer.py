import json
import logging
import threading

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection

log = logging.getLogger(__name__)

class StreamerConnection(SockJSConnection):
    connections = set()

    def on_open(self, info):
        log.info('open')
	log.info(str(info))
	self.connections.add(self)

    def on_message(self, msg):
        log.info('message')
        self.send(msg)

    def on_close(self):
        log.info('close')
	self.connections.remove(self)

def _init_streamer():
    StreamerRouter = SockJSRouter(StreamerConnection, '/streamer')

    app = web.Application(StreamerRouter.urls)
    app.listen(5001)
    ioloop.IOLoop.instance().start()

def init_streamer():
    t = threading.Thread(target=_init_streamer)
    t.daemon = True
    t.start()


def after_save(annotation):
    log.info('after save for: ')
    log.info(str(annotation))
    for connection in StreamerConnection.connections :
    	connection.send(json.dumps(annotation, indent=2))


